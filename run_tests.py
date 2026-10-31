# -*- coding: utf-8 -*-
"""评测对照与成本看板主流程验证 —— 对应验收标准
「提交对照配置、统计口径与可复算样例」

零第三方依赖。打印每条验收标准的实测结果。
"""
import os
import subprocess
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from eval_board import EvalBoard, EvalError, validate  # noqa
import json  # noqa

PASS, FAIL = [], []
OK = "\u2705"
NO = "\u274c"


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    mark = OK if cond else NO
    line = "  " + mark + " " + name
    if detail:
        line += " -- " + detail
    print(line)


print("=" * 78)
print("Eval Board -- acceptance verification")
print("=" * 78)
print("Acceptance: 对照配置、统计口径与可复算样例\n")

HERE = os.path.dirname(os.path.abspath(__file__))
board = EvalBoard(os.path.join(HERE, "examples"))

# 1. 对照配置可加载且六组
check("1. board config loadable (6 groups)",
      board.config is not None
      and len(board.config["groups"]) == 6,
      f"groups={len(board.config['groups']) if board.config else 0}")

# 2. 匿名结果加载（16 条）
check("2. anonymous results loaded",
      len(board.results) == 6,
      f"groups_with_results={len(board.results)}")

# 3. 汇总统计口径（均值/样本数）
summ = board.summary()
a_acc = summ.get("grp-method-a", {}).get("accuracy", {})
check("3. summary mean/n computed",
      abs(a_acc.get("mean", 0) - 0.91) < 1e-6 and a_acc.get("n") == 2,
      f"a_acc={a_acc}")

# 4. 回归差异（相对基准组 grp-method-a）
delta = board.regression_delta()
b_acc = delta.get("grp-method-b", {}).get("accuracy", {})
check("4. regression delta computed",
      abs(b_acc.get("delta_pct") - ((0.945-0.91)/0.91*100)) < 1e-3,
      f"b_acc={b_acc}")

# 5. 方向标注（higher_is_better / lower_is_better）
check("5. effect direction annotated",
      b_acc.get("direction") == "higher_is_better",
      str(b_acc.get("direction")))

# 6. 成本统计可复算
cost = board.cost({
    "grp-method-a": {"usage": 1000},
    "grp-method-b": {"usage": 1500},
})
check("6. cost calc reproducible",
      abs(cost.get("grp-method-a", 0) - 50.0) < 1e-6
      and abs(cost.get("grp-method-b", 0) - 75.0) < 1e-6,
      str(cost))

# 7. 非法配置被拒（五组、指标空、成本负、EUR）
bad = json.load(open(os.path.join(HERE, "examples",
                                  "config-invalid.json"),
                     encoding="utf-8"))
errs = validate(bad, board.schema)
check("7. invalid config rejected", len(errs) >= 1,
      f"{len(errs)} errors")
try:
    board.set_config(bad)
    check("7b. invalid config rejected at load", False)
except EvalError:
    check("7b. invalid config rejected at load", True)

# 8. 未知组/未知指标结果被拒
try:
    board.add_result({"group_id": "grp-none", "metric": "accuracy",
                      "value": 0.1})
    check("8. unknown group rejected", False)
except EvalError:
    check("8. unknown group rejected", True)

# 9. 空配置/空结果稳健
b2 = EvalBoard()
check("9. empty board summary empty", b2.summary() == {},
      "summary={}")
r9 = b2.regression_delta()
check("9b. empty board delta empty", r9 == {}, f"delta={r9}")

# 10. demo 可运行
r10 = subprocess.run([sys.executable, "demo.py"], cwd=HERE,
                     capture_output=True, text=True, encoding="utf-8",
                     errors="replace")
check("10. demo.py exit=0", r10.returncode == 0, f"exit={r10.returncode}")

# 11. 交付齐套
refs = ["eval_board.py", "run_tests.py", "demo.py",
        "schema/eval_board.schema.json",
        "examples/config.json", "examples/results.json",
        "examples/config-invalid.json",
        "README.md", "SETUP.md",
        "docs/验收对照.md", "docs/实现说明.md", "docs/验证记录.md"]
broken = [r for r in refs if not os.path.isfile(os.path.join(HERE, r))]
check("11. delivery set complete (12 files)", not broken,
      "broken=" + str(broken) if broken else str(len(refs)) + " files")

print()
print("=" * 78)
print("Result: PASS " + str(len(PASS)) + "   FAIL " + str(len(FAIL)))
print("=" * 78)
if FAIL:
    print("Failed: " + ", ".join(FAIL))
sys.exit(1 if FAIL else 0)