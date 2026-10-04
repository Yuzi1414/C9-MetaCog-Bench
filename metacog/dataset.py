"""私有评测集加载与题项抽象。

held-out 私有测试集说明：data/ 下的题集为「开发/演示集」，用于跑通管线与验证指标；
真正的私有测试集由主办方持有、不随仓库公开（呼应论文对公开基准污染的担忧）。
"""

import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

TASKS = ("mcq", "true_false", "open_qa", "ik_math")


def _load(name):
    path = DATA_DIR / f"{name}.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_dataset():
    """返回统一的题项列表，每项含 task、id、gold 答案与可选 accept 列表。"""
    items = []
    for task in TASKS:
        for q in _load(task):
            q["task"] = task
            q["id"] = f"{task}-{q['idx']}"
            items.append(q)
    return items
