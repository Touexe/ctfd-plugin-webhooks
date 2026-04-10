import importlib


constants = importlib.import_module("ctfd_plugin_webhooks.constants")
message_templates = importlib.import_module("ctfd_plugin_webhooks.message_templates")


def test_render_event_message_uses_default_template():
    payload = {
        "actor": "blue-team / alice",
        "challenge": {"name": "Warmup", "value": 100},
        "submission": {},
        "user": {"name": "alice"},
        "team": {"name": "blue-team"},
        "links": {},
    }

    result = message_templates.render_event_message(
        constants.EVENT_FIRST_BLOOD,
        payload,
    )

    assert result == "blue-team / alice claimed first blood on Warmup for 100 points."


def test_render_event_message_uses_custom_template():
    payload = {
        "actor": "blue-team / alice",
        "challenge": {"name": "Warmup", "value": 100},
        "submission": {"provided": "flag{wrong}"},
        "user": {"name": "alice"},
        "team": {"name": "blue-team"},
        "links": {"primary": "https://ctfd.local/admin/challenges/10"},
    }

    result = message_templates.render_event_message(
        constants.EVENT_FAILED_FLAG,
        payload,
        template="{{ actor }} tried {{ submission.provided }} on {{ challenge.name }}",
    )

    assert result == "blue-team / alice tried flag{wrong} on Warmup"


def test_render_json_template_supports_custom_payloads():
    payload = {
        "event": constants.EVENT_CHALLENGE_SOLVED,
        "event_label": "Challenge solved",
        "occurred_at": "2026-04-10T20:00:00Z",
        "visibility": "private",
        "actor": "blue-team / alice",
        "message": "blue-team / alice solved Warmup.",
        "ctfd": {"name": "Example CTF", "user_mode": "teams"},
        "account": {"mode": "teams", "id": 2, "name": "blue-team"},
        "user": {"name": "alice"},
        "team": {"name": "blue-team"},
        "challenge": {"name": "Warmup", "category": "web", "value": 100},
        "submission": {"provided": "flag{wrong}"},
        "links": {"primary": "https://ctfd.local/admin/challenges/10"},
    }

    result = message_templates.render_json_template(
        '{"embeds": [{"title": {{ challenge.name|tojson }}, "description": {{ message|tojson }}, "fields": [{"name": "Category", "value": {{ challenge.category|tojson }}}]}]}',
        payload,
    )

    assert result["embeds"][0]["title"] == "Warmup"
    assert result["embeds"][0]["fields"][0]["value"] == "web"