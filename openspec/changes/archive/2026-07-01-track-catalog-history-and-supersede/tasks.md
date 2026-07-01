## 1. 数据库查询与导出优化

- [x] 1.1 重构 `src/db.py` 中的 `export_goods_to_csv` 函数，修改联表查询 SQL，引入 `ROW_NUMBER() OVER (PARTITION BY g.circle_id, g.name ORDER BY CAST(cat.tweet_id AS INTEGER) DESC)` 对同社团同名商品进行分组去重排序，仅保留最新推文对应的商品数据。

## 2. 单元测试与验证

- [x] 2.1 在 `tests/test_db.py` 中新增单元测试 `test_export_goods_to_csv_with_multiple_catalogs`，写入属于同一个社团的两个不同推文的品书，包含同名不同价商品和各自独有商品，验证导出 CSV 文件时被正确合并去重且获取了最新商品信息。
- [x] 2.2 运行全量单元测试（`PYTHONPATH=. uv run pytest`），确保所有单元测试全部通过且没有破坏回归。
