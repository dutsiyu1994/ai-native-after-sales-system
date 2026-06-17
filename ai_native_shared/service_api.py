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
        "path": "/api/v1/insight-tasks",
        "name": "get_insight_tasks",
        "purpose": "convert feedback events and metric anomalies into 2.0 optimization tasks.",
        "storage": "feedback_events + metric anomalies",
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


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return []


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _count_or_len(value: Any) -> int:
    if value is None:
        return 0
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, (list, tuple, dict, set)):
        return len(value)
    return 1


def normalize_case_record(case: dict[str, Any]) -> dict[str, Any]:
    raw_knowledge_refs = case.get("knowledge_refs")
    raw_feedback_events = case.get("feedback_events")
    raw_state_history = case.get("state_history")

    risk_tags = _as_list(case.get("risk_tags"))
    knowledge_refs = _as_list(raw_knowledge_refs)
    feedback_events = _as_list(raw_feedback_events)
    state_history = _as_list(raw_state_history)
    conversation = _as_list(case.get("conversation"))
    slot_status = _as_dict(case.get("slot_status"))

    latest_message = ""
    if conversation and isinstance(conversation[-1], dict):
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
        "knowledge_refs": _count_or_len(raw_knowledge_refs),
        "feedback_count": _count_or_len(raw_feedback_events),
        "state_history_count": _count_or_len(raw_state_history),
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
                return api_response({"item": normalize_case_record(case), "source": "fallback"})
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

    complaint_order_rate = _percent(summary["case_total"], total * 180)
    public_opinion_complaint_rate = rates["high_risk_rate"]
    service_public_opinion_complaint_rate = _percent(summary["unresolved_feedback"], total)
    first_line_transfer_rate = rates["handoff_rate"]
    warning_manual_intervention_rate = rates["handoff_rate"]
    warning_hit_public_opinion_rate = rates["high_risk_rate"]
    sample_metrics = {
        "order_count": 12680,
        "complaint_cases": 68,
        "public_opinion_cases": 9,
        "service_public_opinion_cases": 4,
        "frontline_received": 820,
        "frontline_transferred": 214,
        "timely_replies": 784,
        "reply_cases": 820,
        "one_call_resolved": 181,
        "call_cases": 226,
        "connected_calls": 205,
        "urged_cases": 46,
        "three_plus_urged_cases": 9,
        "warning_cases": 38,
        "warning_handoff_cases": 13,
        "warning_public_opinion_hits": 23,
        "agreement_cases": 57,
        "closed_complaints": 68,
        "reopened_complaints": 5,
        "employee_payout_cases": 7,
        "payout_cases": 42,
        "payout_amount": 18650,
        "review_invited_cases": 512,
        "reviewable_cases": 680,
        "good_reviews": 386,
        "bad_reviews": 28,
        "reviewed_cases": 442,
    }
    complaint_order_rate = _percent(sample_metrics["complaint_cases"], sample_metrics["order_count"])
    public_opinion_complaint_rate = _percent(sample_metrics["public_opinion_cases"], sample_metrics["complaint_cases"])
    service_public_opinion_complaint_rate = _percent(sample_metrics["service_public_opinion_cases"], sample_metrics["complaint_cases"])
    first_line_transfer_rate = _percent(sample_metrics["frontline_transferred"], sample_metrics["frontline_received"])
    reply_timely_rate = _percent(sample_metrics["timely_replies"], sample_metrics["reply_cases"])
    one_call_rate = _percent(sample_metrics["one_call_resolved"], sample_metrics["call_cases"])
    connection_rate = _percent(sample_metrics["connected_calls"], sample_metrics["call_cases"])
    urged_rate = _percent(sample_metrics["urged_cases"], sample_metrics["frontline_received"])
    three_plus_urged_rate = _percent(sample_metrics["three_plus_urged_cases"], sample_metrics["frontline_received"])
    warning_manual_intervention_rate = _percent(sample_metrics["warning_handoff_cases"], sample_metrics["warning_cases"])
    warning_hit_public_opinion_rate = _percent(sample_metrics["warning_public_opinion_hits"], sample_metrics["warning_cases"])
    agreement_rate = _percent(sample_metrics["agreement_cases"], sample_metrics["closed_complaints"])
    complaint_reopen_rate = _percent(sample_metrics["reopened_complaints"], sample_metrics["closed_complaints"])
    employee_payout_rate = _percent(sample_metrics["employee_payout_cases"], sample_metrics["payout_cases"])
    invite_review_rate = _percent(sample_metrics["review_invited_cases"], sample_metrics["reviewable_cases"])
    good_review_rate = _percent(sample_metrics["good_reviews"], sample_metrics["reviewed_cases"])
    bad_review_rate = _percent(sample_metrics["bad_reviews"], sample_metrics["reviewed_cases"])
    payout_amount = f"¥{sample_metrics['payout_amount']:,}"

    layers = [
        {
            "layer": "Overall",
            "name": "整体指标",
            "category": "风险盘面 / 总量结构",
            "data_source": "订单系统 + Case 中台 + 舆情/监管标签",
            "question": "投诉规模、舆情风险和经服承压是否处在可控区间？",
            "metrics": ["投诉订单比", "舆情投诉比", "经服舆情投诉比"],
            "business_use": "判断售后服务风险是否从个案升级为业务面问题，并决定是否触发专项治理。",
            "decision_use": "触发专项治理、资源倾斜、风险升级和跨团队复盘。",
        },
        {
            "layer": "Preprocess",
            "name": "前处理",
            "category": "入口分流 / 一线消化",
            "data_source": "客户入口 + 一线工单状态 + AI 补槽记录",
            "question": "一线是否把问题过早转移，AI 是否减少无效升级？",
            "metrics": ["一线转移率"],
            "business_use": "衡量入口识别、补槽和知识答复是否能在一线阶段消化低风险问题。",
            "decision_use": "判断是否优化入口话术、补槽字段、知识库和一线 SOP。",
        },
        {
            "layer": "Process",
            "name": "过程",
            "category": "履约推进 / 时效与预警",
            "data_source": "IM/工单响应 + 电话系统 + 催办记录 + 预警事件",
            "question": "响应、接通、催办和预警干预是否稳定？",
            "metrics": ["回复及时率", "1call", "接通", "被催率", "3催及以上率", "预警人工干预比", "预警命中舆情比"],
            "business_use": "监控服务过程质量，识别需要人工提前介入或调整预警规则的节点。",
            "decision_use": "判断是否调班、催办升级、人工提前介入或重调预警阈值。",
        },
        {
            "layer": "Outcome",
            "name": "结果",
            "category": "闭环结果 / 争议与成本",
            "data_source": "Case 处理结果 + 投诉重开 + 赔付责任与金额",
            "question": "客户是否达成一致，投诉是否复开，赔付成本是否可控？",
            "metrics": ["达成一致率", "投诉重开率", "员工赔付比", "赔款金额"],
            "business_use": "验证服务闭环是否真正降低争议和成本，而不是只缩短过程动作。",
            "decision_use": "判断服务策略是否有效，是否需要调整补偿边界、培训和质检策略。",
        },
        {
            "layer": "Feedback",
            "name": "反馈",
            "category": "客户评价 / 质量回流",
            "data_source": "评价邀约 + 满意度结果 + 差评 case 回流",
            "question": "客户反馈是否被采集，好评/差评是否进入运营复盘？",
            "metrics": ["邀评率", "好评率", "差评率"],
            "business_use": "把客户评价接回 case、质检、知识库和规则优化，形成质量反馈闭环。",
            "decision_use": "判断体验是否改善，并把差评样本回流到质检、知识和 SOP 优化。",
        },
    ]

    rows = [
        _metric_row("整体指标", "投诉订单比", f"{complaint_order_rate}%", "<= 0.8%", "服务运营", "接入订单总量和投诉 case，按业务线/渠道拆分异常波动", _metric_status(complaint_order_rate, 0.8, False)),
        _metric_row("整体指标", "舆情投诉比", f"{public_opinion_complaint_rate}%", "<= 15%", "风险策略", "复核监管投诉、赔付争议、公开舆情等高风险标签", _metric_status(public_opinion_complaint_rate, 15, False)),
        _metric_row("整体指标", "经服舆情投诉比", f"{service_public_opinion_complaint_rate}%", "<= 8%", "经服运营", "区分经服原因、平台政策原因和商家/物流外部原因", _metric_status(service_public_opinion_complaint_rate, 8, False)),
        _metric_row("前处理", "一线转移率", f"{first_line_transfer_rate}%", "<= 35%", "一线主管", "拆分必要升级和可由 AI 补槽/知识答复解决的转移", _metric_status(first_line_transfer_rate, 35, False)),
        _metric_row("过程", "回复及时率", f"{reply_timely_rate}%", ">= 95%", "服务运营", "IM/工单首次响应超时 case 进入预警队列", _metric_status(reply_timely_rate, 95)),
        _metric_row("过程", "1call", f"{one_call_rate}%", ">= 85%", "热线运营", "低于目标时复盘一次解决失败原因和知识缺口", _metric_status(one_call_rate, 85)),
        _metric_row("过程", "接通", f"{connection_rate}%", ">= 90%", "热线运营", "接通率异常时拆分用户未接、坐席未接和系统呼叫失败", _metric_status(connection_rate, 90)),
        _metric_row("过程", "被催率", f"{urged_rate}%", "<= 10%", "服务运营", "从反馈/催办事件定位超时、解释不清和处理卡点", _metric_status(urged_rate, 10, False)),
        _metric_row("过程", "3催及以上率", f"{three_plus_urged_rate}%", "<= 3%", "服务运营", "高频催办 case 进入人工复盘和根因归类", _metric_status(three_plus_urged_rate, 3, False)),
        _metric_row("过程", "预警人工干预比", f"{warning_manual_intervention_rate}%", "20%-40%", "风险策略", "评估预警后人工介入是否过多或不足", "watch"),
        _metric_row("过程", "预警命中舆情比", f"{warning_hit_public_opinion_rate}%", ">= 60%", "风险策略", "复核预警规则对舆情/监管/公开投诉的命中质量", _metric_status(warning_hit_public_opinion_rate, 60)),
        _metric_row("结果", "达成一致率", f"{agreement_rate}%", ">= 75%", "服务运营", "接入处理结果和客户确认状态，衡量争议是否闭环", _metric_status(agreement_rate, 75)),
        _metric_row("结果", "投诉重开率", f"{complaint_reopen_rate}%", "<= 5%", "服务运营", "重开 case 回看答复口径、承诺边界和补偿方案", _metric_status(complaint_reopen_rate, 5, False)),
        _metric_row("结果", "员工赔付比", f"{employee_payout_rate}%", "<= 12%", "经服运营", "赔付责任归因中员工操作类样本进入质检和培训", _metric_status(employee_payout_rate, 12, False)),
        _metric_row("结果", "赔款金额", payout_amount, "周预算 ¥20,000", "经服运营", "按原因、渠道、处理人和业务线追踪赔付金额", "healthy"),
        _metric_row("反馈", "邀评率", f"{invite_review_rate}%", ">= 70%", "服务运营", "低邀评渠道补触达策略，避免只看自然评价样本", _metric_status(invite_review_rate, 70)),
        _metric_row("反馈", "好评率", f"{good_review_rate}%", ">= 85%", "服务运营", "按场景、坐席、AI 答复类型拆分好评来源", _metric_status(good_review_rate, 85)),
        _metric_row("反馈", "差评率", f"{bad_review_rate}%", "<= 5%", "服务运营", "差评 case 自动进入质检、知识和 SOP 复盘队列", _metric_status(bad_review_rate, 5, False)),
    ]
    layer_meta = {
        layer["name"]: {
            "category": layer["category"],
            "data_source": layer["data_source"],
            "decision_use": layer["decision_use"],
        }
        for layer in layers
    }
    for row in rows:
        row.update(layer_meta.get(row["layer"], {}))

    diagnosis_rules = {
        "投诉订单比": ("投诉规模波动", "接入订单基数后按业务线、渠道、问题类型定位投诉集中来源。"),
        "舆情投诉比": ("高风险投诉占比偏高", "抽样监管/公开舆情/赔付争议 case，复核预警规则和转人工边界。"),
        "经服舆情投诉比": ("经服相关舆情压力", "区分经服处理、平台政策、商家/物流外部原因，明确 owner。"),
        "一线转移率": ("一线消化能力不足", "拆分可由 AI 补槽、知识答复、标准 SOP 解决的前处理问题。"),
        "回复及时率": ("回复时效存在风险", "抽取超时 case，定位入口排队、跨团队卡点或人工处理积压。"),
        "1call": ("一次呼叫解决不足", "复盘一次解决失败原因，补知识口径、权限和回访 SOP。"),
        "接通": ("电话接通率波动", "拆分用户未接、坐席未接和系统呼叫失败，调整触达策略。"),
        "被催率": ("催办压力偏高", "定位超时、答复不清、补偿争议和跨团队卡点。"),
        "3催及以上率": ("重复催办严重", "进入 P0/P1 人工复盘，补 SOP、权限或跨部门协同机制。"),
        "预警人工干预比": ("预警后人机分工需校准", "复核预警后哪些必须人工介入，哪些可由 AI 继续追问。"),
        "预警命中舆情比": ("预警命中质量不足", "优化舆情风险关键词、监管投诉标签和外部扩散信号。"),
        "达成一致率": ("处理结果未稳定闭环", "接入客户确认状态，复盘未达成一致 case 的争议原因。"),
        "投诉重开率": ("首次处理未解决", "回看答复口径、承诺边界、赔付方案和知识依据。"),
        "员工赔付比": ("员工责任赔付偏高", "抽样员工赔付 case，判断是培训、权限、SOP 还是系统提示问题。"),
        "赔款金额": ("赔付金额接近预算线", "按原因、渠道、处理人和业务线追踪赔付，控制异常扩散。"),
        "邀评率": ("评价邀约覆盖不足", "补充评价触达策略，避免只看主动评价样本。"),
        "好评率": ("好评率需持续观察", "按场景、坐席和 AI 答复类型拆分好评来源。"),
        "差评率": ("差评率偏高", "差评 case 进入质检、知识和 SOP 复盘。"),
    }
    priority_order = {"risk": "P0", "watch": "P1", "healthy": "P2"}
    anomaly_queue = [
        {
            "priority": priority_order.get(row["status"], "P2"),
            "layer": row["layer"],
            "metric": row["metric"],
            "current": row["current"],
            "target": row["target"],
            "status": row["status"],
            "diagnosis": diagnosis_rules.get(row["metric"], ("需要持续观察", ""))[0],
            "next_action": diagnosis_rules.get(row["metric"], ("", row["action"]))[1] or row["action"],
            "owner": row["owner"],
        }
        for row in rows
        if row["status"] != "healthy"
    ]
    anomaly_queue.sort(key=lambda item: (item["priority"], item["layer"], item["metric"]))

    priority_actions = [
        {
            "rank": index,
            "owner": item["owner"],
            "metric": item["metric"],
            "action": item["next_action"],
            "acceptance": "下次周报需说明指标变化、样本原因和是否关闭。",
        }
        for index, item in enumerate(anomaly_queue[:5], start=1)
    ]

    metric_definitions = [
        {
            "metric": "投诉订单比",
            "definition": "投诉 case 数量占订单总量的比例。",
            "numerator": "投诉 case 数",
            "denominator": "订单总量",
            "source": "订单系统 + Case 中台",
        },
        {
            "metric": "一线转移率",
            "definition": "从一线入口转入人工/二线/升级处理的比例。",
            "numerator": "转人工、二线或升级 case 数",
            "denominator": "一线受理 case 数",
            "source": "Case 中台 + 工单状态",
        },
        {
            "metric": "预警命中舆情比",
            "definition": "预警命中的 case 中最终被确认具有舆情/监管/公开投诉风险的比例。",
            "numerator": "预警后确认舆情风险 case 数",
            "denominator": "全部预警 case 数",
            "source": "预警记录 + 风险标签 + 人工复核",
        },
        {
            "metric": "投诉重开率",
            "definition": "已关闭投诉再次被打开或再次升级的比例。",
            "numerator": "重开投诉 case 数",
            "denominator": "已关闭投诉 case 数",
            "source": "Case 状态流 + 处理结果",
        },
        {
            "metric": "邀评率 / 好评率 / 差评率",
            "definition": "评价触达、正向反馈和负向反馈的结果指标。",
            "numerator": "已邀评数 / 好评数 / 差评数",
            "denominator": "可邀评 case 数 / 已评价数",
            "source": "评价系统 + Case 中台",
        },
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
            "data_mode": "demo_sample",
            "sample_note": "当前指标使用模拟样本数据展示监控与决策逻辑，非真实生产统计。",
            "sample_metrics": sample_metrics,
            "ops_snapshot": {
                "case_total": summary["case_total"],
                "complaint_order_rate": complaint_order_rate,
                "public_opinion_complaint_rate": public_opinion_complaint_rate,
                "service_public_opinion_complaint_rate": service_public_opinion_complaint_rate,
                "first_line_transfer_rate": first_line_transfer_rate,
                "agreement_rate": agreement_rate,
                "good_review_rate": good_review_rate,
                "auto_resolution_rate": rates["auto_resolution_rate"],
                "handoff_rate": rates["handoff_rate"],
                "knowledge_support_rate": rates["knowledge_support_rate"],
                "high_risk_rate": rates["high_risk_rate"],
                "feedback_pressure_rate": rates["feedback_pressure_rate"],
            },
            "layers": layers,
            "metric_rows": rows,
            "anomaly_queue": anomaly_queue,
            "priority_actions": priority_actions,
            "metric_definitions": metric_definitions,
            "governance": governance,
            "cadence": [
                {"cadence": "日报", "focus": "核心指标快照、异常点、P0/P1 风险"},
                {"cadence": "周报", "focus": "趋势变化、异常归因、转人工/知识缺口聚类"},
                {"cadence": "月报", "focus": "业务结果、项目收益、下月优化计划"},
                {"cadence": "异常反馈", "focus": "当天定位原因、同步 owner、进入优化任务"},
            ],
        }
    )


