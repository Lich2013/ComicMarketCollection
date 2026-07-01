# multi-era-comparative-analysis Specification

## Purpose
TBD - created by archiving change research-multi-era-comparison. Update Purpose after archive.
## Requirements
### Requirement: 多展期指标联合计算
系统必须提供联合计算引擎，能够从数据库中自动汇总并计算以下四个展期大盘的对比指标：
1. **大盘基础规模与题材排行**：统计并对比 C107、C108、CPSP、CP31 的有效社团数与热门题材占比。
2. **题材集中度分析**：计算四展的 $CR_5$ 与 $CR_{10}$ 累积比率，并输出其 Bain 市场结构归属。
3. **意愿供需模型比对**：利用 Allcpp `hotCount` 计算 CPSP 与 CP31 的真实供需 DBI，其中在计算 CPSP 数据时，系统必须自动排除 `['色纸', '纸胶带']` 类型的平面印刷小周边，保留 `手办` 及核心书刊类目，以保证与 CP31 核心制品大盘口径完全一致。
4. **时空调度与物理空间自相关**：分别计算 Comiket 与 Comicup 在不同时期的 Global Moran's I 空间自相关指数，用以进行空间分布结构与规整度的多期动态比对。

#### Scenario: 自动计算大盘多展期统计
- **WHEN** 执行命令 `--analyze-multi-era` 时
- **THEN** 计算引擎自动读取数据库中 C107、C108、CPSP、CP31 的数据，执行周边类别清洗、集中度及 DBI 统计，并在终端或输出对象中返回计算结果

#### Scenario: 多期空间自相关莫兰指数计算
- **WHEN** 执行多展期分析时
- **THEN** 计算引擎对 C107 题材（按 `genre`）和 CPSP 题材（按 `theme_alias` 关联 products 与 circles）执行 Global Moran's I 空间权重计算，并与 C108 和 CP31 的空间集聚强度进行纵向比对

