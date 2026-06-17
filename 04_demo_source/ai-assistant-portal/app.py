"""AI native after-sales service system portal.

This portal presents the six Streamlit demos as one production-oriented
after-sales service system: customer entry, AI orchestration, case center,
operations backend, and the 2.0 optimization layer.
"""

from __future__ import annotations

from html import escape
import os
import sys
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import streamlit as st


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ai_native_shared.portal_service_adapter import load_service_api

_SERVICE_API = load_service_api()
API_ENDPOINTS = _SERVICE_API.API_ENDPOINTS
get_case_detail = _SERVICE_API.get_case_detail
get_business_metric_system = _SERVICE_API.get_business_metric_system
get_database_health = _SERVICE_API.get_database_health
get_insight_tasks = _SERVICE_API.get_insight_tasks
get_ops_dashboard = _SERVICE_API.get_ops_dashboard
get_ops_metrics = _SERVICE_API.get_ops_metrics
list_case_records = _SERVICE_API.list_case_records
list_feedback_records = _SERVICE_API.list_feedback_records
_SERVICE_API_IMPORT_ERROR = _SERVICE_API.import_error


st.set_page_config(
    page_title="AI native 售后服务系统门户",
    page_icon="AI",
    layout="wide",
    initial_sidebar_state="collapsed",
)


@dataclass(frozen=True)
class DemoLink:
    name: str
    url_key: str
    default_url: str
    layer: str
    purpose: str
    input_text: str
    output_text: str
    boundary: str

    @property
    def url(self) -> str:
        return os.getenv(self.url_key, self.default_url)


@dataclass(frozen=True)
class SystemLayer:
    index: str
    title: str
    subtitle: str
    role: str
    capabilities: tuple[str, ...]
    demos: tuple[str, ...]


DEMOS = {
    "对客沟通机器人": DemoLink(
        name="对客沟通机器人",
        url_key="CUSTOMER_AGENT_URL",
        default_url="https://customer-agent-msydemo.streamlit.app/",
        layer="客户入口 / AI 服务编排层",
        purpose="承接客户自然语言输入，创建 case，完成多轮信息补齐、风险判断和转人工决策。",
        input_text="客户问题、订单号、时间、诉求、凭证、历史上下文",
        output_text="case_id、intent、slots、risk_tags、next_action、handoff_summary",
        boundary="不自动承诺退款、赔付、改签或监管结论。",
    ),
    "RAG 知识库": DemoLink(
        name="RAG 知识库",
        url_key="SERVICE_RAG_URL",
        default_url="https://service-rag-demo-msydemo.streamlit.app/",
        layer="AI 服务编排层 / 运营后台",
        purpose="为 AI 判断和客服处理提供 SOP、政策、风险规则和知识引用依据。",
        input_text="客户问题、case 意图、风险标签、业务场景",
        output_text="knowledge_refs、evidence_status、human_confirm_required",
        boundary="知识未命中或冲突时不强答，高风险场景要求人工确认。",
    ),
    "客诉智能分类": DemoLink(
        name="客诉智能分类",
        url_key="COMPLAINT_CLASSIFIER_URL",
        default_url="https://complaint-classifier-msydemo.streamlit.app/",
        layer="AI 服务编排层 / Case 中台",
        purpose="将非结构化投诉转成问题类别、优先级和建议路由。",
        input_text="客户文本、历史摘要、来源渠道",
        output_text="category、priority、routing_label、suggested_action",
        boundary="低置信分类进入人工复核，不直接作为最终责任判断。",
    ),
    "VOC 风险识别": DemoLink(
        name="VOC 风险识别",
        url_key="VOC_RISK_URL",
        default_url="https://voc-risk-detector-msydemo.streamlit.app/",
        layer="AI 服务编排层 / 运营后台 / 2.0 优化层",
        purpose="识别监管投诉、赔付争议、舆情扩散、批量异常和重复未解决问题。",
        input_text="case 文本、风险词、时间趋势、批量反馈",
        output_text="risk_level、risk_tags、trend_signal、alert_reason",
        boundary="风险预警只触发优先级和人工介入，不替代业务责任决策。",
    ),
    "服务事件摘要": DemoLink(
        name="服务事件摘要",
        url_key="SUMMARY_SYSTEM_URL",
        default_url="https://summary-system-msydemo.streamlit.app/",
        layer="Case 中台 / 运营后台",
        purpose="将对话、日志和处理动作压缩成结构化摘要，支撑交接和回填。",
        input_text="客户对话、AI 判断、人工处理记录",
        output_text="case_summary、key_facts、pending_items、followup_notes",
        boundary="摘要用于辅助回填和交接，关键结论仍需人工确认。",
    ),
    "客服对话质检": DemoLink(
        name="客服对话质检",
        url_key="QUALITY_EVALUATOR_URL",
        default_url="https://cs-quality-evaluator-msydemo.streamlit.app/",
        layer="运营后台 / 2.0 优化层",
        purpose="从准确性、同理心、流程合规和承诺边界等维度评估服务质量。",
        input_text="AI/人工回复、case 摘要、知识引用、处理结果",
        output_text="quality_score、issue_tags、rewrite_suggestion、badcase_reason",
        boundary="自动质检负责发现疑点，争议样本进入人工复核。",
    ),
}


LAYERS = [
    SystemLayer(
        index="01",
        title="客户入口",
        subtitle="Web Chat / 小程序 / 企业微信 / Zendesk / 飞书客服",
        role="把客户原始表达转成可处理的服务事件。",
        capabilities=("自然语言输入", "身份与渠道识别", "订单/物流/售后字段采集"),
        demos=("对客沟通机器人",),
    ),
    SystemLayer(
        index="02",
        title="AI 服务编排层",
        subtitle="意图识别 / 多轮信息补齐 / RAG / 风险判断 / 标准答复 / 转人工",
        role="把服务判断拆成可审计、可复核、可转人工的 AI 决策流。",
        capabilities=("intent / slots / risk_tags", "知识依据检索", "next_action 决策"),
        demos=("对客沟通机器人", "RAG 知识库", "客诉智能分类", "VOC 风险识别"),
    ),
    SystemLayer(
        index="03",
        title="Case 中台",
        subtitle="case_id / 用户信息 / 订单字段 / 对话历史 / 风险标签 / 知识引用 / 处理结果",
        role="用统一 case 串联客户、AI、知识、人工和质检，避免模块孤立。",
        capabilities=("case_id 贯穿", "状态与字段沉淀", "人工接管记录"),
        demos=("客诉智能分类", "服务事件摘要"),
    ),
    SystemLayer(
        index="04",
        title="运营后台",
        subtitle="工单列表 / 人工接管台 / 知识库管理 / 质检审核 / 指标看板 / badcase 反馈",
        role="让 AI 输出进入可管理、可复核、可追责的日常运营流程。",
        capabilities=("知识库管理", "风险与工单队列", "质检和反馈闭环"),
        demos=("RAG 知识库", "VOC 风险识别", "服务事件摘要", "客服对话质检"),
    ),
    SystemLayer(
        index="05",
        title="2.0 优化层",
        subtitle="知识未命中 / 高频问题 / 转人工原因 / 风险误判 / Prompt-SOP-知识库优化建议",
        role="从处理问题升级为发现问题、反馈问题并推动服务系统优化。",
        capabilities=("知识缺口分析", "转人工原因聚类", "优化建议生成"),
        demos=("VOC 风险识别", "客服对话质检"),
    ),
]


