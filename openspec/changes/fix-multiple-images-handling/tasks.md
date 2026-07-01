## 1. 数据库模块优化

- [x] 1.1 重构 `src/db.py` 中的 `save_circle`、`get_all_circles`、`get_existing_circle_ids` 等函数，在 `try...finally` 块中显式调用 `conn.close()` 释放 SQLite 连接
- [x] 1.2 重构 `src/db.py` 中的 `save_catalog`、`get_pending_catalogs`、`update_catalog_status`、`save_goods`、`export_goods_to_csv` 等函数，引入 `try...finally: conn.close()` 以彻底消除任何锁库隐患

## 2. 推文同步模块重构

- [x] 2.1 修改 `src/twitter_sync.py` 中的 `sync_circle_twitter`，对于单条推文，先下载全部图片，然后以逗号 `,` 分隔拼接相对路径存入 catalogs 的 `image_path` 字段，推文 ID 采用原始 of `tweet_id`（不带 `_idx` 后缀）
- [x] 2.2 修改 `src/twitter_sync.py` 中的 `sync_single_tweet`，将下载的所有图片相对路径以逗号分隔拼接写入 catalogs 的单行记录中，废弃原本的循环拆分机制

## 3. 制品提取模块改造

- [x] 3.1 重构 `src/goods_extractor.py` 中的 `extract_goods_from_catalog`，对于逗号分隔的 `image_path` 列表，执行串行循环，针对每张图片独立调用单图提取函数以防 LLM 注意力稀释
- [x] 3.2 在 `extract_goods_from_catalog` 循环中，调用单图提取接口，将所有成功提取出的同人制品列表在 Python 层面进行合并，若有任意一张图提取成功则标记品书为 `processed`，否则若无错误则标为 `ignored`，若有连接/调用错误则标为 `failed`

## 4. 单元测试与手动验证

- [x] 4.1 修改并修复 `tests/test_db.py` 中 `test_save_catalog_on_conflict_update` 和 `test_save_catalog_sqlite_fallback` 两个单元测试，以适配单行多图和不带 `_idx` 后缀的 `tweet_id` 设计
- [x] 4.2 运行全量单元测试（`PYTHONPATH=. uv run pytest`），确保所有单元测试全部通过且没有破坏回归
- [ ] 4.3 运行包含多图的推文同步和商品提取测试，通过日志验证在单次 LLM 接口调用中同时识别了所有品书图片并准确归一化输出
