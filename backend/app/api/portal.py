"""
Kiwimath Admin API — Payments, User Flow, Economy & Team RBAC routes.

Payments:
    GET /admin/payments/overview
    GET /admin/payments/subscriptions
    GET /admin/payments/revenue-chart
    GET /admin/payments/plans

User Flow:
    GET /admin/flow/onboarding-funnel
    GET /admin/flow/topic-engagement
    GET /admin/flow/session-flow

Economy:
    GET /admin/economy/overview
    GET /admin/economy/badges
    GET /admin/economy/currency-flow
    GET /admin/economy/avatars
    GET /admin/economy/levels

Team:
    GET  /admin/team/members
    POST /admin/team/members
    PUT  /admin/team/members/{email}
    DELETE /admin/team/members/{email}
    GET  /admin/team/audit-log
    GET  /admin/team/roles
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional

from app.services.portal_store import (
    get_payment_overview, get_subscriptions, get_revenue_chart, get_plans,
    get_onboarding_funnel, get_topic_engagement, get_session_flow,
    get_economy_overview, get_badge_stats, get_currency_flow, get_avatar_adoption, get_level_distribution,
    get_team_members, add_team_member, update_team_member, remove_team_member,
    get_audit_log, get_role_permissions,
)

router = APIRouter(prefix="/admin", tags=["Admin Portal"])


# ── Payments ──────────────────────────────────────────────────

@router.get("/payments/overview")
def payments_overview():
    return get_payment_overview()

@router.get("/payments/subscriptions")
def payments_subscriptions(status: str = Query(""), limit: int = Query(50), offset: int = Query(0)):
    return get_subscriptions(status, limit, offset)

@router.get("/payments/revenue-chart")
def payments_revenue_chart(days: int = Query(30, ge=7, le=90)):
    return get_revenue_chart(days)

@router.get("/payments/plans")
def payments_plans():
    return get_plans()


# ── User Flow ─────────────────────────────────────────────────

@router.get("/flow/onboarding-funnel")
def flow_onboarding():
    return get_onboarding_funnel()

@router.get("/flow/topic-engagement")
def flow_topics():
    return get_topic_engagement()

@router.get("/flow/session-flow")
def flow_sessions():
    return get_session_flow()


# ── Economy ───────────────────────────────────────────────────

@router.get("/economy/overview")
def economy_overview():
    return get_economy_overview()

@router.get("/economy/badges")
def economy_badges():
    return get_badge_stats()

@router.get("/economy/currency-flow")
def economy_currency(days: int = Query(14, ge=7, le=90)):
    return get_currency_flow(days)

@router.get("/economy/avatars")
def economy_avatars():
    return get_avatar_adoption()

@router.get("/economy/levels")
def economy_levels():
    return get_level_distribution()


# ── Team RBAC ─────────────────────────────────────────────────

class TeamMemberCreate(BaseModel):
    email: str
    display_name: str = ""
    role: str = "viewer"

class TeamMemberUpdate(BaseModel):
    display_name: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[int] = None

@router.get("/team/members")
def team_list():
    return get_team_members()

@router.post("/team/members")
def team_add(member: TeamMemberCreate):
    result = add_team_member(member.email, member.display_name, member.role)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@router.put("/team/members/{email}")
def team_update(email: str, updates: TeamMemberUpdate):
    update_dict = {k: v for k, v in updates.dict().items() if v is not None}
    result = update_team_member(email, update_dict)
    if result is None:
        raise HTTPException(status_code=404, detail="User not found")
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@router.delete("/team/members/{email}")
def team_remove(email: str):
    if remove_team_member(email):
        return {"status": "removed", "email": email}
    raise HTTPException(status_code=400, detail="Cannot remove admin users or user not found")

@router.get("/team/audit-log")
def team_audit(limit: int = Query(100), offset: int = Query(0)):
    return get_audit_log(limit, offset)

@router.get("/team/roles")
def team_roles():
    return get_role_permissions()
