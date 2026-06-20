"""一次性脚本：用真实 DeepSeek 跑一段多轮高风险对话，捕获 session_state 固化成回放 JSON。

让线上 demo 在无 API key 时首屏即展示一段真实 LLM 多轮对话 + 全套结构化决策面板，
而不是空屏。用法：python _gen_snapshot.py [key文件路径]   key 默认 ~/.deepseek_key
输出：ai_replay.json
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


os.environ["DEEPSEEK_API_KEY"] = _read_key()


class _Stub:
    session_state = {}
    secrets = {}

    def __getattr__(self, name):
        if name == "session_state":
            return _Stub.session_state
        if name == "secrets":
            return _Stub.secrets
        return _Stub()

    def __call__(self, *a, **k):
        if len(a) == 1 and callable(a[0]) and not k:
            return a[0]
        return _Stub()

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def __getitem__(self, k):
        raise KeyError(k)

    def __setitem__(self, k, v):
        pass


sys.modules["streamlit"] = _Stub()

import importlib.util
spec = importlib.util.spec_from_file_location("caapp", os.path.join(os.path.dirname(__file__), "app.py"))
app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)

# 脚本化的高风险多轮对话：体现 case_id 不变 + 槽位跨轮累积 + 风险升级 + 转人工
turns = [
    "航班延误后我要求退票赔付，如果今天不给方案我就投诉到民航局。",
    "订单号是 A123456789，航班是今天上午10点从上海飞北京的。",
    "我要求全额退款再加误工费赔偿，否则我就去媒体曝光。",
]

print("running %d-turn conversation via DeepSeek ..." % len(turns))
for i, msg in enumerate(turns):
    app._process_user_input(msg, "deepseek")
    conv = _Stub.session_state["conversation"]
    last_agent = next((m["content"] for m in reversed(conv) if m["role"] == "agent"), "")
    print("  turn %d done, agent reply %d chars" % (i + 1, len(last_agent)))

# 捕获驱动渲染的 session 字段（只取可 JSON 序列化的）
ss = _Stub.session_state
replay_keys = [
    "conversation", "slots", "risk_tags", "current_case_id", "case_started_at",
    "case_context", "state_history", "feedback_events", "human_updates",
    "metrics", "last_customer_msg",
]
replay = {}
for k in replay_keys:
    if k in ss:
        try:
            json.dumps(ss[k], ensure_ascii=False)
            replay[k] = ss[k]
        except (TypeError, ValueError):
            print("  skip non-serializable key:", k)

out = {
    "_meta": {
        "model": "DeepSeek-V3 (deepseek-chat)",
        "generated_at": date.today().isoformat(),
        "turns": len(turns),
        "note": "preset multi-turn replay from real DeepSeek output; shown on first load when no API key",
    },
    "replay": replay,
}
out_path = os.path.join(os.path.dirname(__file__), "ai_replay.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
final_action = replay.get("case_context", {}).get("next_action", "?")
print("done: %s (%d turns, final next_action=%s)" % (out_path, len(turns), final_action))
