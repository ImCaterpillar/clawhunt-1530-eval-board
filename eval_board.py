# -*- coding: utf-8 -*-
"""评测对照与成本看板 —— 六组对照结果汇总、回归差异与成本统计。

对应 ClawHunt 任务 #1530（企业 Agent 系统 43/50｜评测对照与成本看板），
验收标准：**提交对照配置、统计口径与可复算样例**。

设计：
  - `schema/eval_board.schema.json`（draft-07）定义六组配置 + 指标 + 成本模型
  - `EvalBoard`：
      · 加载配置与匿名结果（config/ + results/）
      · 汇总：每组每指标均值/样本数
      · 回归差异：相对基准组 delta（% 与方向）
      · 成本统计：按 unit_price 与 usage 计算成本
  - 可复算：所有数字从输入逐行算出，无隐藏口径
"""
import json
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


class EvalError(Exception):
    pass


def _type_ok(value, t):
    if t == "object":
        return isinstance(value, dict)
    if t == "array":
        return isinstance(value, list)
    if t == "string":
        return isinstance(value, str)
    if t == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if t == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if t == "boolean":
        return isinstance(value, bool)
    if t == "null":
        return value is None
    return True


def validate(instance, schema, path="$"):
    errors = []
    if "type" in schema and not _type_ok(instance, schema["type"]):
        return [f"{path}: 期望 {schema['type']} 实为 {type(instance).__name__}"]
    if "enum" in schema and instance not in schema["enum"]:
        errors.append(f"{path}: 值 {instance!r} 不在允许集合 {schema['enum']}")
    if isinstance(instance, str):
        if "minLength" in schema and len(instance) < schema["minLength"]:
            errors.append(f"{path}: 长度 {len(instance)} < {schema['minLength']}")
        if "pattern" in schema and not re.search(schema["pattern"], instance):
            errors.append(f"{path}: 值 {instance!r} 不匹配模式 {schema['pattern']}")
    if isinstance(instance, (int, float)) and not isinstance(instance, bool):
        if "minimum" in schema and instance < schema["minimum"]:
            errors.append(f"{path}: {instance} < {schema['minimum']}")
    if isinstance(instance, list):
        if "minItems" in schema and len(instance) < schema["minItems"]:
            errors.append(f"{path}: 元素数 {len(instance)} < {schema['minItems']}")
        if "maxItems" in schema and len(instance) > schema["maxItems"]:
            errors.append(f"{path}: 元素数 {len(instance)} > {schema['maxItems']}")
        if "items" in schema:
            for i, item in enumerate(instance):
                errors += validate(item, schema["items"], f"{path}[{i}]")
    if isinstance(instance, dict):
        if "required" in schema:
            for k in schema["required"]:
                if k not in instance:
                    errors.append(f"{path}: 缺少必填字段 {k!r}")
        if schema.get("additionalProperties") is False \
                and "properties" in schema:
            for k in instance:
                if k not in schema["properties"]:
                    errors.append(f"{path}: 不允许的额外字段 {k!r}")
        if "properties" in schema:
            for k, sub in schema["properties"].items():
                if k in instance:
                    errors += validate(instance[k], sub, f"{path}.{k}")
    return errors


class EvalBoard:
    def __init__(self, base_dir=None):
        here = os.path.dirname(os.path.abspath(__file__))
        self.schema = json.load(open(
            os.path.join(here, "schema", "eval_board.schema.json"),
            encoding="utf-8"))
        self.config = None
        self.results = {}
        if base_dir:
            self.load_dir(base_dir)

    def load_dir(self, d):
        cfg_path = os.path.join(d, "config.json")
        if os.path.isfile(cfg_path):
            self.set_config(json.load(open(cfg_path, encoding="utf-8")))
        res_path = os.path.join(d, "results.json")
        if os.path.isfile(res_path):
            for row in json.load(open(res_path, encoding="utf-8")):
                self.add_result(row)
        return len(self.results)

    def set_config(self, cfg):
        errs = validate(cfg, self.schema)
        if errs:
            raise EvalError("配置校验失败: " + "; ".join(errs[:4]))
        self.config = cfg
        return cfg["board_name"]

    def add_result(self, row):
        """row: {group_id, metric, value, usage?}"""
        if not self.config:
            raise EvalError("请先 set_config")
        gids = {g["group_id"] for g in self.config["groups"]}
        mids = {m["metric"] for m in self.config["metrics"]}
        if row.get("group_id") not in gids:
            raise EvalError(f"未知组: {row.get('group_id')}")
        if row.get("metric") not in mids:
            raise EvalError(f"未知指标: {row.get('metric')}")
        self.results.setdefault(
            row["group_id"], {}).setdefault(
            row["metric"], []).append(float(row.get("value", 0)))
        return row

    # ── 汇总（每组每指标均值/样本数）─────────────────────────────
    def summary(self):
        out = {}
        if not self.results:
            return out
        for gid, metrics in self.results.items():
            out[gid] = {}
            for metric, vals in metrics.items():
                out[gid][metric] = {
                    "mean": round(sum(vals) / len(vals), 4),
                    "n": len(vals),
                }
        return out

    # ── 回归差异（相对基准组 delta%）────────────────────────────
    def regression_delta(self):
        """返回 {group_id: {metric: {'delta_pct': x, 'direction': ...}}}"""
        if not self.config:
            return {}
        baseline = next((g["group_id"] for g in self.config["groups"]
                         if g["baseline"]), None)
        if not baseline:
            return {}
        summ = self.summary()
        base = summ.get(baseline, {})
        out = {}
        for gid in self.config["groups"]:
            g = gid["group_id"]
            if g == baseline:
                continue
            row = {}
            for metric in base:
                b = base[metric]["mean"]
                a = summ.get(g, {}).get(metric, {}).get("mean", 0.0)
                delta = ((a - b) / b * 100) if b else 0.0
                direction = next(
                    (m["direction"] for m in self.config["metrics"]
                     if m["metric"] == metric), "higher_is_better")
                row[metric] = {
                    "delta_pct": round(delta, 4),
                    "direction": direction,
                }
            out[g] = row
        return out

    # ── 成本统计 ────────────────────────────────────────────────
    def cost(self, usage_by_group):
        """usage_by_group: {group_id: {'usage': n}} → 按 unit_price_usd 计成本"""
        cost = {}
        for gid, data in usage_by_group.items():
            cost[gid] = round(
                data.get("usage", 0) * self.config["cost_model"]["unit_price_usd"],
                4)
        return cost