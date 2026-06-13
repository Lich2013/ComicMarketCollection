## 1. 配置模块优化 (config.py)

- [x] 1.1 在 config.yaml.example 和 config.yaml 中新增可选参数 twitter.since_date，用于配置推文同步的起始时间。
- [x] 1.2 重构 src/config.py 的智能回退逻辑，使其在 tweet_analysis.api_key 为空时仅针对 api_key/base_url/model 等字段分别做 fallback，而不覆盖已配置的其他字段。
- [x] 1.3 在 src/config.py 中解析 twitter.since_date。

## 2. 数据库兼容性修复 (db.py)

- [x] 2.1 修改 src/db.py 的 save_catalog 函数，在 SQLite 不支持 RETURNING id 语法并抛出 sqlite3.Error 时进行降级处理。
- [x] 2.2 在降级处理中，执行不带 RETURNING 的标准 INSERT 语句，再通过 SELECT id 从 catalogs 表中根据 tweet_id 查询并返回对应的记录 ID。

## 3. Playwright 进程安全与防泄露 (twitter_sync.py)

- [x] 3.1 重构 src/twitter_sync.py 中的 scrape_twitter_profile，将浏览器和上下文的创建及初始化逻辑包裹进 try...finally，确保 browser 必定被关闭。
- [x] 3.2 对 src/twitter_sync.py 中的 scrape_single_tweet 执行相同的 try...finally 防泄漏重构。

## 4. 推文同步时间阈值配置化与滚动优化 (twitter_sync.py)

- [x] 4.1 在 src/twitter_sync.py 中读取配置好的 since_date，作为推文过滤的时间阈值（默认 fallback 到 "2026-06-01"）。
- [x] 4.2 优化 scrape_twitter_profile 的滚动机制：在滚动间隔中提取当前已拦截到的非置顶推文最旧发布时间，若已经早于 since_date，则立刻 break 退出滚动以节省时间。

## 5. LLM 多模态提取 fallback 兼容性 (goods_extractor.py)

- [x] 5.1 修改 src/goods_extractor.py 中的 extract_goods_from_catalog，在 Pydantic structured output 识别报错时进行 try...except 拦截。
- [x] 5.2 拦截异常后降级使用标准的 JSON Mode 发送请求，并利用 Pydantic 模型的 model_validate_json 对 JSON 字符串进行序列化反序列化。

## 6. 测试与验证

- [x] 6.1 在 tests/test_db.py 中编写单元测试验证低版本 SQLite 的 save_catalog 降级行为（可直接测试不带 RETURNING 的语句执行和返回）。
- [x] 6.3 编写单元测试验证 tweet_analysis 各字段的精细化 fallback。
- [x] 6.4 运行整个 pytest 测试套件验证修改后没有任何 regression，并进行单条推文/滚动拉取的功能验证。
