"""Safe adapter for portal-facing service_api functions.

The Streamlit portal should not fail completely when one newly added service
function is missing from a deployed service_api.py. This adapter loads the
module once and provides per-function fallbacks.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


def _payload(data: dict[str, Any]) -> dict[str, Any]:
    return {"ok": True, "data": data, "error": ""}


def _fallback_case_records(fallback_cases: list[dict[str, Any]] | None = None, **_: Any) -> dict[str, Any]:
    items = fallback_cases or []
    return _payload({"items": items, "source": "fallback", "total": len(items), "filtered": len(items)})


def _fallback_case_detail(
    case_id: str,
    fallback_cases: list[dict[str, Any]] | None = None,
    **_: Any,
) -> dict[str, Any]:
    items = fallback_cases or []
    item = next((case for case in items if case.get("case_id") == case_id), None)
    return _payload({"item": item, "source": "fallback"})


def _fallback_feedback_records(
    fallback_events: list[dict[str, Any]] | None = None,
    case_id: str | None = None,
    **_: Any,
) -> dict[str, Any]:
    events = fallback_events or []
    if case_id:
        events = [event for event in events if event.get("case_id") == case_id]
    return _payload({"items": events, "source": "fallback", "total": len(events)})


def _fallback_database_health(**_: Any) -> dict[str, Any]:
    return _payload(
        {
            "engine": "fallback",
            "case_count": 0,
            "tables": [],
            "writable": False,
            "case_db_path": "unavailable",
        }
    )


def _fallback_ops_metrics(fallback_cases: list[dict[str, Any]] | None = None, **_: Any) -> dict[str, Any]:
    cases = fallback_cases or []
    return _payload(
        {
            "case_total": len(cases),
            "handoff_pending": sum(1 for case in cases if case.get("next_action") == "human_handoff"),
            "high_risk": sum(1 for case in cases if case.get("risk_level") == "high"),
            "unresolved_feedback": 0,
        }
    )


def _fallback_ops_dashboard(
    fallback_cases: list[dict[str, Any]] | None = None,
    fallback_events: list[dict[str, Any]] | None = None,
    **_: Any,
) -> dict[str, Any]:
    cases = fallback_cases or []
    events = fallback_events or []
    total = max(len(cases), 1)
    handoff = sum(1 for case in cases if case.get("next_action") == "human_handoff")
    high_risk = sum(1 for case in cases if case.get("risk_level") == "high")
    knowledge = sum(1 for case in cases if case.get("knowledge_refs") or case.get("evidence_status") == "sufficient")
    auto_resolved = sum(1 for case in cases if case.get("status") in {"ai_answered", "resolved", "closed"})
    unresolved_feedback = sum(1 for event in events if event.get("priority") in {"P0", "P1"})

    return _payload(
        {
            "case_source": "fallback",
            "feedback_source": "fallback",
            "summary": {
                "case_total": len(cases),
                "auto_resolved_cases": auto_resolved,
                "handoff_cases": handoff,
                "high_risk_cases": high_risk,
                "knowledge_supported_cases": knowledge,
                "unresolved_feedback": unresolved_feedback,
            },
            "rates": {
                "auto_resolution_rate": round(auto_resolved / total * 100, 1),
                "handoff_rate": round(handoff / total * 100, 1),
                "high_risk_rate": round(high_risk / total * 100, 1),
                "knowledge_support_rate": round(knowledge / total * 100, 1),
                "feedback_pressure_rate": round(unresolved_feedback / total * 100, 1),
            },
            "status_distribution": {},
            "risk_distribution": {},
            "priority_distribution": {},
            "evidence_distribution": {},
            "feedback_type_distribution": {},
            "feedback_priority_distribution": {},
            "monitoring_rows": [],
            "optimization_signals": [],
        }
    )


def _fallback_business_metric_system(**_: Any) -> dict[str, Any]:
    return _payload(
        {
            "data_mode": "fallback",
            "sample_note": "共享接口函数缺失，当前使用门户 fallback 指标结构。",
            "ops_snapshot": {},
            "layers": [],
            "metric_rows": [],
            "anomaly_queue": [],
            "priority_actions": [],
            "metric_definitions": [],
            "cadence": [],
        }
    )


def _fallback_insight_tasks(**_: Any) -> dict[str, Any]:
    return _payload({"items": [], "tasks": [], "source": "fallback", "data_mode": "fallback"})


@dataclass(frozen=True)
class PortalServiceApi:
    API_ENDPOINTS: list[dict[str, Any]]
    get_case_detail: Callable[..., dict[str, Any]]
    get_business_metric_system: Callable[..., dict[str, Any]]
    get_database_health: Callable[..., dict[str, Any]]
    get_insight_tasks: Callable[..., dict[str, Any]]
    get_ops_dashboard: Callable[..., dict[str, Any]]
    get_ops_metrics: Callable[..., dict[str, Any]]
    list_case_records: Callable[..., dict[str, Any]]
    list_feedback_records: Callable[..., dict[str, Any]]
    import_error: str = ""


def load_service_api(module: Any = None, import_error: Exception | None = None) -> PortalServiceApi:
    if import_error is not None:
        module = None
        error = str(import_error)
    elif module is None:
        try:
            from ai_native_shared import service_api as module
        except Exception as exc:  # pragma: no cover - Streamlit fallback path
            module = None
            error = str(exc)
        else:
            error = ""
    else:
        error = ""

    return PortalServiceApi(
        API_ENDPOINTS=getattr(module, "API_ENDPOINTS", []) if module else [],
        get_case_detail=getattr(module, "get_case_detail", _fallback_case_detail),
        get_business_metric_system=getattr(module, "get_business_metric_system", _fallback_business_metric_system),
        get_database_health=getattr(module, "get_database_health", _fallback_database_health),
        get_insight_tasks=getattr(module, "get_insight_tasks", _fallback_insight_tasks),
        get_ops_dashboard=getattr(module, "get_ops_dashboard", _fallback_ops_dashboard),
        get_ops_metrics=getattr(module, "get_ops_metrics", _fallback_ops_metrics),
        list_case_records=getattr(module, "list_case_records", _fallback_case_records),
        list_feedback_records=getattr(module, "list_feedback_records", _fallback_feedback_records),
        import_error=error,
    )
