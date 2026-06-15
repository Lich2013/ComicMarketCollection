## ADDED Requirements

### Requirement: CP31 数据库结构初始化
系统必须在 `data/comic_market.db` 中建立专用于 CP31 的独立数据表 `cp31_products` 和 `cp31_circles`，以防止数据与 Comiket 数据污染。
* `cp31_products` 包含字段：`id` (主键), `doujinshi_id` (唯一), `name` (名称), `theme_alias` (题材/IP), `type` (作品类型), `sell_status` (流通状态), `hot_count` (心愿热度), `day_label` (D1或D2).
* `cp31_circles` 包含字段：`id` (主键), `circle_id` (唯一), `name` (社团名), `position_name` (专区名), `position` (摊位号).

#### Scenario: 自动建表与校验
- **WHEN** 运行 CP31 数据导入时
- **THEN** 系统自动在 SQLite 中建立 `cp31_products` 和 `cp31_circles` 表并校验表结构完整性

### Requirement: CP31 JSON 数据清洗与导入
系统必须能读取指定目录下的 Day 1 和 Day 2 的 JSON 数据包，解析其中的商品和社团列表，进行清洗去重后导入至数据库中。

#### Scenario: 成功解析并导入数据
- **WHEN** 运行命令 `--import-cp31` 并指定含有 JSON 文件的目录时
- **THEN** 系统能够无错解析所有商品项，去重并写入数据库，同时在终端打印成功导入的制品和社团总数
