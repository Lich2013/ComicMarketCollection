# circle-ip-tagging Specification

## Purpose
TBD - created by archiving change circle-ip-tagging. Update Purpose after archive.
## Requirements
### Requirement: SQLite 数据库支持多 IP 标签与快速联表视图 (MUST)
系统必须 (MUST) 支持每个社团（`circles`）打上零个或多个 IP 标签，以便在查询时可以针对同一社团支持多项标签的返回。
系统必须 (MUST) 提供一个快速查询视图，使调用方无需在每次查询时手工编写星期与逻辑日期（`Day1`, `Day2`）的关联转换逻辑即可获取完整的社团信息和其对应的 IP。

#### Scenario: 创建关联表和查询视图
- **WHEN** 数据库完成初始化并执行 `init_db()`
- **THEN** 数据库中应当正确创建关系表 `circle_ip_tags` 以及视图 `v_circles_with_ip_tags`，且关系表具有联合唯一约束 `UNIQUE(event, circle_id, ip_tag) ON CONFLICT REPLACE`。

### Requirement: 自动打标流水线（Tagger Pipeline）支持规则组合打标与物理空间传播 (MUST)
系统必须 (MUST) 提供一个基于规则组合的打标工具，它应当自动执行以下三个层级的打标逻辑：
1. **商品多模态标签反推**：若该社团存在已被多模态大模型识别出来的指定 IP 关键字商品，将其标记为该 IP (MUST)，设置置信度为 1.0。
2. **简介与名字关键字匹配**：扫描社团简介与名称，匹配 IP 的翻译、外文、简称（例如 `"アークナイツ"`、`"Arknights"`），将其标记为该 IP (MUST)，设置置信度为 1.0。
3. **空间邻域传播算法**：在相同的 `(day, hall, block)`（日期、馆、排）下，以特定密度窗口将标记传播给物理上排布连续且相邻的未打标社团，将其标记为该 IP (MUST)，设置置信度为 0.8，来源为 `'spatial'`。

#### Scenario: 自动化打标与空间推导
- **WHEN** 运行自动打标逻辑且扫描到 `西 め 01 - 09` 连续区间，在此区间中已有至少 3 个社团直接通过关键字或商品被打上了“明日方舟”标签（置信度为 1.0）
- **THEN** 这一段区间内所有简介留空或未被显式匹配的社团（如 `め01a`, `め03b` 等）均被系统自动打上“明日方舟”标签（置信度为 0.8，标签来源标记为 `spatial`）。

### Requirement: 命令行快速物理路线检索特定 IP 摊位 (MUST)
系统必须 (MUST) 提供命令行 `--search-ip <ip_name>` 检索参数，允许用户直接传入 IP 名字。
系统必须 (MUST) 按参展天、展馆、街区和摊位号对结果进行物理路线排序，并向控制台输出易于阅读的路线指引。

#### Scenario: 检索明日方舟摊位物理路线
- **WHEN** 用户执行命令行 `.venv/bin/python main.py --search-ip "明日方舟"`
- **THEN** 系统从联表视图中提取结果，在控制台按 `Day`, `Hall`, `Block`, `Space` 排序并打印出逛展路线推荐。

### Requirement: 商品数据 CSV 导出包含子 IP 标签 (MUST)
系统的商品 CSV 导出逻辑必须 (MUST) 追加“细分IP（Sub-IP）”数据列。

#### Scenario: 导出含有 IP 字段 of 商品数据
- **WHEN** 运行商品导出命令 `.venv/bin/python main.py --export-goods data/goods.csv`
- **THEN** 生成的 CSV 中包含“细分IP”数据列，且 `西 め 01-09` 范围内的社团制品在此列中显示“明日方舟”。

