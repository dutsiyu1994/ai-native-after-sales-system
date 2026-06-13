import sys, os

_SHARED = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _SHARED not in sys.path:
    sys.path.insert(0, _SHARED)

import streamlit as st
import pandas as pd
from datetime import datetime

from ai_native_shared.case_store import list_cases, count_cases
from ai_native_shared.feedback_store import get_events, count_by_type
from ai_native_shared.metrics_engine import compute_metrics
from ai_native_shared.sample_cases import SAMPLE_CASES


def render():
    st.title("🏠 系统控制台")
    st.markdown("---")

    # 初始化示例数据（首次访问时写入样例）
    all_cases = list_cases()
    if len(all_cases) < 3:
        from ai_native_shared.case_store import save_case
        for c in SAMPLE_CASES:
            save_case(c)
        all_cases = list_cases()

    # ── 概览指标卡片 ──
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        total = count_cases()
        st.metric("📋 总案例数", total)
    with col2:
        events = get_events()
        st.metric("📌 反馈事件", len(events))
    with col3:
        by_type = count_by_type()
        total_events = sum(by_type.values())
        st.metric("📊 事件类型数", len(by_type))
    with col4:
        metrics = compute_metrics(all_cases)
        auto_rate = metrics.get("auto_resolve_rate", 0)
        st.metric("🤖 自动解决率", f"{auto_rate:.1f}%")

    # ── 指标详情 ──
    st.markdown("---")
    st.subheader("📈 运行指标概览")

    if metrics.get("insufficient_data"):
        st.info("数据量不足（< 3 条），部分指标暂不显示。继续使用各模块将积累更多数据。")
    else:
        mcol1, mcol2, mcol3 = st.columns(3)
        with mcol1:
            st.metric("🔄 自动解决率", f"{metrics['auto_resolve_rate']:.1f}%",
                      help=f"自动解决 {metrics['auto_resolve_count']} / 总计 {metrics['total_cases']}")
            st.metric("🧑‍💼 转人工率", f"{metrics['handoff_rate']:.1f}%",
                      help=f"转人工 {metrics['handoff_count']} / 总计 {metrics['total_cases']}")
        with mcol2:
            st.metric("📖 知识命中率", f"{metrics['knowledge_hit_rate']:.1f}%",
                      help=f"命中 {metrics['knowledge_hit_count']} / 未命中 {metrics['knowledge_miss_count']}")
            st.metric("📝 字段完整率", f"{metrics['field_completion_rate']:.1f}%")
        with mcol3:
            risk_dist = metrics.get("risk_tag_distribution", {})
            if risk_dist:
                st.write("**🏷️ 风险标签分布**")
                for tag, cnt in sorted(risk_dist.items(), key=lambda x: -x[1]):
                    st.caption(f"{tag}: {cnt}")

    # ── 日趋势 ──
    trends = metrics.get("daily_case_trends", {})
    if trends:
        st.subheader("📅 每日案例趋势")
        trend_df = pd.DataFrame(list(trends.items()), columns=["日期", "案例数"])
        st.bar_chart(trend_df.set_index("日期"))

    # ── 最近案例列表 ──
    st.markdown("---")
    st.subheader("📋 最近案例")

    recent = list_cases(limit=10)
    if recent:
        rows = []
        for c in recent:
            rows.append({
                "案例 ID": c.get("case_id", ""),
                "客户意图": c.get("customer_intent", ""),
                "创建时间": c.get("created_at", ""),
                "风险标签": ", ".join(c.get("risk_tags", []) or []),
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.info("暂无案例数据。请到其他模块创建案例。")

    # ── 快速跳转 ──
    st.markdown("---")
    st.subheader("🚀 快速跳转")
    quick = st.columns(4)
    with quick[0]:
        st.page_link("pages/customer_agent.py", label="🤖 对客机器人", use_container_width=True)
    with quick[1]:
        st.page_link("pages/complaint_classifier.py", label="🔍 客诉分类", use_container_width=True)
    with quick[2]:
        st.page_link("pages/voc_risk.py", label="⚠️ VOC 风险", use_container_width=True)
    with quick[3]:
        st.page_link("pages/rag_kb.py", label="📚 RAG 知识库", use_container_width=True)


render()
