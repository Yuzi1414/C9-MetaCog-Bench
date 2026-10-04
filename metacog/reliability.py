"""信度/效度实证：把提案里的定性论证落成可复算的数字证据。

覆盖（对应提案 v2 的「科学性论证」章节）：
1. 重测信度(test-retest)：同画像换随机种子(5个)，指标是否稳定(mean±std)
2. 分半信度(split-half)：题集对半，两半的 ECE/AUROC 是否一致（内部一致性）
3. 构念效度(convergent)：置信度与正确率的点双列相关，校准画像应显著为正
4. 区分效度(known-groups)：盲画像应无自知（AUROC≈0.5、相关≈0）
5. 防作弊设计(anti-cheating)：held-out 私有集 + 指标不依赖公开答案键
"""

import json
import statistics
from pathlib import Path

from .dataset import load_dataset
from .models import SimulatedModel
from .cli import run_model, evaluate_rows

PROFILES = ("calibrated", "overconfident", "underconfident", "blind")
SEEDS = range(5)


def _pearson(xs, ys):
    n = len(xs)
    mx = sum(xs) / n
    my = sum(ys) / n
    cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sx = (sum((x - mx) ** 2 for x in xs)) ** 0.5
    sy = (sum((y - my) ** 2 for y in ys)) ** 0.5
    if sx == 0 or sy == 0:
        return float("nan")
    return cov / (sx * sy)


def run_profile(profile, seed, items):
    return run_model(SimulatedModel(profile, seed), items)


def test_retest(items):
    out = {}
    for p in PROFILES:
        acc = {"accuracy": [], "ece": [], "brier": [], "auroc": []}
        conf_corr = []
        for seed in SEEDS:
            rows = run_profile(p, seed, items)
            s = evaluate_rows(rows)
            for k in acc:
                acc[k].append(s[k])
            conf_corr.append(_pearson(
                [r["confidence"] for r in rows],
                [r["correct"] for r in rows],
            ))
        out[p] = {
            k: {"mean": round(statistics.mean(v), 4),
                "std": round(statistics.pstdev(v), 4)}
            for k, v in acc.items()
        }
        out[p]["conf_correct_r"] = {
            "mean": round(statistics.mean(conf_corr), 4),
            "std": round(statistics.pstdev(conf_corr), 4),
        }
    return out


def split_half(items):
    out = {}
    for p in PROFILES:
        rows = run_profile(p, 0, items)
        s = evaluate_rows(rows)
        h1, h2 = s["split_half"]["half1"], s["split_half"]["half2"]
        out[p] = {
            "half1": {"ece": round(h1["ece"], 4), "auroc": round(h1["auroc"], 4),
                      "accuracy": round(h1["accuracy"], 4)},
            "half2": {"ece": round(h2["ece"], 4), "auroc": round(h2["auroc"], 4),
                      "accuracy": round(h2["accuracy"], 4)},
        }
    return out


def main():
    items = load_dataset()
    tr = test_retest(items)
    sh = split_half(items)
    report = {
        "n_items": len(items),
        "profiles": list(PROFILES),
        "test_retest": tr,
        "split_half": sh,
        "anti_cheating": {
            "held_out_private_set": "data/ 为演示集；真正私有测试集由主办方持有，不随仓库公开",
            "no_public_leak": "指标基于模型内部置信度信号，不依赖公开答案键",
        },
    }
    out_path = (Path(__file__).resolve().parent.parent / "results"
                / "reliability_validity.json")
    out_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"\n已写入 {out_path}")


if __name__ == "__main__":
    main()
