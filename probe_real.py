"""诊断脚本：打印真实模型对样例题的原始输出，定位判分 bug。"""
import os
os.environ.setdefault("OPENAI_API_KEY", "ollama")
os.environ.setdefault("OPENAI_BASE_URL", "http://localhost:11434/v1")
os.environ.setdefault("OPENAI_MODEL", "qwen2.5")

from metacog.models import OpenAICompatibleModel

m = OpenAICompatibleModel(model="qwen2.5")

samples = [
    {"task": "mcq", "question": "水的化学式是什么？", "options": ["H2O", "CO2", "O2", "NaCl"], "answer": "H2O"},
    {"task": "mcq", "question": "世界上最高的山峰是哪一座？", "options": ["珠穆朗玛峰", "乔戈里峰", "干城章嘉峰", "洛子峰"], "answer": "珠穆朗玛峰"},
    {"task": "true_false", "statement": "地球绕太阳公转。", "answer": True},
    {"task": "true_false", "statement": "鲸鱼属于鱼类。", "answer": False},
]

for s in samples:
    prompt = m._prompt(s)
    raw = m._chat(prompt)
    print("=" * 60)
    print("TASK:", s["task"])
    print("RAW OUTPUT:", repr(raw))
    try:
        parsed = m._parse(raw, s)
        print("PARSED:", parsed)
    except Exception as e:
        print("PARSE ERROR:", repr(e))
