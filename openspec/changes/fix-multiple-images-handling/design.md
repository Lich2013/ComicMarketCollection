## Context

在抓取推文并提取同人制品信息的过程中，如果推文含有多张图片，现行系统会采用 `f"{tweet_id}_{idx}"` 的命名方式在 `catalogs` 数据库表中存储为多条记录。这带来两方面问题：
1. **SQLite 数据库连接泄露与锁死**：Python 的 `sqlite3.Connection` 在 `with` 语句中只会控制事务（事务提交/回滚），但**不会关闭连接**。在多图循环中高频重复打开连接而未关闭，会导致 `database is locked` 错误而中断抓取流程，致使本地虽下载了图片却无法录入数据库。
2. **多图上下文丢失与解析成本**：每张图片被独立保存并作为独立的 pending 商品提取任务由 LLM 独立处理。由于视觉 LLM 每次只能看到单张图片，无法进行跨图片信息整合（如封面图与制品明细图的配合），且每次独立调用都产生一次 API 费用。

## Goals / Non-Goals

**Goals:**
- 修复 `src/db.py` 中的数据库连接泄露，确保每次 CRUD 操作后都显式释放 SQLite 连接，彻底消除锁库异常。
- 改造 `src/twitter_sync.py`，对于多图推文，将所有本地图片相对路径用逗号（`,`）拼接后存储在单条 `catalogs` 记录的 `image_path` 字段中，不再使用 `_{idx}` 拆分 `tweet_id`。
- 改造 `src/goods_extractor.py` 中的 OpenAI 视觉提取模块，使其在遇到逗号分隔的多图路径时，将多张图片同时编码并在一请求中一次性发给 LLM。
- 改造 `src/goods_extractor.py` 中的命令行（`cmd`）提取模块，支持解析逗号分隔的绝对路径，并在参数列表参数（`args`）中若检测到独立的 `"{image_path}"` / `"{abs_image_path}"` 占位符则展开为多个平铺参数传入。
- 修复所有受此修改影响的测试用例（如 `tests/test_db.py` 中手工构造的带后缀的 `tweet_id` 测试）。

**Non-Goals:**
- 不修改数据库的物理 Schema，不增加新的数据表或表字段。
- 不引入重度的 ORM 框架（如 SQLAlchemy）。
- 不改变现有的 CSV 导出或题材分析逻辑。

## Decisions

### 决策一：多图路径存储格式
选择以 **逗号连接的相对路径字符串** 形式存入现有的 `image_path` 文本列，而不是引入关联表或 JSON 序列化。
* **原因**：本地图片路径的命名规范为 `data/images/{circle_id}/{filename}`，文件名由 Twitter 生成，不包含逗号字符，因而逗号分割绝对安全；这样无需进行任何数据库迁移，完全向后兼容。
* **备选方案**：
  - 方案 A（新建表 `catalog_images`）：结构更干净，但需要做数据库 Schema 变更，开发和迁移成本高。
  - 方案 B（JSON 数组）：如 `["path1", "path2"]`。相比逗号分割，存取时需要 `json.loads/dumps` 开销，且在 CSV 导出或调试查看时不够直观。

### 决策二：SQLite 连接管理生命周期
所有数据库 CRUD 函数显式包装在 `try...finally: conn.close()` 中。
* **原因**：这是最直观且保证 100% 释放连接的方案，从根本上解决 `database is locked` 报错。
* **实现模式**：
  ```python
  conn = get_db_connection(db_path)
  try:
      with conn:
          cursor = conn.cursor()
          # 数据库写入/读取逻辑
  finally:
      conn.close()
  ```

### 决策三：大模型视觉识别多图输入与聚合模式
在 Python 中对逗号分隔的图片列表进行 `split(",")` 切分。在 `extract_goods_from_catalog` 中引入串行循环，针对每张图片独立发起一次 OpenAI 多模态请求（或命令行调用）。
* **原因**：如果一次性把多张图片发给大模型，会产生注意力稀释（LLM attention dilution），严重降低小尺寸商品字体和价格的识别率。通过逐图串行调用，确保 LLM 每次只看一张图，注意力最集中。最后在 Python 层面将所有识别出的 `items` 列表进行汇总并归一化，既保证了识别准确率，又完成了单条推文下的数据聚合。

### 决策四：命令行 (cmd) 工具的多图兼容
由于在 Python 层面已经实现了多图列表的逐个串行循环，命令行识别器（`cmd` provider）在 `extract_goods_via_cmd` 阶段将**维持原有单图解析入参逻辑不变**。每次外部命令行被调用时，传入的 `{image_path}` 或 `{abs_image_path}` 占位符仍是唯一的单张图片路径，调用执行多次，由主分发器进行结果合并。这降低了 CLI 命令端的参数复杂度。

## Risks / Trade-offs

- **[Risk] 文件名中意外包含逗号阻碍切分** → **[Mitigation]** 编写严格的下载和保存文件名过滤，在 `download_image` 中确保生成的文件名不含逗号。
- **[Risk] 旧数据兼容性问题** → **[Mitigation]** 现有的老数据（以前留存的 `_0`、`_1` 条目）在 split 时也会当作单图片记录正常工作，不需要做历史数据清理。
- **[Risk] 视觉 LLM 输入图片数量过多引发 Rate Limit / Token 超限** → **[Mitigation]** OpenAI 限制单次请求的多模态图片数量（如 10 张以下，且 Twitter 单推最高限制 4 张图，因而绝不会超限）。我们在 `encode_image_to_jpeg_base64` 中有图片压缩和分辨率自适应下采样控制，这极大节省了 Token 流量和降低了耗时。
