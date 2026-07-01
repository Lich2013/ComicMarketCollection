## Context

目前，系统已成功扩展并导入了日本 C107（2025年12月）和中国 CPSP（2025年10月）的历史数据，形成了包含 C107、C108、CPSP、CP31 四个展期的丰富数据源。然而，现有的分析逻辑（如 `src/cp31_analyzer.py`）仅支持 CP31 与 Comiket (C108) 的单期横向对比，缺乏多展期、跨时序的联合分析能力。

为了最大化挖掘两国同人生态在时序演进和跨文化交融中的核心规律，我们需要设计并构建一个多展期联合分析引擎，并在此基础上生成一份包含纵向时序演化与横向倾向性对比的学术级双城同人集聚研究报告。

## Goals / Non-Goals

**Goals:**
* **构建多展期联合计算引擎**：新建 `src/multi_era_analyzer.py`，能够对 C107、C108、CPSP、CP31 进行统一的大盘基础规模（有效社团数、制品数）、热门题材排行、题材集中度（$CR_5$ 与 $CR_{10}$ 累积比率及 Bain 分类）的联合计算。
* **物理周边清洗与过滤**：在对 CPSP 数据进行统计计算时，必须自动过滤排除平面印刷小周边（`['色纸', '纸胶带']`），保留 `手办`、核心书刊（小说、漫画、图集等）及核心制品类目，从而使 CPSP 与 CP31 的大盘统计口径一致。
* **计算意愿供需偏离度 (Real-time DBI)**：使用心愿单热度 (`hotCount`) 作为需求，制品数作为供给，计算 CPSP 与 CP31 头部题材的供需偏离度。
* **多期空间自相关莫兰指数计算 (Global Moran's I)**：
  - Comiket (C107, C108)：根据同一场馆（hall）和排（block）内摊位号（space）物理距离相差 3 以内的邻接规则计算。
  - Comicup (CPSP, CP31)：根据是否处于相同的专区街道（position_name）的邻接规则计算。
* **自动生成深度学术研究报告**：动态将计算指标与分析结论写入 `research/comiket_vs_comicup_multi_era_study.md`，报告需以中文（简体）撰写，配以清晰的 Mermaid 流程图，探讨两国在组织逻辑、创作倾向、集中度、流通通路以及非商业互惠 Gifts 经济上的生态差异。
* **扩充命令行接口**：在 `main.py` 中增加 `--analyze-multi-era` 参数。
* **单元测试保障**：在 `tests/` 下编写针对联合计算引擎与过滤规则的单元测试。

**Non-Goals:**
* 抓取、同步新推文或图片的爬虫机制改进：本项目专注于已有历史数据的分析和挖掘，不修改已有的爬虫及 Playwright 代码。
* 多模态大模型 OCR 物理图像解析算法的二次优化：此部分不属于本设计的范畴。
* Comiket 的空间自相关计算中引入真实三维坐标建模：继续沿用现有的“同一 Hall 同一 Block 下桌号差值 <= 3”一维线性映射作为空间邻近准则。

## Decisions

### 1. 架构设计与模块划分
我们将新增分析引擎 `src/multi_era_analyzer.py`，而不是在原有的 `src/cp31_analyzer.py` 上打补丁。
* **理由**：`src/cp31_analyzer.py` 是针对单期 CP31 与 C108 对比硬编码的。新建 `src/multi_era_analyzer.py` 能够更好地提取通用的 Moran's I 空间自相关计算逻辑，对四展（C107, C108, CPSP, CP31）的表结构进行解耦读取，确保代码高内聚、低耦合。
* **备选方案**：直接修改 `src/cp31_analyzer.py`。但这会引入大量 if-else 分支，使原单期逻辑混乱，且不便于未来对其他展期的横向扩展。

### 2. CPSP 数据周边过滤机制
在读取 `cpsp_products` 数据时，通过 SQL 或 Pandas/Python 过滤，将 `type IN ('色纸', '纸胶带')` 剔除，保留包括 `手办` 在内的其他制品。
* **理由**：CPSP 数据集中包含了大量平面小周边（如色纸和纸胶带），这两类制品的数量非常多（总计 6,434 件，占大盘的 21.2%）。如果不予以过滤，会极大地稀释和干扰核心同人本/刊物类目的大盘倾向性分析。而 CP31 原始数据中并没有色纸和纸胶带的独立分类，过滤后双方大盘均以核心书刊和立体手办为主，能够实现精确的同口径对比。
* **备选方案**：不对 CPSP 进行任何过滤，直接与 CP31 比较。但这会导致 CPSP 的集中度和媒介类型分布与 CP31 产生虚假的口径偏差，降低研究报告的科学性。

### 3. Moran's I 计算的底层设计
在 `src/multi_era_analyzer.py` 中抽象出两个通用的 Moran's I 计算方法：
- `calculate_comiket_moran_i(db_path, table_name, target_genre)`: 读取 Comiket 表（`circles` / `c107_circles`），邻近权重定义为：同一 `hall` 且同一 `block` 且 `abs(space_i - space_j) <= 3`。
- `calculate_comicup_moran_i(db_path, circles_table, products_table, target_theme, filter_types=None)`: 读取 Comicup 表（`cp31_circles` / `cpsp_circles`），邻近权重定义为：同一 `position_name`（专区街道）。
* **理由**：这不仅满足了 Comiket 一维桌号线性排序特征与 Comicup “专区网格化街区”特征的差异性，而且通过 `filter_types` 参数能够让 CPSP 的 Moran's I 计算自动应用上面的周边过滤规则。

### 4. 学术级报告动态生成设计
分析引擎中将内置报告生成模板，并在 `--analyze-multi-era` 执行时，动态渲染计算结果，并写入 `research/comiket_vs_comicup_multi_era_study.md`。
* **理由**：直接动态渲染指标数据（有效社团数、CR 值、DBI 指数、Moran's I 等）能够保证数据的绝对真实与准确，避免手动修改数据带来的潜在错误。

## Risks / Trade-offs

### 1. 数据缺失或不一致的风险
* **Risk**: CPSP 是单日展，没有双日数据（`day_label` 全部为 `D1`）。而 CP31 是双日展（`D1` 和 `D2`）。这导致在分析“双日重合度”时，CPSP 无法提供直接的时序重合度指标。
* **Mitigation**: 在计算和报告中，对于 CPSP 的双日调度重合度，系统将其标记为 `100% 集中于单日（D1）` 或者是 `N/A (单日展)`，并与 CP31 高达 94.7% 的题材重合度进行对比，以此作为中日两国展期物理组织策略（Comiket 强拆分互斥 vs. CP31 双日高并发 overlap vs. CPSP 单日高效凝聚）差异的分析素材。

### 2. CPSP 和 CP31 题材归一化映射差异
* **Risk**: 即使导入时有 `normalize_theme`，在不同展期中仍可能存在部分长尾题材的命名偏差（例如“星穹铁道”在不同表中分别导入为“崩坏星穹铁道”或“星穹铁道”）。
* **Mitigation**: 统一复用 `src/cp31_importer.py` 中的 `normalize_theme` 函数，并在多展期联合分析中对主要比对的主题进行静态名对齐。对于排名前十的题材，在计算集中度时采用归一化后的 `theme_alias` 进行 Group By，确保合并无误。
