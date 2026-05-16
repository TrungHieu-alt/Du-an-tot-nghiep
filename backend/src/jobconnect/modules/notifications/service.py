from __future__ import annotations

from typing import Any, Optional

from jobconnect.modules.api.shared import CurrentUser, NotificationStatus, Paginated, business_error
from jobconnect.modules.notifications.schemas import NotificationDetail, NotificationsReadAllResponse


def _api():
    from jobconnect.modules.api import router as api_router

    return api_router


def notification_detail(row: tuple) -> NotificationDetail:
    return NotificationDetail(
        notification_id=row[0],
        recipient_user_id=row[1],
        type=row[2],
        status=row[3],
        title=row[4],
        body=row[5],
        entity_type=row[6],
        entity_id=row[7],
    )


def list_notifications(status: Optional[NotificationStatus], limit: int, offset: int, user: CurrentUser) -> Paginated:
    where = ["recipient_user_id = %s"]
    params: list[Any] = [user.user_id]
    if status:
        where.append("status = %s")
        params.append(status)
    sql_where = " AND ".join(where)
    with _api().get_connection() as conn, conn.cursor() as cur:
        cur.execute(f"SELECT COUNT(*) FROM notifications WHERE {sql_where}", params)
        total = cur.fetchone()[0]
        cur.execute(
            f"""
            SELECT notification_id, recipient_user_id, type, status, title, body, entity_type, entity_id
            FROM notifications WHERE {sql_where}
            ORDER BY notification_id DESC LIMIT %s OFFSET %s
            """,
            (*params, limit, offset),
        )
        items = [notification_detail(r) for r in cur.fetchall()]
    return Paginated(items=items, total=total, limit=limit, offset=offset)


def mark_notification_read(notification_id: int, user: CurrentUser) -> NotificationDetail:
    with _api().get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            UPDATE notifications SET status = 'read', updated_at = now()
            WHERE notification_id = %s AND recipient_user_id = %s
            RETURNING notification_id, recipient_user_id, type, status, title, body, entity_type, entity_id
            """,
            (notification_id, user.user_id),
        )
        row = cur.fetchone()
    if row is None:
        raise business_error(404, "not_found", "Notification not found.")
    return notification_detail(row)


def mark_all_notifications_read(user: CurrentUser) -> NotificationsReadAllResponse:
    with _api().get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            "UPDATE notifications SET status = 'read', updated_at = now() WHERE recipient_user_id = %s AND status = 'unread'",
            (user.user_id,),
        )
        count = cur.rowcount
    return NotificationsReadAllResponse(updated_count=max(0, count))
