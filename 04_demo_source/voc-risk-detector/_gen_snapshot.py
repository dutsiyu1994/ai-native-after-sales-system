"""一次性脚本：用真实 DeepSeek 跑 VOC 语义聚类，固化成快照 JSON。

让线上 demo 在无 API key 时也能展示 AI 语义聚类预警（基于真实 LLM 输出的预置样例）。
用法：python _gen_snapshot.py [key文件路径]   key 默认 ~/.deepseek_key
输出：ai_snapshot.json
"""

import sys
import os
import json
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
spec = importlib.util.spec_from_file_location("vocapp", os.path.join(os.path.dirname(__file__), "app.py"))
app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)

from openai import OpenAI
client = OpenAI(base_url="https://api.deepseek.com", api_key=API_KEY, timeout=60.0, max_retries=2)

df = app.generate_sample_data()
texts = df["voc_text"].tolist()
print("sample %d texts, calling DeepSeek semantic clustering ..." % len(texts))

clusters = app.llm_semantic_cluster(texts, "deepseek", client)
print("returned %d clusters" % len(clusters))
for c in clusters:
    print("  - %s %s (size=%s, conf=%s)" % (
        c.get("severity", ""), c.get("topic", "?"), c.get("size", "?"), c.get("detection_confidence", "?")))

# anchor validation: first text of the three hardcoded anomaly groups (silver / logistics / infant food).
# deterministic source literals that the clusters describe; more robust than hashing whole corpus.
anchors = [t for t in texts if ("999" in t and "纯银" in t) or "台湾集运" in t or "婴幼儿米粉" in t][:3]

out = {
    "_meta": {
        "model": "DeepSeek-V3 (deepseek-chat)",
        "generated_at": date.today().isoformat(),
        "input_count": len(texts),
        "anchors": anchors,
        "cluster_count": len(clusters),
        "note": "preset semantic clusters from real DeepSeek output; shown when no API key configured",
    },
    "clusters": clusters,
}
out_path = os.path.join(os.path.dirname(__file__), "ai_snapshot.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print("done: %s (%d clusters, %d anchors)" % (out_path, len(clusters), len(anchors)))
