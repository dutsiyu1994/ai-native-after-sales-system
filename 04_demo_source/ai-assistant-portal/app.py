"""AI native after-sales service system portal.

The portal is a navigation and architecture console. It shows six business
demos through the production workflow layers:
customer entry -> AI orchestration -> case center -> operations backend ->
2.0 optimization.
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
class Layer:
    title: str
    subtitle: str
    items: tuple[str, ...]
    demos: tuple[str, ...]
    system_meaning: str


DEMOS = {
    "对客沟通机器人": DemoLink(
        name="对客沟通机器人",
        url_key="CUSTOMER_AGENT_URL",
        default_url="https://customer-agent-demo.streamlit.app/",
        layer="客户入口 / AI 服务编排层",
        purpose="承接客户自然语言输入，创建 case，完成多轮补槽、风险判断和转人工决策。",
        input_text="客户问题、订单号、时间、诉求、凭证、历史上下文",
        output_text="case_id、intent、slots、risk_tags、next_action、handoff_summary",
        boundary="不自动承诺退款、赔付、改签或监管结论。",
    ),
    "RAG 知识库": DemoLink(
        name="RAG 知识库",
        url_key="SERVICE_RAG_URL",
        default_url="https://service-rag-msydemo.streamlit.app/",
        layer="AI 服务编排层 / 运营后台",
        purpose="为 AI 判断和客服处理提供 SOP、政策、风险规则和知识引用依据。",
        input_text="客户问题、case 意图、风险标签、业务场景",
        output_text="knowledge_refs、evidence_status、human_confirm_required",
        boundary="知识未命中或冲突时不强答，高风险场景要求人工确认。",
    ),
    "客诉智能分类": DemoLink(
        name="客诉智能分类",
        url_key="COMPLAINT_CLASSIFIER_URL",
        default_url="https://complaint-classifier-demo.streamlit.app/",
        layer="AI 服务编排层 / Case 中台",
        purpose="将非结构化投诉转成问题类别、优先级和建议路由。",
        input_text="客户文本、历史摘要、来源渠道",
        output_text="category、priority、routing_label、suggested_action",
        boundary="低置信分类进入人工复核，不直接作为最终责任判断。",
    ),
    "VOC 风险识别": DemoLink(
        name="VOC 风险识别",
        url_key="VOC_RISK_URL",
        default_url="https://voc-risk-detector-demo.streamlit.app/",
        layer="AI 服务编排层 / 运营后台 / 2.0 优化层",
        purpose="识别监管投诉、赔付争议、舆情扩散、批量异常和重复未解决问题。",
        input_text="case 文本、风险词、时间趋势、批量反馈",
        output_text="risk_level、risk_tags、trend_signal、alert_reason",
        boundary="风险预警只触发优先级和人工介入，不替代业务责任决策。",
    ),
    "服务事件摘要": DemoLink(
        name="服务事件摘要",
        url_key="SUMMARY_SYSTEM_URL",
        default_url="https://summary-system-demo.streamlit.app/",
        layer="Case 中台 / 运营后台",
        purpose="将对话、日志和处理动作压缩成结构化摘要，支撑交接和回填。",
        input_text="客户对话、AI 判断、人工处理记录",
        output_text="case_summary、key_facts、pending_items、followup_notes",
        boundary="摘要用于辅助回填和交接，关键结论仍需人工确认。",
    ),
    "客服对话质检": DemoLink(
        name="客服对话质检",
        url_key="QUALITY_EVALUATOR_URL",
        default_url="https://cs-quality-evaluator-demo.streamlit.app/",
        layer="运营后台 / 2.0 优化层",
        purpose="从准确性、同理心、流程合规和承诺边界等维度评估服务质量。",
        input_text="AI/人工回复、case 摘要、知识引用、处理结果",
        output_text="quality_score、issue_tags、rewrite_suggestion、badcase_reason",
        boundary="自动质检负责发现疑点，争议样本进入人工复核。",
    ),
}


LAYERS = [
    Layer(
        title="客户入口",
        subtitle="Web Chat / 小程序 / 企业微信 / Zendesk / 飞书客服",
        items=(
            "接收客户自然语言售后问题",
            "识别客户身份、渠道和会话来源",
            "收集订单、物流、售后诉求和凭证",
        ),
        demos=("对客沟通机器人",),
        system_meaning="这是整个系统的信息输入端，目标是把客户原始表达转成可处理的服务事件。",
    ),
    Layer(
        title="AI 服务编排层",
        subtitle="意图识别 / 多轮补槽 / RAG 知识检索 / 风险判断 / 标准答复 / 转人工",
        items=(
            "识别 intent、slots、risk_tags 和客户情绪",
            "根据知识依据生成标准答复或继续追问",
            "高风险、低置信、政策冲突场景触发人工接管",
        ),
        demos=("对客沟通机器人", "RAG 知识库", "客诉智能分类", "VOC 风险识别"),
        system_meaning="这一层不是脚本自动化，而是把服务判断拆成可审计的 AI 决策流。",
    ),
    Layer(
        title="Case 中台",
        subtitle="case_id / 用户信息 / 订单字段 / 对话历史 / 风险标签 / 知识引用 / 人工记录 / 处理结果",
        items=(
            "用 case_id 串联客户消息、AI 判断和人工处理",
            "沉淀订单、物流、售后字段和知识引用",
            "保留人工接管记录、处理结果和状态变化",
        ),
        demos=("客诉智能分类", "服务事件摘要"),
        system_meaning="这一层是生产系统的数据底座，避免各模块只做孤立判断。",
    ),
    Layer(
        title="运营后台",
        subtitle="工单列表 / 人工接管台 / 知识库管理 / 质检审核 / 指标看板 / badcase 反馈",
        items=(
            "处理工单队列和高风险人工接管",
            "管理知识库、质检审核和指标看板",
            "记录 badcase、人工改写、知识未命中和客户反馈",
        ),
        demos=("RAG 知识库", "VOC 风险识别", "服务事件摘要", "客服对话质检"),
        system_meaning="这一层面向服务团队日常运营，让 AI 输出进入可管理、可复核、可追责流程。",
    ),
    Layer(
        title="2.0 优化层",
        subtitle="知识未命中分析 / 高频问题发现 / 转人工原因聚类 / 风险误判分析 / Prompt-SOP-知识库优化建议",
        items=(
            "从知识未命中、转人工原因和质检低分中发现系统问题",
            "聚类高频问题、风险误判和流程卡点",
            "生成 Prompt、SOP、知识库和追问策略优化建议",
        ),
        demos=("VOC 风险识别", "客服对话质检"),
        system_meaning="这一层体现系统从处理问题升级为发现问题、反馈问题并推动优化。",
    ),
]


SAMPLE_CASES = [
    {
        "case_id": "CASE-AIR-001",
        "topic": "航班延误退票赔付，并提到民航局投诉",
        "layer": "AI 服务编排层 -> 运营后台",
        "risk": "监管投诉 / 赔付争议",
        "next_action": "human_handoff",
    },
    {
        "case_id": "CASE-LOG-002",
        "topic": "物流迟迟未更新，第二轮补充订单号",
        "layer": "客户入口 -> Case 中台",
        "risk": "信息缺失 / 低风险",
        "next_action": "ask_followup",
    },
    {
        "case_id": "CASE-RAG-003",
        "topic": "咨询自愿退票手续费政策",
        "layer": "AI 服务编排层 -> RAG 知识检索",
        "risk": "低风险 / 知识命中",
        "next_action": "standard_answer",
    },
]


def inject_css() -> None:
    st.markdown(
        """
        <style>
        .block-container {
            padding-top: 1.25rem;
            padding-bottom: 2rem;
            max-width: 1280px;
        }
        h1, h2, h3, p, li, div {
            letter-spacing: 0;
        }
        .topbar {
            border-bottom: 1px solid #d9e2ec;
            padding-bottom: 14px;
            margin-bottom: 18px;
        }
        .topbar h1 {
            margin: 0 0 6px 0;
            color: #102a43;
            font-size: 30px;
            font-weight: 760;
        }
        .muted {
            color: #52606d;
            line-height: 1.65;
            font-size: 14px;
        }
        .layer-card {
            border: 1px solid #d9e2ec;
            border-radius: 8px;
            background: #ffffff;
            padding: 16px;
            margin-bottom: 14px;
        }
        .layer-card h3 {
            margin: 0 0 4px 0;
            color: #102a43;
            font-size: 20px;
        }
        .demo-card {
            border: 1px solid #d9e2ec;
            border-radius: 8px;
            background: #ffffff;
            padding: 16px;
            min-height: 292px;
            margin-bottom: 14px;
        }
        .demo-card h3 {
            margin-top: 0;
            margin-bottom: 8px;
            color: #102a43;
            font-size: 19px;
        }
        .pill {
            display: inline-block;
            padding: 3px 8px;
            border-radius: 999px;
            border: 1px solid #b2f5ea;
            background: #e6fffa;
            color: #0f766e;
            font-size: 12px;
            margin-right: 6px;
            margin-bottom: 8px;
        }
        .open-link {
            display: inline-block;
            padding: 8px 12px;
            border-radius: 6px;
            background: #0f766e;
            color: #ffffff !important;
            text-decoration: none;
            font-weight: 700;
            margin-top: 10px;
        }
        .case-row {
            border: 1px solid #d9e2ec;
            border-radius: 8px;
            padding: 12px;
            background: #ffffff;
            margin-bottom: 10px;
        }
        .risk-high {
            color: #b42318;
            font-weight: 700;
        }
        .risk-low {
            color: #0f766e;
            font-weight: 700;
        }
        .band {
            border: 1px solid #d9e2ec;
            border-radius: 8px;
            background: #f8fafc;
            padding: 16px;
            margin: 14px 0;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_header() -> None:
    st.markdown(
        """
        <div class="topbar">
            <h1>AI native 售后服务系统门户</h1>
            <div class="muted">
                这不是 6 个 AI 工具的罗列，而是按真实上线逻辑组织的售后服务系统入口。
                门户只负责展示系统逻辑层、模块入口、case 流转和上线边界；具体能力由 6 个业务 demo 承担。
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_kpis() -> None:
    cols = st.columns(5)
    cols[0].metric("逻辑层", "5", "入口到优化")
    cols[1].metric("业务 demo", "6", "门户统一导航")
    cols[2].metric("核心对象", "case_id", "贯穿全链路")
    cols[3].metric("高风险策略", "转人工", "赔付/监管/舆情")
    cols[4].metric("2.0 方向", "自主优化", "发现-反馈-改进")


def render_layer(layer: Layer) -> None:
    demo_tags = "".join(f'<span class="pill">{demo}</span>' for demo in layer.demos)
    items = "".join(f"<li>{item}</li>" for item in layer.items)
    st.markdown(
        f"""
        <div class="layer-card">
            <h3>{layer.title}</h3>
            <div class="muted"><strong>{layer.subtitle}</strong></div>
            <ul>{items}</ul>
            <div class="muted"><strong>系统意义：</strong>{layer.system_meaning}</div>
            <div style="margin-top:10px;">{demo_tags}</div>
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
            <div class="muted"><strong>职责：</strong>{demo.purpose}</div>
            <div class="muted"><strong>输入：</strong>{demo.input_text}</div>
            <div class="muted"><strong>输出：</strong>{demo.output_text}</div>
            <div class="muted"><strong>边界：</strong>{demo.boundary}</div>
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
    st.caption("这里展示的是后台应如何把客户问题映射到 case、风险、知识和人工动作。")
    for case in SAMPLE_CASES:
        high_risk = "监管" in case["risk"] or "赔付" in case["risk"]
        risk_class = "risk-high" if high_risk else "risk-low"
        st.markdown(
            f"""
            <div class="case-row">
                <strong>{case["case_id"]}</strong>
                <div class="muted">客户问题：{case["topic"]}</div>
                <div class="muted">流转层级：{case["layer"]}</div>
                <div class="{risk_class}">风险：{case["risk"]}</div>
                <div class="muted">下一步动作：{case["next_action"]}</div>
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
