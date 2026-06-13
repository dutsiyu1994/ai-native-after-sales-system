import sys, os

_SHARED = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _SHARED not in sys.path:
    sys.path.insert(0, _SHARED)

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

from ai_native_shared.case_store import list_cases, save_case, get_case
from ai_native_shared.case_schema import generate_case_id, build_case_context
from ai_native_shared.sample_cases import SAMPLE_CASES
from ai_native_shared.feedback_store import save_event


# ── 示例对话数据 ──
SAMPLE_CONVERSATIONS = [
    {
        "case_id": "EVAL-001",
        "title": "航班延误退票咨询",
        "dialogue": [
            ("客户", "我的航班延误了3个小时，我要退票！"),
            ("客服", "理解您的情况，请问您的订单号是多少？"),
            ("客户", "TK20240615001"),
            ("客服", "好的，我查到了，您这个航班确实延误了。根据航司政策，非自愿退票可以全额退款，我来帮您提交申请。"),
            ("客户", "好的，那尽快吧。"),
            ("客服", "已经提交，预计1-3个工作日退款到账，请留意支付账户。"),
        ],
    },
    {
        "case_id": "EVAL-002",
        "title": "产品质量换货",
        "dialogue": [
            ("客户", "我买的耳机用了两天就坏了，你们怎么回事！"),
            ("客服", "这是公司规定，我们不能处理已经使用过的商品。"),
            ("客户", "可是是质量问题啊！刚买就坏了。"),
            ("客服", "那您提供一下购买凭证和照片，我帮您登记。"),
            ("客户", "好的，我发你。"),
            ("客服", "收到，我们会在3个工作日内处理。"),
        ],
    },
]


# ── 质检评分维度定义 ──
QUALITY_DIMENSIONS = [
    {"name": "识别需求", "weight": 0.25, "desc": "客服是否准确理解并复述客户核心诉求"},
    {"name": "有效共情", "weight": 0.20, "desc": "客服是否结合客户处境表达理解和情绪支持"},
    {"name": "达成一致", "weight": 0.30, "desc": "服务过程是否和客户就处理方案达成明确共识"},
    {"name": "承诺回复", "weight": 0.25, "desc": "客服是否给出明确的回复时间、处理节点和方式"},
]


def mock_evaluate_dialogue(dialogue: list) -> dict:
    """Mock 质检评分"""
    scores = {}
    total_weighted = 0
    total_weight = 0

    # 简单规则评分
    full_text = " ".join([f"{role}: {text}" for role, text in dialogue])

    # 识别需求
    identify_score = 4.0
    if any("您的" in text for _, text in dialogue):
        identify_score = 4.5
    identify_score += 0.5 if "理解" in full_text else 0
    scores["识别需求"] = round(min(identify_score, 5.0), 1)

    # 有效共情
    empathy_score = 3.0
    if "理解" in full_text or "不好意思" in full_text or "抱歉" in full_text:
        empathy_score = 4.0
    if "愤怒" in full_text or "生气" in full_text or "这是公司规定" in full_text:
        empathy_score = 2.0  # 扣分项
    scores["有效共情"] = round(min(empathy_score, 5.0), 1)

    # 达成一致
    agree_score = 3.5
    if "好的" in full_text or "可以" in full_text or "没问题" in full_text:
        agree_score = 4.0
    scores["达成一致"] = round(min(agree_score, 5.0), 1)

    # 承诺回复
    commit_score = 3.0
    import re
    time_matches = re.findall(r'\d+个?工作日|\d+小时|\d+天内|\d+-\d+天', full_text)
    if time_matches:
        commit_score = 4.5
    if "尽快" in full_text:
        commit_score = max(commit_score, 3.5)
    scores["承诺回复"] = round(min(commit_score, 5.0), 1)

    # 计算加权总分
    total_weighted = 0
    total_weight = 0
    dim_details = []
    for dim in QUALITY_DIMENSIONS:
        name = dim["name"]
        score = scores.get(name, 3.0)
        weighted = score * dim["weight"]
        total_weighted += weighted
        total_weight += dim["weight"]
        dim_details.append({
            "维度": name,
            "评分": score,
            "权重": f"{dim['weight']*100:.0f}%",
            "加权得分": round(weighted, 2),
            "说明": dim["desc"],
        })

    total_score = round(total_weighted / total_weight, 1) if total_weight > 0 else 0

    return {
        "dimensions": dim_details,
        "total_score": total_score,
        "pass_status": "✅ 通过" if total_score >= 3.5 else "⚠️ 需改进" if total_score >= 2.5 else "❌ 不合格",
    }


def render():
    st.title("🎧 客服质检")
    st.markdown("---")

    # ── 选择对话 ──
    st.subheader("📋 选择质检对话")
    conv_options = {f"{c['title']} ({c['case_id']})": c for c in SAMPLE_CONVERSATIONS}

    # 也从数据库加载案例
    db_cases = list_cases(limit=5)
    for c in db_cases:
        case_id = c.get("case_id", "")
        intent = c.get("customer_intent", "unknown")
        conv_options[f"[DB] {case_id} ({intent})"] = {
            "case_id": case_id,
            "title": intent,
            "dialogue": [("客户", c.get("customer_message", "")),
                         ("客服", "已收到您的反馈，正在处理中。")],
        }

    selected_label = st.selectbox("选择要质检的对话：", list(conv_options.keys()))
    selected = conv_options[selected_label]

    # ── 显示对话内容 ──
    st.markdown("---")
    st.subheader("💬 对话记录")

    dialogue_container = st.container()
    with dialogue_container:
        for role, text in selected["dialogue"]:
            if role == "客户":
                st.markdown(f"> **🧑 客户**：{text}")
            else:
                st.markdown(f"> **🤖 客服**：{text}")

    # ── 开始质检 ──
    st.markdown("---")
    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader("📊 质检评分")
    with col2:
        eval_btn = st.button("⭐ 开始质检", type="primary", use_container_width=True)

    if eval_btn:
        result = mock_evaluate_dialogue(selected["dialogue"])

        # 显示总分
        total = result["total_score"]
        status = result["pass_status"]
        st.metric("总分", f"{total}/5", delta="通过" if total >= 3.5 else "需改进",
                  delta_color="normal" if total >= 3.5 else "inverse")

        # 维度详情
        dim_df = pd.DataFrame(result["dimensions"])
        st.dataframe(dim_df, use_container_width=True, hide_index=True)

        # 雷达图
        dim_names = [d["维度"] for d in result["dimensions"]]
        dim_scores = [d["评分"] for d in result["dimensions"]]
        fig = px.line_polar(
            r=dim_scores + [dim_scores[0]],
            theta=dim_names + [dim_names[0]],
            line_close=True,
            title="质检维度雷达图",
            range_r=[0, 5],
        )
        fig.update_traces(fill="toself")
        st.plotly_chart(fig, use_container_width=True)

        # 保存质检结果
        save_event(
            case_id=selected["case_id"],
            event_type="quality_low_score" if total < 3.5 else "human_modification",
            source_module="quality_evaluator",
            description=f"质检评分 {total}/5 — {selected['title']}",
            root_cause="script_issue" if total < 3.5 else "knowledge_gap",
            priority="P1" if total < 3.0 else "P2",
        )
        st.success(f"质检完成，结果已保存。{status}")
    else:
        st.info("点击「开始质检」按钮进行评分。")


render()
