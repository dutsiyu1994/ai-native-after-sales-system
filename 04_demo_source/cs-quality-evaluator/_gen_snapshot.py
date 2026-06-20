"""一次性脚本：用真实 DeepSeek 跑客服质检评估，固化成快照 JSON。

让线上 demo 在无 API key 时也能展示 AI 深度质检（基于真实 LLM 输出的预置样例）。
用法：python _gen_snapshot.py [key文件路径]   key 默认 ~/.deepseek_key
输出：ai_snapshot.json （按对话文本索引）
"""

import sys
import os
import json
import time
from datetime import date


def _read_key():
    paths = [sys.argv[1]] if len(sys.argv) > 1 else [
        os.path.expanduser("~/.deepseek_key"),
        os.path.expanduser("~/.deepseek_key.txt"),
    ]
    for p in paths:
        if p and os.path.isfile(p):
            with open(p, "r", encoding="utf-8") as f:
                k = f.read().strip()
            if k:
                return k
    print("ERROR: key file not found / empty.")
    sys.exit(2)


API_KEY = _read_key()


class _Stub:
    session_state = {}

    def __getattr__(self, name):
        return _Stub.session_state if name == "session_state" else _Stub()

    def __call__(self, *a, **k):
        if len(a) == 1 and callable(a[0]) and not k:
            return a[0]
        return _Stub()

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def __getitem__(self, k):
        return _Stub()

    def __setitem__(self, k, v):
        pass


sys.modules["streamlit"] = _Stub()

import importlib.util
spec = importlib.util.spec_from_file_location("csapp", os.path.join(os.path.dirname(__file__), "app.py"))
app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)

from openai import OpenAI
client = OpenAI(base_url="https://api.deepseek.com", api_key=API_KEY, timeout=60.0, max_retries=2)

samples = app.generate_samples()
print("samples %d, calling DeepSeek per conversation ..." % len(samples))

results = {}
fail = 0
for i, conv in enumerate(samples):
    res = None
    for _ in range(3):
        res = app.llm_evaluate(conv["text"], "deepseek", client)
        if res and all(d in res for d in app.EVALUATION_DIMENSIONS):
            break
        time.sleep(1.5)
    if not res or not all(d in res for d in app.EVALUATION_DIMENSIONS):
        fail += 1
        print("  [%d/%d] %s FAILED" % (i + 1, len(samples), conv["id"]))
        continue
    # key by conversation text so both single & batch modes can match
    results[conv["text"]] = res
    if (i + 1) % 5 == 0:
        print("  progress %d/%d" % (i + 1, len(samples)))

out = {
    "_meta": {
        "model": "DeepSeek-V3 (deepseek-chat)",
        "generated_at": date.today().isoformat(),
        "sample_count": len(samples),
        "failed": fail,
        "note": "preset evaluations from real DeepSeek output; shown when no API key configured",
    },
    "results": results,
}
out_path = os.path.join(os.path.dirname(__file__), "ai_snapshot.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print("done: %s (%d results, %d failed)" % (out_path, len(results), fail))
