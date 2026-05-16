from __future__ import annotations

from typing import Any, Optional

from jobconnect.modules.api.shared import CurrentUser, Paginated, audit, business_error
from jobconnect.modules.organizations.schemas import Organization, OrganizationRequest


def _api():
    from jobconnect.modules.api import router as api_router

    return api_router


def _recruiter_in_organization(user_id: int, organization_id: int) -> bool:
    with _api().get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT 1 FROM recruiter_profiles WHERE user_id = %s AND organization_id = %s",
            (user_id, organization_id),
        )
        return cur.fetchone() is not None


def list_organizations(
    q: Optional[str],
    limit: int,
    offset: int,
) -> Paginated:
    where = ["TRUE"]
    params: list[Any] = []
    if q:
        where.append("(name ILIKE %s OR slug ILIKE %s)")
        pat = f"%{q}%"
        params.extend([pat, pat])
    sql_where = " AND ".join(where)
    with _api().get_connection() as conn, conn.cursor() as cur:
        cur.execute(f"SELECT COUNT(*) FROM organizations WHERE {sql_where}", params)
        total = cur.fetchone()[0]
        cur.execute(
            f"""
            SELECT organization_id, name, slug, logo_url, about
            FROM organizations WHERE {sql_where}
            ORDER BY organization_id ASC LIMIT %s OFFSET %s
            """,
            (*params, limit, offset),
        )
        items = [
            Organization(organization_id=r[0], name=r[1], slug=r[2], logo_url=r[3], about=r[4])
            for r in cur.fetchall()
        ]
    return Paginated(items=items, total=total, limit=limit, offset=offset)


def create_organization(request: OrganizationRequest, user: CurrentUser) -> Organization:
    with _api().get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO organizations (name, slug, logo_url, about)
            VALUES (%s, %s, %s, %s)
            RETURNING organization_id, name, slug, logo_url, about
            """,
            (request.name, request.slug, request.logo_url, request.about),
        )
        row = cur.fetchone()
        audit(cur, user.user_id, "organization_created", "organization", row[0])
    return Organization(organization_id=row[0], name=row[1], slug=row[2], logo_url=row[3], about=row[4])


def get_organization(organization_id: int) -> Organization:
    with _api().get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT organization_id, name, slug, logo_url, about FROM organizations WHERE organization_id = %s",
            (organization_id,),
        )
        row = cur.fetchone()
    if row is None:
        raise business_error(404, "not_found", "Organization not found.")
    return Organization(organization_id=row[0], name=row[1], slug=row[2], logo_url=row[3], about=row[4])


def update_organization(organization_id: int, request: OrganizationRequest, user: CurrentUser) -> Organization:
    if user.role == "recruiter" and not _recruiter_in_organization(user.user_id, organization_id):
        raise business_error(404, "not_found", "Organization not found.")
    with _api().get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            UPDATE organizations SET name = %s, slug = %s, logo_url = %s, about = %s, updated_at = now()
            WHERE organization_id = %s
            RETURNING organization_id, name, slug, logo_url, about
            """,
            (request.name, request.slug, request.logo_url, request.about, organization_id),
        )
        row = cur.fetchone()
        if row:
            audit(cur, user.user_id, "organization_updated", "organization", organization_id)
    if row is None:
        raise business_error(404, "not_found", "Organization not found.")
    return Organization(organization_id=row[0], name=row[1], slug=row[2], logo_url=row[3], about=row[4])
