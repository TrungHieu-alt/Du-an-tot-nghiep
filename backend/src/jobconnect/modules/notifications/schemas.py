from __future__ import annotations

from typing import Optional

from jobconnect.modules.api.shared import APIModel, NotificationStatus


class NotificationsReadAllResponse(APIModel):
    updated_count: int


class NotificationDetail(APIModel):
    notification_id: int
    recipient_user_id: int
    type: str
    status: NotificationStatus
    title: str
    body: str
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
