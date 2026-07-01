## 1. Core Analytics Implementation

- [x] 1.1 创建 `src/analytics.py` 模块，并定义内置 of 二次元大盘“大众受众热度基线”静态数据映射。
- [x] 1.2 在 `src/analytics.py` 中编写 SQL 聚合分析逻辑，提取题材总排行、星期分布（对齐映射为 Day1/Day2）和场馆集聚矩阵。
- [x] 1.3 实现 DBI (同人偏离度指数) 计算，并将聚合结果序列化为指定格式的 JSON 报告保存至本地。

## 2. CLI Integration

- [x] 2.1 修改 `main.py` 的 ArgumentParser，添加 `--analyze-genres <output_path>` 选项。
- [x] 2.2 在 `main.py` 逻辑流中接入对该选项的拦截处理，自动提取输出目录并执行题材分析。

## 3. Testing & Verification

- [x] 3.1 编写单元测试 `tests/test_analytics.py`，模拟社团数据库并验证统计数据及 DBI 计算精度。
- [x] 3.2 运行命令行实际执行题材大盘分析，验证导出的 JSON 报告结构是否完全符合规划格式。
