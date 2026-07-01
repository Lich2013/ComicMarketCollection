## Context

当前 X.com (Twitter) 推文抓取主要是使用 Playwright 爬取页面和拦截 GraphQL 请求。X.com 对会话凭证 (Cookie) 具有极高的防爬虫策略，其 Session Cookies (如 CSRF 令牌 `ct0`) 具有频繁更新的性质。目前本地程序只能单向读取 `cookies_file` (默认 `data/twitter_cookies.json`) 并在上下文初始化时注入。没有将 Playwright 内存中最新更新的 Cookie 持久化保存至本地的逻辑，导致用户需要频繁地重新手动更新 Cookie 凭证。

## Goals / Non-Goals

**Goals:**
- 在 `scrape_twitter_profile` (用户主页抓取) 逻辑中，当确认成功拉取推文且会话未失效时，提取最新的 Browser Context Cookies 并写回 `cookies_file`。
- 在 `sync_single_tweet` (单条推文抓取) 逻辑中，完成抓取后同样实现自动写回更新。
- 确保写入操作是安全的，具备“防空值覆盖”、“防异常污染” 的保护机制。
- 采用原子写入方式 (即先写入 `.tmp` 临时文件再替换)，防止写入中断导致文件损坏。

**Non-Goals:**
- 不支持更新直接写在 `config.yaml` 里的 `cookie_string`。
- 不提供模拟账号密码自动登录的会话维持逻辑，仅在用户已提供有效初始 Cookie 的基础上实现“被动续期”。

## Decisions

### 1. 抓取与回写的触发时机
- **决定**：在 Playwright 抓取流程最后（即关闭 Browser/Context 前），若已成功抓取到有效推文或通过单推解析，则获取 `context.cookies()`。
- **Rationale**：
  - 相比在 Playwright 的事件监听 `response` 中实时写入，最后统一处理能够极大减少 IO 开销。
  - 仅在主业务逻辑（抓取推文）未抛出异常且成功返回数据的情况下才触发回写，能有效避免因登录拦截、网络波动导致空 Cookie 覆盖旧的有效 Cookie 的问题。

### 2. Cookie 写入方式与格式
- **决定**：抓取到的最新 Cookie 列表直接用 `json.dump` 覆盖写入所配置的 `cookies_file`。
- **Rationale**：
  - 现有的 `twitter_sync.py` 已经在加载 `cookies_file` 时提供了自适应解析逻辑：首字符为 `[` 时将其解析为 JSON 列表，否则按 name=value 形式拆分。
  - `json.dump` 保存后的标准 Playwright Cookie 列表可以被下一次加载流程无缝读取。
  - **原子写入机制**：使用 `open(temp_path)` 写入数据，再利用 `os.replace(temp_path, target_path)` 替换，防止写入过程中进程崩溃导致文件损坏。

## Risks / Trade-offs

- **[Risk]**：写入空 Cookie 或失效会话污染原有配置。
  - **Mitigation**：在执行回写前，增加对抓取结果及 Cookie 数据的双重校验：
    1. 校验本次抓取中是否出现了重定向至登录页（或捕获到 `Not Logged In` 等状态）。
    2. 校验抓取到的 Cookie 列表里是否包含必要的会话凭证（如 `auth_token` 字段）。只有两者均通过时才写入。
- **[Risk]**：并发执行同步时产生写入冲突。
  - **Mitigation**：目前系统主要为串行社团推特抓取。如果后续引入并发模式，可以采用轻量级文件锁 (如 `fcntl` 或 `portalocker`)，或是在更高层统一管理 Cookie 状态。当前版本下，增加原子写入替换足以保证大部分单进程场景的安全性。
