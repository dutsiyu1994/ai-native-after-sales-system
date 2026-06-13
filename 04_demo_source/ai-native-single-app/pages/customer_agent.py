import sys, os

_SHARED = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _SHARED not in sys.path:
    sys.path.insert(0, _SHARED)

import streamlit as st

from ai_native_shared.case_schema import generate_case_id, build_case_context, missing_slots, is_handoff_required
from ai_native_shared.case_store import save_case, get_case


# ── Mock 回复函数 ──
def mock_reply(user_input: str) -> str:
    """当 LLM 不可用时返回规则回复"""
    if "退款" in user_input or "退钱" in user_input:
        return "您好，关于退款问题，我已记录您的诉求，将在 24 小时内由专员跟进处理。"
    if "投诉" in user_input or "民航局" in user_input or "12315" in user_input:
        return "感谢您的反馈，我已将您的投诉转交至客诉处理团队，专员会优先处理。"
    if "换货" in user_input or "坏了" in user_input or "质量问题" in user_input:
        return "收到您的换货请求，请提供订单号和问题描述（如照片/视频），我将为您提交换货工单。"
    if "物流" in user_input or "快递" in user_input or "没到" in user_input:
        return "好的，我帮您查询物流状态。请提供订单号，我将为您核实最新物流节点。"
    return f"已收到您的消息：「{user_input}」，客服人员将尽快为您处理。"


def render():
    st.title("🤖 对客机器人")
    st.markdown("---")

    # 初始化对话历史
    if "agent_conversation" not in st.session_state:
        st.session_state.agent_conversation = [
            {"role": "assistant", "content": "您好，这里是售后服务中心，我是客服小助，请问有什么可以帮您的？"}
        ]
    if "agent_case_id" not in st.session_state:
        st.session_state.agent_case_id = None
    if "agent_slots" not in st.session_state:
        st.session_state.agent_slots = {}

    # ── 侧边栏：槽位状态 ──
    with st.sidebar:
        st.subheader("📋 槽位填充状态")
        slots = st.session_state.agent_slots
        if slots:
            for field, info in slots.items():
                status = info.get("status", "missing")
                if status == "provided":
                    st.success(f"✅ {field}: {info.get('value', '')}")
                else:
                    st.warning(f"⏳ {field}: 未收集")
        else:
            st.caption("暂无槽位数据，开始对话后自动生成。")

        # 转人工按钮
        st.markdown("---")
        if st.button("🔄 转人工", use_container_width=True, type="primary"):
            case_id = st.session_state.agent_case_id
            if case_id:
                st.session_state.agent_conversation.append(
                    {"role": "assistant", "content": "✅ 已转接人工专员，我已将您的信息和对话记录整理好，专员马上接入，请稍候~"}
                )
                # 更新 case
                case = get_case(case_id)
                if case:
                    case["next_action"] = "human_handoff"
                    save_case(case)
            else:
                st.warning("暂无活跃案例，请先发送一条消息。")

    # ── 对话显示区域 ──
    chat_container = st.container()
    with chat_container:
        for msg in st.session_state.agent_conversation:
            role = "user" if msg["role"] == "user" else "assistant"
            with st.chat_message(role):
                st.write(msg["content"])

    # ── 输入框 ──
    user_input = st.chat_input("请输入您的问题...")
    if user_input:
        # 添加用户消息
        st.session_state.agent_conversation.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.write(user_input)

        # 创建或更新 case
        if st.session_state.agent_case_id is None:
            case_id = generate_case_id()
            st.session_state.agent_case_id = case_id
        else:
            case_id = st.session_state.agent_case_id

        # Mock 回复
        reply = mock_reply(user_input)

        # 更新槽位
        slots = st.session_state.agent_slots
        if "订单" in user_input or "订单号" in user_input:
            # 简单提取
            import re
            match = re.search(r'[A-Za-z0-9]{6,20}', user_input)
            if match:
                slots["order_id"] = {"status": "provided", "value": match.group()}
            else:
                slots["order_id"] = {"status": "provided", "value": user_input[:20]}

        # 更新 required_slots
        required_slots = {
            "order_id": slots.get("order_id", {"status": "missing", "value": ""}),
            "customer_request": {"status": "provided", "value": user_input},
        }
        for field in ["event_time", "evidence"]:
            if field not in slots:
                slots[field] = {"status": "missing", "value": ""}
            required_slots[field] = slots[field]

        # 检测风险
        risk_tags = []
        if any(kw in user_input for kw in ["投诉", "民航局", "12315", "曝光", "媒体"]):
            risk_tags.append("regulatory_or_public_risk")
        if any(kw in user_input for kw in ["退款", "退钱", "赔付", "赔偿"]):
            risk_tags.append("compensation_or_refund")
        if any(kw in user_input for kw in ["生气", "愤怒", "欺骗", "欺诈"]):
            risk_tags.append("high_emotion")

        # 转人工判断
        need_handoff = is_handoff_required(risk_tags, "continue_inquiry")
        next_action = "human_handoff" if need_handoff else "continue_inquiry"

        # 构建并保存 case_context
        conversation = [{"role": "customer" if m["role"] == "user" else "agent", "content": m["content"]}
                        for m in st.session_state.agent_conversation]
        if len(conversation) >= 2 and conversation[-1]["role"] == "agent":
            conversation = conversation[:-1]  # 去掉机器人最后一条（还未作为 agent 回复保存）

        case_context = build_case_context(
            customer_message=user_input,
            conversation=conversation,
            required_slots=required_slots,
            risk_tags=risk_tags,
            next_action=next_action,
            handoff_summary="需人工介入" if need_handoff else "",
            customer_intent="refund_compensation_complaint" if risk_tags else "general_inquiry",
            case_id=case_id,
            state_history=[{"next_action": next_action, "timestamp": __import__("datetime").datetime.now().strftime("%Y-%m-%d %H:%M:%S")}],
        )
        save_case(case_context)
        st.session_state.agent_case_id = case_id
        st.session_state.agent_slots = slots

        # 添加机器人回复
        st.session_state.agent_conversation.append({"role": "assistant", "content": reply})
        with st.chat_message("assistant"):
            st.write(reply)

        # 如果需要转人工，追加提示
        if need_handoff:
            handoff_msg = "⚠️ 检测到高风险场景，建议转人工处理。您可以在左侧侧边栏点击「转人工」按钮。"
            st.session_state.agent_conversation.append({"role": "assistant", "content": handoff_msg})
            with st.chat_message("assistant"):
                st.write(handoff_msg)

        st.rerun()

    # ── 清空对话 ──
    st.markdown("---")
    if st.button("🗑️ 清空对话", type="secondary"):
        st.session_state.agent_conversation = [
            {"role": "assistant", "content": "您好，这里是售后服务中心，我是客服小助，请问有什么可以帮您的？"}
        ]
        st.session_state.agent_case_id = None
        st.session_state.agent_slots = {}
        st.rerun()


render()
