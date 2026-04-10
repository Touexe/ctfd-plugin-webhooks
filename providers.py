from .constants import EVENT_LABELS, PROVIDER_DISCORD, PROVIDER_GENERIC_JSON
from .message_templates import render_json_template


EVENT_COLORS = {
    "first_blood": 0xD4A017,
    "challenge_solved": 0x2E8B57,
    "failed_flag": 0xC0392B,
    "new_registration": 0x1F6FB2,
    "challenge_partial": 0xCC7A00,
    "rate_limited": 0x6C757D,
}


def build_provider_payload(provider, event_payload, payload_template=None):
    if str(payload_template or "").strip():
        return render_json_template(payload_template, event_payload)
    if provider == PROVIDER_DISCORD:
        return build_discord_payload(event_payload)
    if provider == PROVIDER_GENERIC_JSON:
        return event_payload
    raise ValueError(f"Unsupported provider: {provider}")


def build_discord_payload(event_payload):
    title = render_event_title(event_payload)
    embed = {
        "title": title,
        "description": render_event_summary(event_payload),
        "timestamp": event_payload["occurred_at"],
        "fields": render_event_fields(event_payload)[:25],
        "color": EVENT_COLORS.get(event_payload["event"], 0x1F6FB2),
        "footer": {"text": event_payload["ctfd"]["name"]},
    }

    links = event_payload.get("links") or {}
    if links.get("primary"):
        embed["url"] = links["primary"]

    return {"embeds": [embed]}


def render_event_title(event_payload):
    event_type = event_payload["event"]
    challenge = event_payload.get("challenge")
    user = event_payload.get("user")

    if event_type == "first_blood" and challenge:
        return f"First Blood: {challenge['name']}"
    if event_type == "challenge_solved" and challenge:
        return f"Solve Recorded: {challenge['name']}"
    if event_type == "failed_flag" and challenge:
        return f"Incorrect Submission: {challenge['name']}"
    if event_type == "challenge_partial" and challenge:
        return f"Partial Solve: {challenge['name']}"
    if event_type == "rate_limited" and challenge:
        return f"Rate Limited: {challenge['name']}"
    if event_type == "new_registration" and user:
        return f"New Registration: {user['name']}"
    return EVENT_LABELS.get(event_type, event_type)


def render_event_summary(event_payload):
    return event_payload.get("message") or EVENT_LABELS.get(
        event_payload["event"], event_payload["event"]
    )


def render_event_fields(event_payload):
    fields = []
    challenge = event_payload.get("challenge")
    user = event_payload.get("user")
    team = event_payload.get("team")
    links = event_payload.get("links") or {}
    submission = event_payload.get("submission") or {}

    if challenge:
        fields.append({"name": "Challenge", "value": challenge["name"], "inline": True})
        if challenge.get("category"):
            fields.append({"name": "Category", "value": challenge["category"], "inline": True})
        if challenge.get("value") is not None:
            fields.append({"name": "Value", "value": str(challenge["value"]), "inline": True})

    if team:
        fields.append({"name": "Team", "value": team["name"], "inline": True})
    if user:
        fields.append({"name": "User", "value": user["name"], "inline": True})
    if event_payload.get("event") == "failed_flag" and submission.get("provided"):
        fields.append(
            {
                "name": "Attempted submission",
                "value": submission["provided"],
                "inline": False,
            }
        )

    if event_payload.get("visibility") == "private":
        if links.get("challenge_admin"):
            fields.append({"name": "Admin challenge", "value": links["challenge_admin"], "inline": False})
        if links.get("team_admin"):
            fields.append({"name": "Admin team", "value": links["team_admin"], "inline": False})
        if links.get("user_admin"):
            fields.append({"name": "Admin user", "value": links["user_admin"], "inline": False})
        if links.get("plugin_admin"):
            fields.append({"name": "Plugin", "value": links["plugin_admin"], "inline": False})

    return fields