import sys, os

_SHARED = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _SHARED not in sys.path:
    sys.path.insert(0, _SHARED)

import streamlit as st
import pandas as pd

from ai_native_shared.knowledge_base import KNOWLEDGE_CHUNKS, retrieve_knowledge, has_sufficient_evidence
from ai_native_shared.feedback_store import save_event


def render():
    st.title("📚 RAG 知识库")
    st.markdown("---")

    tab1, tab2 = st.tabs(["🔍 知识检索", "📖 知识库浏览"])

    with tab1:
        st.subheader("🔍 知识检索")
        st.caption("输入问题，系统将基于关键词匹配检索相关知识片段。")

        query = st.text_input("请输入您的问题：", placeholder="例如：退款规则、退换货流程、物流异常处理...")

        col1, col2 = st.columns([1, 3])
        with col1:
            top_k = st.slider("返回结果数", min_value=1, max_value=5, value=3)
        with col2:
            search_btn = st.button("🔍 检索", type="primary", use_container_width=True)

        if search_btn and query.strip():
            with st.spinner("正在检索知识库..."):
                results = retrieve_knowledge(query, top_k=top_k)

            if results:
                st.success(f"找到 {len(results)} 条相关知识。")

                for i, r in enumerate(results):
                    with st.expander(f"📄 #{i+1} [{r['source']}] {r['title']} (匹配度: {r['score']:.3f})", expanded=i == 0):
                        st.markdown(r["text"])
                        st.caption(f"来源: {r['source']} | 片段: {r['chunk_id']} | 匹配度: {r['score']:.3f}")

                # 是否足够回答问题
                sufficient = has_sufficient_evidence(results)
                if sufficient:
                    st.success("✅ 知识检索结果充足，可以基于此回答问题。")
                else:
                    st.warning("⚠️ 检索结果匹配度偏低，建议补充知识或转人工处理。")

                # 记录知识命中事件
                save_event(
                    case_id="",
                    event_type="knowledge_miss" if not sufficient else "human_modification",
                    source_module="rag",
                    description=f"知识检索: {query} — {'命中' if sufficient else '未命中'}",
                    root_cause="knowledge_gap" if not sufficient else "knowledge_gap",
                    priority="P2",
                )
            else:
                st.warning("未找到相关知识片段。请尝试换个关键词提问。")

                # 记录知识未命中
                save_event(
                    case_id="",
                    event_type="knowledge_miss",
                    source_module="rag",
                    description=f"知识未命中: {query}",
                    root_cause="knowledge_gap",
                    priority="P2",
                    suggested_action="补充知识库相关条目",
                )
        elif search_btn:
            st.warning("请输入问题后再检索。")

        # 常见问题快速检索
        st.markdown("---")
        st.subheader("💡 常见问题快速检索")
        quick_qs = ["退款规则", "退换货流程", "物流异常处理", "投诉处理流程", "客服沟通话术"]
        cols = st.columns(len(quick_qs))
        for i, q in enumerate(quick_qs):
            with cols[i]:
                if st.button(q, use_container_width=True, key=f"quick_{i}"):
                    results = retrieve_knowledge(q, top_k=3)
                    st.session_state["rag_results"] = results
                    st.session_state["rag_query"] = q
                    st.rerun()

        # 显示快速检索结果
        if "rag_results" in st.session_state and st.session_state["rag_results"]:
            st.markdown("---")
            st.subheader(f"📊 检索结果：{st.session_state.get('rag_query', '')}")
            for i, r in enumerate(st.session_state["rag_results"]):
                with st.expander(f"📄 #{i+1} [{r['source']}] {r['title']} (匹配度: {r['score']:.3f})", expanded=i == 0):
                    st.markdown(r["text"])

    with tab2:
        st.subheader("📖 知识库总览")
        st.caption(f"共 {len(KNOWLEDGE_CHUNKS)} 条知识片段")

        # 按来源分组
        source_groups = {}
        for chunk in KNOWLEDGE_CHUNKS:
            source_groups.setdefault(chunk.source, []).append(chunk)

        for source, chunks in source_groups.items():
            with st.expander(f"📁 {source}（{len(chunks)} 条）"):
                for c in chunks:
                    st.markdown(f"**{c.title}**")
                    st.caption(c.text[:200] + ("..." if len(c.text) > 200 else ""))
                    st.markdown("---")


render()
