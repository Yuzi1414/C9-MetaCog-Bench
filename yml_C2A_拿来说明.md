# 拿来说明：已有 benchmark 调研与「参考 / 拿了 / 改了」

> 依据 CHALLENGE.md 要求：必须调研已有 benchmark（ARC、BIG-Bench、MMLU、HumanEval 等），写明参考了什么、拿了什么、改了什么。

## 一、调研清单与结论

| 已有基准 | 测什么 | 与元认知的关系 | 我的判断 |
| --- | --- | --- | --- |
| **ARC**（Chollet 2019, arXiv:1911.01547） | 抽象推理 / 技能习得 | 测「能力」，不测自知 | 参考其「防背答案」的题项设计思路 |
| **MMLU**（Hendrycks et al. 2020, arXiv:2009.03300） | 57 学科知识问答 | 可作为校准任务的知识载体 | 拿了它的**多项选择+真假判断任务格式**，不直接用原题 |
| **BIG-Bench**（2022, arXiv:2206.04615） | 200+ 任务综合能力 | 有少量校准相关任务 | 参考其「多任务聚合出剖面」思路 |
| **HumanEval**（Chen et al. 2021, arXiv:2107.03374） | 代码生成正确率 | 与元认知弱相关 | 仅作反例：纯正确率基准，不纳入 |
| **TruthfulQA**（Lin et al. 2021, arXiv:2109.07958） | 真实性 / 模仿人类谬误 | 开放生成自评的载体 | 拿了它的**开放问答自评范式** |
| **P(True)/P(IK)**（Kadavath et al. 2022, arXiv:2207.05221） | 模型自我评估 / 自知 | **核心范式来源** | 拿了它的「先作答再评概率」与「预判我是否会做」两个协议 |
| **CalibratedMath**（Lin, Hilton & Evans 2022, arXiv:2205.14334） | 词面化不确定性 / 校准 | **核心范式来源** | 拿了它的「词面置信度 + 分布偏移校准」评测法 |

## 二、参考了什么

1. **DeepMind《Measuring Progress Toward AGI》**：认知剖面框架、10 项能力、元认知定义与子维度、人类基线口径（人口代表性样本 + 高中及以上学历）。
2. **ARC**：题项需「不能靠死记硬背」的防污染设计哲学。
3. **BIG-Bench**：用多任务聚合生成「认知剖面」而非单一分数。

## 三、拿了什么

1. **MMLU 的任务格式**：多项选择 + 真假判断，作为校准测量的知识载体。
2. **TruthfulQA 的开放问答自评范式**：先自由作答，再对答案做置信度自评。
3. **Kadavath 2022 的 P(True) / P(IK) 协议**：这是本基准的核心评测协议。
4. **CalibratedMath 的词面置信度 + 分布偏移校准法**：让校准在 out-of-distribution 上依然可测。

## 四、改了什么（我的增量）

1. **聚焦元认知缺口**：上述基准没有一个把「监控 + 控制」作为主测对象，我把它从附属指标提为主指标。
2. **三子任务族合一**：把知识校准、开放自评、已知未知预判整合进一个可对比的「元认知剖面」。
3. **加入「弃答后准确率」**：把「监控」接到「控制」（弃答）上，度量自知能否转化为有效行为——原范式未直接度量。
4. **held-out 私有测试集**：直接回应论文「公开基准易污染」的担忧，作为防作弊的核心机制。
5. **KSTAR ΔE → ECE/Brier**：把 KSTAR 的能力差距概念落到可计算的校准误差上。

## 五、文献出处（可核验）

- Burnell et al. (2026). *Measuring Progress Toward AGI*. Google DeepMind.
- Kadavath et al. (2022). *Language Models (Mostly) Know What They Know*. arXiv:2207.05221.
- Lin, Hilton & Evans (2022). *Teaching Models to Express Their Uncertainty in Words*. arXiv:2205.14334.
- Lin et al. (2021). *TruthfulQA: Measuring How Models Mimic Human Falsehoods*. arXiv:2109.07958.
- Hendrycks et al. (2020). *Measuring Massive Multitask Language Understanding*. arXiv:2009.03300.
- Chollet (2019). *On the Measure of Intelligence*. arXiv:1911.01547.
