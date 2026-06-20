"""一次性脚本：用真实 DeepSeek 跑一遍内置样本，把 AI 分类结果固化成快照 JSON。

用途：让线上 demo 在无 API key 时也能展示"双引擎对比报告"（基于真实 LLM 输出的预置样例）。

用法：
    python _gen_snapshot.py <key文件路径>
  或在 key 文件位于默认路径时直接：
    python _gen_snapshot.py

key 文件：纯文本，仅一行 DeepSeek API key。脚本只读不写、不回显，跑完可删。
输出：ai_snapshot.json（按 complaint_id 索引的 AI 字段 + 元信息）。
"""

import sys
import os
import json
import time
import types
from datetime import date

# ── 1. 读取 key（仅从文件，不接受命令行明文，避免泄漏到进程列表/历史） ──
DEFAULT_KEY_PATHS = [
    os.path.expanduser("~/.deepseek_key"),
    os.path.expanduser("~/.deepseek_key.txt"),
]
key_path = sys.argv[1] if len(sys.argv) > 1 else None
if key_path is None:
    for p in DEFAULT_KEY_PATHS:
        if os.path.isfile(p):
            key_path = p
            break
if not key_path or not os.path.isfile(key_path):
    print("ERROR: 未找到 key 文件。请把 DeepSeek key 写入 ~/.deepseek_key 或传路径参数。")
    sys.exit(2)
with open(key_path, "r", encoding="utf-8") as f:
    API_KEY = f.read().strip()
if not API_KEY:
    print("ERROR: key 文件为空。")
    sys.exit(2)

# ── 2. 用 streamlit 桩导入 app，拿到样本生成 / 分类 / 模型配置，避免重复实现 ──
class _Stub:
    def __getattr__(self, name):
        return _Stub()
    def __call__(self, *a, **k):
        if len(a) == 1 and callable(a[0]) and not k:
            return a[0]  # 支持 @st.cache_data 直接装饰
        return _Stub()
    def __enter__(self):
        return self
    def __exit__(self, *a):
        return False
    def __getitem__(self, k):
        return _Stub()
    def __setitem__(self, k, v):
        pass
    def __iter__(self):
        return iter([])

sys.modules["streamlit"] = _Stub()

import importlib.util
spec = importlib.util.spec_from_file_location("ccapp", os.path.join(os.path.dirname(__file__), "app.py"))
app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)

# ── 3. 构建 DeepSeek 客户端（openai 兼容接口） ──
from openai import OpenAI
client = OpenAI(base_url="https://api.deepseek.com", api_key=API_KEY, timeout=40.0, max_retries=1)

df = app.generate_sample_data()
print(f"样本 {len(df)} 条，开始逐条调用 DeepSeek ...")

snapshot = {}
fail = 0
for i, (_, row) in enumerate(df.iterrows()):
    cid = row["complaint_id"]
    text = row["complaint_text"]
    result = None
    for attempt in range(3):  # 解析失败 / 置信度 0 时重试
        result = app.llm_classify(text, "deepseek", client)
        if result and result.get("confidence", 0) > 0:
            break
        time.sleep(1.5)
    if not result or result.get("confidence", 0) == 0:
        fail += 1
        print(f"  [{i+1}/{len(df)}] {cid} 失败，保留兜底结果")
    snapshot[cid] = {
        "category": result.get("category", "其他"),
        "confidence": round(float(result.get("confidence", 0.0)), 3),
        "sentiment": result.get("sentiment", "平静"),
        "priority": result.get("priority", "P2-普通"),
        "reasoning": result.get("reasoning", ""),
        "is_compound": bool(result.get("is_compound", False)),
        "compound_types": result.get("compound_types", []),
        "keywords_extracted": result.get("keywords_extracted", []),
        "action_recommendation": result.get("action_recommendation", ""),
    }
    if (i + 1) % 10 == 0:
        print(f"  进度 {i+1}/{len(df)}")

out = {
    "_meta": {
        "model": "DeepSeek-V3 (deepseek-chat)",
        "generated_at": date.today().isoformat(),
        "sample_count": len(df),
        "failed": fail,
        "note": "基于真实 DeepSeek 输出的预置样例，供无 API key 时演示双引擎对比",
    },
    "results": snapshot,
}
out_path = os.path.join(os.path.dirname(__file__), "ai_snapshot.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print(f"完成：{out_path}（{len(df)} 条，失败 {fail} 条）")
