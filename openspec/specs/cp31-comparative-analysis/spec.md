# cp31-comparative-analysis Specification

## Purpose
TBD - created by archiving change research-cp31-comparison. Update Purpose after archive.
## Requirements
### Requirement: CP31 多维度指标统计与计算
系统必须提供计算引擎，能够从数据库中提取 CP31 的数据，并自动计算出以下量化指标：
1. **媒介类型分布**：计算各类制品类型（漫画、小说、图集、合志、海报）的数量及占比。
2. **特殊实体指标**：统计提及“无料”、“再录”、“合志”、“突发本”的制品数量及占比。
3. **市场集中度**：计算制品供给前 5 和前 10 大题材的累计占比（$CR_5$、$CR_{10}$）并输出对应的贝恩分类。
4. **真实供需偏离度 (Real-time DBI)**：利用 `hotCount` 计算大盘受众热度分母，计算各个热门题材的 Real-time DBI 供需比例。
5. **双日重合度**：计算 Day 1 和 Day 2 的题材重合与互斥程度。

#### Scenario: 自动计算大盘统计数据
- **WHEN** 执行命令 `--analyze-cp31` 时
- **THEN** 计算引擎在后台完成对 CP31 库表的多维度聚合分析，并在终端或以 JSON 格式输出所有指标

