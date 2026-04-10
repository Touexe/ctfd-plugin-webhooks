import datetime

from CTFd.models import db
from sqlalchemy import inspect, text


class WebhookEndpoint(db.Model):
    __tablename__ = "webhook_endpoints"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=True)
    provider = db.Column(db.String(32), nullable=False)
    target_url = db.Column(db.Text, nullable=False)
    is_private = db.Column(db.Boolean, nullable=False, default=False)
    is_paused = db.Column(db.Boolean, nullable=False, default=False)
    last_attempt_at = db.Column(db.DateTime, nullable=True)
    last_success_at = db.Column(db.DateTime, nullable=True)
    last_error = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
    )

    subscriptions = db.relationship(
        "WebhookSubscription",
        back_populates="webhook",
        cascade="all, delete-orphan",
        lazy="joined",
        order_by="WebhookSubscription.event_type.asc()",
    )

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "provider": self.provider,
            "target_url": self.target_url,
            "is_private": self.is_private,
            "is_paused": self.is_paused,
            "event_types": [sub.event_type for sub in self.subscriptions],
            "event_templates": {
                sub.event_type: sub.template for sub in self.subscriptions if sub.template
            },
            "event_payload_templates": {
                sub.event_type: sub.payload_template
                for sub in self.subscriptions
                if sub.payload_template
            },
            "last_attempt_at": _isoformat(self.last_attempt_at),
            "last_success_at": _isoformat(self.last_success_at),
            "last_error": self.last_error,
            "created_at": _isoformat(self.created_at),
            "updated_at": _isoformat(self.updated_at),
        }


class WebhookSubscription(db.Model):
    __tablename__ = "webhook_subscriptions"
    __table_args__ = (db.UniqueConstraint("webhook_id", "event_type"), {})

    id = db.Column(db.Integer, primary_key=True)
    webhook_id = db.Column(
        db.Integer, db.ForeignKey("webhook_endpoints.id", ondelete="CASCADE")
    )
    event_type = db.Column(db.String(64), nullable=False)
    template = db.Column(db.Text, nullable=True)
    payload_template = db.Column(db.Text, nullable=True)

    webhook = db.relationship("WebhookEndpoint", back_populates="subscriptions")


def ensure_webhook_schema():
    WebhookEndpoint.__table__.create(bind=db.engine, checkfirst=True)
    WebhookSubscription.__table__.create(bind=db.engine, checkfirst=True)
    _ensure_webhook_endpoint_columns()
    _ensure_webhook_subscription_columns()


def _ensure_webhook_endpoint_columns():
    inspector = inspect(db.engine)
    column_names = {
        column["name"] for column in inspector.get_columns(WebhookEndpoint.__tablename__)
    }

    if "is_private" not in column_names:
        with db.engine.begin() as connection:
            connection.execute(
                text(
                    "ALTER TABLE webhook_endpoints ADD COLUMN is_private BOOLEAN NOT NULL DEFAULT 0"
                )
            )


def _ensure_webhook_subscription_columns():
    inspector = inspect(db.engine)
    column_names = {
        column["name"]
        for column in inspector.get_columns(WebhookSubscription.__tablename__)
    }

    if "template" not in column_names:
        with db.engine.begin() as connection:
            connection.execute(
                text("ALTER TABLE webhook_subscriptions ADD COLUMN template TEXT")
            )

    if "payload_template" not in column_names:
        with db.engine.begin() as connection:
            connection.execute(
                text(
                    "ALTER TABLE webhook_subscriptions ADD COLUMN payload_template TEXT"
                )
            )


def _isoformat(value):
    if value is None:
        return None
    return value.replace(microsecond=0).isoformat() + "Z"