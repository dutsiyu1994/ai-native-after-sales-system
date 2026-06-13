import sys, os

_SHARED = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _SHARED not in sys.path:
    sys.path.insert(0, _SHARED)

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

from ai_native_shared.case_store import list_cases, count_cases, save_case
from ai_native_shared.feedback_store import get_events, count_by_type, count_by_priority, get_unresolved, resolve_event, save_event
from ai_native_shared.metrics_engine import compute_metrics
from ai_native_shared.insight_engine import generate_insights
from ai_native_shared.sample_cases import SAMPLE_CASES


def render():
    st.title("📊 指标 / 反馈 / 2.0 优化")
    st.markdown("---")

    # ── 初始化数据 ──
    all_cases = list_cases()
    if len(all_cases) < 3:
        for c in SAMPLE_CASES:
            save_case(c)
        all_cases = list_cases()

    all_events = get_events()

    # ── 三个主 Tab ──
    tab1, tab2, tab3 = st.tabs(["📊 指标看板", "📋 反馈事件", "💡 2.0 优化建议"])

    # =========================================================
    # Tab 1: 指标看板
    # =========================================================
    with tab1:
        st.subheader("📊 系统运行指标")

        metrics = compute_metrics(all_cases)

        if metrics.get("insufficient_data"):
            st.info("数据量不足（< 3 条），暂时无法计算完整指标。请在其他模块多创建一些案例。")
            # 显示已有 case 数
            st.metric("当前案例数", metrics["total_cases"])
        else:
            # 概览指标卡片
            mcol1, mcol2, mcol3, mcol4 = st.columns(4)
            with mcol1:
                st.metric("📋 总案例数", metrics["total_cases"])
            with mcol2:
                st.metric("🤖 自动解决率", f"{metrics['auto_resolve_rate']:.1f}%",
                          help=f"自动解决 {metrics['auto_resolve_count']} 条")
            with mcol3:
                st.metric("🧑‍💼 转人工率", f"{metrics['handoff_rate']:.1f}%",
                          help=f"转人工 {metrics['handoff_count']} 条")
            with mcol4:
                st.metric("📖 知识命中率", f"{metrics['knowledge_hit_rate']:.1f}%",
                          help=f"命中 {metrics['knowledge_hit_count']} / 未命中 {metrics['knowledge_miss_count']}")

            # 指标图表
            st.markdown("---")
            chart_col1, chart_col2 = st.columns(2)

            with chart_col1:
                # 风险标签分布
                risk_dist = metrics.get("risk_tag_distribution", {})
                if risk_dist:
                    st.subheader("🏷️ 风险标签分布")
                    risk_df = pd.DataFrame(list(risk_dist.items()), columns=["风险标签", "数量"])
                    fig = px.bar(risk_df, x="风险标签", y="数量", color="风险标签",
                                 title="风险标签分布")
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("暂无风险标签数据。")

            with chart_col2:
                # 转人工原因分布
                handoff_reasons = metrics.get("handoff_reasons", {})
                if handoff_reasons:
                    st.subheader("🔄 转人工原因分布")
                    ho_df = pd.DataFrame(list(handoff_reasons.items()), columns=["原因", "数量"])
                    fig2 = px.pie(ho_df, values="数量", names="原因", title="转人工原因分布")
                    st.plotly_chart(fig2, use_container_width=True)
                else:
                    st.info("暂无转人工原因数据。")

            # 日趋势
            trends = metrics.get("daily_case_trends", {})
            if trends:
                st.subheader("📅 每日案例趋势")
                trend_df = pd.DataFrame(list(trends.items()), columns=["日期", "案例数"])
                fig3 = px.line(trend_df, x="日期", y="案例数", markers=True, title="每日案例趋势")
                st.plotly_chart(fig3, use_container_width=True)

            # 混合指标
            st.markdown("---")
            st.subheader("📊 核心指标对比")
            bar_df = pd.DataFrame({
                "指标": ["自动解决率", "转人工率", "知识命中率", "字段完整率"],
                "百分比": [
                    metrics["auto_resolve_rate"],
                    metrics["handoff_rate"],
                    metrics["knowledge_hit_rate"],
                    metrics["field_completion_rate"],
                ],
            })
            fig4 = px.bar(bar_df, x="指标", y="百分比", color="指标",
                          title="核心指标对比",
                          text=bar_df["百分比"].apply(lambda x: f"{x:.1f}%"))
            fig4.update_traces(textposition="outside")
            st.plotly_chart(fig4, use_container_width=True)

    # =========================================================
    # Tab 2: 反馈事件
    # =========================================================
    with tab2:
        st.subheader("📋 反馈事件管理")

        events = get_events()
        if not events:
            st.info("暂无反馈事件。在各模块操作后将自动生成事件记录。")

            # 生成一些示例事件
            st.markdown("---")
            if st.button("📝 生成示例反馈事件", type="secondary"):
                sample_events = [
                    ("knowledge_miss", "RAG", "知识未命中: 退款规则变更", "knowledge_gap", "P2"),
                    ("handoff_reason", "customer_agent", "客户要求转人工处理投诉", "process_block", "P1"),
                    ("quality_low_score", "quality_evaluator", "质检低分: 共情不足", "script_issue", "P2"),
                    ("inquiry_failure", "customer_agent", "追问失败: 订单号重复追问", "prompt_issue", "P1"),
                ]
                for evt_type, src, desc, root, pri in sample_events:
                    save_event(
                        case_id="SAMPLE",
                        event_type=evt_type,
                        source_module=src,
                        description=desc,
                        root_cause=root,
                        priority=pri,
                    )
                st.success("已生成 4 条示例反馈事件。")
                st.rerun()
        else:
            # 按类型统计
            by_type = count_by_type()
            by_priority = count_by_priority()

            ecol1, ecol2, ecol3 = st.columns(3)
            with ecol1:
                st.metric("📌 总事件数", len(events))
            with ecol2:
                st.metric("📊 类型数", len(by_type))
            with ecol3:
                unresolved = len([e for e in events if not e.get("is_resolved")])
                st.metric("⏳ 未解决", unresolved)

            # 事件列表
            st.subheader("事件列表")
            event_df = pd.DataFrame(events)
            if not event_df.empty:
                display_cols = [c for c in ["id", "event_type", "description", "source_module", "priority", "created_at", "is_resolved"] if c in event_df.columns]
                st.dataframe(event_df[display_cols], use_container_width=True, hide_index=True)

            # 未解决事件
            st.markdown("---")
            st.subheader("⏳ 未解决事件")
            unresolved_events = [e for e in events if not e.get("is_resolved")]
            if unresolved_events:
                for i, evt in enumerate(unresolved_events[:5]):
                    col1, col2 = st.columns([5, 1])
                    with col1:
                        st.caption(f"[{evt.get('priority', 'P2')}] {evt.get('event_type', '')} — {evt.get('description', '')[:60]}")
                    with col2:
                        if st.button(f"✅ 解决", key=f"resolve_{evt.get('id', i)}", use_container_width=True):
                            resolve_event(evt["id"])
                            st.rerun()
            else:
                st.success("所有事件已解决！🎉")

    # =========================================================
    # Tab 3: 2.0 优化建议
    # =========================================================
    with tab3:
        st.subheader("💡 2.0 自主优化建议")
        st.caption("基于反馈事件和案例数据自动分析，发现系统短板并生成可执行的优化建议。")

        # 生成洞察
        events_for_insight = get_events()
        all_insights = []

        if not events_for_insight:
            st.info("暂无反馈事件数据，请先在「反馈事件」Tab 生成示例事件。")
        else:
            with st.spinner("正在分析反馈数据..."):
                all_insights = generate_insights(events_for_insight, all_cases)

            if not all_insights:
                st.info("当前数据量不足以生成优化洞察（需要至少 2 条同类反馈事件进行聚类）。")
            else:
                st.success(f"生成 {len(all_insights)} 条优化洞察建议。")

                # 按热度排序
                all_insights.sort(key=lambda x: x.get("hot_score", 0), reverse=True)

                for insight in all_insights:
                    issue_type = insight.get("issue_type", "")
                    priority = insight.get("priority", "P3")
                    hot_score = insight.get("hot_score", 0)

                    # 类型 emoji
                    type_icons = {
                        "knowledge_gap": "📖",
                        "rule_conflict": "⚖️",
                        "process_block": "🔧",
                        "prompt_issue": "💬",
                        "quality_issue": "⭐",
                    }
                    icon = type_icons.get(issue_type, "💡")

                    with st.expander(
                        f"{icon} [{priority}] {insight.get('title', '')} — 热度 {hot_score}",
                        expanded=hot_score >= 3,
                    ):
                        st.markdown(f"**描述**：{insight.get('description', '')}")
                        st.markdown(f"**根因分类**：{issue_type}")
                        st.markdown(f"**优先级**：{priority} | **热度评分**：{hot_score}")
                        st.markdown(f"**建议优化动作**：")
                        st.info(insight.get('suggested_action', ''))
                        related = insight.get('related_case_ids', [])
                        if related:
                            st.caption(f"关联案例：{', '.join(related[:5])}")


render()