def get_insight_tasks(
    fallback_cases: list[dict[str, Any]] | None = None,
    fallback_events: list[dict[str, Any]] | None = None,
    limit: int = 12,
) -> dict[str, Any]:
    feedback_payload = list_feedback_records(fallback_events=fallback_events)["data"]
    metric_payload = get_business_metric_system(
        fallback_cases=fallback_cases,
        fallback_events=fallback_events,
    )["data"]

    events = feedback_payload.get("items", [])
    anomalies = metric_payload.get("anomaly_queue", [])
    tasks: list[dict[str, Any]] = []

    action_by_event = {
        "knowledge_miss": ("知识补齐", "新增或修订知识片段，补充引用条件和适用边界。"),
        "handoff_reason": ("风险规则校准", "复核转人工原因，调整高风险识别和人工接管条件。"),
        "human_modification": ("话术/SOP 修订", "沉淀人工改写内容，更新标准答复和承诺边界。"),
        "low_quality_score": ("质检规则优化", "复盘低分样本，更新质检项、培训点和 AI 回复过滤规则。"),
        "inquiry_failure": ("补槽策略优化", "补充必要字段、追问顺序和失败兜底动作。"),
    }
    priority_rank = {"P0": 0, "P1": 1, "P2": 2}

    for index, event in enumerate(events, start=1):
        priority = event.get("priority", "P2")
        if priority not in {"P0", "P1"}:
            continue
        event_type = event.get("event_type", "feedback_event")
        action_type, recommendation = action_by_event.get(
            event_type,
            ("反馈复盘", event.get("suggested_action", "复盘反馈事件并明确 owner。")),
        )
        tasks.append(
            {
                "task_id": f"INS-FB-{index:03d}",
                "priority": priority,
                "source_signal": event_type,
                "case_id": event.get("case_id", ""),
                "owner": "AI 产品运营" if event_type in {"knowledge_miss", "human_modification"} else "服务运营",
                "action_type": action_type,
                "recommendation": event.get("suggested_action") or recommendation,
                "acceptance": "形成知识/SOP/Prompt/规则变更记录，并在下次样本中复核命中效果。",
                "status": "待评审",
            }
        )

    for index, anomaly in enumerate(anomalies[:5], start=1):
        priority = anomaly.get("priority", "P1")
        tasks.append(
            {
                "task_id": f"INS-MT-{index:03d}",
                "priority": priority,
                "source_signal": anomaly.get("metric", "metric_anomaly"),
                "case_id": "",
                "owner": anomaly.get("owner", "服务运营"),
                "action_type": "指标异常治理",
                "recommendation": anomaly.get("next_action", "定位指标异常原因并进入周报复盘。"),
                "acceptance": "输出异常原因、样本证据、处理动作和指标回看结果。",
                "status": "待处理" if priority == "P0" else "待排期",
            }
        )

    tasks.sort(key=lambda item: (priority_rank.get(item["priority"], 9), item["task_id"]))
    tasks = tasks[:limit]

    return api_response(
        {
            "items": tasks,
            "total": len(tasks),
            "feedback_source": feedback_payload.get("source", "unknown"),
            "metric_source": metric_payload.get("source", "unknown"),
            "data_mode": metric_payload.get("data_mode", "demo_sample"),
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
