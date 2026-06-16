"""AI native after-sales service system portal.

This portal presents the six Streamlit demos as one production-oriented
after-sales service system: customer entry, AI orchestration, case center,
operations backend, and the 2.0 optimization layer.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

import streamlit as st


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
        @media (max-width: 900px) {
            .hero-grid,
            .layer-card,
            .case-row {
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


def render_kpis() -> None:
    cols = st.columns(5)
    cols[0].metric("逻辑层", "5", "入口到优化")
    cols[1].metric("业务 Demo", "6", "门户统一导航")
    cols[2].metric("核心对象", "case_id", "贯穿全链路")
    cols[3].metric("高风险策略", "转人工", "赔付 / 监管 / 舆情")
    cols[4].metric("2.0 方向", "自主优化", "发现 - 反馈 - 改进")


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


def render_launch_logic() -> None:
    st.subheader("上线逻辑与边界")
    st.markdown(
        """
        | 层级 | 当前展示方式 | 真实生产要补齐 |
        | --- | --- | --- |
        | 客户入口 | 对客机器人 demo | 真实渠道接入、身份鉴权、会话持久化 |
        | AI 服务编排层 | 对客机器人、RAG、分类、VOC demo | 统一 Agent 决策服务、模型日志、置信度和安全策略 |
        | Case 中台 | 门户用样例 case 呈现 | 数据库、状态机、字段模型、人工接管记录 |
        | 运营后台 | RAG、摘要、质检、VOC demo | 工单队列、权限、审计、指标看板、知识发布流程 |
        | 2.0 优化层 | VOC 和质检展示方向 | 聚类、归因、优化建议、审批、灰度和效果追踪 |
        """
    )
    st.markdown(
        """
        <div class="band">
            <strong>表达边界：</strong>
            当前系统是生产逻辑原型，不表述为已经接入真实客户系统。
            可强调已经具备完整上线逻辑理解：输入端、编排层、case 中台、运营后台和 2.0 优化闭环。
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

    tab_arch, tab_demos, tab_cases, tab_launch = st.tabs(
        ["系统架构", "demo 入口", "case 流转", "上线逻辑"]
    )

    with tab_arch:
        render_architecture()
        render_ai_native_logic()

    with tab_demos:
        render_demos()

    with tab_cases:
        render_case_flow()

    with tab_launch:
        render_launch_logic()


if __name__ == "__main__":
    main()
