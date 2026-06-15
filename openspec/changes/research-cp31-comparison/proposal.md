## Why

当前的 Comiket (C108) 同人创作生态分析主要集中在日本成熟的同人市场。为了获得更全面的跨文化与跨国同人创作比较，我们需要将中国最大的同人展会 Comicup (CP31) 的数据引入分析。通过对比，能够深入揭示中日创作者在题材集聚（时空排布）、媒介偏好（漫画 vs 小说）以及供需对齐机制（心愿单热度 vs 制品供给）上的本质生态差异。

## What Changes

1. **CP31 数据导入模块**：在 `main.py` 及 `src/` 中新增针对 CP31 day1 和 day2 JSON 数据包（共 334 个包）的结构化清洗与解析功能，并将其独立导入至 `data/comic_market.db` 的新表（`cp31_products`、`cp31_circles`）中，确保不污染 C108 原有数据库。
2. **比较指标计算引擎**：实现 CP31 数据统计，包括：
   * 各题材制品开本与媒介类型分布（漫画、小说、图集、合志等）。
   * 物理与流通特性统计（现场贩售比例、无料比例、合志比例、再录比例）。
   * 双日题材并发重合度。
   * 题材市场集中度（$CR_5$ 与 $CR_{10}$）及贝恩分类。
   * 基于心愿单热度 `hotCount` 的真实实时供需偏离度（Real-time DBI）。
   * 空间局部莫兰指数（Moran's I）自相关计算。
3. **比较研究报告及图表产出**：输出正式的对比研究报告 `research/comiket_vs_comicup_comparison.md`，并在其中集成题材集中度对比表、两栖营销漏斗 Mermaid 流程图和时空分流图景对比。

## Capabilities

### New Capabilities
- `cp31-data-import`: 解析 CP31 数据目录（day1data 和 day2data JSON 包）并结构化导入 SQLite 新表。
- `cp31-comparative-analysis`: 自动计算 CP31 的媒介占比、市场集中度、莫兰指数与实时 DBI，支持命令行调用。
- `cp31-comparison-report`: 自动或手动汇总计算结果，在 `research/` 目录下输出中日双城同人集聚与创作生态对比研究报告。

### Modified Capabilities
<!-- 空 -->

## Impact

* **数据库 (`data/comic_market.db`)**：新建 `cp31_products` 与 `cp31_circles` 表，对原有 C108 摊位及社团表零影响。
* **命令行工具 (`main.py`)**：新增 `--import-cp31 <dir>` 及 `--analyze-cp31` 等控制台命令接口。
* **文档与研究中心 (`research/`)**：新增 `research/comiket_vs_comicup_comparison.md` 研究报告。
