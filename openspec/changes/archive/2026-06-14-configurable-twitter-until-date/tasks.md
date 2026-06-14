## 1. 配置项更新

- [x] 1.1 在 config.yaml 和 config.yaml.example 中新增 twitter.until_date 可选配置，默认值为 "2026-06-05"
- [x] 1.2 在 src/config.py 中的默认配置字典里增加 until_date，支持从配置文件和环境变量读取

## 2. 爬虫与过滤逻辑实现

- [x] 2.1 修改 src/twitter_sync.py 中的 scrape_twitter_profile 函数，引入 until_date 参数，并解析为 timezone-aware 的 datetime 对象 until_threshold
- [x] 2.2 在 API 拦截过滤逻辑中，对推文发布日期进行上限校验，过滤掉超限推文
- [x] 2.3 在 DOM 备份解析过滤逻辑中，进行相同的截止时间上限校验
- [x] 2.4 在 sync_circle_twitter 函数中读取配置中的 until_date 并传递给 scrape_twitter_profile

## 3. 验证与测试

- [x] 3.1 在 tests/ 中添加/修改单元测试，验证 until_date 对推文的过滤逻辑是否按预期工作
- [x] 3.2 运行现有的单元测试（PYTHONPATH=. uv run pytest）确保无回归问题，且测试完全通过
