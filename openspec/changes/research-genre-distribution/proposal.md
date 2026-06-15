## Why

当前系统已经成功抓取并积累了大量的 Comic Market 社团元数据（如 `circles` 表中包含 22,856 条记录）。为了深入了解 Comiket 展会的题材构成、探讨题材与受众及大盘的关系，我们需要对这些元数据进行系统化研究，并生成可交互、结构化的分析数据，为未来的可视化看板及逛展路线算法提供基础洞察与量化依据。

## What Changes

- **新增分析能力**：引入对参展社团题材（`genre`）在日期和展馆维度下的交叉统计与偏离度（DBI）计算能力。
- **命令行工具扩展**：在 `main.py` 中新增 `--analyze-genres` 命令行参数，用于一键计算题材大盘分布，并支持将分析数据以 JSON 格式输出至指定路径。
- **数据导出接口**：实现将分析结果导出为结构化 JSON 文件的接口，包含题材总体频率排行、日夜受众排程对比、场馆集聚矩阵以及外部受众偏离度（DBI）指数。

## Capabilities

### New Capabilities
- `genre-distribution-analysis`: 提供对社团题材分布和受众偏离度的分析统计。该能力将解析数据库中 `circles` 表的 `genre`、`day`（`土`/`日`）、`hall` 字段，结合外部受众参考指标计算同人偏离度指数（DBI），并生成结构化 JSON 报告。

### Modified Capabilities

## Impact

- **Affected code**: `main.py`, `src/db.py`
- **APIs**: 无外部 API 变更。
- **Dependencies**: 仅依赖现有的 `sqlite3`、`json`、`yaml` 等库。
- **Systems**: 生成的分析报告存放在 `data/` 目录或用户自定义路径下。
