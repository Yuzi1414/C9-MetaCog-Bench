# MetaCog-Bench 交付物索引

> C2A / C9：衡量 AGI 的认知能力 · Track 2 Metacognition · 提交人 yml（单干）

本仓库即 `*benchmark*` 交付物——一个衡量大模型**元认知校准与自知能力**的可运行评测基准。

## 一、这是什么

MetaCog-Bench 用四类任务（单选 / 真假 / 开放问答 / 数学）共 64 题，从三条元认知信号出发，
对模型同时输出「答案 + 置信度」，再用五项指标量化其**校准质量**与**自知能力**：

| 指标 | 含义 |
|------|------|
| accuracy | 答案正确率 |
| ECE（期望校准误差） | 置信度与正确率的对齐程度 |
| Brier | 概率预测的整体误差 |
| AUROC | 以置信度区分「对/错」的能力 |
| 弃答增益 | 按阈值 τ 弃答低置信度题后的正确率增益 |

## 二、目录结构

```
yml_C9_benchmark/
├── benchmark.md            # 本文件（交付物索引）
├── README.md               # 完整设计说明 + 运行方式 + 结果汇总
├── metacog/                # 基准包：dataset / models / scorer / cli / reliability
├── data/                   # 演示题集（4 类 × 64 题）
├── results/                # 逐模型 JSON + summary.md
├── probe_real.py           # 真实模型输出探针
└── requirements.txt        # 纯标准库（无第三方依赖）
```

## 三、运行

```bash
python -m metacog                # 合成校准画像验证管线（--seed 0 可复现）
python -m metacog --real         # 对接 OpenAI 兼容 /chat/completions 的真实模型
```

## 四、关键结果（真实模型，本地 ollama qwen2.5:latest）

- 64 题：acc **0.984** / ECE **0.009** / Brier **0.014** / AUROC **0.937**
- 诚实标注：演示集上近乎全对 → **天花板效应**，弃答增益≈0、AUROC 区分度信息量有限，
  故正式评测应落在主办方 held-out 私有集上（演示集不可当正式评测集）。

详见 `README.md` §7 与 `results/summary.md`。
