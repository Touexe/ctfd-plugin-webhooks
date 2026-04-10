from flask import Blueprint, jsonify, request

from CTFd.models import db
from CTFd.utils.decorators import admins_only

from .core import get_plugin_meta, validate_webhook_payload
from .models import WebhookEndpoint, WebhookSubscription

webhooks_api = Blueprint(
    "ctfd_plugin_webhooks_api",
    __name__,
    url_prefix="/plugins/ctfd-plugin-webhooks/api/v1",
)


def register_api(app):
    app.register_blueprint(webhooks_api)


@webhooks_api.route("/meta", methods=["GET"])
@admins_only
def meta():
    return jsonify({"success": True, "data": get_plugin_meta()})


@webhooks_api.route("/webhooks", methods=["GET", "POST"])
@admins_only
def webhooks_list():
    if request.method == "GET":
        webhooks = (
            WebhookEndpoint.query.order_by(WebhookEndpoint.created_at.desc(), WebhookEndpoint.id.desc()).all()
        )
        return jsonify(
            {"success": True, "data": [webhook.to_dict() for webhook in webhooks]}
        )

    payload = _get_json_payload()
    cleaned, errors = validate_webhook_payload(payload, partial=False)
    if errors:
        return jsonify({"success": False, "errors": errors}), 400

    webhook = WebhookEndpoint(
        name=cleaned.get("name"),
        provider=cleaned["provider"],
        target_url=cleaned["target_url"],
        is_private=cleaned["is_private"],
    )
    _replace_subscriptions(
        webhook,
        cleaned["event_types"],
        cleaned.get("event_templates", {}),
        cleaned.get("event_payload_templates", {}),
    )

    db.session.add(webhook)
    db.session.commit()

    return jsonify({"success": True, "data": webhook.to_dict()})


@webhooks_api.route("/webhooks/<int:webhook_id>", methods=["GET", "PATCH", "DELETE"])
@admins_only
def webhook_detail(webhook_id):
    webhook = WebhookEndpoint.query.filter_by(id=webhook_id).first_or_404()

    if request.method == "GET":
        return jsonify({"success": True, "data": webhook.to_dict()})

    if request.method == "DELETE":
        db.session.delete(webhook)
        db.session.commit()
        return jsonify({"success": True})

    payload = _get_json_payload()
    cleaned, errors = validate_webhook_payload(payload, partial=True)
    if errors:
        return jsonify({"success": False, "errors": errors}), 400

    if "name" in cleaned:
        webhook.name = cleaned["name"]
    if "provider" in cleaned:
        webhook.provider = cleaned["provider"]
    if "target_url" in cleaned:
        webhook.target_url = cleaned["target_url"]
    if "is_private" in cleaned:
        webhook.is_private = cleaned["is_private"]
    if (
        "event_types" in cleaned
        or "event_templates" in cleaned
        or "event_payload_templates" in cleaned
    ):
        event_types = cleaned.get(
            "event_types", [sub.event_type for sub in webhook.subscriptions]
        )
        event_templates = {sub.event_type: sub.template for sub in webhook.subscriptions}
        event_templates.update(cleaned.get("event_templates", {}))
        event_payload_templates = {
            sub.event_type: sub.payload_template for sub in webhook.subscriptions
        }
        event_payload_templates.update(cleaned.get("event_payload_templates", {}))
        _replace_subscriptions(
            webhook,
            event_types,
            event_templates,
            event_payload_templates,
        )

    db.session.commit()

    return jsonify({"success": True, "data": webhook.to_dict()})


@webhooks_api.route("/webhooks/<int:webhook_id>/pause", methods=["POST"])
@admins_only
def pause_webhook(webhook_id):
    webhook = WebhookEndpoint.query.filter_by(id=webhook_id).first_or_404()
    webhook.is_paused = True
    db.session.commit()
    return jsonify({"success": True, "data": webhook.to_dict()})


@webhooks_api.route("/webhooks/<int:webhook_id>/resume", methods=["POST"])
@admins_only
def resume_webhook(webhook_id):
    webhook = WebhookEndpoint.query.filter_by(id=webhook_id).first_or_404()
    webhook.is_paused = False
    db.session.commit()
    return jsonify({"success": True, "data": webhook.to_dict()})


def _replace_subscriptions(
    webhook,
    event_types,
    event_templates,
    event_payload_templates,
):
    existing_by_type = {sub.event_type: sub for sub in list(webhook.subscriptions)}
    selected_types = set(event_types)

    for subscription in list(webhook.subscriptions):
        if subscription.event_type not in selected_types:
            webhook.subscriptions.remove(subscription)

    for event_type in event_types:
        subscription = existing_by_type.get(event_type)
        if subscription is None:
            subscription = WebhookSubscription(event_type=event_type)
            webhook.subscriptions.append(subscription)

        subscription.template = event_templates.get(event_type)
        subscription.payload_template = event_payload_templates.get(event_type)


def _get_json_payload():
    payload = request.get_json(silent=True)
    if isinstance(payload, dict):
        return payload
    return {}