## Why

在同步 X.com (Twitter) 的社团推文时，系统需要依赖有效的 X.com Cookie (包括 `auth_token`、`ct0` 等)。目前系统仅实现了从 `config.yaml` 或指定的 `cookies_file` (如 `data/twitter_cookies.json`) 中单向读取并注入到 Playwright 浏览器上下文中。

当 X.com 服务端在会话期间刷新 Cookie (尤其是 `ct0` CSRF 令牌) 时，系统由于缺乏回写机制，无法将最新的 Cookie 保留到本地。这导致本地的 Cookie 会在较短时间内失效，增加用户需要频繁手动从浏览器复制、更新 Cookie 的负担。通过自动在本地保存刷新后的 Cookie，可以显著延长会话有效期，保障自动同步的稳定性。

## What Changes

- **自动抓取与持久化**：在 `scrape_twitter_profile` 及 `sync_single_tweet` 中，在成功完成页面请求且确认数据抓取成功后，从 Playwright 的 `BrowserContext` 中获取最新的 Cookie 列表，并自动将其写回所配置的 `cookies_file`。
- **安全保障与防污染**：如果抓取失败（如遇到明显的登录拦截重定向或无推文返回等异常情况），系统不应执行回写，以防止用失效或空的会话覆盖掉原有的有效 Cookie。
- **仅限文件模式回写**：只针对指定了 `cookies_file` 的情况进行自动 JSON 回写。对于直接在 `config.yaml` 中配置 `cookie_string` 的情况不做自动写回，以避免破坏 YAML 结构和注释。

## Capabilities

### New Capabilities
- `twitter-cookie-sync`: 实现自动提取并保存 X.com 刷新后的 Cookie，确保后续同步任务可以无缝复用最新的会话凭证。

### Modified Capabilities
无

## Impact

- **核心逻辑**: 修改 `src/twitter_sync.py` 中的 `scrape_twitter_profile` 和 `sync_single_tweet` 函数，在浏览器会话关闭前抓取并更新本地 Cookie JSON 文件。
- **配置文件**: `data/twitter_cookies.json` 将会被自动更新和覆盖。
