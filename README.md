# 评测对照与成本看板 — 六组对照汇总、回归差异与成本统计

对应 ClawHunt 任务 **#1530**（企业 Agent 系统 43/50｜评测对照与成本看板）。

**验收标准**：提交**对照配置、统计口径与可复算样例**。

## 一条命令验证全部

```bash
python run_tests.py      # -> PASS 13 / FAIL 0
python demo.py           # -> 六组对照演示
```

## 验收三要素（与验收标准逐条对应）

**① 对照配置路径**
`schema/eval_board.schema.json` + `examples/config.json` —— 六组对照
实验配置（6 groups，其中 1 基准组）+ 指标方向 + 成本模型。

**② 统计口径（回归差异与成本）**
`eval_board.py` —— `EvalBoard`：
- `summary()` 每组每指标均值/样本数
- `regression_delta()` 相对基准组 delta%（带 higher/lower_is_better）
- `cost()` 按 unit_price × usage 算成本

**③ 可复算样例：运行命令 + 预期输出**

```bash
python run_tests.py
# ✅ 3. summary mean/n computed -- a_acc={'mean': 0.91, 'n': 2}
# ✅ 4. regression delta computed -- b_acc={'delta_pct': 3.8462, ...}
# ✅ 6. cost calc reproducible -- $50 / $75
# ✅ 7. invalid config rejected
# Result: PASS 13   FAIL 0
```

所有数字从匿名结果逐行算出，无隐藏口径，可复算。

## 快速开始

```bash
# 零第三方依赖（纯 Python 标准库）
python run_tests.py          # 全部验收验证
python demo.py               # 六组对照演示
```

## 目录

```
.
├── eval_board.py            # 汇总/回归差异/成本（核心）
├── run_tests.py             # 验收验证
├── demo.py                  # 六组对照演示
├── schema/
│   └── eval_board.schema.json  # 对照配置模板（6 组）
├── examples/
│   ├── config.json          # 六组对照配置（1 基准）
│   ├── results.json         # 匿名结果（16 条）
│   └── config-invalid.json  # 反例（校验拒绝路径）
├── docs/（验收对照 / 实现说明 / 验证记录）
├── SETUP.md
└── README.md
```

## 设计要点

1. **六组对照硬约束**：schema `groups.minItems=maxItems=6`，其中须有
   baseline=true（回归差异基准）。
2. **统计口径显式**：汇总=均值/样本数；回归差异=（组均值-基准）/基准×100；
   成本=unit_price × usage——全部可复算。
3. **指标方向**：higher_is_better / lower_is_better 标注，避免"上升=好"
   误导（latency 下降才是好）。
4. **匿名合规**：样例全部脱敏（企业 Agent 系列方法论/路由/分类 A/B 组）。

## 环境

- Python 3.8+
- **零第三方依赖**（纯标准库 json/os/re/sys）

## 边界说明

本单范围 = 六组对照实验的汇总、回归差异与成本统计；
真实实验运行、模型调用、可视化 —— 属其他拆分单。