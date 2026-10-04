"""模型接口：合成校准画像模型（验证管线）+ OpenAI 兼容真实模型适配器。"""

import json
import os
import random
import urllib.request


class Model:
    name = "base"

    def predict(self, item):
        """返回 {"answer": ..., "confidence": float∈[0,1]}。子类实现。"""
        raise NotImplementedError


class SimulatedModel(Model):
    """合成校准画像模型：用于验证指标管线正确、且能区分不同校准/区分度。

    不是真实前沿模型。按题项 idx 派生一个确定性真实正确率 p∈[0.5,0.95]，
    作答服从 Bernoulli(p)，置信度按画像偏移：
      calibrated     conf ≈ p         → ECE 接近 0
      overconfident  conf = p + 0.25  → ECE ≈ 0.25（高估）
      underconfident conf = p − 0.25  → ECE ≈ 0.25（低估）
      blind          conf 与正确率无关 → AUROC ≈ 0.5（无自知）
    """

    def __init__(self, profile, seed=0):
        if profile not in ("calibrated", "overconfident", "underconfident", "blind"):
            raise ValueError(f"未知画像: {profile}")
        self.profile = profile
        self.rng = random.Random(seed)

    @property
    def name(self):
        return f"simulated-{self.profile}"

    def _p(self, item):
        idx = item["idx"]
        return 0.5 + 0.45 * ((idx * 7 + 3) % 10) / 9

    def predict(self, item):
        p = self._p(item)
        correct = self.rng.random() < p
        if self.profile == "calibrated":
            conf = p + self.rng.uniform(-0.03, 0.03)
        elif self.profile == "overconfident":
            conf = p + 0.25
        elif self.profile == "underconfident":
            conf = p - 0.25
        else:  # blind
            conf = self.rng.uniform(0.30, 0.70)
        conf = max(0.01, min(0.99, conf))
        return {"answer": self._answer(item, correct), "confidence": conf}

    def _answer(self, item, correct):
        task = item["task"]
        if correct:
            return item["answer"]
        if task == "mcq":
            opts = [o for o in item["options"] if o != item["answer"]]
            return self.rng.choice(opts)
        if task == "true_false":
            return not item["answer"]
        if task == "open_qa":
            return "错误答案（模拟）"
        if task == "ik_math":
            return item["answer"] + 1
        return None


class OpenAICompatibleModel(Model):
    """接入真实前沿模型（OpenAI 兼容 /chat/completions 端点，纯标准库）。

    环境变量：OPENAI_API_KEY（必填）、OPENAI_BASE_URL、OPENAI_MODEL。
    通过词面置信度（0–100）获取校准信号，与 CalibratedMath 词面化范式一致。
    """

    name = "openai-compatible"

    def __init__(self, model=None, base_url=None, api_key=None):
        self.model = model or os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
        self.base_url = (
            base_url or os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
        ).rstrip("/")
        self.key = api_key or os.environ.get("OPENAI_API_KEY")
        self.name = self.model

    def predict(self, item):
        if not self.key:
            raise RuntimeError("缺少 OPENAI_API_KEY，无法调用真实模型")
        content = self._chat(self._prompt(item))
        return self._parse(content, item)

    def _prompt(self, item):
        task = item["task"]
        if task == "mcq":
            opts = "\n".join(
                f"{chr(65 + i)}. {o}" for i, o in enumerate(item["options"])
            )
            body = (
                f"请回答以下单项选择题，并给出你对答案的置信度。\n"
                f"问题：{item['question']}\n选项：\n{opts}\n"
            )
        elif task == "true_false":
            body = (
                f"请判断以下陈述的真假，并给出你对答案的置信度。\n"
                f"陈述：{item['statement']}\n"
            )
        elif task == "open_qa":
            body = (
                f"请回答以下开放问题，并给出你认为答案正确的概率 P(True)。\n"
                f"问题：{item['question']}\n"
            )
        else:  # ik_math
            body = (
                f"请先判断你有多大把握解出这道题（0–100），然后作答。\n"
                f"题目：{item['question']}\n"
            )
        return (
            body
            + "只输出一个 JSON 对象，格式："
            + '{"answer": "<你的答案>", "confidence": <0到100的整数>}'
        )

    def _chat(self, prompt):
        payload = json.dumps(
            {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0,
                "max_tokens": 256,
            }
        ).encode()
        req = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.key}",
            },
        )
        with urllib.request.urlopen(req, timeout=120) as r:
            data = json.load(r)
        return data["choices"][0]["message"]["content"]

    def _parse(self, content, item):
        """从模型输出中容错提取 JSON，并把 confidence 归一化到 [0,1]。"""
        text = content.strip()
        if text.startswith("```"):
            text = text.strip("`")
            if text.startswith("json"):
                text = text[4:]
        start, end = text.find("{"), text.rfind("}")
        if start == -1 or end == -1:
            raise ValueError(f"无法从输出解析 JSON: {content!r}")
        obj = json.loads(text[start : end + 1])
        conf = float(obj["confidence"])
        if conf > 1:
            conf = conf / 100.0
        return {"answer": obj["answer"], "confidence": max(0.0, min(1.0, conf))}
