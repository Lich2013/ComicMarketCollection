## 1. 数据库多条件筛选功能实现

- [x] 1.1 在 `src/db.py` 中编写 `get_filtered_circle_ids` 函数，利用动态 SQL 及参数化查询实现按日期、展馆、社团 ID 列表、社团/作者名模糊匹配返回 ID 集合。
- [x] 1.2 在 `src/db.py` 中重构或调整 `get_pending_catalogs` 函数，使其支持通过可选的 `circle_ids` 集合进行过滤查询。

## 2. 命令行与抓取/提取端适配

- [x] 2.1 修改 `main.py` 的 argparse，增加 `--circle-ids` 和 `--circle-name` 输入解析。
- [x] 2.2 在 `main.py` 调用 `sync_all_circles_twitter` 时，传递完整的筛选过滤参数。
- [x] 2.3 在 `main.py` 调用 `process_pending_catalogs` 时，传递完整的筛选过滤参数。
- [x] 2.4 在 `src/twitter_sync.py` 中更新 `sync_all_circles_twitter` 签名与过滤逻辑。
- [x] 2.5 在 `src/goods_extractor.py` 中更新 `process_pending_catalogs` 签名与过滤逻辑。

## 3. 测试与验证

- [x] 3.1 编写单元测试验证 `get_filtered_circle_ids` 的多维筛选机制和 SQL 的正确性。
- [x] 3.2 运行命令行示例，指定单一社团，验证推文同步和 LLM 提取是否仅对该社团生效。