SAMPLE_CASES = [
    {
        "case_id": "CASE-AIR-001",
        "topic": "航班延误退票赔付，并提到民航局投诉",
        "route": "客户入口 -> AI 服务编排层 -> 运营后台",
        "risk": "监管投诉 / 赔付争议",
        "action": "human_handoff",
        "severity": "high",
    },
    {
        "case_id": "CASE-LOG-002",
        "topic": "物流迟迟未更新，第二轮补充订单号",
        "route": "客户入口 -> Case 中台",
        "risk": "信息缺失 / 低风险",
        "action": "ask_followup",
        "severity": "low",
    },
    {
        "case_id": "CASE-RAG-003",
        "topic": "咨询自愿退票手续费政策",
        "route": "AI 服务编排层 -> RAG 知识检索",
        "risk": "低风险 / 知识命中",
        "action": "standard_answer",
        "severity": "low",
    },
]


BACKEND_CASES = [
    {
        "case_id": "CASE-AIR-001",
        "created_at": "2026-06-16 10:20",
        "updated_at": "2026-06-16 10:48",
        "channel": "Web Chat",
        "customer": "客户 A",
        "intent": "refund_compensation_complaint",
        "source": "对客沟通机器人",
        "status": "handoff_pending",
        "priority": "P0",
        "risk_level": "high",
        "next_action": "human_handoff",
        "evidence_status": "partial",
        "knowledge_refs": 2,
        "feedback_count": 2,
        "sla": "2h",
        "owner": "人工接管队列",
        "summary": "航班延误退票赔付，并提到民航局投诉；需人工确认政策边界和回复时限。",
    },
    {
        "case_id": "CASE-RAG-003",
        "created_at": "2026-06-16 11:05",
        "updated_at": "2026-06-16 11:06",
        "channel": "小程序",
        "customer": "客户 B",
        "intent": "policy_inquiry",
        "source": "RAG 知识库",
        "status": "ai_answered",
        "priority": "P3",
        "risk_level": "low",
        "next_action": "standard_answer",
        "evidence_status": "sufficient",
        "knowledge_refs": 3,
        "feedback_count": 0,
        "sla": "24h",
        "owner": "AI 自动答复",
        "summary": "自愿退票手续费咨询，知识命中且风险可控，可给标准解释。",
    },
    {
        "case_id": "CASE-QA-006",
        "created_at": "2026-06-16 11:30",
        "updated_at": "2026-06-16 12:10",
        "channel": "人工工单",
        "customer": "客户 C",
        "intent": "quality_review",
        "source": "客服对话质检",
        "status": "review_required",
        "priority": "P1",
        "risk_level": "medium",
        "next_action": "quality_review",
        "evidence_status": "sufficient",
        "knowledge_refs": 1,
        "feedback_count": 1,
        "sla": "8h",
        "owner": "质检复核",
        "summary": "客服回复中存在承诺边界不清，需复核并回流话术规则。",
    },
    {
        "case_id": "CASE-LOG-002",
        "created_at": "2026-06-16 12:18",
        "updated_at": "2026-06-16 12:24",
        "channel": "企业微信",
        "customer": "客户 D",
        "intent": "logistics_inquiry",
        "source": "客诉智能分类",
        "status": "collecting_info",
        "priority": "P2",
        "risk_level": "low",
        "next_action": "ask_followup",
        "evidence_status": "missing",
        "knowledge_refs": 0,
        "feedback_count": 1,
        "sla": "12h",
        "owner": "AI 追问",
        "summary": "物流迟迟未更新，客户尚未提供订单号，需继续补齐关键字段。",
    },
    {
        "case_id": "CASE-VOC-009",
        "created_at": "2026-06-16 13:05",
        "updated_at": "2026-06-16 13:40",
        "channel": "批量 VOC",
        "customer": "多客户聚合",
        "intent": "batch_risk_alert",
        "source": "VOC 风险识别",
        "status": "escalated",
        "priority": "P1",
        "risk_level": "medium",
        "next_action": "create_ticket",
        "evidence_status": "partial",
        "knowledge_refs": 1,
        "feedback_count": 2,
        "sla": "4h",
        "owner": "服务运营",
        "summary": "同一物流节点相关咨询突增，需运营确认是否为批量异常并同步口径。",
    },
]


CASE_STATUS_FLOW = [
    ("new", "新建"),
    ("collecting_info", "补齐信息"),
    ("ai_answered", "AI 答复"),
    ("handoff_pending", "待人工"),
    ("human_in_progress", "人工处理中"),
    ("review_required", "质检复核"),
    ("escalated", "升级处理"),
    ("resolved", "已解决"),
    ("closed", "已关闭"),
]


FEEDBACK_EVENTS = [
    {
        "event_type": "handoff_reason",
        "case_id": "CASE-AIR-001",
        "source": "customer_agent",
        "priority": "P0",
        "root_cause": "policy_unclear",
        "suggested_action": "补充监管投诉和赔付争议 SOP，明确必须人工确认的边界。",
    },
    {
        "event_type": "knowledge_miss",
        "case_id": "CASE-LOG-002",
        "source": "rag",
        "priority": "P1",
        "root_cause": "knowledge_gap",
        "suggested_action": "新增物流长时间未更新的追问字段和处理口径。",
    },
    {
        "event_type": "low_quality_score",
        "case_id": "CASE-QA-006",
        "source": "quality_evaluator",
        "priority": "P1",
        "root_cause": "script_issue",
        "suggested_action": "把客服承诺词过滤规则同步到 AI 回复和人工话术审核。",
    },
    {
        "event_type": "human_modification",
        "case_id": "CASE-AIR-001",
        "source": "human_handoff",
        "priority": "P0",
        "root_cause": "policy_unclear",
        "suggested_action": "人工确认赔付边界后，回流监管投诉 SOP 和对客话术边界。",
    },
]


HUMAN_HANDOFF_RECORDS = [
    {
        "case_id": "CASE-AIR-001",
        "handler": "人工客服A",
        "outcome": "继续跟进",
        "ai_review": "AI判断正确",
        "root_cause": "policy_unclear",
        "note": "已安抚客户并说明需要核实航班延误和票规，承诺 24 小时内补充处理进度。",
    },
    {
        "case_id": "CASE-QA-006",
        "handler": "质检专员B",
        "outcome": "已解决",
        "ai_review": "话术需优化",
        "root_cause": "script_issue",
        "note": "人工修改了承诺边界，建议同步到 AI 回复过滤和客服标准话术。",
    },
]


INSIGHT_TASKS = [
    {
        "title": "监管投诉场景转人工规则加严",
        "input": "handoff_reason + human_modification + regulatory risk",
        "action": "调整风险规则",
        "expected": "提升高风险正确转人工率，降低越权答复风险。",
    },
    {
        "title": "物流未更新知识缺口补齐",
        "input": "knowledge_miss 聚类",
        "action": "新增知识片段和追问字段",
        "expected": "减少重复追问和无依据答复。",
    },
    {
        "title": "承诺边界话术统一",
        "input": "low_quality_score + badcase",
        "action": "优化 Prompt / SOP / 质检规则",
        "expected": "降低退款、赔付、监管结论的误承诺率。",
    },
]


