## Why

为了深入分析跨期、跨地域的同人创作生态变迁，系统需要引入日本 C107（2025.12 举行）和中国 CPSP（2025.10 举行）的历史展会数据。这将为后续中日双城同人集聚的多时期动态演进研究提供坚实的数据支撑。

## What Changes

- **C107 数据导入**：编写 C107 社团 WebCatalog JSON 解析器，扫描并解析所有的社团详情文件，将其导入至 SQLite 新表 `c107_circles` 中。
- **CPSP 数据导入**：编写 CPSP 制品及社团分包 JSON 解析器，支持对题材名称进行标准化清洗和内存去重，将其导入至 SQLite 新表 `cpsp_products` 与 `cpsp_circles` 中。
- **命令行工具扩展**：在 `main.py` 中扩充 `--import-c107 <dir>` 和 `--import-cpsp <dir>` 参数。
- **单元测试验证**：编写对应的自动化单元测试，验证导入的正确性与幂等性。

## Capabilities

### New Capabilities
- `c107-data-import`: 自动扫描并读取 C107 原始社团数据包并结构化导入隔离数据库中。
- `cpsp-data-import`: 自动扫描并读取 CPSP 原始制品与社团分包，执行清洗与标准化后导入隔离数据库中。

### Modified Capabilities
<!-- 空 -->

## Impact

* **数据库 (`data/comic_market.db`)**：新建 `c107_circles`、`cpsp_products` 与 `cpsp_circles` 表，对现有 C108 与 CP31 数据完全物理隔离，防止主键及数据交叉污染。
* **命令行工具 (`main.py`)**：新增 `--import-c107` 及 `--import-cpsp` 的参数接收与业务挂载。
