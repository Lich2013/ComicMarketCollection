## Why

当前系统支持从 WebCatalog 同步社团以及通过 X.com 推文解析同人制品（商品）数据并入库，但缺少将解析到的商品数据结构化导出的功能。为了方便用户进行逛展规划与线下购买核对，需要提供将数据库中提取到的商品数据批量导出为 CSV 文件的能力。

## What Changes

- 在命令行工具中增加 `--export-goods <output_file_path>` 参数，用于指定导出 CSV 的路径。
- 实现根据用户参数（如 `--days`, `--halls`, `--circle-ids`, `--circle-name`）过滤需要导出的社团及商品。
- 将导出的 CSV 格式规范化，包含：日期、场馆、区域、摊位号、社团名、作者、类别 (genre)、类型、商品、数量、价格、来源推文、社交媒体链接。
- CSV 编码使用 UTF-8 with BOM (utf-8-sig)，以兼容中日文字符集在 Excel 下直接打开不乱码。

## Capabilities

### New Capabilities

- `goods-export`: 提供将数据库中的社团及对应的商品制品信息按逛展规划排序并导出为 CSV 文件的功能，支持多条件筛选过滤。

### Modified Capabilities

无

## Impact

- 命令行主入口：`main.py` 新增 `--export-goods` 控制参数和处理逻辑。
- 数据库管理模块：`src/db.py` 新增数据联查及 CSV 文件生成方法。
