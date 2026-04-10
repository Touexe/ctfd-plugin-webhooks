from CTFd.utils.validators import validate_url

from .constants import (
    DEFAULT_EVENT_TEMPLATES,
    EVENT_OPTIONS,
    PROVIDER_OPTIONS,
    TEMPLATE_VARIABLE_HINTS,
    VALID_EVENT_TYPES,
    VALID_PROVIDERS,
)
from .message_templates import validate_json_template


def get_plugin_meta():
    return {
        "providers": PROVIDER_OPTIONS,
        "events": EVENT_OPTIONS,
        "template_variable_hints": TEMPLATE_VARIABLE_HINTS,
    }


def validate_webhook_payload(payload, partial=False):
    cleaned = {}
    errors = {}

    name_present = "name" in payload
    if name_present or not partial:
        name = str(payload.get("name", "") or "").strip()
        if len(name) > 128:
            errors.setdefault("name", []).append("Name must be 128 characters or fewer")
        cleaned["name"] = name or None

    provider_present = "provider" in payload
    if provider_present or not partial:
        provider = str(payload.get("provider", "") or "").strip()
        if not provider:
            errors.setdefault("provider", []).append("Webhook type is required")
        elif provider not in VALID_PROVIDERS:
            errors.setdefault("provider", []).append("Webhook type is invalid")
        else:
            cleaned["provider"] = provider

    target_url_present = "target_url" in payload
    if target_url_present or not partial:
        target_url = str(payload.get("target_url", "") or "").strip()
        if not target_url:
            errors.setdefault("target_url", []).append("Target URL is required")
        elif not validate_url(target_url):
            errors.setdefault("target_url", []).append(
                "Target URL must start with http or https"
            )
        else:
            cleaned["target_url"] = target_url

    private_present = "is_private" in payload
    if private_present or not partial:
        raw_private_value = payload.get("is_private", False)
        private_value, private_error = _parse_bool(raw_private_value)
        if private_error:
            errors.setdefault("is_private", []).append(private_error)
        else:
            cleaned["is_private"] = private_value

    event_types_present = "event_types" in payload
    if event_types_present or not partial:
        raw_event_types = payload.get("event_types")
        if not isinstance(raw_event_types, list):
            errors.setdefault("event_types", []).append(
                "Hook types must be provided as a list"
            )
        else:
            event_types = normalize_event_types(raw_event_types)
            if not event_types:
                errors.setdefault("event_types", []).append(
                    "Select at least one hook type"
                )
            else:
                invalid_event_types = [
                    event_type
                    for event_type in event_types
                    if event_type not in VALID_EVENT_TYPES
                ]
                if invalid_event_types:
                    errors.setdefault("event_types", []).append(
                        "One or more hook types are invalid"
                    )
                else:
                    cleaned["event_types"] = event_types

    templates_present = "event_templates" in payload
    if templates_present or not partial:
        raw_event_templates = payload.get("event_templates", {})
        selected_event_types = cleaned.get("event_types")
        if selected_event_types is None and isinstance(payload.get("event_types"), list):
            selected_event_types = normalize_event_types(payload.get("event_types", []))
        templates, template_errors = normalize_event_templates(
            raw_event_templates,
            selected_event_types=selected_event_types,
        )
        if template_errors:
            for key, messages in template_errors.items():
                errors.setdefault(key, []).extend(messages)
        else:
            cleaned["event_templates"] = templates

    payload_templates_present = "event_payload_templates" in payload
    if payload_templates_present or not partial:
        raw_event_payload_templates = payload.get("event_payload_templates", {})
        selected_event_types = cleaned.get("event_types")
        if selected_event_types is None and isinstance(payload.get("event_types"), list):
            selected_event_types = normalize_event_types(payload.get("event_types", []))
        payload_templates, payload_template_errors = normalize_event_payload_templates(
            raw_event_payload_templates,
            selected_event_types=selected_event_types,
        )
        if payload_template_errors:
            for key, messages in payload_template_errors.items():
                errors.setdefault(key, []).extend(messages)
        else:
            cleaned["event_payload_templates"] = payload_templates

    return cleaned, errors


def normalize_event_types(raw_event_types):
    normalized = []
    seen = set()
    for event_type in raw_event_types:
        normalized_event_type = str(event_type or "").strip()
        if not normalized_event_type or normalized_event_type in seen:
            continue
        seen.add(normalized_event_type)
        normalized.append(normalized_event_type)
    return normalized


def normalize_event_templates(raw_event_templates, selected_event_types=None):
    if not isinstance(raw_event_templates, dict):
        return None, {"event_templates": ["Templates must be provided as an object"]}

    template_errors = {}
    templates = {}
    selected = set(selected_event_types or [])

    for raw_event_type, raw_template in raw_event_templates.items():
        event_type = str(raw_event_type or "").strip()
        if not event_type:
            continue
        if event_type not in VALID_EVENT_TYPES:
            template_errors.setdefault("event_templates", []).append(
                f"Template event type '{event_type}' is invalid"
            )
            continue
        if selected and event_type not in selected:
            template_errors.setdefault("event_templates", []).append(
                f"Template event type '{event_type}' is not selected"
            )
            continue

        template = str(raw_template or "").strip()
        if not template:
            template = DEFAULT_EVENT_TEMPLATES[event_type]
        if len(template) > 5000:
            template_errors.setdefault("event_templates", []).append(
                f"Template for '{event_type}' must be 5000 characters or fewer"
            )
            continue
        templates[event_type] = template

    for event_type in selected:
        templates.setdefault(event_type, DEFAULT_EVENT_TEMPLATES[event_type])

    return templates, template_errors or None


def normalize_event_payload_templates(
    raw_event_payload_templates, selected_event_types=None
):
    if not isinstance(raw_event_payload_templates, dict):
        return None, {
            "event_payload_templates": [
                "Payload templates must be provided as an object"
            ]
        }

    template_errors = {}
    payload_templates = {}
    selected = set(selected_event_types or [])

    for raw_event_type, raw_template in raw_event_payload_templates.items():
        event_type = str(raw_event_type or "").strip()
        if not event_type:
            continue
        if event_type not in VALID_EVENT_TYPES:
            template_errors.setdefault("event_payload_templates", []).append(
                f"Payload template event type '{event_type}' is invalid"
            )
            continue
        if selected and event_type not in selected:
            template_errors.setdefault("event_payload_templates", []).append(
                f"Payload template event type '{event_type}' is not selected"
            )
            continue

        template = str(raw_template or "").strip()
        if not template:
            payload_templates[event_type] = None
            continue
        if len(template) > 20000:
            template_errors.setdefault("event_payload_templates", []).append(
                f"Payload template for '{event_type}' must be 20000 characters or fewer"
            )
            continue
        try:
            validate_json_template(template)
        except ValueError as exc:
            template_errors.setdefault("event_payload_templates", []).append(
                f"Payload template for '{event_type}' is invalid: {exc}"
            )
            continue
        payload_templates[event_type] = template

    return payload_templates, template_errors or None


def _parse_bool(value):
    if isinstance(value, bool):
        return value, None
    if value in (0, 1):
        return bool(value), None
    if isinstance(value, str):
        normalized_value = value.strip().lower()
        if normalized_value in {"true", "1", "yes", "on"}:
            return True, None
        if normalized_value in {"false", "0", "no", "off", ""}:
            return False, None
    return None, "Private webhook must be true or false"