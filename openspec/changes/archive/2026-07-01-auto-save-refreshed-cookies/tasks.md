## 1. 基础工具与验证逻辑

- [x] 1.1 在 `src/twitter_sync.py` 中实现原子写入 JSON 文件的辅助函数 `save_cookies_to_file(cookies: list[dict], filepath: str)`，利用临时文件写入并重命名的机制保障数据安全性。
- [x] 1.2 实现 `validate_cookies(cookies: list[dict]) -> bool` 辅助验证函数，检查返回的 Cookie 列表中是否包含 `auth_token` 等核心登录态字段，防止污染性覆写。

## 2. 抓取逻辑改造

- [x] 2.1 修改 `src/twitter_sync.py` 中的 `scrape_twitter_profile` 函数，在抓取完毕且确定数据获取成功后，提取 `context.cookies()` 并调用保存函数。
- [x] 2.2 修改 `src/twitter_sync.py` 中的 `sync_single_tweet` 函数，在成功获取单条推特数据后，提取 `context.cookies()` 并同步回写。
- [x] 2.3 确保对于直接使用 `cookie_string` (非文件模式) 的情况以及发生错误（如重定向、报错）的情况，能正确跳过回写逻辑。

## 3. 测试与验证

- [x] 3.1 编写单元测试，模拟 Playwright 返回更新后的 Cookie 列表，验证是否能成功写入临时测试文件并被再次读取。
- [x] 3.2 模拟抓取失败和重定向的测试用例，验证原 Cookie 文件内容不会被清空或损坏。
