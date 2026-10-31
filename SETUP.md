# 设置与运行

零第三方依赖，无需安装任何包。

## 环境要求

- Python 3.8+（标准库：json / os / re / sys）

## 快速验证

```bash
# 在项目根目录
python run_tests.py        # 验收断言，期望 PASS 13 / FAIL 0
python demo.py             # 六组对照演示，期望退出码 0
```

## 在自己的代码中使用

```python
from eval_board import EvalBoard

board = EvalBoard("examples")   # 自动加载配置 + 匿名结果

# 汇总
board.summary()   # {grp-x: {metric: {'mean':..., 'n':...}}}

# 回归差异（相对基准组）
board.regression_delta()

# 成本统计
cost = board.cost({"grp-method-a": {"usage": 1000}})
# -> {"grp-method-a": 50.0}
```

## 新增对照实验

1. 复制 `examples/config.json`，保持 6 组（1 个 baseline=true）
2. 调整 metrics（保留 direction）与 cost_model
3. 把结果写入 `examples/results.json`（每条带 group_id/metric/value）
4. 重跑 `run_tests.py` 核对统计口径

## 常见问题

- **为什么要求恰好 6 组？** schema `minItems=maxItems=6` 锁死验收
  标准"六组对照实验"，防止漏组。
- **delta 负值表示什么？** 取决于 direction：lower_is_better 时负 delta
  是改善；higher_is_better 时负 delta 是回退。
- **Windows 中文乱码？** 脚本已内置 UTF-8 重配置。