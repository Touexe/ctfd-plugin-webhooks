PROVIDER_DISCORD = "discord"
PROVIDER_GENERIC_JSON = "generic_json"

EVENT_CHALLENGE_SOLVED = "challenge_solved"
EVENT_FIRST_BLOOD = "first_blood"
EVENT_FAILED_FLAG = "failed_flag"
EVENT_NEW_REGISTRATION = "new_registration"
EVENT_CHALLENGE_PARTIAL = "challenge_partial"
EVENT_RATE_LIMITED = "rate_limited"

DEFAULT_EVENT_TEMPLATES = {
    EVENT_FIRST_BLOOD: "{{ actor }} claimed first blood on {{ challenge.name }}{% if challenge.value %} for {{ challenge.value }} points{% endif %}.",
    EVENT_CHALLENGE_SOLVED: "{{ actor }} solved {{ challenge.name }}.",
    EVENT_FAILED_FLAG: "{{ actor }} submitted an incorrect flag on {{ challenge.name }}{% if submission.provided %}: {{ submission.provided }}{% endif %}.",
    EVENT_NEW_REGISTRATION: "{{ user.name }} completed a new registration.",
    EVENT_CHALLENGE_PARTIAL: "{{ actor }} submitted a partial solve on {{ challenge.name }}.",
    EVENT_RATE_LIMITED: "{{ actor }} hit a submission limit on {{ challenge.name }}.",
}

TEMPLATE_VARIABLE_HINTS = [
    "{{ event }}",
    "{{ event_label }}",
    "{{ occurred_at }}",
    "{{ actor }}",
    "{{ ctfd.name }}",
    "{{ ctfd.user_mode }}",
    "{{ account.mode }}",
    "{{ account.name }}",
    "{{ challenge.name }}",
    "{{ challenge.category }}",
    "{{ challenge.type }}",
    "{{ challenge.value }}",
    "{{ user.name }}",
    "{{ user.email }}",
    "{{ team.name }}",
    "{{ team.email }}",
    "{{ submission.status }}",
    "{{ submission.provided }}",
    "{{ links.primary }}",
    "{{ message|tojson }}",
    "{{ challenge.category|tojson }}",
]

PROVIDER_OPTIONS = [
    {
        "value": PROVIDER_DISCORD,
        "label": "Discord",
        "description": "Send a Discord-friendly embed payload.",
    },
    {
        "value": PROVIDER_GENERIC_JSON,
        "label": "Generic JSON",
        "description": "Send the plugin's canonical JSON payload.",
    },
]

EVENT_OPTIONS = [
    {
        "value": EVENT_FIRST_BLOOD,
        "label": "First blood",
        "description": "Triggered once for the first recorded solve on a challenge.",
        "default_template": DEFAULT_EVENT_TEMPLATES[EVENT_FIRST_BLOOD],
    },
    {
        "value": EVENT_CHALLENGE_SOLVED,
        "label": "Challenge solved",
        "description": "Triggered when CTFd records a solve.",
        "default_template": DEFAULT_EVENT_TEMPLATES[EVENT_CHALLENGE_SOLVED],
    },
    {
        "value": EVENT_FAILED_FLAG,
        "label": "Failed flag",
        "description": "Triggered when CTFd records an incorrect submission.",
        "default_template": DEFAULT_EVENT_TEMPLATES[EVENT_FAILED_FLAG],
    },
    {
        "value": EVENT_NEW_REGISTRATION,
        "label": "New registration",
        "description": "Triggered when a user registers through the public registration flow.",
        "default_template": DEFAULT_EVENT_TEMPLATES[EVENT_NEW_REGISTRATION],
    },
    {
        "value": EVENT_CHALLENGE_PARTIAL,
        "label": "Partial solve",
        "description": "Triggered when a challenge records a partial submission.",
        "default_template": DEFAULT_EVENT_TEMPLATES[EVENT_CHALLENGE_PARTIAL],
    },
    {
        "value": EVENT_RATE_LIMITED,
        "label": "Rate limited",
        "description": "Triggered when a submission is recorded as rate limited.",
        "default_template": DEFAULT_EVENT_TEMPLATES[EVENT_RATE_LIMITED],
    },
]

EVENT_LABELS = {item["value"]: item["label"] for item in EVENT_OPTIONS}
PROVIDER_LABELS = {item["value"]: item["label"] for item in PROVIDER_OPTIONS}
VALID_EVENT_TYPES = set(EVENT_LABELS)
VALID_PROVIDERS = set(PROVIDER_LABELS)

DELIVERY_TIMEOUT_SECONDS = 5