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
        "path": "/api/v1/ops/dashboard",
        "name": "get_ops_dashboard",
        "purpose": "return service operations ratios, distributions, monitoring rows, and optimization signals.",
        "storage": "cases + feedback_events",
    },
    {
        "method": "GET",
        "path": "/api/v1/metrics/system",
        "name": "get_business_metric_system",
        "purpose": "return the full after-sales business metric framework from input to optimization loop.",
        "storage": "metric definitions + cases + feedback_events",
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


def _percent(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round(numerator / denominator * 100, 1)


def _count_by(items: list[dict[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        value = str(item.get(key) or "unknown")
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items(), key=lambda pair: pair[0]))


def _feedback_unresolved_count(events: list[dict[str, Any]]) -> int:
    unresolved = 0
    for event in events:
        if "is_resolved" in event:
            unresolved += 0 if event.get("is_resolved") else 1
        elif event.get("priority") in {"P0", "P1"}:
            unresolved += 1
    return unresolved


def _metric_status(value: float, target: float, higher_is_better: bool = True) -> str:
    if higher_is_better:
        if value >= target:
            return "healthy"
        if value >= target * 0.8:
            return "watch"
        return "risk"
    if value <= target:
        return "healthy"
    if value <= target * 1.25:
        return "watch"
    return "risk"


def get_ops_dashboard(
    fallback_cases: list[dict[str, Any]] | None = None,
    fallback_events: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    cases_payload = list_case_records(fallback_cases=fallback_cases)["data"]
    feedback_payload = list_feedback_records(fallback_events=fallback_events)["data"]
    cases = cases_payload["items"]
    events = feedback_payload["items"]
    total = len(cases)

    auto_resolved = sum(
        1
        for case in cases
        if case.get("next_action") == "standard_answer"
        or case.get("status") in {"ai_answered", "resolved", "closed"}
    )
    handoff = sum(
        1
        for case in cases
        if case.get("next_action") == "human_handoff"
        or case.get("status") in {"handoff_pending", "human_in_progress", "escalated"}
    )
    high_risk = sum(1 for case in cases if case.get("risk_level") == "high")
    knowledge_supported = sum(
        1
        for case in cases
        if case.get("evidence_status") == "sufficient" or int(case.get("knowledge_refs") or 0) > 0
    )
    unresolved_feedback = _feedback_unresolved_count(events)

    rates = {
        "auto_resolution_rate": _percent(auto_resolved, total),
        "handoff_rate": _percent(handoff, total),
        "high_risk_rate": _percent(high_risk, total),
        "knowledge_support_rate": _percent(knowledge_supported, total),
        "feedback_pressure_rate": _percent(unresolved_feedback, max(total, 1)),
    }

    monitoring_rows = [
        {
            "metric": "Auto resolution rate",
            "value": f"{rates['auto_resolution_rate']}%",
            "target": ">= 45%",
            "status": _metric_status(rates["auto_resolution_rate"], 45),
            "meaning": "Low-risk cases that can be answered or closed by AI with evidence.",
        },
        {
            "metric": "Human handoff rate",
            "value": f"{rates['handoff_rate']}%",
            "target": "<= 35%",
            "status": _metric_status(rates["handoff_rate"], 35, higher_is_better=False),
            "meaning": "Cases that need human responsibility, policy judgment, or escalation.",
        },
        {
            "metric": "Knowledge support rate",
            "value": f"{rates['knowledge_support_rate']}%",
            "target": ">= 70%",
            "status": _metric_status(rates["knowledge_support_rate"], 70),
            "meaning": "Cases with sufficient knowledge references or traceable evidence.",
        },
        {
            "metric": "High-risk case rate",
            "value": f"{rates['high_risk_rate']}%",
            "target": "<= 20%",
            "status": _metric_status(rates["high_risk_rate"], 20, higher_is_better=False),
            "meaning": "Regulatory, compensation, public complaint, or severe service risk cases.",
        },
        {
            "metric": "Feedback pressure",
            "value": f"{rates['feedback_pressure_rate']}%",
            "target": "<= 30%",
            "status": _metric_status(rates["feedback_pressure_rate"], 30, higher_is_better=False),
            "meaning": "Open P0/P1 feedback events relative to current case volume.",
        },
    ]

    signals: list[dict[str, str]] = []
    if rates["knowledge_support_rate"] < 70:
        signals.append(
            {
                "signal": "knowledge_gap",
                "severity": "P1",
                "recommendation": "Cluster knowledge_miss and missing-evidence cases, then add SOP snippets and required slots.",
            }
        )
    if rates["handoff_rate"] > 35:
        signals.append(
            {
                "signal": "handoff_pressure",
                "severity": "P1",
                "recommendation": "Review handoff reasons and split unavoidable risk handoff from avoidable missing-information handoff.",
            }
        )
    if rates["feedback_pressure_rate"] > 30:
        signals.append(
            {
                "signal": "feedback_backlog",
                "severity": "P1",
                "recommendation": "Prioritize unresolved P0/P1 feedback events and convert repeated causes into rules, SOP, or prompts.",
            }
        )
    if not signals:
        signals.append(
            {
                "signal": "stable_baseline",
                "severity": "P2",
                "recommendation": "Keep sampling badcases and compare AI decisions with human review before increasing automation scope.",
            }
        )

    return api_response(
        {
            "case_source": cases_payload["source"],
            "feedback_source": feedback_payload["source"],
            "summary": {
                "case_total": total,
                "auto_resolved_cases": auto_resolved,
                "handoff_cases": handoff,
                "high_risk_cases": high_risk,
                "knowledge_supported_cases": knowledge_supported,
                "unresolved_feedback": unresolved_feedback,
            },
            "rates": rates,
            "status_distribution": _count_by(cases, "status"),
            "risk_distribution": _count_by(cases, "risk_level"),
            "priority_distribution": _count_by(cases, "priority"),
            "evidence_distribution": _count_by(cases, "evidence_status"),
            "feedback_type_distribution": _count_by(events, "event_type"),
            "feedback_priority_distribution": _count_by(events, "priority"),
            "monitoring_rows": monitoring_rows,
            "optimization_signals": signals,
        }
    )


def _metric_row(
    layer: str,
    metric: str,
    current: str,
    target: str,
    owner: str,
    action: str,
    status: str = "watch",
) -> dict[str, str]:
    return {
        "layer": layer,
        "metric": metric,
        "current": current,
        "target": target,
        "status": status,
        "owner": owner,
        "action": action,
    }


def get_business_metric_system(
    fallback_cases: list[dict[str, Any]] | None = None,
    fallback_events: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    ops_payload = get_ops_dashboard(
        fallback_cases=fallback_cases,
        fallback_events=fallback_events,
    )
    ops_data = ops_payload["data"]
    summary = ops_data["summary"]
    rates = ops_data["rates"]
    total = max(summary["case_total"], 1)

    repeat_signal = _percent(summary["unresolved_feedback"], total)
    qa_coverage = 100.0 if ops_data["feedback_type_distribution"].get("low_quality_score") else 62.0
    badcase_loop_rate = _percent(summary["unresolved_feedback"], summary["unresolved_feedback"] + 3)

    layers = [
        {
            "layer": "Input",
            "name": "输入层",
            "question": "问题规模、来源渠道和重复问题是否可见？",
            "metrics": ["咨询量", "问题类型占比", "重复问题率", "渠道占比"],
            "business_use": "判断问题是否高频、是否值得 AI 化、是否需要调整入口和分流。",
        },
        {
            "layer": "Recognition",
            "name": "识别层",
            "question": "AI/规则是否识别对了意图、风险和知识依据？",
            "metrics": ["分类准确率", "风险召回率", "知识命中率", "必要字段完整率"],
            "business_use": "决定是否允许 AI 继续答复、追问字段，还是转人工复核。",
        },
        {
            "layer": "Handling",
            "name": "处理层",
            "question": "服务流程是否变短，复杂问题是否被正确升级？",
            "metrics": ["自动解决率", "转人工率", "一次解决率", "处理时长", "升级率"],
            "business_use": "衡量 AI 是否真的降低重复处理成本，而不是把用户困在机器人里。",
        },
        {
            "layer": "Quality",
            "name": "质量层",
            "question": "AI 和人工输出是否可靠、合规、可复核？",
            "metrics": ["质检覆盖率", "人工修改率", "误判率", "漏判率", "无依据回答占比"],
            "business_use": "控制越权承诺、错误解释和服务口径不一致。",
        },
        {
            "layer": "Outcome",
            "name": "结果层",
            "question": "客户体验、投诉风险和业务成本是否改善？",
            "metrics": ["CSAT/NPS", "投诉率", "复咨率", "赔付率", "SLA 达成率"],
            "business_use": "验证业务价值是否成立，防止只优化过程指标。",
        },
        {
            "layer": "Iteration",
            "name": "迭代层",
            "question": "badcase、知识缺口和规则问题是否进入优化闭环？",
            "metrics": ["badcase 回流率", "知识更新周期", "规则命中变化", "优化任务关闭率"],
            "business_use": "判断系统是否持续变好，而不是上线后停留在静态 demo。",
        },
    ]

    rows = [
        _metric_row("输入层", "咨询量", str(summary["case_total"]), "按渠道日/周趋势监控", "服务运营", "按渠道和问题类型拆分流量来源", "watch"),
        _metric_row("输入层", "重复问题率", f"{repeat_signal}%", "<= 15%", "服务运营", "聚类重复咨询，判断是否补知识或 SOP", _metric_status(repeat_signal, 15, False)),
        _metric_row("识别层", "知识命中率", f"{rates['knowledge_support_rate']}%", ">= 70%", "知识库运营", "补齐未命中知识、冲突知识和证据引用", _metric_status(rates["knowledge_support_rate"], 70)),
        _metric_row("识别层", "高风险识别占比", f"{rates['high_risk_rate']}%", "<= 20%", "风险策略", "复核监管投诉、赔付争议、舆情风险规则", _metric_status(rates["high_risk_rate"], 20, False)),
        _metric_row("处理层", "自动解决率", f"{rates['auto_resolution_rate']}%", ">= 45%", "AI 服务运营", "扩大低风险标准场景，保留人工兜底", _metric_status(rates["auto_resolution_rate"], 45)),
        _metric_row("处理层", "转人工率", f"{rates['handoff_rate']}%", "<= 35%", "一线主管", "拆分必要转人工和可通过追问/知识补齐避免的转人工", _metric_status(rates["handoff_rate"], 35, False)),
        _metric_row("质量层", "质检覆盖率", f"{qa_coverage}%", ">= 90%", "质检主管", "扩大 AI 初筛覆盖，争议样本进入人工复核", _metric_status(qa_coverage, 90)),
        _metric_row("质量层", "无依据回答占比", f"{max(0.0, 100 - rates['knowledge_support_rate'])}%", "<= 10%", "AI 质检", "低证据回答转人工确认或拒答", _metric_status(max(0.0, 100 - rates["knowledge_support_rate"]), 10, False)),
        _metric_row("结果层", "CSAT/NPS", "未接入", "上线后接入", "服务运营", "接入满意度、投诉结果和复咨数据", "watch"),
        _metric_row("结果层", "复咨率", f"{repeat_signal}%", "<= 15%", "服务运营", "检查一次解决率和用户重复描述问题", _metric_status(repeat_signal, 15, False)),
        _metric_row("迭代层", "badcase 回流率", f"{badcase_loop_rate}%", ">= 80%", "AI 产品运营", "将 P0/P1 反馈转成知识、SOP、Prompt 或规则任务", _metric_status(badcase_loop_rate, 80)),
        _metric_row("迭代层", "优化任务关闭率", "演示口径", ">= 70%", "服务运营", "后续接入任务状态和关闭周期", "watch"),
    ]

    governance = [
        {
            "rule": "口径统一",
            "detail": "每个指标必须明确业务定义、分子、分母、时间范围、排除条件和数据源。",
        },
        {
            "rule": "链路联动",
            "detail": "不能只看单点指标，转人工率下降必须同时看 CSAT、复咨率、误答率和高风险转人工。",
        },
        {
            "rule": "行动绑定",
            "detail": "每个指标变化都要对应 owner 和下一步动作，否则就是噪音指标。",
        },
        {
            "rule": "节奏管理",
            "detail": "日看异常、周看归因、月看趋势和项目收益，重大异常当天同步。",
        },
    ]

    return api_response(
        {
            "source": "job3.0 EXP-004 + AI service methodology",
            "ops_snapshot": {
                "case_total": summary["case_total"],
                "auto_resolution_rate": rates["auto_resolution_rate"],
                "handoff_rate": rates["handoff_rate"],
                "knowledge_support_rate": rates["knowledge_support_rate"],
                "high_risk_rate": rates["high_risk_rate"],
                "feedback_pressure_rate": rates["feedback_pressure_rate"],
            },
            "layers": layers,
            "metric_rows": rows,
            "governance": governance,
            "cadence": [
                {"cadence": "日报", "focus": "核心指标快照、异常点、P0/P1 风险"},
                {"cadence": "周报", "focus": "趋势变化、异常归因、转人工/知识缺口聚类"},
                {"cadence": "月报", "focus": "业务结果、项目收益、下月优化计划"},
                {"cadence": "异常反馈", "focus": "当天定位原因、同步 owner、进入优化任务"},
            ],
        }
    )


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
