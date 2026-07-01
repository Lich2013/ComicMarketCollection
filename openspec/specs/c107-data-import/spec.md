# c107-data-import Specification

## Purpose
TBD - created by archiving change import-c107-cpsp-data. Update Purpose after archive.
## Requirements
### Requirement: C107 数据库结构初始化
系统必须在 `data/comic_market.db` 中建立专用于 C107 的独立数据表 `c107_circles`，以防止与 C108 等其他展会数据混淆或主键冲突。
该表必须包含与 C108 `circles` 表同等的字段：`id` (主键/Table ID), `circle_id` (社团唯一ID), `name`, `author`, `genre`, `description`, `hall`, `day`, `block`, `space`, `twitter_url`, `twitter_username`, `pixiv_url`, `circle_cut_url` 以及 `updated_at`。

#### Scenario: 自动建表与校验
- **WHEN** 运行 C107 数据导入时
- **THEN** 系统自动在 SQLite 中建立 `c107_circles` 表并校验表结构完整性

### Requirement: C107 原始数据包导入与解析
系统必须能读取指定目录（tables 目录）下的所有 C107 社团 JSON 详情包，提取社团各项元数据信息（包括解析 Twitter 链接提取用户名，以及提取 Cut 首个 URL），进行批量合并写入并确保导入的幂等性。

#### Scenario: 成功解析并导入数据
- **WHEN** 运行命令 `--import-c107` 并指定 C107 的 tables 目录时
- **THEN** 系统能够无错解析并批量导入所有社团，并在终端打印成功导入的社团总数

