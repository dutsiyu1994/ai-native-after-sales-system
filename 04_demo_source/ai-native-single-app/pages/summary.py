import sys, os

_SHARED = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _SHARED not in sys.path:
    sys.path.insert(0, _SHARED)

import streamlit as st
import pandas as pd
import jieba
from collections import Counter
from datetime import datetime

from ai_native_shared.case_store import list_cases, save_case
from ai_native_shared.case_schema import generate_case_id, build_case_context
from ai_native_shared.sample_cases import SAMPLE_CASES, RAW_TEST_INPUTS


# ── Mock 摘要生成 ──
def mock_generate_summary(text: str) -> dict:
    """Mock 智能摘要生成，基于规则提取关键词和摘要"""
    import re

    # 提取关键信息
    result = {
        "原文": text,
        "摘要": "",
        "关键词": [],
        "客户意图": "一般咨询",
        "情绪倾向": "中性",
        "核心诉求": "",
        "建议操作": "继续跟进",
    }

    # 规则摘要
    if "退款" in text or "退钱" in text or "赔付" in text:
        result["摘要"] = "客户提出退款/赔付诉求，情绪较为急切，需核实订单状态后处理。"
        result["客户意图"] = "退款赔付"
        result["核心诉求"] = "要求退款或赔付"
        if "投诉" in text or "民航局" in text:
            result["情绪倾向"] = "激烈"
            result["建议操作"] = "优先转人工处理，防范监管投诉风险"
        else:
            result["情绪倾向"] = "着急"
            result["建议操作"] = "核实订单信息，启动退款流程"
    elif "换货" in text or "坏了" in text or "质量问题" in text:
        result["摘要"] = "客户反映产品存在质量问题，要求换货处理，需提供相关证据后进行售后流程。"
        result["客户意图"] = "质量换货"
        result["核心诉求"] = "要求换货"
        result["建议操作"] = "引导客户提供订单号和问题证据"
    elif "物流" in text or "快递" in text or "没到" in text:
        result["摘要"] = "客户查询物流配送进度，需核实订单号后提供最新物流状态。"
        result["客户意图"] = "物流咨询"
        result["核心诉求"] = "查询物流进度"
        result["建议操作"] = "查询物流状态并告知客户预计到达时间"
    elif "投诉" in text:
        result["摘要"] = "客户表达不满情绪，提出投诉，需安抚后了解具体情况并给出解决方案。"
        result["客户意图"] = "客户投诉"
        result["情绪倾向"] = "不满"
        result["核心诉求"] = "投诉处理和方案"
        result["建议操作"] = "安抚客户情绪，了解具体投诉原因，给出解决方案"
    else:
        result["摘要"] = f"客户咨询：「{text}」，需进一步了解具体需求后提供相应服务。"
        result["客户意图"] = "一般咨询"
        result["核心诉求"] = text[:50]

    # 提取关键词（jieba + 规则）
    words = jieba.lcut(text)
    stop_words = {"的", "了", "在", "是", "我", "有", "和", "就", "不", "人", "都", "一", "一个", "上", "也", "很", "到", "说", "要", "去", "你", "会", "着", "没有", "看", "好", "自己", "这"}
    keywords = [w for w in words if len(w) >= 2 and w not in stop_words]

    # 加入领域关键词
    domain_keywords = []
    if any(kw in text for kw in ["退款", "退票", "退钱", "赔付", "赔偿"]):
        domain_keywords.append("退款")
    if any(kw in text for kw in ["换货", "坏了", "维修", "质量问题"]):
        domain_keywords.append("质量")
    if any(kw in text for kw in ["物流", "快递", "配送", "没到"]):
        domain_keywords.append("物流")
    if any(kw in text for kw in ["投诉", "民航局", "12315", "曝光"]):
        domain_keywords.append("投诉")

    keywords = list(set(keywords + domain_keywords))
    # 去重并排序
    word_counts = Counter(keywords)
    top_keywords = [w for w, _ in word_counts.most_common(8)]
    result["关键词"] = top_keywords

    return result


def render():
    st.title("📝 智能总结")
    st.markdown("---")

    tab1, tab2 = st.tabs(["📝 摘要生成", "📋 历史摘要"])

    with tab1:
        st.subheader("输入要生成摘要的文本")

        # 示例文本选择
        sample_texts = ["选择一条示例..."] + RAW_TEST_INPUTS
        selected_sample = st.selectbox("快速选择示例文本：", sample_texts)

        default_text = selected_sample if selected_sample != "选择一条示例..." else "我在你们平台买的蓝牙耳机用了三天就充不进电了，要求换货。"

        input_text = st.text_area("文本内容：", value=default_text, height=120)

        col1, col2 = st.columns([1, 3])

        with col1:
            generate_btn = st.button("✨ 生成摘要", type="primary", use_container_width=True)

        with col2:
            st.caption("系统将自动提取摘要、关键词和客户意图。支持中英文混合输入。")

        if generate_btn and input_text.strip():
            result = mock_generate_summary(input_text)

            st.markdown("---")
            st.subheader("📊 摘要结果")

            # 摘要
            st.info(f"**摘要**：{result['摘要']}")

            # 关键信息
            mcol1, mcol2, mcol3 = st.columns(3)
            with mcol1:
                st.metric("客户意图", result["客户意图"])
            with mcol2:
                st.metric("情绪倾向", result["情绪倾向"])
            with mcol3:
                st.metric("建议操作", result["建议操作"])

            # 关键词
            st.subheader("🏷️ 关键词")
            keywords_html = " ".join([f"<span style='background-color:#e0e0e0;padding:2px 8px;border-radius:12px;margin:4px;display:inline-block'>{kw}</span>" for kw in result["关键词"]])
            st.markdown(keywords_html, unsafe_allow_html=True)

            # 核心诉求
            st.subheader("🎯 核心诉求")
            st.write(result["核心诉求"])

            # 保存案例
            case_id = generate_case_id()
            ctx = build_case_context(
                customer_message=input_text,
                customer_intent=result["客户意图"],
                case_id=case_id,
                next_action="human_handoff" if result["情绪倾向"] == "激烈" else "continue_inquiry",
                risk_tags=[],
            )
            save_case(ctx)

            st.success(f"摘要已生成并保存为案例 {case_id}")

        elif generate_btn:
            st.warning("请输入文本内容。")

    with tab2:
        st.subheader("📋 历史摘要记录")
        recent_cases = list_cases(limit=10)
        if recent_cases:
            history_rows = []
            for c in recent_cases:
                history_rows.append({
                    "案例 ID": c.get("case_id", ""),
                    "意图": c.get("customer_intent", ""),
                    "消息": c.get("customer_message", "")[:60] + ("..." if len(c.get("customer_message", "")) > 60 else ""),
                    "时间": c.get("created_at", ""),
                })
            st.dataframe(pd.DataFrame(history_rows), use_container_width=True, hide_index=True)
        else:
            st.info("暂无历史摘要记录。请先在上方 Tab 生成摘要。")


render()
