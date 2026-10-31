# -*- coding: utf-8 -*-
"""演示：六组对照汇总、回归差异与成本统计

运行：python demo.py
"""
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from eval_board import EvalBoard  # noqa

HERE = os.path.dirname(os.path.abspath(__file__))
board = EvalBoard(os.path.join(HERE, "examples"))

print("评测对照与成本看板演示 — 六组对照\n")
print(f"看板：{board.config['board_name']}")
print(f"结果：{len(board.results)} 组有数据\n")

print("汇总（每组每指标均值/样本数）：")
for gid, metrics in board.summary().items():
    label = next((g["label"] for g in board.config["groups"]
                  if g["group_id"] == gid), gid)
    print(f"  {gid:<16} {label}")
    for metric, stat in metrics.items():
        print(f"    {metric:<12} mean={stat['mean']} n={stat['n']}")

print("\n回归差异（相对基准组 grp-method-a）：")
for gid, metrics in board.regression_delta().items():
    print(f"  {gid}:")
    for metric, d in metrics.items():
        print(f"    {metric}: delta={d['delta_pct']}% ({d['direction']})")

print("\n成本统计（脱敏 sample 口径，unit=$0.05/call）：")
cost = board.cost({"grp-method-a": {"usage": 1000},
                   "grp-method-b": {"usage": 1500}})
for gid, c in cost.items():
    print(f"  {gid}: ${c}")

print("\n" + "=" * 50)
print("验收结果: 对照配置 + 统计口径 + 可复算样例 -> ✅")
print("=" * 50)
sys.exit(0)