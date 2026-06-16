"""Service API facade for the AI native after-sales demos.

The Streamlit apps still run as lightweight demos, but this module gives them
a backend-shaped boundary: endpoint contracts, repository calls, response
envelopes, and database health checks. A future FastAPI service can expose
these functions as HTTP routes with limited rewrite.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from . import case_store, feedback_store


API_ENDPOINTS = [
    {
        "method": "POST",
        "path": "/api/v1/cases",
        "name": "create_or_update_case",
        "purpose": "write or update case_context across customer input, AI decision, handoff, QA, and feedback.",
        "storage": "cases",
    },
    {
        "method": "GET",
        "path": "/api/v1/cases",
        "name": "list_cases",
        "purpose": "query the case center by status, risk level, priority, and keyword.",
        "storage": "cases",
    },
    {
        "method": "GET",
        "path": "/api/v1/cases/{case_id}",
        "name": "get_case_detail",
        "purpose": "read case context, risks, knowledge refs, handoff summary, and state history.",
        "storage": "cases",
    },
    {
        "method": "POST",
        "path": "/api/v1/feedback-events",
        "name": "create_feedback_event",
        "purpose": "write knowledge miss, human rewrite, handoff reason, low QA score, or inquiry failure events.",
        "storage": "feedback_events",
    },
    {
        "method": "GET",
        "path": "/api/v1/feedback-events?case_id={case_id}",
        "name": "list_case_feedback_events",
        "purpose": "read feedback events attached to one case for audit and optimization follow-up.",
        "storage": "feedback_events",
    },
    {
        "method": "GET",
        "path": "/api/v1/ops/metrics",
        "name": "get_ops_metrics",
        "purpose": "aggregate queue, handoff, high-risk, and unresolved feedback metrics.",
        "storage": "cases + feedback_events",
    },
    {
        "method": "GET",
        "path": "/api/v1/system/db-health",
        "name": "get_database_health",
        "purpose": "show database path, table status, record counts, and write readiness.",
        "storage": "SQLite demo DB",
    },
]


def api_response(data: Any = None, ok: bool = True, error: str = "") -> dict[str, Any]:
    return {
        "ok": ok,
        "error": error,
        "data": data,
        "served_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


def normalize_case_record(case: dict[str, Any]) -> dict[str, Any]:
    risk_tags = case.get("risk_tags") or []
    knowledge_refs = case.get("knowledge_refs") or []
    feedback_events = case.get("feedback_events") or []
    state_history = case.get("state_history") or []
    conversation = case.get("conversation") or []
    slot_status = case.get("slot_status") or {}

    latest_message = ""
    if conversation:
        latest_message = conversation[-1].get("content", "")

    missing_slot_count = sum(
        1
        for slot in slot_status.values()
        if isinstance(slot, dict) and slot.get("status") == "missing"
    )
    risk_level = case.get("risk_level") or ("high" if len(risk_tags) >= 2 else "low")
    priority = case.get("priority") or ("P0" if risk_level == "high" else "P2")
    next_action = case.get("next_action") or "continue_inquiry"
    status = case.get("status")
    if not status:
        if next_action == "human_handoff":
            status = "handoff_pending"
        elif missing_slot_count:
            status = "collecting_info"
        else:
            status = "ai_answered"

    return {
        "case_id": case.get("case_id", ""),
        "created_at": case.get("created_at", ""),
        "updated_at": case.get("updated_at", ""),
        "source": case.get("source", "customer_agent"),
        "channel": case.get("channel", "Customer Agent"),
        "customer": case.get("customer", "demo_customer"),
        "intent": case.get("customer_intent", "general_inquiry"),
        "summary": case.get("handoff_summary") or latest_message or "No summary yet",
        "status": status,
        "priority": priority,
        "risk_level": risk_level,
        "evidence_status": case.get("evidence_status") or (
            "sufficient" if knowledge_refs else "missing"
        ),
        "next_action": next_action,
        "owner": case.get("owner", "AI orchestration"),
        "knowledge_refs": len(knowledge_refs),
        "feedback_count": len(feedback_events),
        "state_history_count": len(state_history),
        "sla": case.get("sla", "By priority"),
        "risk_tags": risk_tags,
        "slot_status": slot_status,
        "knowledge_ref_items": knowledge_refs,
        "feedback_event_items": feedback_events,
        "state_history": state_history,
        "conversation": conversation,
        "raw": case,
    }


def list_case_records(
    status: str = "全部",
    risk_level: str = "全部",
    priority: str = "全部",
    keyword: str = "",
    limit: int = 100,
    fallback_cases: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    try:
        rows = case_store.list_cases(limit=limit)
        cases = [normalize_case_record(row) for row in rows]
        source = "sqlite"
    except Exception as exc:
        if fallback_cases is None:
            return api_response([], ok=False, error=str(exc))
        cases = fallback_cases
        source = "fallback"

    if not cases and fallback_cases:
        cases = fallback_cases
        source = "fallback"

    filtered = cases
    if status != "全部":
        filtered = [case for case in filtered if case["status"] == status]
    if risk_level != "全部":
        filtered = [case for case in filtered if case["risk_level"] == risk_level]
    if priority != "全部":
        filtered = [case for case in filtered if case["priority"] == priority]
    if keyword.strip():
        kw = keyword.strip().lower()
        filtered = [
            case
            for case in filtered
            if kw in case["case_id"].lower()
            or kw in case["summary"].lower()
            or kw in case["intent"].lower()
            or kw in case["owner"].lower()
        ]

    return api_response(
        {
            "items": filtered,
            "total": len(cases),
            "filtered": len(filtered),
            "source": source,
        }
    )


def get_case_detail(case_id: str, fallback_cases: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    try:
        case = case_store.get_case(case_id)
        if case:
            return api_response({"item": normalize_case_record(case), "source": "sqlite"})
    except Exception as exc:
        if fallback_cases is None:
            return api_response(None, ok=False, error=str(exc))

    if fallback_cases:
        for case in fallback_cases:
            if case.get("case_id") == case_id:
                return api_response({"item": case, "source": "fallback"})
    return api_response(None, ok=False, error="case_not_found")


def list_feedback_records(
    case_id: str | None = None,
    limit: int = 50,
    fallback_events: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    try:
        events = feedback_store.get_events(case_id=case_id, limit=limit)
        source = "sqlite"
    except Exception as exc:
        if fallback_events is None:
            return api_response([], ok=False, error=str(exc))
        events = fallback_events
        source = "fallback"
    if not events and fallback_events:
        events = fallback_events
        source = "fallback"
    if case_id:
        events = [event for event in events if event.get("case_id") == case_id]
    return api_response({"items": events, "total": len(events), "source": source})


def get_ops_metrics(fallback_cases: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    cases_payload = list_case_records(fallback_cases=fallback_cases)["data"]
    cases = cases_payload["items"]
    try:
        unresolved = len(feedback_store.get_unresolved(limit=500))
    except Exception:
        unresolved = 0
    return api_response(
        {
            "case_total": cases_payload["total"],
            "case_source": cases_payload["source"],
            "handoff_pending": sum(1 for case in cases if case["next_action"] == "human_handoff"),
            "high_risk": sum(1 for case in cases if case["risk_level"] == "high"),
            "unresolved_feedback": unresolved,
        }
    )


def get_database_health() -> dict[str, Any]:
    try:
        total_cases = case_store.count_cases()
        feedback_counts = feedback_store.count_by_priority()
        return api_response(
            {
                "engine": "sqlite",
                "case_db_path": case_store.DB_PATH,
                "tables": ["cases", "feedback_events"],
                "case_count": total_cases,
                "feedback_by_priority": feedback_counts,
                "writable": True,
            }
        )
    except Exception as exc:
        return api_response(
            {
                "engine": "sqlite",
                "case_db_path": getattr(case_store, "DB_PATH", ""),
                "tables": ["cases", "feedback_events"],
                "case_count": 0,
                "feedback_by_priority": {},
                "writable": False,
            },
            ok=False,
            error=str(exc),
        )
