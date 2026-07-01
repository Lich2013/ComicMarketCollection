## Context

由于需要对比日本 Comic Market 108 (C108) 与中国 Comicup 31 (CP31) 的同人创作生态，我们需要建立一套数据摄入、清洗和指标计算的工程流水线。CP31 的原始数据以分包 JSON 文件形式存放，包含商品及摊位元数据，需结构化导入 SQLite 并进行关联计算，最后输出研究报告。

## Goals / Non-Goals

**Goals:**
* 在现有的 SQLite 数据库中创建隔离的 CP31 数据表。
* 编写健壮的 JSON 解析器，能自动去重并清洗拼写变体（例如合并同一 IP 题材的不同标点写法）。
* 编写计算引擎，从数据库提取数据并自动计算媒介占比、市场集中度、Real-time DBI 以及时空并发重合度。
* 支持通过 `main.py` 命令行接口一键执行导入和分析，并自动在 `research/` 目录下生成对比报告 `research/comiket_vs_comicup_comparison.md`。

**Non-Goals:**
* 本次设计不修改 Comiket C108 原有数据库表和字段，不对原有同步和计算流水线引入侵入性修改。
* 本次设计不涉及在 CP31 数据上执行 NLP/LLM 简介预分析，仅对制品的标题和标签进行常规关键词匹配。

## Decisions

### 1. 数据库隔离设计 (Database Isolation)
*   **决策**：在 `data/comic_market.db` 中建立全新的 `cp31_products` 与 `cp31_circles` 表。
*   **理由**：CP31 数据与 C108 数据的结构不同（CP31 包含制品级心愿热度 `hotCount`、制品类型 `type`、流通状态 `sellStatus`；而 C108 仅提供社团级摊位物理信息及简介文本）。单独建表可实现物理隔离，防止数据污染，同时两表均使用主键唯一性约束（`doujinshi_id` / `circle_id`）实现幂等导入。

### 2. IP 题材标准化清洗 (Theme Standardization & Merging)
*   **决策**：在导入和计算阶段，设计 IP 题材标准化字典。例如，将 `崩坏：星穹铁道` 与 `崩坏星穹铁道` 统一合并为 `《崩坏：星穹铁道》`；将 `ウマ娘` 映射为 `《赛马娘》` 以进行跨国题材直接对比。
*   **理由**：不同展会的申报平台及创作者对 IP 的拼写习惯不同（带冒号、括号等），若不进行归一化，会导致市场集中度与 DBI 计算产生严重偏差（分母被稀释）。

### 3. CLI 命令行参数扩展 (CLI Arguments)
*   **决策**：在 `main.py` 中扩展以下参数：
    *   `--import-cp31 <dir_path>`：指定 CP31 原始 day1data/day2data 所在目录，自动扫包并导入。
    *   `--analyze-cp31`：执行中日双城同人指标对比计算，并自动生成研究报告。
*   **理由**：保持与项目现有 CLI 设计规范一致，便于用户离线运行及复现。

## Risks / Trade-offs

*   **[风险]** CP31 数据库的表在多次导入时可能产生冗余。
    *   *缓解方案*：导入时使用 `INSERT OR IGNORE` 或 `INSERT OR REPLACE` 确保主键唯一性，并在导入前对同一 doujinshiId 进行内存级去重。
*   **[折衷]** 物理坐标自相关（Moran's I）由于两展展馆结构不同无法直接拼合。
    *   *折衷方案*：对两展分别独立计算莫兰指数，并在报告中横向对比它们的聚集强度（Moran's I 绝对值大小及 Z-score 显著性），以此反应空间调度差异。
