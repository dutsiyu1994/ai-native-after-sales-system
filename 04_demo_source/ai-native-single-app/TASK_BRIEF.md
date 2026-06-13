# TASK BRIEF：7 个独立 Streamlit 应用 → 单个统一应用

## 1. 范围（SCOPE）

### 目标
将 `D:\job3.0\04_demo_source\` 下 **7 个独立 Streamlit 应用** 合并为 **1 个单入口 Streamlit 应用**，通过标签页（Tab）组织所有模块。**不是重写，而是合并**——每个 tab 从对应原始 app.py 中提取核心展示逻辑并适配到共享 session_state 模式。

### 保留原始应用
**严禁删除**任何已有 demo 目录。新应用独立存在于 `ai-native-single-app/` 目录下，原始 7 个 app 完整保留。

### 第一版本范围
第一版本目标是**可在单个在线 URL 上运行和演示**，不需要完整复刻 7 个 app 的所有高级功能。每个 tab 至少做到：
- 正确渲染页面标题 / 描述
- 加载演示数据（mock / sample data）
- 核心交互可用（输入框可输入、按钮可点击、结果区域有输出）
- 不报红（无 Streamlit 异常抛出）

### 部署约束
- **不得从 `D:\job3.0`（主工作区）push 到 GitHub**
- 只有 `D:\job3.0\_deploy_ai-native-after-sales-system_v2` 可以 push
- 合并后的 app 需部署到 Streamlit Cloud，URL 示例：`https://ai-native-single-app.streamlit.app`（最终 URL 由部署方确定）

### 个人文档排除
**严禁包含**任何求职文档、简历、面试材料、agent_memory 文件。

---

## 2. 架构（ARCHITECTURE）

### 2.1 总体结构

```
ai-native-single-app/
├── app.py                  # 主入口 — st.navigation() 驱动
├── requirements.txt        # 合并后的依赖
├── README.md               # 应用说明
└── pages/                  # （可选）若使用 st.navigation/pages 模式
    └── ...                 # 每个模块一个 page
```

### 2.2 导航方案（推荐）

**推荐方案 A（首选）：`st.navigation()` + `st.Page()`**

Streamlit >= 1.36 支持 `st.navigation()` API，可以在 `app.py` 中定义所有页面，天然支持侧边栏导航。

```python
# app.py 结构伪代码
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import streamlit as st

# --- 定义页面 ---
home_page = st.Page("pages/home.py", title="首页 / 系统控制台", icon="🏠")
customer_agent_page = st.Page("pages/customer_agent.py", title="对客机器人", icon="🤖")
complaint_classifier_page = st.Page("pages/complaint_classifier.py", title="客诉分类", icon="🔍")
voc_risk_page = st.Page("pages/voc_risk.py", title="VOC 风险", icon="⚠️")
quality_eval_page = st.Page("pages/quality_eval.py", title="客服质检", icon="🎧")
summary_page = st.Page("pages/summary.py", title="智能总结", icon="📝")
rag_kb_page = st.Page("pages/rag_kb.py", title="RAG 知识库", icon="📚")
metrics_page = st.Page("pages/metrics.py", title="指标 / 反馈 / 2.0 优化", icon="📊")

pg = st.navigation([home_page, customer_agent_page, complaint_classifier_page,
                    voc_risk_page, quality_eval_page, summary_page,
                    rag_kb_page, metrics_page])
pg.run()
```

**备选方案 B（兼容旧 Streamlit）：`st.tabs()`**

如果 Streamlit Cloud 版本较旧，也可以用 `st.tabs()` 在单页内实现标签页切换。

### 2.3 模块 / Tab 清单

