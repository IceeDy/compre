from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AuditLog, DomainEvent


def record_audit(
    db: Session,
    *,
    tenant_id: UUID,
    actor_user_id: UUID | None,
    action: str,
    entity_type: str,
    entity_id: UUID | str,
    metadata: dict[str, Any] | None = None,
) -> AuditLog:
    entry = AuditLog(
        tenant_id=tenant_id,
        actor_user_id=actor_user_id,
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id),
        metadata=metadata or {},
    )
    db.add(entry)
    return entry


def record_event(
    db: Session,
    *,
    tenant_id: UUID,
    event_key: str,
    event_type: str,
    aggregate_type: str,
    aggregate_id: UUID | str,
    payload: dict[str, Any] | None = None,
) -> DomainEvent:
    existing = db.scalar(
        select(DomainEvent).where(
            DomainEvent.tenant_id == tenant_id,
            DomainEvent.event_key == event_key,
        )
    )
    if existing:
        return existing

    event = DomainEvent(
        tenant_id=tenant_id,
        event_key=event_key,
        event_type=event_type,
        aggregate_type=aggregate_type,
        aggregate_id=str(aggregate_id),
        payload=payload or {},
    )
    db.add(event)
    return event
