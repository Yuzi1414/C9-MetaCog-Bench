"""CLI：运行基准、汇总指标、输出结果 JSON 与 Markdown 摘要。"""

import argparse
import json
import re
from pathlib import Path

from .dataset import load_dataset
from .models import SimulatedModel, OpenAICompatibleModel
from .scorer import abstain_gain, core_metrics, tune_tau

PROFILES = ("calibrated", "overconfident", "underconfident", "blind")


def _norm(s):
    return "".join(str(s).lower().split())


def _is_correct(item, answer):
    task = item["task"]
    gold = item["answer"]
    if task == "mcq":
        return _mcq_correct(item, answer)
    if task == "true_false":
        return _tf_correct(gold, answer)
    if task == "ik_math":
        try:
            return abs(float(answer) - float(gold)) < 1e-6
        except (TypeError, ValueError):
            return False
    if task == "open_qa":
        accepted = [gold] + item.get("accept", [])
        return _norm(answer) in {_norm(a) for a in accepted}
    return False


def _mcq_correct(item, answer):
    """容错判分：接受「全文」「选项字母」「字母+全文」等真实模型常见输出。"""
    gold = str(item["answer"]).strip()
    options = item["options"]
    a = str(answer).strip()
    if _norm(a) == _norm(gold):
        return True
    m = re.match(r"^\s*[\(（]?\s*([A-Za-z])\s*[\)）]?\s*[\.、:：]?", a)
    if m:
        idx = ord(m.group(1).upper()) - ord("A")
        if 0 <= idx < len(options) and _norm(options[idx]) == _norm(gold):
            return True
    return bool(gold) and gold in a


def _tf_correct(gold, answer):
    """容错判分：真/假、对/错、是/否、true/false、T/F 等映射到布尔。"""
    a = str(answer).strip().lower()
    true_set = {"true", "t", "yes", "y", "1", "真", "对", "是", "正确", "对"}
    false_set = {"false", "f", "no", "n", "0", "假", "错", "否", "错误", "错"}
    if a in true_set:
        return bool(gold) is True
    if a in false_set:
        return bool(gold) is False
    return False


def run_model(model, items):
    rows = []
    for it in items:
        out = model.predict(it)
        rows.append(
            {
                "id": it["id"],
                "task": it["task"],
                "idx": it["idx"],
                "confidence": round(out["confidence"], 4),
                "correct": int(_is_correct(it, out["answer"])),
            }
        )
    return rows


def evaluate_rows(rows):
    confs = [r["confidence"] for r in rows]
    corrects = [r["correct"] for r in rows]
    n = len(rows)
    # 分半信度：前一半调 τ，后一半评弃答增益（诚实留出调参）
    h1, h2 = rows[: n // 2], rows[n // 2 :]
    tau, _ = tune_tau(
        [r["confidence"] for r in h1], [r["correct"] for r in h1]
    )
    gain, kept = abstain_gain(confs, corrects, tau)
    summary = core_metrics(confs, corrects)
    summary.update(
        {
            "tau": tau,
            "abstain_gain": gain,
            "kept_ratio": kept,
            "split_half": {
                "half1": core_metrics(
                    [r["confidence"] for r in h1], [r["correct"] for r in h1]
                ),
                "half2": core_metrics(
                    [r["confidence"] for r in h2], [r["correct"] for r in h2]
                ),
            },
            "per_task": _per_task(rows),
        }
    )
    return summary


def _per_task(rows):
    by_task = {}
    for r in rows:
        by_task.setdefault(r["task"], []).append(r)
    out = {}
    for task, rs in sorted(by_task.items()):
        out[task] = core_metrics(
            [r["confidence"] for r in rs], [r["correct"] for r in rs]
        )
    return out


def _summary_md(summaries):
    lines = ["# MetaCog-Bench 运行汇总", ""]
    lines.append("| 模型 | 正确率 | ECE | Brier | AUROC | 弃答增益 | 弃答后占比 |")
    lines.append("| --- | --- | --- | --- | --- | --- | --- |")
    for s in summaries:
        lines.append(
            f"| {s['model']} | {s['accuracy']:.3f} | {s['ece']:.3f} | "
            f"{s['brier']:.3f} | {s['auroc']:.3f} | {s['abstain_gain']:.3f} | "
            f"{s['kept_ratio']:.3f} |"
        )
    return "\n".join(lines) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(prog="metacog", description="MetaCog-Bench")
    ap.add_argument("--models", default=",".join(PROFILES))
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", default="results")
    ap.add_argument(
        "--real",
        action="store_true",
        help="改用 OpenAI 兼容真实模型（需 OPENAI_API_KEY）",
    )
    args = ap.parse_args(argv)

    items = load_dataset()
    outdir = Path(args.out)
    outdir.mkdir(parents=True, exist_ok=True)

    summaries = []
    for name in args.models.split(","):
        name = name.strip()
        model = OpenAICompatibleModel(model=name) if args.real else SimulatedModel(name, args.seed)
        rows = run_model(model, items)
        summary = evaluate_rows(rows)
        summary["model"] = model.name
        summaries.append(summary)
        (outdir / f"{model.name}.json").write_text(
            json.dumps(
                {"model": model.name, "rows": rows, "summary": summary},
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        print(
            f"[{model.name}] acc={summary['accuracy']:.3f} ece={summary['ece']:.3f} "
            f"brier={summary['brier']:.3f} auroc={summary['auroc']:.3f} "
            f"abstain_gain={summary['abstain_gain']:.3f}"
        )

    (outdir / "summary.md").write_text(_summary_md(summaries), encoding="utf-8")
    print(f"\n结果已写入 {outdir}/（含 summary.md）")
    return 0
