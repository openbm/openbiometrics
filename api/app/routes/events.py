"""Event system and webhook management endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.deps import get_event_bus, get_kernel
from app.schemas import EventSchema, WebhookRequest, WebhookSchema
from openbiometrics.events.types import EventType
from openbiometrics.kernel import BiometricKernel

router = APIRouter()


def _get_dispatcher(kernel: BiometricKernel = Depends(get_kernel)):
    """Get the webhook dispatcher from the kernel, or 503 if unavailable."""
    dispatcher = kernel.webhooks
    if dispatcher is None:
        raise HTTPException(
            status_code=503,
            detail="Webhook dispatcher not available",
        )
    return dispatcher


@router.post("/webhooks", response_model=WebhookSchema)
async def register_webhook(
    req: WebhookRequest,
    dispatcher=Depends(_get_dispatcher),
):
    """Register a new webhook endpoint."""
    # Resolve event type strings to EventType enums
    event_types: list[EventType] = []
    for et_str in req.event_types:
        try:
            event_types.append(EventType(et_str))
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid event type: '{et_str}'. "
                f"Valid types: {[t.value for t in EventType]}",
            )

    webhook_id = dispatcher.register(
        url=req.url,
        event_types=event_types,
        secret=req.secret,
    )

    # Find the registered webhook to return its full schema
    for wh in dispatcher.list_webhooks():
        if wh.id == webhook_id:
            return WebhookSchema(
                id=wh.id,
                url=wh.url,
                event_types=[et.value for et in wh.event_types],
                created_at=wh.created_at.isoformat(),
            )

    # Shouldn't happen, but return minimal response
    return WebhookSchema(
        id=webhook_id,
        url=req.url,
        event_types=req.event_types,
        created_at="",
    )


@router.delete("/webhooks/{webhook_id}")
async def unregister_webhook(
    webhook_id: str,
    dispatcher=Depends(_get_dispatcher),
):
    """Remove a registered webhook."""
    if not dispatcher.unregister(webhook_id):
        raise HTTPException(status_code=404, detail="Webhook not found")
    return {"removed": webhook_id}


@router.get("/webhooks", response_model=list[WebhookSchema])
async def list_webhooks(
    dispatcher=Depends(_get_dispatcher),
):
    """List all registered webhooks."""
    return [
        WebhookSchema(
            id=wh.id,
            url=wh.url,
            event_types=[et.value for et in wh.event_types],
            created_at=wh.created_at.isoformat(),
        )
        for wh in dispatcher.list_webhooks()
    ]


@router.get("/recent", response_model=list[EventSchema])
async def recent_events(
    limit: int = 100,
    event_type: str | None = None,
    bus=Depends(get_event_bus),
):
    """Get recent events, optionally filtered by type."""
    type_filter: EventType | None = None
    if event_type is not None:
        try:
            type_filter = EventType(event_type)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid event type: '{event_type}'. "
                f"Valid types: {[t.value for t in EventType]}",
            )

    events = bus.recent(limit=limit, event_type=type_filter)
    return [
        EventSchema(
            id=e.id,
            type=e.type.value,
            timestamp=e.timestamp.isoformat(),
            source=e.source,
            data=e.data,
            camera_id=e.camera_id,
        )
        for e in events
    ]
