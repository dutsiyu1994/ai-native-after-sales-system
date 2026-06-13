import sys, os

_SHARED = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _SHARED not in sys.path:
    sys.path.insert(0, _SHARED)

import streamlit as st
import pandas as pd
from datetime import datetime

from ai_native_shared.sample_cases import SAMPLE_CASES


# ── 简单规则分类器 ──
def classify_complaint(text: str) -> dict:
    """基于关键词的简单客诉分类"""
    result = {
        "类别": "一般咨询",
        "子类": "其他",
        "优先级": "P3",
        "情绪等级": "中性",
        "需要转人工": False,
    }

    # 优先级检测
    if any(kw in text for kw in ["民航局", "12315", "曝光", "媒体", "律师", "起诉"]):
        result["类别"] = "监管投诉风险"
        result["优先级"] = "P0"
        result["需要转人工"] = True
        result["情绪等级"] = "激烈"
    elif any(kw in text for kw in ["退款", "退钱", "赔付", "赔偿", "补偿"]):
        result["类别"] = "退款赔付"
        result["子类"] = "退款诉求"
        result["优先级"] = "P1"
    elif any(kw in text for kw in ["换货", "坏了", "质量问题", "维修"]):
        result["类别"] = "退换货"
        result["子类"] = "质量退换"
        result["优先级"] = "P2"
    elif any(kw in text for kw in ["物流", "快递", "没到", "配送", "慢"]):
        result["类别"] = "物流咨询"
        result["子类"] = "物流进度"
        result["优先级"] = "P3"
    elif any(kw in text for kw in ["投诉", "不满", "差评"]):
        result["类别"] = "客户投诉"
        result["子类"] = "服务投诉"
        result["优先级"] = "P1"
        result["需要转人工"] = True
        result["情绪等级"] = "不满"

    # 情绪等级判断
    if any(kw in text for kw in ["生气", "愤怒", "欺诈", "欺骗", "骗子"]):
        result["情绪等级"] = "激烈"
        result["需要转人工"] = True
    elif any(kw in text for kw in ["着急", "急", "催"]):
        result["情绪等级"] = "着急"

    return result


def mock_classifier_summary(classified: list) -> str:
    """Mock LLM 分类总结"""
    cats = {}
    for item in classified:
        cat = item.get("类别", "未知")
        cats[cat] = cats.get(cat, 0) + 1
    parts = [f"{k} {v}条" for k, v in sorted(cats.items(), key=lambda x: -x[1])]
    return "分类完成。" + "；".join(parts) + "。"


def render():
    st.title("🔍 客诉分类")
    st.markdown("---")

    # ── 示例投诉列表 ──
    st.subheader("📋 示例投诉列表")
    raw_inputs = [
        "航班延误后我要求退票赔付，如果今天不给方案我就投诉到民航局。",
        "我在你们平台买的蓝牙耳机用了三天就充不进电了，要求换货。",
        "我三天前买的快递怎么还没到？能帮我查一下物流进度吗？",
        "你们这是在欺骗消费者！我要求全额退款并赔偿我的时间损失。",
        "帮我查一下 CA1234 航班今天有没有延误。",
        "你们的客服态度太差了，我要去12315投诉！",
    ]

    sample_df = pd.DataFrame(raw_inputs, columns=["客户投诉内容"])
    st.dataframe(sample_df, use_container_width=True, hide_index=True)

    # ── 分类操作 ──
    st.markdown("---")
    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader("🎯 分类测试")
        input_text = st.text_area(
            "输入投诉文本进行试分类：",
            value="我在你们平台买的蓝牙耳机用了三天就充不进电了，要求换货。",
            height=100,
        )
    with col2:
        st.write("")
        st.write("")
        classify_btn = st.button("🔍 开始分类", use_container_width=True, type="primary")
        use_all_btn = st.button("📋 批量分类全部", use_container_width=True)

    # ── 分类结果 ──
    results_container = st.container()

    with results_container:
        if classify_btn and input_text.strip():
            result = classify_complaint(input_text)
            st.subheader("📊 分类结果")

            res_col1, res_col2, res_col3, res_col4 = st.columns(4)
            with res_col1:
                st.metric("类别", result["类别"])
            with res_col2:
                st.metric("优先级", result["优先级"])
            with res_col3:
                st.metric("情绪等级", result["情绪等级"])
            with res_col4:
                st.metric("转人工", "是" if result["需要转人工"] else "否")

            st.info(f"**分类描述**：{mock_classifier_summary([result])}")

        if use_all_btn:
            all_results = []
            for text in raw_inputs:
                result = classify_complaint(text)
                result["投诉内容"] = text
                all_results.append(result)

            df = pd.DataFrame(all_results)
            df = df[["投诉内容", "类别", "子类", "优先级", "情绪等级", "需要转人工"]]
            st.subheader("📊 批量分类结果")
            st.dataframe(df, use_container_width=True, hide_index=True)

            # 统计
            st.subheader("📈 分类统计")
            cat_counts = df["类别"].value_counts()
            st.bar_chart(cat_counts)

            st.info(mock_classifier_summary(all_results))

    # ── 转人工判断 ──
    st.markdown("---")
    st.subheader("🚨 需要转人工的案例")
    if use_all_btn or classify_btn:
        need_handoff = [r for r in (all_results if use_all_btn else [classify_complaint(input_text)]) if r.get("需要转人工")]
        if need_handoff:
            df_ho = pd.DataFrame(need_handoff)
            st.dataframe(df_ho[["投诉内容", "类别", "优先级", "情绪等级"]], use_container_width=True, hide_index=True)
        else:
            st.success("当前无需要转人工的案例。")
    else:
        st.caption("请先进行单条分类或批量分类。")


render()
