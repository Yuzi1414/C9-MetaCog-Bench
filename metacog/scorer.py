"""元认知指标：ECE、Brier、AUROC、弃答增益、分半信度。纯标准库实现。"""

import bisect


def expected_calibration_error(confs, corrects, n_bins=10):
    """ECE：把置信度等宽分箱，每箱 |平均置信 − 正确率| 按样本量加权。"""
    assert len(confs) == len(corrects) and len(confs) > 0
    bins = [[] for _ in range(n_bins)]
    for c, y in zip(confs, corrects):
        b = min(n_bins - 1, int(c * n_bins))
        bins[b].append((c, y))
    ece = 0.0
    n = len(confs)
    for bucket in bins:
        if not bucket:
            continue
        avg_conf = sum(c for c, _ in bucket) / len(bucket)
        acc = sum(y for _, y in bucket) / len(bucket)
        ece += len(bucket) / n * abs(avg_conf - acc)
    return ece


def brier_score(confs, corrects):
    return sum((c - y) ** 2 for c, y in zip(confs, corrects)) / len(confs)


def auroc(scores, corrects):
    """Rank-based AUC = P(随机正例分数 > 随机负例分数)，平局计 0.5。"""
    pos = sorted(s for s, y in zip(scores, corrects) if y == 1)
    neg = sorted(s for s, y in zip(scores, corrects) if y == 0)
    if not pos or not neg:
        return float("nan")
    wins = 0.0
    for p in pos:
        lt = bisect.bisect_left(neg, p)
        eq = bisect.bisect_right(neg, p) - lt
        wins += lt + 0.5 * eq
    return wins / (len(pos) * len(neg))


def abstain_gain(confs, corrects, tau):
    """弃答增益：置信度 ≥ τ 才作答，返回（剩余准确率 − 全量准确率, 剩余占比）。"""
    full = sum(corrects) / len(corrects)
    kept = [(c, y) for c, y in zip(confs, corrects) if c >= tau]
    if not kept:
        return 0.0, 0.0
    rem = sum(y for _, y in kept) / len(kept)
    return rem - full, len(kept) / len(corrects)


def tune_tau(confs, corrects, grid=None):
    """在留出集上调 τ，使弃答增益最大（无改进返回 0，即全量作答）。"""
    grid = grid or [i / 20 for i in range(21)]
    best_tau, best_gain = 0.0, 0.0
    for t in grid:
        g, _ = abstain_gain(confs, corrects, t)
        if g > best_gain:
            best_gain, best_tau = g, t
    return best_tau, best_gain


def core_metrics(confs, corrects):
    return {
        "n": len(confs),
        "accuracy": sum(corrects) / len(corrects),
        "ece": expected_calibration_error(confs, corrects),
        "brier": brier_score(confs, corrects),
        "auroc": auroc(confs, corrects),
    }