| # | Tab 名称 | 中文名称 | 源文件来源 | 行数 | 核心功能 |
|---|----------|----------|-----------|------|---------|
| 1 | 首页 / 系统控制台 | Home / System Console | `ai-assistant-portal/app.py` | 733 | 系统总览、统计仪表盘、案例列表 |
| 2 | 对客机器人 | Customer Agent | `customer-agent-demo/app.py` | 742 | 多轮对话、槽位继承、转人工判断 |
| 3 | 客诉分类 | Complaint Classification | `complaint-classifier/app.py` | 1431 | 投诉文本分类、模型选择、趋势分析 |
| 4 | VOC 风险 | VOC Risk Detection | `voc-risk-detector/app.py` | 1360 | 批量风险检测、聚类分析、风险预警 |
| 5 | 客服质检 | Quality Evaluation | `cs-quality-evaluator/app.py` | 875 | 对话质检评分、维度分析 |
| 6 | 智能总结 | Smart Summary | `summary-system/app.py` | 1351 | 会话摘要生成、关键词提取 |
| 7 | RAG 知识库 | RAG Knowledge Base | `service-rag-demo/app.py` | 389 | 知识检索、TF-IDF 匹配 |
| 8 | 指标 / 反馈 / 2.0 优化 | Metrics / Feedback / Optimization | `ai-assistant-portal/app.py` + 新建 | — | 指标看板、反馈事件、优化建议 |

### 2.4 共享代码路径

所有 page 模块通过 `sys.path.insert(0, "../..")`（相对于 `04_demo_source/ai-native-single-app/`）或绝对路径引用：

```python
import sys, os
_SHARED = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _SHARED not in sys.path:
    sys.path.insert(0, _SHARED)
```

然后导入共享模块：

```python
from ai_native_shared.case_schema import generate_case_id, build_case_context, missing_slots, is_handoff_required
from ai_native_shared.knowledge_base import KNOWLEDGE_CHUNKS, retrieve_knowledge, has_sufficient_evidence
from ai_native_shared.feedback_schema import build_feedback_event
from ai_native_shared.sample_cases import SAMPLE_CASES
from ai_native_shared.case_store import save_case, get_case, list_cases, count_cases, delete_case, export_cases_as_json, init_db
from ai_native_shared.feedback_store import save_event, get_events, count_by_type, count_by_priority, get_unresolved, resolve_event, delete_event, init_db as init_feedback_db
from ai_native_shared.metrics_engine import compute_metrics
from ai_native_shared.insight_engine import generate_insights
```

### 2.5 Session State 共享

```python
# app.py 或 pages/home.py 中初始化
if "current_case_id" not in st.session_state:
    st.session_state.current_case_id = None
if "case_data" not in st.session_state:
    st.session_state.case_data = {}          # dict: case_id -> case_context
if "feedback_events" not in st.session_state:
    st.session_state.feedback_events = []
if "knowledge_results" not in st.session_state:
    st.session_state.knowledge_results = []
if "db_initialized" not in st.session_state:
    init_db()
    init_feedback_db()
    st.session_state.db_initialized = True
```

各 tab 可以读写这些共享 state，实现跨 tab 数据传递（例如：对客机器人创建的 case 可以在指标 tab 中统计）。

### 2.6 各 Tab 提取指南（最小可行版本）

每个 tab 从原 app.py 中提取的核心内容：

1. **首页/控制台** — 系统总览：case 数量、反馈事件数量、最近案例列表（`list_cases` + `get_events` + `compute_metrics`）
2. **对客机器人** — 对话界面：用户输入框、多轮对话历史显示、槽位填充状态、转人工判断按钮（mock 或 LLM 模式）
3. **客诉分类** — 文本输入 + 分类展示：`SAMPLE_CASES` 加载 + 规则/模型分类 + 结果表格
4. **VOC 风险** — 批量风险检测：加载示例数据 → 风险评分 → 风险分布图表
5. **客服质检** — 评分界面：选择案例 → 质检评分维度展示 → 总分
6. **智能总结** — 摘要生成：输入/选择文本 → 生成摘要 → 关键词展示
7. **RAG 知识库** — 知识检索：用户提问 → `retrieve_knowledge` 检索 → 展示匹配结果
8. **指标/反馈/2.0 优化** — 指标看板：`compute_metrics` 图表 + `get_events` 列表 + `generate_insights` 优化建议

### 2.7 页面配置

```python
st.set_page_config(
    page_title="AI 售后服务系统 — 统一平台",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded",
)
```

将此配置放在 `app.py` 顶部（必须是第一个 st 命令）。

---

## 3. 文件清单（FILE LIST）

### 3.1 新建文件

