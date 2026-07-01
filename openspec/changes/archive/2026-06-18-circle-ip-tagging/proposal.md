## Why

当前系统在分析 Comiket（C108）大盘社团数据时，由于官方分类口径较粗（例如《明日方舟》、《明日方舟：终末地》均被收录在通用的“社交网络游戏”大类下），无法直接统计和筛选特定子 IP 的摊位分布。由于部分社团在 WebCatalog 的简介留空或写得极简，单纯使用文本模糊匹配会导致大量漏报。

我们需要建立一套社团与摊位的子 IP 自动识别、打标以及物理空间邻域传播算法，以支持精确的 IP 分布检索和多维度大盘对比。

## What Changes

- **数据库模型扩展**：新增 `circle_ip_tags` 多对多关系表以及快速查询视图 `v_circles_with_ip_tags`。
- **自动打标流水线（Tagger Pipeline）**：新增打标脚本，组合“文本匹配种子点”、“商品多模态标签反推”以及“物理空间邻域传播”三种维度进行打标。
- **命令行检索功能**：在命令行工具中集成 `--search-ip <name>`，支持按物理路线排序一键检索特定 IP 的所有参展摊位。
- **导出报表增强**：在商品数据 CSV 导出（`--export-goods`）中新增“细分IP（Sub-IP）”列。

## Capabilities

### New Capabilities
- `circle-ip-tagging`: 自动识别并对齐社团 IP 标签，支持基于空间位置邻域传播的打标推理与命令行便捷物理位置检索。

### Modified Capabilities
<!-- Existing capabilities whose REQUIREMENTS are changing -->

## Impact

- **数据库初始化与 CRUD (`src/db.py`)**：新增表结构和视图创建，更新商品导出查询。
- **命令行入口 (`main.py`)**：增加打标触发选项和 IP 物理路线检索。
- **新增模块 (`src/circle_tagger.py`)**：核心自动打标与空间传播算法的实现。