def inject_css() -> None:
    st.markdown(
        """
        <style>
        :root {
            --surface: #f5f7fb;
            --panel: #ffffff;
            --ink: #111827;
            --muted: #64748b;
            --line: #dbe3ef;
            --primary: #0c5cab;
            --teal: #0f766e;
            --success: #10b981;
            --warning: #f59e0b;
            --danger: #ef4444;
            --dark: #111827;
        }
        .stApp {
            background:
                radial-gradient(circle at top left, rgba(12, 92, 171, 0.10), transparent 28rem),
                linear-gradient(180deg, #f8fafc 0%, var(--surface) 100%);
            color: var(--ink);
        }
        .block-container {
            max-width: 1240px;
            padding-top: 1.2rem;
            padding-bottom: 2rem;
        }
        h1, h2, h3, p, li, div, span {
            letter-spacing: 0;
        }
        div[data-testid="stMetric"] {
            border: 1px solid var(--line);
            border-radius: 8px;
            background: rgba(255,255,255,0.90);
            padding: 14px 16px;
            box-shadow: 0 10px 30px rgba(15, 23, 42, 0.05);
        }
        div[data-testid="stMetricLabel"] p {
            color: var(--muted);
            font-size: 13px;
        }
        div[data-testid="stMetricValue"] {
            color: var(--ink);
            font-weight: 760;
        }
        .hero {
            border: 1px solid rgba(255,255,255,0.18);
            border-radius: 8px;
            background:
                linear-gradient(135deg, rgba(17, 24, 39, 0.98), rgba(12, 92, 171, 0.90)),
                #111827;
            color: #f8fafc;
            padding: 26px 28px;
            margin-bottom: 18px;
            box-shadow: 0 20px 50px rgba(15, 23, 42, 0.18);
        }
        .hero-grid {
            display: grid;
            grid-template-columns: minmax(0, 1.5fr) minmax(260px, 0.75fr);
            gap: 22px;
            align-items: end;
        }
        .eyebrow {
            color: #93c5fd;
            font-size: 12px;
            font-weight: 800;
            text-transform: uppercase;
            margin-bottom: 8px;
        }
        .hero h1 {
            margin: 0 0 10px 0;
            font-size: 32px;
            line-height: 1.18;
            color: #ffffff;
        }
        .hero p {
            margin: 0;
            color: #dbeafe;
            font-size: 15px;
            line-height: 1.75;
        }
        .hero-status {
            display: grid;
            gap: 8px;
        }
        .status-row {
            display: flex;
            justify-content: space-between;
            gap: 12px;
            border: 1px solid rgba(255,255,255,0.16);
            border-radius: 8px;
            padding: 10px 12px;
            background: rgba(255,255,255,0.07);
            color: #e0f2fe;
            font-size: 13px;
        }
        .section-label {
            color: var(--muted);
            font-size: 12px;
            font-weight: 800;
            text-transform: uppercase;
            margin: 8px 0 4px;
        }
        .subtle {
            color: var(--muted);
            line-height: 1.65;
            font-size: 14px;
        }
        .layer-card, .demo-card, .case-row, .band {
            border: 1px solid var(--line);
            border-radius: 8px;
            background: rgba(255,255,255,0.94);
            box-shadow: 0 10px 26px rgba(15, 23, 42, 0.05);
        }
        .layer-card {
            padding: 18px;
            margin-bottom: 14px;
            display: grid;
            grid-template-columns: 72px minmax(0, 1fr) minmax(220px, 0.38fr);
            gap: 16px;
            align-items: start;
        }
        .layer-index {
            width: 48px;
            height: 48px;
            border-radius: 8px;
            background: #eff6ff;
            color: var(--primary);
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 800;
            border: 1px solid #bfdbfe;
        }
        .layer-card h3, .demo-card h3 {
            margin: 0 0 6px 0;
            color: var(--ink);
            font-size: 19px;
        }
        .layer-card ul {
            margin: 10px 0 0 18px;
            color: #334155;
            line-height: 1.7;
        }
        .pill {
            display: inline-flex;
            align-items: center;
            min-height: 24px;
            padding: 3px 8px;
            border-radius: 999px;
            border: 1px solid #b2f5ea;
            background: #ecfdf5;
            color: var(--teal);
            font-size: 12px;
            font-weight: 700;
            margin: 0 6px 6px 0;
            max-width: 100%;
        }
        .demo-card {
            padding: 17px;
            min-height: 305px;
            margin-bottom: 14px;
        }
        .demo-card p {
            margin: 8px 0;
        }
        .open-link {
            display: inline-flex;
            min-height: 38px;
            align-items: center;
            justify-content: center;
            padding: 8px 13px;
            border-radius: 6px;
            background: var(--primary);
            color: #ffffff !important;
            text-decoration: none;
            font-weight: 760;
            margin-top: 10px;
        }
        .open-link:hover {
            background: #084a8e;
        }
        .case-row {
            padding: 15px;
            margin-bottom: 12px;
            display: grid;
            grid-template-columns: minmax(180px, 0.55fr) minmax(0, 1.2fr) minmax(220px, 0.55fr);
            gap: 16px;
        }
        .ops-grid {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 12px;
            margin: 12px 0 16px;
        }
        .ops-card {
            border: 1px solid var(--line);
            border-radius: 8px;
            background: rgba(255,255,255,0.94);
            padding: 15px;
            box-shadow: 0 10px 26px rgba(15, 23, 42, 0.05);
            min-height: 150px;
        }
        .ops-card h4 {
            margin: 0 0 8px 0;
            font-size: 15px;
            color: var(--ink);
        }
        .ops-meta {
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
            margin: 8px 0;
        }
        .status-chip {
            display: inline-flex;
            border-radius: 999px;
            padding: 3px 8px;
            font-size: 12px;
            font-weight: 760;
            border: 1px solid #cbd5e1;
            color: #334155;
            background: #f8fafc;
        }
        .chip-p0 {
            border-color: #fecaca;
            color: #b42318;
            background: #fef2f2;
        }
        .chip-p1 {
            border-color: #fed7aa;
            color: #c2410c;
            background: #fff7ed;
        }
        .chip-ok {
            border-color: #bbf7d0;
            color: #047857;
            background: #ecfdf5;
        }
        .state-flow {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin: 12px 0;
        }
        .state-step {
            border: 1px solid var(--line);
            border-radius: 8px;
            padding: 8px 10px;
            background: #f8fafc;
            color: #64748b;
            font-size: 12px;
            font-weight: 760;
        }
        .state-step.active {
            border-color: #93c5fd;
            background: #eff6ff;
            color: var(--primary);
        }
        .state-step.done {
            border-color: #bbf7d0;
            background: #ecfdf5;
            color: #047857;
        }
        .case-id {
            font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
            font-size: 13px;
            color: var(--primary);
            font-weight: 800;
        }
        .risk-high {
            color: #b42318;
            font-weight: 800;
        }
        .risk-low {
            color: var(--teal);
            font-weight: 800;
        }
        .band {
            padding: 16px;
            margin: 14px 0;
        }
        .metric-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 12px;
            margin: 12px 0 18px;
        }
        .metric-card {
            border: 1px solid var(--line);
            border-radius: 8px;
            background: rgba(255,255,255,0.96);
            box-shadow: 0 10px 26px rgba(15, 23, 42, 0.05);
            padding: 14px 15px;
            min-height: 112px;
            overflow: visible;
        }
        .metric-label {
            color: #475569;
            font-size: 13px;
            font-weight: 780;
            line-height: 1.35;
            white-space: normal;
            overflow-wrap: anywhere;
        }
        .metric-value {
            color: #0f172a;
            font-size: 27px;
            font-weight: 860;
            line-height: 1.15;
            margin-top: 12px;
            white-space: normal;
            overflow-wrap: anywhere;
        }
        .metric-delta {
            color: #0f766e;
            font-size: 12px;
            font-weight: 720;
            line-height: 1.35;
            margin-top: 8px;
            white-space: normal;
            overflow-wrap: anywhere;
        }
        .launch-flow {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
            gap: 12px;
            margin: 12px 0 20px;
        }
        .launch-card, .boundary-card {
            border: 1px solid var(--line);
            border-radius: 8px;
            background: rgba(255,255,255,0.96);
            box-shadow: 0 10px 26px rgba(15, 23, 42, 0.05);
            padding: 16px;
            min-height: 154px;
        }
        .launch-index {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 32px;
            height: 32px;
            border-radius: 8px;
            background: #eff6ff;
            color: var(--primary);
            font-weight: 850;
            border: 1px solid #bfdbfe;
            margin-bottom: 10px;
        }
        .launch-card h4, .boundary-card h4 {
            margin: 0 0 8px 0;
            color: var(--ink);
            font-size: 16px;
        }
        .launch-card p, .boundary-card p {
            margin: 6px 0;
            color: #475569;
            font-size: 13px;
            line-height: 1.6;
        }
        .boundary-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 12px;
            margin: 12px 0 18px;
        }
        .boundary-tag {
            display: inline-flex;
            border-radius: 999px;
            padding: 3px 8px;
            font-size: 12px;
            font-weight: 760;
            color: #0f766e;
            background: #ecfdf5;
            border: 1px solid #99f6e4;
            margin-bottom: 8px;
        }
        @media (max-width: 900px) {
            .hero-grid,
            .layer-card,
            .case-row {
                grid-template-columns: 1fr;
            }
            .ops-grid {
                grid-template-columns: 1fr;
            }
            .hero h1 {
                font-size: 26px;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_header() -> None:
    st.markdown(
        """
        <div class="hero">
            <div class="hero-grid">
                <div>
                    <div class="eyebrow">AI native after-sales operating system</div>
                    <h1>售后服务系统门户</h1>
                    <p>
                    按真实上线逻辑组织 6 个业务 demo：客户入口、AI 服务编排、Case 中台、
                    运营后台和 2.0 优化层。重点展示服务信息流、风险判断、人机分工、
                    知识口径和质量反馈闭环，而不是单点工具提效。
                    </p>
                </div>
                <div class="hero-status">
                    <div class="status-row"><span>部署状态</span><strong>线上可访问</strong></div>
                    <div class="status-row"><span>业务模块</span><strong>6 个 demo</strong></div>
                    <div class="status-row"><span>主链路</span><strong>5 层闭环</strong></div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_metric_cards(items: list[tuple[str, object, object | None]]) -> None:
    cards = []
    for label, value, delta in items:
        delta_html = f'<div class="metric-delta">{escape(str(delta))}</div>' if delta else ""
        cards.append(
            '<div class="metric-card">'
            f'<div class="metric-label">{escape(str(label))}</div>'
            f'<div class="metric-value">{escape(str(value))}</div>'
            f"{delta_html}"
            "</div>"
        )
    st.markdown(f'<div class="metric-grid">{"".join(cards)}</div>', unsafe_allow_html=True)


def render_kpis() -> None:
    render_metric_cards(
        [
            ("逻辑层", "5", "入口到优化"),
            ("业务 Demo", "6", "门户统一导航"),
            ("核心对象", "case_id", "贯穿全链路"),
            ("高风险策略", "转人工", "赔付 / 监管 / 舆情"),
            ("2.0 方向", "自主优化", "发现 - 反馈 - 改进"),
        ]
    )


def render_layer(layer: SystemLayer) -> None:
    demo_tags = "".join(f'<span class="pill">{demo}</span>' for demo in layer.demos)
    capability_tags = "".join(f'<span class="pill">{item}</span>' for item in layer.capabilities)
    st.markdown(
        f"""
        <div class="layer-card">
            <div class="layer-index">{layer.index}</div>
            <div>
                <h3>{layer.title}</h3>
                <div class="subtle"><strong>{layer.subtitle}</strong></div>
                <p class="subtle">{layer.role}</p>
                <div>{capability_tags}</div>
            </div>
            <div>
                <div class="section-label">关联 demo</div>
                <div>{demo_tags}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_architecture() -> None:
    st.subheader("系统逻辑层")
    for layer in LAYERS:
        render_layer(layer)


def render_demo_card(demo: DemoLink) -> None:
    st.markdown(
        f"""
        <div class="demo-card">
            <span class="pill">{demo.layer}</span>
            <h3>{demo.name}</h3>
            <p class="subtle"><strong>职责：</strong>{demo.purpose}</p>
            <p class="subtle"><strong>输入：</strong>{demo.input_text}</p>
            <p class="subtle"><strong>输出：</strong>{demo.output_text}</p>
            <p class="subtle"><strong>边界：</strong>{demo.boundary}</p>
            <a class="open-link" href="{demo.url}" target="_blank">打开 demo</a>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_demos() -> None:
    st.subheader("6 个业务 demo 入口")
    demo_values = list(DEMOS.values())
    for start in range(0, len(demo_values), 2):
        cols = st.columns(2)
        for offset, col in enumerate(cols):
            index = start + offset
            if index < len(demo_values):
                with col:
                    render_demo_card(demo_values[index])


def render_case_flow() -> None:
    st.subheader("Case 流转示例")
    st.caption("展示后台应如何把客户问题映射到 case、风险、知识和人工动作。")
    for case in SAMPLE_CASES:
        risk_class = "risk-high" if case["severity"] == "high" else "risk-low"
        st.markdown(
            f"""
            <div class="case-row">
                <div>
                    <div class="case-id">{case["case_id"]}</div>
                    <div class="subtle">{case["topic"]}</div>
                </div>
                <div>
                    <div class="section-label">流转路径</div>
                    <div>{case["route"]}</div>
                </div>
                <div>
                    <div class="{risk_class}">{case["risk"]}</div>
                    <div class="subtle">next_action: <strong>{case["action"]}</strong></div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def _priority_class(priority: str, evidence_status: str = "") -> str:
    if priority == "P0":
        return "chip-p0"
    if priority == "P1":
        return "chip-p1"
    if evidence_status == "sufficient":
        return "chip-ok"
    return ""


def _status_stage(status: str) -> int:
    order = [item[0] for item in CASE_STATUS_FLOW]
    return order.index(status) if status in order else 0


def _render_state_flow(status: str) -> None:
    current = _status_stage(status)
    steps = []
    for idx, (key, label) in enumerate(CASE_STATUS_FLOW):
        cls = "active" if key == status else "done" if idx < current else ""
        steps.append(f'<span class="state-step {cls}">{label}</span>')
    st.markdown(f'<div class="state-flow">{"".join(steps)}</div>', unsafe_allow_html=True)


def _tag_text(items: list | tuple | None, empty: str = "无") -> str:
    if not items:
        return empty
    return " / ".join(str(item) for item in items)


def _as_list(value):
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return []


def _as_dict(value):
    return value if isinstance(value, dict) else {}


def _count_or_len(value) -> int:
    if value is None:
        return 0
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, (list, tuple, dict, set)):
        return len(value)
    return 1


def _snapshot_value(snapshot: dict, key: str, fallback: object = "待接入") -> object:
    return snapshot.get(key, fallback) if isinstance(snapshot, dict) else fallback


def render_case_detail_panel(selected: dict, data_source: str) -> None:
    case_id = selected["case_id"]
    if _SERVICE_API_IMPORT_ERROR:
        detail = selected
        detail_source = "fallback"
        feedback_payload = {"data": {"items": [], "source": "fallback"}}
    else:
        detail_payload = get_case_detail(case_id, fallback_cases=BACKEND_CASES)
        detail_data = detail_payload.get("data") or {}
        detail = detail_data.get("item") or selected
        detail_source = detail_data.get("source", data_source)
        feedback_payload = list_feedback_records(case_id=case_id, fallback_events=FEEDBACK_EVENTS)

    raw = detail.get("raw", detail)
    raw = raw if isinstance(raw, dict) else {}
    state_history = _as_list(detail.get("state_history")) or _as_list(raw.get("state_history"))
    slot_status = _as_dict(detail.get("slot_status")) or _as_dict(raw.get("slot_status"))
    risk_tags = _as_list(detail.get("risk_tags")) or _as_list(raw.get("risk_tags"))
    knowledge_refs = _as_list(detail.get("knowledge_ref_items")) or _as_list(raw.get("knowledge_refs"))
    conversation = _as_list(detail.get("conversation")) or _as_list(raw.get("conversation"))
    feedback_data = _as_dict(feedback_payload.get("data"))
    case_feedback = _as_list(feedback_data.get("items"))
    knowledge_ref_count = _count_or_len(detail.get("knowledge_refs")) or len(knowledge_refs)

    st.markdown("#### Case 详情 / 审计视图")
    st.caption(f"case_id: {case_id} / 数据来源: {detail_source} / 接口: GET /api/v1/cases/{case_id}")

    overview_cols = st.columns([1.2, 1, 1])
    with overview_cols[0]:
        st.markdown(f"**{case_id} · {detail['intent']}**")
        st.caption(f"{detail['channel']} / {detail['customer']} / {detail['source']}")
        st.write(detail["summary"])
    with overview_cols[1]:
        render_metric_cards(
            [
                ("状态历史", len(state_history), None),
                ("风险标签", len(risk_tags), None),
            ]
        )
    with overview_cols[2]:
        render_metric_cards(
            [
                ("知识引用", knowledge_ref_count, None),
                ("反馈事件", len(case_feedback), None),
            ]
        )

    _render_state_flow(detail["status"])

    tab_slots, tab_trace, tab_feedback, tab_raw = st.tabs(
        ["字段与风险", "状态与对话", "反馈事件", "原始上下文"]
    )
    with tab_slots:
        st.markdown(f"**风险标签：** {_tag_text(risk_tags)}")
        if slot_status:
            slot_rows = [
                {
                    "slot": name,
                    "status": info.get("status", "") if isinstance(info, dict) else "",
                    "value": info.get("value", "") if isinstance(info, dict) else str(info),
                }
                for name, info in slot_status.items()
            ]
            st.dataframe(pd.DataFrame(slot_rows), use_container_width=True, hide_index=True)
        else:
            st.info("当前 case 暂无结构化槽位。")
        if knowledge_refs:
            st.markdown("**知识引用**")
            st.json(knowledge_refs)
    with tab_trace:
        if state_history:
            trace_rows = []
            for idx, item in enumerate(state_history, start=1):
                trace_rows.append(
                    {
                        "step": idx,
                        "status": item.get("status", ""),
                        "next_action": item.get("next_action", ""),
                        "risk_level": item.get("risk_level", ""),
                        "reason": item.get("decision_reason", item.get("reason", "")),
                        "time": item.get("created_at", item.get("time", "")),
                    }
                )
            st.dataframe(pd.DataFrame(trace_rows), use_container_width=True, hide_index=True)
        else:
            st.info("当前 case 暂无状态历史。")
        if conversation:
            with st.expander("查看对话上下文", expanded=False):
                st.json(conversation)
    with tab_feedback:
        st.caption(f"接口: GET /api/v1/feedback-events?case_id={case_id}")
        if case_feedback:
            feedback_rows = [
                {
                    "event_type": event.get("event_type", ""),
                    "priority": event.get("priority", ""),
                    "source": event.get("source", event.get("source_module", "")),
                    "root_cause": event.get("root_cause", ""),
                    "suggested_action": event.get("suggested_action", ""),
                    "created_at": event.get("created_at", ""),
                }
                for event in case_feedback
            ]
            st.dataframe(pd.DataFrame(feedback_rows), use_container_width=True, hide_index=True)
        else:
            st.info("当前 case 暂无独立反馈事件。")
    with tab_raw:
        st.json(raw)


def _filter_cases(cases: list[dict], status: str, risk: str, priority: str, keyword: str) -> list[dict]:
    result = cases
    if status != "全部":
        result = [case for case in result if case["status"] == status]
    if risk != "全部":
        result = [case for case in result if case["risk_level"] == risk]
    if priority != "全部":
        result = [case for case in result if case["priority"] == priority]
    if keyword.strip():
        kw = keyword.strip().lower()
        result = [
            case
            for case in result
            if kw in case["case_id"].lower()
            or kw in case["summary"].lower()
            or kw in case["intent"].lower()
            or kw in case["owner"].lower()
        ]
    return result


def render_case_center() -> list[dict]:
    st.markdown("#### Case 中台列表")
    base_payload = list_case_records(fallback_cases=BACKEND_CASES) if not _SERVICE_API_IMPORT_ERROR else {
        "data": {"items": BACKEND_CASES, "source": "fallback", "total": len(BACKEND_CASES), "filtered": len(BACKEND_CASES)}
    }
    base_cases = base_payload["data"]["items"]
    status_options = ["全部"] + sorted({case["status"] for case in base_cases})
    risk_options = ["全部"] + sorted({case["risk_level"] for case in base_cases})
    priority_options = ["全部"] + sorted({case["priority"] for case in base_cases})
    f1, f2, f3, f4 = st.columns([1, 1, 1, 1.4])
    status_filter = f1.selectbox("状态", status_options, key="ops_status_filter")
    risk_filter = f2.selectbox("风险", risk_options, key="ops_risk_filter")
    priority_filter = f3.selectbox("优先级", priority_options, key="ops_priority_filter")
    keyword = f4.text_input("搜索 case / 意图 / 负责人", key="ops_keyword_filter")

    if _SERVICE_API_IMPORT_ERROR:
        filtered = _filter_cases(BACKEND_CASES, status_filter, risk_filter, priority_filter, keyword)
        data_source = "fallback"
    else:
        payload = list_case_records(
            status=status_filter,
            risk_level=risk_filter,
            priority=priority_filter,
            keyword=keyword,
            fallback_cases=BACKEND_CASES,
        )
        filtered = payload["data"]["items"]
        data_source = payload["data"]["source"]
    st.caption(f"数据来源: {data_source} / 接口: GET /api/v1/cases")
    if not filtered:
        st.info("当前筛选条件下没有 case。")
        return []

    table_rows = [
        {
            "case_id": case["case_id"],
            "status": case["status"],
            "priority": case["priority"],
            "risk_level": case["risk_level"],
            "next_action": case["next_action"],
            "evidence": case["evidence_status"],
            "owner": case["owner"],
            "updated_at": case["updated_at"],
        }
        for case in filtered
    ]
    st.dataframe(pd.DataFrame(table_rows), use_container_width=True, hide_index=True)

    selected_id = st.selectbox(
        "查看 case 详情",
        [case["case_id"] for case in filtered],
        key="ops_selected_case",
    )
    selected = next(case for case in filtered if case["case_id"] == selected_id)
    render_case_detail_panel(selected, data_source)
    return filtered


def render_api_database_panel() -> None:
    st.markdown("#### API / 数据库接口")
    if _SERVICE_API_IMPORT_ERROR:
        st.warning(f"共享接口层加载失败: {_SERVICE_API_IMPORT_ERROR}")
        return

    db_health = get_database_health()
    health = db_health["data"]
    render_metric_cards(
        [
            ("DB Engine", health["engine"], None),
            ("Case Rows", health["case_count"], None),
            ("Tables", len(health["tables"]), None),
            ("Writable", "Yes" if health["writable"] else "No", None),
        ]
    )
    st.caption(f"SQLite path: {health['case_db_path']}")

    endpoint_rows = [
        {
            "method": endpoint["method"],
            "path": endpoint["path"],
            "name": endpoint["name"],
            "storage": endpoint["storage"],
            "purpose": endpoint["purpose"],
        }
        for endpoint in API_ENDPOINTS
    ]
    st.dataframe(pd.DataFrame(endpoint_rows), use_container_width=True, hide_index=True)


def render_operations_backend() -> None:
    st.subheader("运营后台 / Case 中台")
    st.caption("用统一 case_id 串联客户输入、AI 判断、知识依据、人工接管、质检和 2.0 优化任务。")

    if _SERVICE_API_IMPORT_ERROR:
        metrics = {
            "case_total": len(BACKEND_CASES),
            "handoff_pending": sum(1 for c in BACKEND_CASES if c["next_action"] == "human_handoff"),
            "high_risk": sum(1 for c in BACKEND_CASES if c["risk_level"] == "high"),
            "unresolved_feedback": sum(1 for e in FEEDBACK_EVENTS if e["priority"] in ("P0", "P1")),
        }
    else:
        metrics = get_ops_metrics(fallback_cases=BACKEND_CASES)["data"]
    render_metric_cards(
        [
            ("Case 队列", metrics["case_total"], None),
            ("待人工接管", metrics["handoff_pending"], None),
            ("高风险 Case", metrics["high_risk"], None),
            ("人工回填", len(HUMAN_HANDOFF_RECORDS), f"{metrics['unresolved_feedback']} 条待优化"),
        ]
    )

    filtered_cases = render_case_center()
    render_api_database_panel()

    st.markdown('<div class="section-label">Case 队列</div>', unsafe_allow_html=True)
    case_cards = []
    for case in filtered_cases or BACKEND_CASES:
        priority_class = _priority_class(case["priority"], case["evidence_status"])
        case_cards.append(
            '<div class="ops-card">'
            f'<div class="case-id">{escape(str(case["case_id"]))}</div>'
            f'<h4>{escape(str(case["summary"]))}</h4>'
            '<div class="ops-meta">'
            f'<span class="status-chip {priority_class}">{escape(str(case["priority"]))}</span>'
            f'<span class="status-chip">{escape(str(case["status"]))}</span>'
            f'<span class="status-chip">{escape(str(case["risk_level"]))}</span>'
            f'<span class="status-chip">{escape(str(case["evidence_status"]))}</span>'
            "</div>"
            f'<p class="subtle"><strong>来源：</strong>{escape(str(case["source"]))}</p>'
            f'<p class="subtle"><strong>动作：</strong>{escape(str(case["next_action"]))}</p>'
            f'<p class="subtle"><strong>负责人：</strong>{escape(str(case["owner"]))}</p>'
            "</div>"
        )
    st.markdown(f'<div class="ops-grid">{"".join(case_cards)}</div>', unsafe_allow_html=True)

    st.markdown("#### 人工接管回填")
    handoff_cards = []
    for record in HUMAN_HANDOFF_RECORDS:
        handoff_cards.append(
            '<div class="ops-card">'
            f'<div class="case-id">{escape(str(record["case_id"]))}</div>'
            '<div class="ops-meta">'
            f'<span class="status-chip">{escape(str(record["handler"]))}</span>'
            f'<span class="status-chip">{escape(str(record["outcome"]))}</span>'
            f'<span class="status-chip">{escape(str(record["ai_review"]))}</span>'
            "</div>"
            f'<p class="subtle"><strong>根因：</strong>{escape(str(record["root_cause"]))}</p>'
            f'<p class="subtle"><strong>处理说明：</strong>{escape(str(record["note"]))}</p>'
            "</div>"
        )
    st.markdown(f'<div class="ops-grid">{"".join(handoff_cards)}</div>', unsafe_allow_html=True)

    left, right = st.columns([1, 1])
    with left:
        st.markdown("#### 反馈事件队列")
        feedback_payload = (
            {"data": {"items": FEEDBACK_EVENTS, "source": "fallback"}}
            if _SERVICE_API_IMPORT_ERROR
            else list_feedback_records(fallback_events=FEEDBACK_EVENTS)
        )
        st.caption(f"数据来源: {feedback_payload['data']['source']} / 接口: GET /api/v1/feedback-events")
        for event in feedback_payload["data"]["items"]:
            priority_class = _priority_class(event["priority"])
            source = event.get("source") or event.get("source_module", "")
            st.markdown(
                '<div class="ops-card">'
                '<div class="ops-meta">'
                f'<span class="status-chip {priority_class}">{escape(str(event["priority"]))}</span>'
                f'<span class="status-chip">{escape(str(event["event_type"]))}</span>'
                f'<span class="status-chip">{escape(str(source))}</span>'
                "</div>"
                f'<div class="case-id">{escape(str(event["case_id"]))}</div>'
                f'<p class="subtle"><strong>根因：</strong>{escape(str(event["root_cause"]))}</p>'
                f'<p class="subtle"><strong>建议：</strong>{escape(str(event["suggested_action"]))}</p>'
                "</div>",
                unsafe_allow_html=True,
            )

    with right:
        st.markdown("#### 2.0 优化任务")
        if _SERVICE_API_IMPORT_ERROR or get_insight_tasks is None:
            insight_payload = {"data": {"items": INSIGHT_TASKS, "data_mode": "fallback"}}
        else:
            insight_payload = get_insight_tasks(
                fallback_cases=BACKEND_CASES,
                fallback_events=FEEDBACK_EVENTS,
            )
        insight_data = insight_payload.get("data") or {}
        st.caption(f"数据模式: {insight_data.get('data_mode', 'demo_sample')} / 接口: GET /api/v1/insight-tasks")
        for task in insight_data.get("items", []):
            if "task_id" in task:
                priority_class = _priority_class(task.get("priority", "P1"))
                st.markdown(
                    '<div class="ops-card">'
                    '<div class="ops-meta">'
                    f'<span class="status-chip {priority_class}">{escape(str(task.get("priority", "")))}</span>'
                    f'<span class="status-chip">{escape(str(task.get("status", "")))}</span>'
                    f'<span class="status-chip">{escape(str(task.get("action_type", "")))}</span>'
                    "</div>"
                    f'<div class="case-id">{escape(str(task.get("task_id", "")))}</div>'
                    f'<h4>{escape(str(task.get("source_signal", "")))}</h4>'
                    f'<p class="subtle"><strong>Owner：</strong>{escape(str(task.get("owner", "")))}</p>'
                    f'<p class="subtle"><strong>建议动作：</strong>{escape(str(task.get("recommendation", "")))}</p>'
                    f'<p class="subtle"><strong>验收标准：</strong>{escape(str(task.get("acceptance", "")))}</p>'
                    "</div>",
                    unsafe_allow_html=True,
                )
                continue
            st.markdown(
                '<div class="ops-card">'
                f'<h4>{escape(str(task["title"]))}</h4>'
                f'<p class="subtle"><strong>输入信号：</strong>{escape(str(task["input"]))}</p>'
                f'<p class="subtle"><strong>建议动作：</strong>{escape(str(task["action"]))}</p>'
                f'<p class="subtle"><strong>预期收益：</strong>{escape(str(task["expected"]))}</p>'
                "</div>",
                unsafe_allow_html=True,
            )


def _distribution_frame(distribution: dict[str, int], label: str) -> pd.DataFrame:
    return pd.DataFrame(
        [{"name": key, label: value} for key, value in distribution.items()]
    )


def render_ops_metrics_dashboard() -> None:
    st.subheader("运营指标 / 服务闭环监控")
    st.caption(
        "用 case 与 feedback 事件衡量系统是否真的形成售后服务闭环，而不是只展示单点 AI 工具。接口: GET /api/v1/ops/dashboard"
    )

    if _SERVICE_API_IMPORT_ERROR:
        dashboard = {
            "case_source": "fallback",
            "feedback_source": "fallback",
            "summary": {
                "case_total": len(BACKEND_CASES),
                "auto_resolved_cases": sum(
                    1
                    for case in BACKEND_CASES
                    if case["next_action"] == "standard_answer"
                    or case["status"] in {"ai_answered", "resolved", "closed"}
                ),
                "handoff_cases": sum(
                    1
                    for case in BACKEND_CASES
                    if case["next_action"] == "human_handoff"
                    or case["status"] in {"handoff_pending", "human_in_progress", "escalated"}
                ),
                "high_risk_cases": sum(1 for case in BACKEND_CASES if case["risk_level"] == "high"),
                "knowledge_supported_cases": sum(
                    1
                    for case in BACKEND_CASES
                    if case["evidence_status"] == "sufficient" or case["knowledge_refs"] > 0
                ),
                "unresolved_feedback": sum(1 for event in FEEDBACK_EVENTS if event["priority"] in ("P0", "P1")),
            },
            "rates": {
                "auto_resolution_rate": 20.0,
                "handoff_rate": 40.0,
                "high_risk_rate": 20.0,
                "knowledge_support_rate": 80.0,
                "feedback_pressure_rate": 80.0,
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
    else:
        payload = get_ops_dashboard(
            fallback_cases=BACKEND_CASES,
            fallback_events=FEEDBACK_EVENTS,
        )
        dashboard = payload["data"]

    summary = dashboard["summary"]
    rates = dashboard["rates"]
    st.caption(
        f"case_source: {dashboard['case_source']} / feedback_source: {dashboard['feedback_source']}"
    )

    render_metric_cards(
        [
            ("自动解决率", f"{rates['auto_resolution_rate']}%", f"{summary['auto_resolved_cases']} case"),
            ("转人工率", f"{rates['handoff_rate']}%", f"{summary['handoff_cases']} case"),
            ("知识覆盖率", f"{rates['knowledge_support_rate']}%", f"{summary['knowledge_supported_cases']} case"),
            ("高风险占比", f"{rates['high_risk_rate']}%", f"{summary['high_risk_cases']} case"),
            ("反馈压力", f"{rates['feedback_pressure_rate']}%", f"{summary['unresolved_feedback']} open"),
        ]
    )

    st.markdown("#### 指标守门")
    monitoring_rows = dashboard.get("monitoring_rows", [])
    if monitoring_rows:
        st.dataframe(pd.DataFrame(monitoring_rows), use_container_width=True, hide_index=True)
    else:
        st.info("暂无指标守门数据。")

    dist_left, dist_mid, dist_right = st.columns(3)
    with dist_left:
        st.markdown("#### Case 状态")
        frame = _distribution_frame(dashboard["status_distribution"], "cases")
        if frame.empty:
            st.info("暂无状态分布。")
        else:
            st.bar_chart(frame.set_index("name"))
    with dist_mid:
        st.markdown("#### 风险等级")
        frame = _distribution_frame(dashboard["risk_distribution"], "cases")
        if frame.empty:
            st.info("暂无风险分布。")
        else:
            st.bar_chart(frame.set_index("name"))
    with dist_right:
        st.markdown("#### 证据状态")
        frame = _distribution_frame(dashboard["evidence_distribution"], "cases")
        if frame.empty:
            st.info("暂无证据分布。")
        else:
            st.bar_chart(frame.set_index("name"))

    feedback_left, feedback_right = st.columns(2)
    with feedback_left:
        st.markdown("#### 反馈事件类型")
        frame = _distribution_frame(dashboard["feedback_type_distribution"], "events")
        if frame.empty:
            st.info("暂无反馈事件。")
        else:
            st.dataframe(frame, use_container_width=True, hide_index=True)
    with feedback_right:
        st.markdown("#### 反馈优先级")
        frame = _distribution_frame(dashboard["feedback_priority_distribution"], "events")
        if frame.empty:
            st.info("暂无反馈优先级。")
        else:
            st.bar_chart(frame.set_index("name"))

    st.markdown("#### 2.0 优化信号")
    signals = dashboard.get("optimization_signals", [])
    if signals:
        st.dataframe(pd.DataFrame(signals), use_container_width=True, hide_index=True)
    else:
        st.info("暂无优化信号。")


def render_business_metric_system() -> None:
    st.subheader("数据指标体系 / 全链路业务监控")
    st.caption(
        "基于 job3.0 的 EXP-004 数据指标体系和全链路服务指标方法，把售后 AI 系统从“能跑”升级为“能监控、能归因、能推动动作”。接口: GET /api/v1/metrics/system"
    )

    if _SERVICE_API_IMPORT_ERROR:
        st.warning(f"共享接口层加载失败，无法读取数据指标体系: {_SERVICE_API_IMPORT_ERROR}")
        return

    payload = get_business_metric_system(
        fallback_cases=BACKEND_CASES,
        fallback_events=FEEDBACK_EVENTS,
    )
    metric_system = payload.get("data") or {}
    snapshot = metric_system.get("ops_snapshot") or {}

    st.caption(
        f"数据模式: {metric_system.get('data_mode', 'demo_sample')} / "
        f"{metric_system.get('sample_note', '当前为模拟业务指标，用于展示监控和决策逻辑；运营指标页仍保留原系统使用指标。')}"
    )
    render_metric_cards(
        [
            ("投诉订单比", f"{_snapshot_value(snapshot, 'complaint_order_rate')}%", "整体风险盘面"),
            ("舆情投诉比", f"{_snapshot_value(snapshot, 'public_opinion_complaint_rate')}%", "高风险投诉结构"),
            ("一线转移率", f"{_snapshot_value(snapshot, 'first_line_transfer_rate')}%", "前处理消化能力"),
            ("达成一致率", f"{_snapshot_value(snapshot, 'agreement_rate')}%", "结果闭环质量"),
            ("好评率", f"{_snapshot_value(snapshot, 'good_review_rate')}%", "客户反馈结果"),
        ]
    )

    st.markdown("#### 五层指标地图")
    layer_cards = []
    for layer in metric_system.get("layers", []):
        metrics = " / ".join(layer.get("metrics", []))
        layer_cards.append(
            '<div class="ops-card">'
            f'<div class="case-id">{escape(str(layer.get("name", "未命名层")))}</div>'
            f'<p class="subtle"><strong>指标分类：</strong>{escape(str(layer.get("category", "业务监控")))}</p>'
            f'<h4>{escape(str(layer.get("question", "当前层级用于监控售后服务链路。")))}</h4>'
            f'<p class="subtle"><strong>核心指标：</strong>{escape(metrics)}</p>'
            f'<p class="subtle"><strong>数据来源：</strong>{escape(str(layer.get("data_source", "Case 中台 + 业务系统")))}</p>'
            f'<p class="subtle"><strong>业务用途：</strong>{escape(str(layer.get("business_use", "用于定位链路问题并触发运营动作。")))}</p>'
            f'<p class="subtle"><strong>决策动作：</strong>{escape(str(layer.get("decision_use", "进入 owner 跟进和周报复盘。")))}</p>'
            "</div>"
        )
    if layer_cards:
        st.markdown(f'<div class="ops-grid">{"".join(layer_cards)}</div>', unsafe_allow_html=True)
    else:
        st.info("暂无指标地图数据。")

    st.markdown("#### 指标口径与动作看板")
    metric_rows = pd.DataFrame(metric_system.get("metric_rows", []))
    st.dataframe(metric_rows, use_container_width=True, hide_index=True)

    st.markdown("#### 异常诊断队列")
    anomaly_queue = metric_system.get("anomaly_queue", [])
    if anomaly_queue:
        st.dataframe(pd.DataFrame(anomaly_queue), use_container_width=True, hide_index=True)
    else:
        st.success("当前指标没有触发异常诊断。")

    action_left, action_right = st.columns([1, 1])
    with action_left:
        st.markdown("#### 优先动作")
        priority_actions = metric_system.get("priority_actions", [])
        if priority_actions:
            st.dataframe(pd.DataFrame(priority_actions), use_container_width=True, hide_index=True)
        else:
            st.info("暂无优先动作。")
    with action_right:
        st.markdown("#### 指标口径详情")
        definitions = metric_system.get("metric_definitions", [])
        if definitions:
            st.dataframe(pd.DataFrame(definitions), use_container_width=True, hide_index=True)
        else:
            st.info("暂无指标口径详情。")

    left, right = st.columns([1.2, 0.8])
    with left:
        st.markdown("#### 分层指标状态")
        if {"layer", "status"}.issubset(metric_rows.columns) and not metric_rows.empty:
            status_frame = (
                metric_rows.groupby(["layer", "status"])
                .size()
                .reset_index(name="count")
                .pivot(index="layer", columns="status", values="count")
                .fillna(0)
            )
            st.bar_chart(status_frame)
        else:
            st.info("暂无可绘制的分层状态数据。")
    with right:
        st.markdown("#### 管理节奏")
        st.dataframe(pd.DataFrame(metric_system.get("cadence", [])), use_container_width=True, hide_index=True)

    st.markdown("#### 指标治理规则")
    for item in metric_system.get("governance", []):
        st.markdown(
            f"""
            <div class="band">
                <strong>{item["rule"]}：</strong>{item["detail"]}
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_launch_logic() -> None:
    st.subheader("上线逻辑与边界")
    st.caption("把 6 个 demo 收束成真实系统上线逻辑：入口接入、AI 编排、Case 中台、运营后台和 2.0 优化闭环。")

    launch_steps = [
        ("01", "客户入口", "承接 Web Chat / 企业微信 / 客服系统输入", "当前由对客机器人模拟客户自然语言、补槽和风险识别。"),
        ("02", "AI 服务编排", "统一意图识别、RAG、风险判断和转人工决策", "当前由对客机器人、RAG、分类、VOC 模块组合呈现。"),
        ("03", "Case 中台", "用 case_id 串联用户、订单、对话、风险和知识引用", "当前已有 Case 列表、详情、状态流、反馈事件和 SQLite 接口。"),
        ("04", "运营后台", "承接人工接管、质检复核、指标监控和知识维护", "当前已有运营后台、运营指标、数据指标体系和人工回填样例。"),
        ("05", "2.0 优化层", "从 badcase、舆情、低质检和知识缺口中发现问题", "当前已有异常诊断、优先动作和反馈闭环入口。"),
    ]
    step_cards = []
    for index, title, goal, current in launch_steps:
        step_cards.append(
            '<div class="launch-card">'
            f'<div class="launch-index">{escape(index)}</div>'
            f'<h4>{escape(title)}</h4>'
            f'<p><strong>上线要求：</strong>{escape(goal)}</p>'
            f'<p><strong>原型覆盖：</strong>{escape(current)}</p>'
            "</div>"
        )
    st.markdown("#### 1.0 上线闭环")
    st.markdown(f'<div class="launch-flow">{"".join(step_cards)}</div>', unsafe_allow_html=True)

    col_left, col_right = st.columns(2)
    with col_left:
        st.markdown("#### 1.0 可上线边界")
        st.markdown(
            """
            <div class="band">
                <strong>目标：</strong>让系统能在真实售后流程中承接低风险问题、生成可追溯 case、识别高风险并转人工。<br>
                <strong>必须具备：</strong>渠道接入、身份映射、case 状态机、知识依据、人工接管、权限审计和基础指标监控。<br>
                <strong>不可越界：</strong>AI 不直接承诺赔付、退改、监管结论或最终责任归属。
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_right:
        st.markdown("#### 2.0 优化边界")
        st.markdown(
            """
            <div class="band">
                <strong>目标：</strong>让系统从运行数据中发现知识缺口、流程卡点、风险误判和质检问题。<br>
                <strong>优化对象：</strong>知识库、SOP、Prompt、风险规则、人工培训和服务指标口径。<br>
                <strong>审批要求：</strong>优化建议必须有人审核、灰度验证，并通过指标变化复盘效果。
            </div>
            """,
            unsafe_allow_html=True,
        )

    boundary_cards = [
        ("AI 可自主处理", "低风险、规则清晰、知识依据充分、无赔付承诺的标准咨询。", "生成标准答复，保留 knowledge_refs 和 decision_trace。"),
        ("AI 继续追问补槽", "订单号、物流节点、退款原因、联系方式等关键字段缺失。", "继续多轮补槽，不提前承诺处理结果。"),
        ("必须人工接管", "监管投诉、舆情扩散、赔付争议、政策冲突、用户强烈不满。", "next_action=human_handoff，生成 handoff_summary。"),
        ("进入优化闭环", "知识未命中、人工改写、质检低分、重复催办、投诉重开。", "生成反馈事件，进入知识/SOP/Prompt/规则优化队列。"),
    ]
    cards = []
    for title, scene, action in boundary_cards:
        cards.append(
            '<div class="boundary-card">'
            f'<div class="boundary-tag">{escape(title)}</div>'
            f'<p><strong>适用场景：</strong>{escape(scene)}</p>'
            f'<p><strong>系统动作：</strong>{escape(action)}</p>'
            "</div>"
        )
    st.markdown("#### 人机分工边界")
    st.markdown(f'<div class="boundary-grid">{"".join(cards)}</div>', unsafe_allow_html=True)

    st.markdown("#### 数据与表达边界")
    data_col, expression_col = st.columns(2)
    with data_col:
        st.markdown(
            """
            <div class="band">
                <strong>数据边界：</strong>
                当前业务指标使用 demo sample 模拟数据，用于展示监控口径、异常判断和决策动作。
                运营指标页仍保留系统使用指标，不与业务指标体系混用。
            </div>
            """,
            unsafe_allow_html=True,
        )
    with expression_col:
        st.markdown(
            """
            <div class="band">
                <strong>表达边界：</strong>
                当前系统定位为可落地的生产逻辑原型；可以说明具备真实上线链路理解，
                但不表述为已经接入真实企业客户系统、真实订单或真实客服渠道。
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_ai_native_logic() -> None:
    st.subheader("AI native 口径")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(
            """
            **反对的方式**

            - 把客服脚本自动化后包装成 AI。
            - 只展示单点工具提效。
            - 让模型直接替代人工责任判断。
            - 每个 demo 各自为政，没有统一 case。
            """
        )
    with col2:
        st.markdown(
            """
            **这套系统的方式**

            - AI 重新组织服务信息流和判断流。
            - case_id 串联客户、知识、风险、人工和质检。
            - 人机分工明确，高风险必须人工接管。
            - badcase、知识缺口、质检低分进入反馈闭环。
            """
        )


def main() -> None:
    inject_css()
    render_header()
    render_kpis()

    tab_arch, tab_demos, tab_cases, tab_ops, tab_metrics, tab_metric_system, tab_launch = st.tabs(
        ["系统架构", "demo 入口", "case 流转", "运营后台", "运营指标", "数据指标体系", "上线逻辑"]
    )

    with tab_arch:
        render_architecture()
        render_ai_native_logic()

    with tab_demos:
        render_demos()

    with tab_cases:
        render_case_flow()

    with tab_ops:
        render_operations_backend()

    with tab_metrics:
        render_ops_metrics_dashboard()

    with tab_metric_system:
        render_business_metric_system()

    with tab_launch:
        render_launch_logic()


if __name__ == "__main__":
    main()
