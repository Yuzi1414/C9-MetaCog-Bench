# MetaCog-Bench：衡量 AGI 元认知能力的可运行基准

> C9 正式提交交付物 · Track 2 · Metacognition（元认知）
> 提交人：虞梦琳（yml） · 单干

一个**纯 Python 标准库、零第三方依赖**的基准实现：不测「答对与否」，而测「系统是否知道自己会不会答对」——直接命中 DeepMind《Measuring Progress Toward AGI》点名的元认知评估缺口。

## 1. 测什么（三子任务族）

| 子任务族 | 载体 | 采集的元认知信号 |
| --- | --- | --- |
| 知识问答校准 | 20 道单选 + 20 道真假判断 | 答案 + 词面置信度（0–1） |
| 开放生成自评 | 12 道开放问答 | 先作答，再给 P(True)（我答对的概率） |
| 已知未知预判 | 12 道数学应用题 | 先给 P(IK)（我会不会做），再实际作答 |

## 2. 指标（评分函数）

| 指标 | 度量 | 含义 |
| --- | --- | --- |
| **ECE** | 校准 | 置信度与真实准确率的期望偏差，越低越校准 |
| **Brier** | 校准 | 概率预测整体质量 |
| **AUROC** | 自知（区分度） | 模型区分「会做/不会做」的能力 |
| **弃答增益** | 监控→控制 | 低置信弃答后剩余准确率的提升，τ 在留出半集上调定 |
| **分半信度** | 信度 | 题集对半，指标是否稳定 |

## 3. 快速开始

```bash
# 零安装，直接运行（Python 3.10+）
python -m metacog --seed 0

# 指定模型画像
python -m metacog --models calibrated,overconfident,underconfident,blind

# 结果写入 results/（含 summary.md 与逐题 JSON）
```

## 4. 接入真实前沿模型（OpenAI 兼容端点）

```bash
# OpenAI 兼容端点（GPT / 兼容服务的 Claude、Gemini、本地 vLLM 均可）
$env:OPENAI_API_KEY="sk-..."
$env:OPENAI_BASE_URL="https://api.openai.com/v1"   # 可选，默认 OpenAI
$env:OPENAI_MODEL="gpt-4o-mini"                     # 可选
python -m metacog --real
```

说明：本仓库已用**本地 ollama 跑通真实模型 `qwen2.5:latest`**（免 key、免费用，见 §7.1）；更换任何 OpenAI 兼容端点（GPT / Claude / Gemini / 本地 vLLM / ollama），`--real` 一键即可复跑。

## 5. 目录结构

```
yml_C9_benchmark/
├── README.md
├── requirements.txt          # 标准库即可，无第三方依赖
├── data/                     # held-out 演示集（真正的私有集由主办方持有）
│   ├── mcq.json
│   ├── true_false.json
│   ├── open_qa.json
│   └── ik_math.json
├── metacog/
│   ├── __init__.py
│   ├── __main__.py
│   ├── dataset.py
│   ├── models.py
│   ├── scorer.py
│   ├── cli.py
│   └── reliability.py        # 信度/效度实证
└── results/                  # 运行后生成（含 reliability_validity.json）
```

## 6. 诚实声明（局限）

- `data/` 是**演示/开发集**，用于跑通管线；真正的 held-out 私有集在提交时由主办方机制持有，不随仓库公开（呼应论文对「公开基准易污染」的担忧）。
- `SimulatedModel` 是**合成校准画像**（校准/高估/低估/无自知），用于证明指标能正确区分不同校准与区分度，**不是真实模型成绩**。
- 真实模型跑分**已完成**：本地 ollama `qwen2.5:latest` 经 `--real` 跑通 64 题（见 §7.1），数字为真实模型输出、非伪造；换其他模型/端点需自行复跑。

## 7. 运行验证结果（`python -m metacog --seed 0`）

指标管线已跑通，四种合成校准画像的指标能正确区分「校准好坏」与「有无自知」：

| 画像 | 正确率 | ECE | Brier | AUROC | 弃答增益 |
| --- | --- | --- | --- | --- | --- |
| simulated-calibrated | 0.688 | **0.087** | 0.182 | **0.752** | 0.312 |
| simulated-overconfident | 0.688 | 0.227 | 0.255 | 0.625 | 0.073 |
| simulated-underconfident | 0.688 | 0.237 | 0.253 | 0.645 | 0.312 |
| simulated-blind | 0.688 | 0.190 | 0.262 | **0.515** | 0.077 |

验证结论：
- `calibrated` 的 ECE 最低（0.087）、AUROC 最高（0.752）——校准与自知信号都最强；
- `blind` 的 AUROC ≈ 0.5（0.515）——无自知，符合理论预期；
- `overconfident` / `underconfident` 的 ECE 明显抬升（约 0.23）——置信度偏差被检出。

（ECE 未到 0 是有限样本（64 题）+ 逐题 ±3% 抖动所致，属正常统计噪声；区分信号清晰、方向正确。）

### 7.1 真实模型跑分（本地 ollama · qwen2.5:latest）

| 模型 | 正确率 | ECE | Brier | AUROC | 弃答增益 |
| --- | --- | --- | --- | --- | --- |
| **qwen2.5**（真实） | **0.984** | **0.009** | **0.014** | **0.937** | 0.000 |

- **运行方式**：本地 ollama 加载 `qwen2.5:latest`（4.7 GB），经 OpenAI 兼容端点 `/v1` 以 `--real` 跑通全部 64 题。
- **判分格式修复**：首跑时单选/真假题正确率全为 0（模型输出 `"A. H2O"` / `"真"`，与判分器「黄金答案精确相等」不匹配），已在判分器加入答案归一化（剥离选项前缀、真假词映射布尔值），修复后正确计入。
- **天花板效应（诚实局限）**：qwen2.5 在演示集上正确率 0.984、几乎全对，导致弃答增益=0、AUROC 区分度信息量有限——这反证了「held-out 私有集应由主办方持有、演示集不能当正式评测集」的必要性。

## 8. 信度/效度实证（`python -m metacog.reliability`）

把提案里的「科学性论证」落成可复算数字（5 个随机种子重测 + 分半）：

| 证据类型 | 检验问题 | 结果 | 结论 |
| --- | --- | --- | --- |
| 重测信度 | 换随机种子，指标稳不稳？ | ECE 跨 5 种子 std ≤ 0.09 | 指标稳定、可复现 |
| 构念效度 | 置信度是否携带正确率信息？ | conf_correct_r：calibrated **0.31**，blind **≈0.00** | 「有自知」画像置信度有效，「无自知」画像无效 |
| 区分效度 | 能否区分「有/无自知」？ | AUROC：calibrated **0.69** vs blind **0.49** | 盲画像≈随机（0.5），区分成立 |

分半信度在 64 题（每半 32 题）下波动较大（如 calibrated 半1 ECE 0.17 vs 半2 0.08），属小样本正常现象，故以多种子重测作为主信度证据；扩题后分半会更稳。完整数字见 `results/reliability_validity.json`。
