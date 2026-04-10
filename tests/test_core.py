import importlib


core = importlib.import_module("ctfd_plugin_webhooks.core")
constants = importlib.import_module("ctfd_plugin_webhooks.constants")


def test_validate_webhook_payload_accepts_multiple_event_types():
    payload_template = (
        '{"embeds": [{"title": {{ challenge.name|tojson }}, '
        '"description": {{ message|tojson }}, '
        '"category": {{ challenge.category|tojson }}}]}'
    )
    cleaned, errors = core.validate_webhook_payload(
        {
            "name": "Discord webhook",
            "provider": constants.PROVIDER_DISCORD,
            "target_url": "https://discord.example/webhook",
            "event_templates": {
                constants.EVENT_CHALLENGE_SOLVED: "{{ actor }} solved {{ challenge.name }}.",
                constants.EVENT_FAILED_FLAG: "{{ actor }} failed {{ challenge.name }}.",
            },
            "event_payload_templates": {
                constants.EVENT_CHALLENGE_SOLVED: payload_template,
            },
            "event_types": [
                constants.EVENT_CHALLENGE_SOLVED,
                constants.EVENT_FAILED_FLAG,
                constants.EVENT_CHALLENGE_SOLVED,
            ],
        }
    )

    assert errors == {}
    assert cleaned["provider"] == constants.PROVIDER_DISCORD
    assert cleaned["is_private"] is False
    assert cleaned["event_types"] == [
        constants.EVENT_CHALLENGE_SOLVED,
        constants.EVENT_FAILED_FLAG,
    ]
    assert cleaned["event_templates"][constants.EVENT_FAILED_FLAG] == "{{ actor }} failed {{ challenge.name }}."
    assert (
        cleaned["event_payload_templates"][constants.EVENT_CHALLENGE_SOLVED]
        == payload_template
    )


def test_validate_webhook_payload_requires_at_least_one_event_type():
    _cleaned, errors = core.validate_webhook_payload(
        {
            "provider": constants.PROVIDER_GENERIC_JSON,
            "target_url": "https://example.com/webhook",
            "event_types": [],
        }
    )

    assert "event_types" in errors


def test_validate_webhook_payload_rejects_invalid_provider():
    _cleaned, errors = core.validate_webhook_payload(
        {
            "provider": "slack",
            "target_url": "https://example.com/webhook",
            "event_types": [constants.EVENT_NEW_REGISTRATION],
        }
    )

    assert "provider" in errors


def test_validate_webhook_payload_accepts_private_flag():
    cleaned, errors = core.validate_webhook_payload(
        {
            "provider": constants.PROVIDER_GENERIC_JSON,
            "target_url": "https://example.com/webhook",
            "is_private": True,
            "event_types": [constants.EVENT_NEW_REGISTRATION],
        }
    )

    assert errors == {}
    assert cleaned["is_private"] is True


def test_validate_webhook_payload_rejects_template_for_unselected_event():
    _cleaned, errors = core.validate_webhook_payload(
        {
            "provider": constants.PROVIDER_GENERIC_JSON,
            "target_url": "https://example.com/webhook",
            "event_types": [constants.EVENT_NEW_REGISTRATION],
            "event_templates": {
                constants.EVENT_FAILED_FLAG: "{{ actor }} failed {{ challenge.name }}.",
            },
        }
    )

    assert "event_templates" in errors


def test_validate_webhook_payload_rejects_invalid_payload_template_json():
    _cleaned, errors = core.validate_webhook_payload(
        {
            "provider": constants.PROVIDER_GENERIC_JSON,
            "target_url": "https://example.com/webhook",
            "event_types": [constants.EVENT_CHALLENGE_SOLVED],
            "event_payload_templates": {
                constants.EVENT_CHALLENGE_SOLVED: '{"embeds": [}',
            },
        }
    )

    assert "event_payload_templates" in errors