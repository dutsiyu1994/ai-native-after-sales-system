# AI 售后服务系统 — 统一平台

将 7 个独立 Streamlit 应用合并为单个单入口应用，通过侧边栏导航组织所有模块。

## 本地启动

```bash
# 1. 安装依赖
cd D:\job3.0\04_demo_source\ai-native-single-app
pip install -r requirements.txt

# 2. 启动应用
streamlit run app.py --server.port 8510 --server.address 127.0.0.1

# 3. 访问
http://127.0.0.1:8510
```

## 模块清单

| # | 模块 | 说明 |
|---|------|------|
| 1 | 🏠 首页/系统控制台 | 系统总览、统计仪表盘、案例列表 |
| 2 | 🤖 对客机器人 | 多轮对话、槽位填充、转人工判断 |
| 3 | 🔍 客诉分类 | 投诉文本分类、批量分类、趋势分析 |
| 4 | ⚠️ VOC 风险 | 批量风险检测、聚类分析、风险分布 |
| 5 | 🎧 客服质检 | 对话质检评分、维度分析 |
| 6 | 📝 智能总结 | 会话摘要生成、关键词提取 |
| 7 | 📚 RAG 知识库 | 知识检索、TF-IDF 匹配 |
| 8 | 📊 指标/反馈/2.0 优化 | 指标看板、反馈事件、优化建议 |

## 技术栈

- **框架**: Streamlit >= 1.36 (st.navigation + st.Page)
- **数据**: SQLite (case_store + feedback_store)
- **图表**: Plotly + Pandas
- **NLP**: jieba (中文分词)
- **ML**: scikit-learn (用于分类/聚类)
- **LLM**: Mock 兜底（无需 API Key）

## 目录结构

```
ai-native-single-app/
├── app.py                    # 主入口 — st.navigation() 驱动
├── requirements.txt          # 依赖
├── README.md                 # 本文件
├── pages/
│   ├── home.py               # 首页/控制台
│   ├── customer_agent.py     # 对客机器人
│   ├── complaint_classifier.py # 客诉分类
│   ├── voc_risk.py           # VOC 风险
│   ├── quality_eval.py       # 客服质检
│   ├── summary.py            # 智能总结
│   ├── rag_kb.py             # RAG 知识库
│   └── metrics.py            # 指标/反馈/2.0优化
```

## 共享代码

共享代码位于 `D:\job3.0\ai_native_shared\`，通过 `sys.path.insert(0, "../..")` 引用。
