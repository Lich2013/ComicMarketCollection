## Why

当前系统在同步包含多张图片的品书推文时，会在数据库 `catalogs` 表中将图片拆分为多行记录（如 `tweet_id_0`、`tweet_id_1`）。这导致了两个严重问题：
1. **SQLite 锁冲突崩溃**：在写入多条记录时，未释放的数据库连接会导致 `sqlite3.OperationalError: database is locked` 并使抓取过程崩溃，导致只有第一张图片能成功落库，其他图片仅存在于本地而无法记录和解析。
2. **LLM 解析上下文丢失与成本高昂**：多图被拆分成多条记录后，商品提取模块会对每张图片独立发起一次 LLM 请求。如果推文封面与实际商品单分布在不同图片中，独立分析将导致封面图被忽略（ignored），商品单图由于缺乏推文文本上下文导致解析不全，且多次 API 调用也成倍增加了 Token 开销。

## What Changes

- **单推文单行记录归一化**：废弃 `tweet_id` 的 `_{idx}` 后缀拆分模式。一条推文在数据库 `catalogs` 表中仅占用一行记录，其主键直接使用原始的 `tweet_id`。
- **图片路径多合一存储**：当推文包含多张图片时，所有下载到本地的图片路径以逗号 `,` 分隔的字符串形式统一合并存储在 `image_path` 字段中（例如 `path1.jpg,path2.jpg`）。
- **多图联合 LLM 品书提取 (OpenAI)**：在进行商品制品提取（goods extraction）时，解析模块检测到逗号分隔的多张图片路径，会在 Python 内部依次循环处理：对每张图片独立调用视觉 LLM 进行分析以保持注意力集中，最后在 Python 端对所有提取出的商品列表进行合并去重。
- **命令行工具支持多图扩展 (cmd)**：当使用命令行识别器（`cmd` provider）时，同样会在 Python 内部串行循环，多次调用外部 CLI 工具，每次传入单张图片路径，最后将所有 CLI 输出的商品结果进行汇总。
- **修复 SQLite 连接泄露**：对 `src/db.py` 中所有的数据库 CRUD 操作函数进行重构，在 `try...finally` 块中显式调用 `conn.close()` 释放连接，彻底解决高频数据库写入时的锁定报错。

## Capabilities

### New Capabilities
*无*

### Modified Capabilities
- `catalog-sync`: 调整推文图片下载与 catalogs 记录的关联方式，从“一张图片对应一条目录记录”变更为“一条推文对应一条目录记录，多张图片地址使用逗号拼接”。
- `goods-extractor`: 调整商品解析模块，支持读取逗号分隔的多张图片路径，将它们合并作为单次视觉 LLM（或外部命令行）调用的入参，以实现多图联合制品分析提取。

## Impact

- **Affected Code**:
  - `src/db.py`: 重构连接生命周期管理，在所有 CRUD 函数中加入 `try...finally: conn.close()`。
  - `src/twitter_sync.py`: 调整推文抓取落库逻辑，写入单行多图目录。
  - `src/goods_extractor.py`: 提取模块支持多图 Base64 并行传输与识别。
  - `tests/test_db.py`: 修改涉及 `tweet_id_0` 以及 `save_catalog` 覆盖测试的单元测试。
- **Database Schema**:
  - 无物理 Schema 改变，但 `catalogs.tweet_id` 从以 `_idx` 结尾变成原始推文 ID，`catalogs.image_path` 从单个路径字符串变更为可能包含逗号分隔的多路径字符串。
