from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query

from jobconnect.modules.api.shared import CurrentUser, NotificationStatus, Paginated, require_active
from jobconnect.modules.notifications import service
from jobconnect.modules.notifications.schemas import NotificationDetail, NotificationsReadAllResponse

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=Paginated)
def list_notifications(
    status: Optional[NotificationStatus] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: CurrentUser = Depends(require_active),
):
    return service.list_notifications(status, limit, offset, user)


@router.post("/{notification_id}/read", response_model=NotificationDetail)
def mark_notification_read(notification_id: int, user: CurrentUser = Depends(require_active)):
    return service.mark_notification_read(notification_id, user)


@router.post("/read-all", response_model=NotificationsReadAllResponse)
def mark_all_notifications_read(user: CurrentUser = Depends(require_active)):
    return service.mark_all_notifications_read(user)
