import sys, os

# ── 共享代码路径 ──
_SHARED = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _SHARED not in sys.path:
    sys.path.insert(0, _SHARED)

import streamlit as st

# ── set_page_config 必须在最顶部 ──
st.set_page_config(
    page_title="AI 售后服务系统 — 统一平台",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Session State 初始化 ──
if "case_data" not in st.session_state:
    st.session_state.case_data = {}
if "current_case_id" not in st.session_state:
    st.session_state.current_case_id = None
if "feedback_events" not in st.session_state:
    st.session_state.feedback_events = []
if "knowledge_results" not in st.session_state:
    st.session_state.knowledge_results = []
if "db_initialized" not in st.session_state:
    from ai_native_shared.case_store import init_db
    from ai_native_shared.feedback_store import init_db as init_feedback_db
    init_db()
    init_feedback_db()
    st.session_state.db_initialized = True

# ── 定义页面导航 ──
home_page = st.Page("pages/home.py", title="首页 / 系统控制台", icon="🏠")
customer_agent_page = st.Page("pages/customer_agent.py", title="对客机器人", icon="🤖")
complaint_classifier_page = st.Page("pages/complaint_classifier.py", title="客诉分类", icon="🔍")
voc_risk_page = st.Page("pages/voc_risk.py", title="VOC 风险", icon="⚠️")
quality_eval_page = st.Page("pages/quality_eval.py", title="客服质检", icon="🎧")
summary_page = st.Page("pages/summary.py", title="智能总结", icon="📝")
rag_kb_page = st.Page("pages/rag_kb.py", title="RAG 知识库", icon="📚")
metrics_page = st.Page("pages/metrics.py", title="指标 / 反馈 / 2.0 优化", icon="📊")

pg = st.navigation([
    home_page, customer_agent_page, complaint_classifier_page,
    voc_risk_page, quality_eval_page, summary_page,
    rag_kb_page, metrics_page,
])
pg.run()
