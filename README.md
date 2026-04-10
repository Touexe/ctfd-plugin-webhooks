# ctfd-plugin-webhooks

Standalone CTFd plugin that lets administrators register outbound webhooks for challenge and registration activity without modifying core CTFd.

## Features

- Standalone admin page at `/admin/plugins/ctfd-plugin-webhooks`
- Multiple webhook endpoints with create, edit, delete, pause, and resume actions
- Public/private webhook visibility toggle
- Multi-select hook subscriptions per webhook
- Editable per-event message templates from the admin panel
- Optional per-event JSON payload overrides for custom Discord embeds or arbitrary webhook bodies
- Provider support for:
	- `discord`
	- `generic_json`
- Hook support for:
	- `first_blood`
	- `challenge_solved`
	- `failed_flag`
	- `new_registration`
	- `challenge_partial`
	- `rate_limited`
- Best-effort delivery with last-attempt / last-success / last-error status in the admin UI

## Compatibility

Challenge activity hooks are emitted from the standard CTFd persistence layer by observing `Solves`, `Fails`, `Partials`, and `Ratelimiteds`. That means challenge events continue to work for plugin-provided challenge types as long as they integrate with CTFd by recording normal submission rows.

`new_registration` is scoped to the public registration flow in CTFd, so admin-created users and import paths are ignored.

## Admin UI

Open the plugin from the admin `Plugins` dropdown or directly at:

```text
/admin/plugins/ctfd-plugin-webhooks
```

Each webhook stores:

- Optional display name
- Provider type
- Target URL
- Public/private visibility
- One or more subscribed hooks
- A message template for each selected hook type
- An optional JSON payload override for each selected hook type
- Pause/resume state
- Last delivery status

## Payloads

### Generic JSON

The generic JSON provider sends the plugin's canonical payload shape. Example fields:

```json
{
	"event": "challenge_solved",
	"occurred_at": "2026-04-10T19:42:00Z",
	"ctfd": {
		"name": "Example CTF",
		"user_mode": "teams"
	},
	"account": {
		"mode": "teams",
		"id": 4,
		"name": "blue-team"
	},
	"user": {
		"id": 7,
		"name": "alice",
		"email": "alice@example.com",
		"affiliation": null,
		"country": null
	},
	"team": {
		"id": 4,
		"name": "blue-team",
		"email": "team@example.com",
		"affiliation": null,
		"country": null
	},
	"challenge": {
		"id": 12,
		"name": "Warmup",
		"category": "web",
		"type": "standard",
		"value": 100,
		"state": "visible"
	},
	"submission": {
		"id": 91,
		"status": "correct",
		"date": "2026-04-10T19:42:00Z"
	}
}
```

Raw flag submissions and IP addresses are intentionally excluded.

For public webhooks, account payloads stay minimal. For private webhooks, the payload also includes extended account details and admin-panel links for the related challenge, user, team, and plugin page when available.

## Templates

Each selected hook can define its own message template in the admin modal.

Templates use Jinja-style placeholders. Common values include:

- `{{ event }}`
- `{{ event_label }}`
- `{{ actor }}`
- `{{ ctfd.name }}`
- `{{ challenge.name }}`
- `{{ challenge.category }}`
- `{{ challenge.type }}`
- `{{ challenge.value }}`
- `{{ user.name }}`
- `{{ team.name }}`
- `{{ submission.status }}`
- `{{ submission.provided }}`
- `{{ links.primary }}`

When you need full control over the request body, set a JSON payload override for the event. The rendered output must be valid JSON and replaces the provider's default payload entirely. This is the path to custom Discord embeds.

Use `|tojson` when inserting dynamic values into JSON templates. Example:

```json
{
	"embeds": [
		{
			"title": {{ challenge.name|tojson }},
			"description": {{ message|tojson }},
			"fields": [
				{
					"name": "Category",
					"value": {{ challenge.category|tojson }}
				}
			]
		}
	]
}
```

The rendered result is stored in the outgoing payload as `message`. Discord uses that value as the embed body, and `generic_json` includes it in the canonical JSON payload.

### Discord

The Discord provider sends a single embed with a cleaner event title, event-specific summary text, color coding, and selected context fields. Private webhooks also include direct admin URLs in the embed so moderators can jump straight into CTFd.

## Delivery semantics

- Delivery is synchronous and best-effort.
- The original CTFd request is never failed because of a webhook delivery error.
- No retries or background queueing are implemented in this version.


## Tests

Run the plugin-local tests from the repo root:

```bash
pytest tests
```
