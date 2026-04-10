import json

from jinja2 import ChainableUndefined, Undefined
from jinja2.sandbox import SandboxedEnvironment

from .constants import DEFAULT_EVENT_TEMPLATES

_ENV = SandboxedEnvironment(
    autoescape=False,
    trim_blocks=True,
    lstrip_blocks=True,
    undefined=ChainableUndefined,
)
_ENV.filters["tojson"] = lambda value: json.dumps(
    None if isinstance(value, Undefined) else value,
    ensure_ascii=False,
)


def render_event_message(event_type, event_payload, template=None):
    message_template = (template or "").strip() or DEFAULT_EVENT_TEMPLATES[event_type]
    rendered = _ENV.from_string(message_template).render(**event_payload)
    return " ".join(rendered.split())


def render_json_template(template, template_context):
    payload_template = str(template or "").strip()
    if not payload_template:
        raise ValueError("Payload template cannot be empty")

    rendered = _ENV.from_string(payload_template).render(**template_context).strip()
    if not rendered:
        raise ValueError("Payload template rendered an empty response body")

    try:
        parsed = json.loads(rendered)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Payload template rendered invalid JSON: {exc.msg}"
        ) from exc

    if not isinstance(parsed, (dict, list)):
        raise ValueError("Payload template must render a JSON object or array")

    return parsed


def validate_json_template(template):
    render_json_template(template, _validation_payload())


def _validation_payload():
    return {
        "event": "challenge_solved",
        "event_label": "Challenge solved",
        "occurred_at": "2026-04-10T20:00:00Z",
        "visibility": "private",
        "actor": "blue-team / alice",
        "message": "blue-team / alice solved Warmup.",
        "ctfd": {
            "name": "Example CTF",
            "user_mode": "teams",
        },
        "account": {
            "mode": "teams",
            "id": 2,
            "name": "blue-team",
        },
        "user": {
            "id": 7,
            "name": "alice",
            "email": "alice@example.com",
            "affiliation": None,
            "country": None,
        },
        "team": {
            "id": 2,
            "name": "blue-team",
            "email": "team@example.com",
            "affiliation": None,
            "country": None,
        },
        "challenge": {
            "id": 10,
            "name": "Warmup",
            "category": "web",
            "type": "standard",
            "value": 100,
            "state": "visible",
        },
        "submission": {
            "id": 19,
            "status": "correct",
            "date": "2026-04-10T20:00:00Z",
            "provided": "flag{sample}",
        },
        "links": {
            "primary": "https://ctfd.local/admin/challenges/10",
            "challenge_admin": "https://ctfd.local/admin/challenges/10",
            "team_admin": "https://ctfd.local/admin/teams/2",
            "user_admin": "https://ctfd.local/admin/users/7",
            "plugin_admin": "https://ctfd.local/admin/plugins/ctfd-plugin-webhooks",
        },
    }