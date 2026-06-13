import sys, os

_SHARED = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _SHARED not in sys.path:
    sys.path.insert(0, _SHARED)

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

from ai_native_shared.case_store import list_cases, save_case
from ai_native_shared.case_schema import generate_case_id, build_case_context
from ai_native_shared.sample_cases import SAMPLE_CASES


# ── 示例 VOC 数据 ──
def generate_sample_voc_data() -> pd.DataFrame:
    """生成示例 VOC 风险检测数据"""
    import random
    now = datetime.now()
    records = []
    sources = ["在线客服", "电话客服", "社交媒体", "邮件投诉", "在线评价"]
    intents = ["物流咨询", "退换货", "退款赔付", "投诉", "产品咨询", "账号问题"]
    risk_labels = ["低风险", "低风险", "低风险", "中风险", "中风险", "高风险"]

    for i in range(20):
        ts = (now - timedelta(hours=random.randint(1, 48), minutes=random.randint(0, 59))).strftime("%Y-%m-%d %H:%M")
        records.append({
            "案例 ID": f"VOC-{i+1:04d}",
            "时间": ts,
            "来源": random.choice(sources),
            "内容": f"示例投诉内容 {i+1}",
            "意图": random.choice(intents),
            "风险评分": round(random.uniform(0.1, 0.95), 2),
            "风险等级": random.choice(risk_labels),
        })

    df = pd.DataFrame(records)
    df = df.sort_values("风险评分", ascending=False).reset_index(drop=True)
    return df


def mock_risk_analysis(texts: list) -> list[dict]:
    """Mock 风险分析"""
    results = []
    for text in texts:
        risk_score = 0.1
        risk_tags = []

        if any(kw in text for kw in ["民航局", "12315", "曝光", "媒体", "律师", "起诉"]):
            risk_score = max(risk_score, 0.9)
            risk_tags.append("监管投诉风险")
        if any(kw in text for kw in ["退款", "退钱", "赔付", "赔偿"]):
            risk_score = max(risk_score, 0.7)
            risk_tags.append("赔付风险")
        if any(kw in text for kw in ["生气", "愤怒", "欺诈", "欺骗"]):
            risk_score = max(risk_score, 0.8)
            risk_tags.append("情绪激烈")
        if any(kw in text for kw in ["集体", "大家", "一起", "维权"]):
            risk_score = max(risk_score, 0.85)
            risk_tags.append("集体维权风险")

        risk_level = "高风险" if risk_score >= 0.7 else "中风险" if risk_score >= 0.4 else "低风险"
        results.append({
            "内容": text,
            "风险评分": round(risk_score, 2),
            "风险等级": risk_level,
            "风险标签": ", ".join(risk_tags) if risk_tags else "无",
            "建议动作": "立即转人工" if risk_level == "高风险" else "优先处理" if risk_level == "中风险" else "自动回复",
        })
    return results


def render():
    st.title("⚠️ VOC 风险检测")
    st.markdown("---")

    # ── 加载示例数据 ──
    if "voc_data" not in st.session_state:
        st.session_state.voc_data = generate_sample_voc_data()

    df = st.session_state.voc_data

    # ── 概览指标 ──
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        total = len(df)
        st.metric("📋 检测总数", total)
    with col2:
        high_risk = len(df[df["风险等级"] == "高风险"])
        st.metric("🔴 高风险", high_risk)
    with col3:
        mid_risk = len(df[df["风险等级"] == "中风险"])
        st.metric("🟡 中风险", mid_risk)
    with col4:
        low_risk = len(df[df["风险等级"] == "低风险"])
        st.metric("🟢 低风险", low_risk)

    # ── 风险分布图表 ──
    st.markdown("---")
    st.subheader("📊 风险分布")

    tab1, tab2, tab3 = st.tabs(["风险等级分布", "来源分布", "风险评分分布"])
    with tab1:
        risk_counts = df["风险等级"].value_counts().reset_index()
        risk_counts.columns = ["风险等级", "数量"]
        fig = px.pie(risk_counts, values="数量", names="风险等级",
                      color="风险等级",
                      color_discrete_map={"高风险": "#ff4444", "中风险": "#ffaa00", "低风险": "#44bb44"},
                      title="风险等级分布")
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        source_counts = df["来源"].value_counts()
        fig2 = px.bar(source_counts, title="来源分布", labels={"index": "来源", "value": "数量"})
        st.plotly_chart(fig2, use_container_width=True)

    with tab3:
        fig3 = px.histogram(df, x="风险评分", nbins=10, title="风险评分分布",
                             color_discrete_sequence=["#ff6b6b"])
        st.plotly_chart(fig3, use_container_width=True)

    # ── 数据表格 ──
    st.markdown("---")
    st.subheader("📋 风险检测数据")
    st.dataframe(df, use_container_width=True, hide_index=True)

    # ── 自定义检测 ──
    st.markdown("---")
    st.subheader("🔍 自定义风险检测")
    custom_text = st.text_area(
        "输入文本进行风险检测（每行一条）：",
        value="航班延误后我要求退票赔付，如果今天不给方案我就投诉到民航局。\n我三天前买的快递还没到，能帮我查一下吗？",
        height=100,
    )

    if st.button("开始检测", type="primary", use_container_width=True):
        texts = [t.strip() for t in custom_text.split("\n") if t.strip()]
        if texts:
            results = mock_risk_analysis(texts)
            result_df = pd.DataFrame(results)

            st.subheader("📊 检测结果")
            st.dataframe(result_df, use_container_width=True, hide_index=True)

            # 保存为 case
            for i, r in enumerate(results):
                case_id = generate_case_id()
                ctx = build_case_context(
                    customer_message=r["内容"],
                    risk_tags=r["风险标签"].split(", ") if r["风险标签"] != "无" else [],
                    next_action="human_handoff" if r["风险等级"] == "高风险" else "continue_inquiry",
                    case_id=case_id,
                )
                save_case(ctx)

            st.success(f"已检测 {len(texts)} 条文本，高风险 {len([r for r in results if r['风险等级']=='高风险'])} 条。")

    # ── 刷新数据 ──
    st.markdown("---")
    if st.button("🔄 刷新示例数据"):
        st.session_state.voc_data = generate_sample_voc_data()
        st.rerun()


render()
