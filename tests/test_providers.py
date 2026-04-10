import importlib


constants = importlib.import_module("ctfd_plugin_webhooks.constants")
providers = importlib.import_module("ctfd_plugin_webhooks.providers")


def _sample_payload():
    return {
        "event": constants.EVENT_CHALLENGE_SOLVED,
        "occurred_at": "2026-04-10T20:00:00Z",
        "visibility": "private",
        "message": "blue-team / alice solved Warmup.",
        "ctfd": {"name": "Example CTF", "user_mode": "teams"},
        "account": {"mode": "teams", "id": 2, "name": "blue-team"},
        "user": {"id": 7, "name": "alice", "email": "alice@example.com", "affiliation": None, "country": None},
        "team": {"id": 2, "name": "blue-team", "email": "team@example.com", "affiliation": None, "country": None},
        "challenge": {"id": 10, "name": "Warmup", "category": "web", "type": "standard", "value": 100, "state": "visible"},
        "submission": {"id": 19, "status": "correct", "date": "2026-04-10T20:00:00Z"},
        "links": {"primary": "https://ctfd.local/admin/challenges/10", "challenge_admin": "https://ctfd.local/admin/challenges/10"},
    }


def test_generic_json_provider_returns_payload_unchanged():
    payload = _sample_payload()

    assert (
        providers.build_provider_payload(constants.PROVIDER_GENERIC_JSON, payload)
        == payload
    )


def test_discord_provider_builds_embed_payload():
    discord_payload = providers.build_provider_payload(
        constants.PROVIDER_DISCORD,
        _sample_payload(),
    )

    assert "content" not in discord_payload
    assert len(discord_payload["embeds"]) == 1
    assert discord_payload["embeds"][0]["title"] == "Solve Recorded: Warmup"
    assert discord_payload["embeds"][0]["url"] == "https://ctfd.local/admin/challenges/10"
    assert discord_payload["embeds"][0]["description"] == "blue-team / alice solved Warmup."


def test_discord_provider_formats_first_blood_prettily():
    payload = _sample_payload()
    payload["event"] = constants.EVENT_FIRST_BLOOD
    payload["message"] = "blue-team / alice claimed first blood on Warmup for 100 points."

    discord_payload = providers.build_provider_payload(
        constants.PROVIDER_DISCORD,
        payload,
    )

    assert discord_payload["embeds"][0]["title"] == "First Blood: Warmup"
    assert (
        discord_payload["embeds"][0]["description"]
        == "blue-team / alice claimed first blood on Warmup for 100 points."
    )


def test_discord_provider_includes_attempted_submission_for_failed_flags():
    payload = _sample_payload()
    payload["event"] = constants.EVENT_FAILED_FLAG
    payload["message"] = "blue-team / alice submitted an incorrect flag on Warmup: flag{wrong-one}."
    payload["submission"] = {
        "id": 25,
        "status": "incorrect",
        "date": "2026-04-10T20:00:00Z",
        "provided": "flag{wrong-one}",
    }

    discord_payload = providers.build_provider_payload(
        constants.PROVIDER_DISCORD,
        payload,
    )

    fields = discord_payload["embeds"][0]["fields"]
    attempted_field = next(field for field in fields if field["name"] == "Attempted submission")
    assert attempted_field["value"] == "flag{wrong-one}"


def test_provider_payload_template_can_override_discord_body():
    payload = _sample_payload()

    discord_payload = providers.build_provider_payload(
        constants.PROVIDER_DISCORD,
        payload,
        payload_template='{"embeds": [{"title": {{ challenge.category|tojson }}, "description": {{ message|tojson }}}]}',
    )

    assert discord_payload["embeds"][0]["title"] == "web"
    assert discord_payload["embeds"][0]["description"] == "blue-team / alice solved Warmup."