| # | 文件路径 | 类型 | 说明 |
|---|---------|------|------|
| 1 | `04_demo_source/ai-native-single-app/app.py` | 新建 | **主入口** — `st.navigation()` 定义和页面路由 |
| 2 | `04_demo_source/ai-native-single-app/pages/home.py` | 新建 | 首页/系统控制台 tab |
| 3 | `04_demo_source/ai-native-single-app/pages/customer_agent.py` | 新建 | 对客机器人 tab |
| 4 | `04_demo_source/ai-native-single-app/pages/complaint_classifier.py` | 新建 | 客诉分类 tab |
| 5 | `04_demo_source/ai-native-single-app/pages/voc_risk.py` | 新建 | VOC 风险检测 tab |
| 6 | `04_demo_source/ai-native-single-app/pages/quality_eval.py` | 新建 | 客服质检 tab |
| 7 | `04_demo_source/ai-native-single-app/pages/summary.py` | 新建 | 智能总结 tab |
| 8 | `04_demo_source/ai-native-single-app/pages/rag_kb.py` | 新建 | RAG 知识库 tab |
| 9 | `04_demo_source/ai-native-single-app/pages/metrics.py` | 新建 | 指标/反馈/2.0 优化 tab |
| 10 | `04_demo_source/ai-native-single-app/requirements.txt` | 新建 | 合并后的 Python 依赖 |
| 11 | `04_demo_source/ai-native-single-app/README.md` | 新建 | 应用说明文档 |
| 12 | `04_demo_source/README.md` | **修改** | 更新 README，添加 ai-native-single-app 入口 |

### 3.2 不修改的文件（保留原样）

| 路径 | 原因 |
|------|------|
| `04_demo_source/ai-assistant-portal/app.py` | 保留原始应用 |
| `04_demo_source/customer-agent-demo/app.py` | 保留原始应用 |
| `04_demo_source/complaint-classifier/app.py` | 保留原始应用 |
| `04_demo_source/voc-risk-detector/app.py` | 保留原始应用 |
| `04_demo_source/cs-quality-evaluator/app.py` | 保留原始应用 |
| `04_demo_source/summary-system/app.py` | 保留原始应用 |
| `04_demo_source/service-rag-demo/app.py` | 保留原始应用 |
| `ai_native_shared/` (全部文件) | 共享代码，不改动 |

---

## 4. 验收标准（ACCEPTANCE CRITERIA）

### 4.1 编译与运行

| # | 标准 | 验证方式 |
|---|------|----------|
| A1 | `app.py` 无语法错误 | `python -m py_compile app.py` 返回 0 |
| A2 | Streamlit 启动无 import 错误 | `streamlit run app.py --server.port 8510` 正常启动 |
| A3 | 所有 8 个 tab 渲染不崩溃 | 依次点击每个 tab，无 Streamlit 异常 |
| A4 | HTTP 200 响应 | `curl http://127.0.0.1:8510` 返回 200 |

### 4.2 各 Tab 功能验收

| # | Tab | 最低验收标准 |
|---|-----|-------------|
| B1 | 首页/控制台 | 显示系统概览统计（case 数量、反馈数量），不报错 |
| B2 | 对客机器人 | 输入框可输入文本，"发送"按钮点按后显示回复 |
| B3 | 客诉分类 | 展示示例投诉列表，点击分类后显示分类结果 |
| B4 | VOC 风险 | 展示示例数据，显示风险评分或分布图表 |
| B5 | 客服质检 | 展示质检维度评分界面，显示评分结果 |
| B6 | 智能总结 | 输入/选择文本后生成摘要（mock 或 LLM） |
| B7 | RAG 知识库 | 输入查询后返回 `retrieve_knowledge` 检索结果 |
| B8 | 指标/反馈/2.0 优化 | 显示 `compute_metrics` 生成的指标图表和 `generate_insights` 优化建议 |

### 4.3 非功能验收

| # | 标准 |
|---|------|
| C1 | 7 个原始 app 目录未被删除或修改 |
| C2 | `D:\job3.0` 目录下没有任何 git push 操作 |
| C3 | 代码中不包含任何求职/简历/面试/agent_memory 内容 |
| C4 | `README.md` 包含明确的本地启动和线上入口说明 |

---

## 5. 验证命令（VERIFICATION COMMANDS）

### 5.1 本地启动

