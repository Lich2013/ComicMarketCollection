## ADDED Requirements

### Requirement: CPSP 数据库结构初始化
系统必须在 `data/comic_market.db` 中建立专用于 CPSP 的独立数据表 `cpsp_products` 和 `cpsp_circles`，以防止数据被污染。
* `cpsp_products` 包含字段：`id` (主键), `doujinshi_id` (唯一), `name`, `theme_alias`, `type`, `sell_status`, `hot_count`, `day_label`, `circle_id`, `tags` 以及 `created_at`。
* `cpsp_circles` 包含字段：`id` (主键), `circle_id` (唯一), `name`, `position_name`, `position` 以及 `created_at`。

#### Scenario: 自动建表与校验
- **WHEN** 运行 CPSP 数据导入时
- **THEN** 系统自动在 SQLite 中建立 `cpsp_products` 和 `cpsp_circles` 表并校验表结构完整性

### Requirement: CPSP 原始数据包导入与解析
系统必须能读取指定目录下的所有 CPSP JSON 数据包，解析其中的商品和社团列表，对题材字段进行标准化清洗（与 CP31 共享统一的 IP Standard Dict），进行内存级去重及批量合并后，写入数据库中。

#### Scenario: 成功解析并导入数据
- **WHEN** 运行命令 `--import-cpsp` 并指定含有 JSON 文件的目录时
- **THEN** 系统能够无错解析所有商品项及所属社团，去重并写入数据库，同时在终端打印成功导入的制品和社团总数