```bash
# 1. 语法检查（在 ai-native-single-app 目录下执行）
cd /d/job3.0/04_demo_source/ai-native-single-app
python -m py_compile app.py

# 2. 启动 Streamlit 应用
streamlit run app.py --server.port 8510 --server.address 127.0.0.1 --server.headless true

# 3. 检查 HTTP 可达性（新终端）
curl -o /dev/null -s -w "%{http_code}\n" http://127.0.0.1:8510
# 应输出: 200

# 4. 检查所有 page 模块的语法
python -m py_compile pages/home.py
python -m py_compile pages/customer_agent.py
python -m py_compile pages/complaint_classifier.py
python -m py_compile pages/voc_risk.py
python -m py_compile pages/quality_eval.py
python -m py_compile pages/summary.py
python -m py_compile pages/rag_kb.py
python -m py_compile pages/metrics.py
```

### 5.2 启动脚本更新

更新 `D:\job3.0\00_流程SOP\start-local-demos.bat` 添加新应用（可选，但推荐）：

```batch
call :start_app 8510 ai-native-single-app D:\job3.0\04_demo_source\ai-native-single-app
```

### 5.3 部署验证

```bash
# 在 deploy repo 中验证（注意：不要从 D:\job3.0 push）
cd /d/job3.0/_deploy_ai-native-after-sales-system_v2
# 确保 ai-native-single-app 目录已复制到 deploy repo 对应位置
# 在 Streamlit Cloud 上部署后验证线上 URL
```

---

## 6. 实现提示

### 6.1 Stub / Mock 策略

第一版本中，所有 LLM 调用（DeepSeek / Gemini / Ollama）应使用 **mock 兜底**：

```python
# mock 回复示例
def mock_reply(user_input: str) -> str:
    """当 LLM 不可用时返回规则回复"""
    if "退款" in user_input:
        return "您好，关于退款问题，我已记录您的诉求，将在 24 小时内由专员跟进处理。"
    if "投诉" in user_input:
        return "感谢您的反馈，我已将您的投诉转交至客诉处理团队。"
    return f"已收到您的消息：{user_input}，客服人员将尽快为您处理。"
```

### 6.2 依赖合并

将所有 7 个 app 的 `requirements.txt` 依赖合并去重：

```txt
streamlit>=1.28.0
pandas>=2.0.0
plotly>=5.14.0
openpyxl>=3.1.0
scikit-learn>=1.3.0
jieba>=0.42.1
openai>=1.0.0
google-generativeai>=0.8.0
```

### 6.3 需要特别注意的点

1. **`st.set_page_config()` 只能调用一次** — 必须在 `app.py` 顶部调用，pages 中不可重复调用
2. **共享 path 解析** — `os.path.dirname(__file__)` 在 pages/ 子目录中需要往上层多走一级
3. **SQLite 数据库路径** — `case_store.py` 默认使用 `./cases.db`，在 pages 中运行时需确保路径正确（使用绝对路径或相对于 `ai-native-single-app/`）
4. **Streamlit Cloud 路径** — 线上路径为 `/mount/src/ai-native-after-sales-system/`，`sys.path.insert(0, "../..")` 在 Cloud 上同样适用

### 6.4 推荐的实现顺序

1. 创建目录结构 + `app.py`（导航框架）+ `requirements.txt`
2. 实现 `pages/home.py`（最简单，纯展示）
3. 实现 `pages/customer_agent.py`（对话交互）
4. 实现 `pages/rag_kb.py`（知识检索）
5. 实现 `pages/complaint_classifier.py`（分类展示）
6. 实现 `pages/voc_risk.py`（风险检测）
7. 实现 `pages/quality_eval.py`（质检评分）
8. 实现 `pages/summary.py`（摘要生成）
9. 实现 `pages/metrics.py`（指标看板）
10. 写 `README.md` + 更新 `04_demo_source/README.md`
11. 本地验证 + 修复问题

---

## 7. 附录：原始应用依赖映射

| 原始应用 | 依赖 | 行数 |
|---------|------|------|
| ai-assistant-portal | streamlit | 733 |
| customer-agent-demo | streamlit, openai | 742 |
| complaint-classifier | streamlit, pandas, plotly, openpyxl, openai | 1431 |
| voc-risk-detector | streamlit, pandas, plotly, jieba, scikit-learn, openpyxl | 1360 |
| cs-quality-evaluator | streamlit, pandas, plotly, openpyxl | 875 |
| summary-system | streamlit, pandas, plotly, openai, google-generativeai | 1351 |
| service-rag-demo | streamlit, pandas, scikit-learn | 389 |
