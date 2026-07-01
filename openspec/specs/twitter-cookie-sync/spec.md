# twitter-cookie-sync Specification

## Purpose
TBD - created by archiving change auto-save-refreshed-cookies. Update Purpose after archive.
## Requirements
### Requirement: 自动持久化保存 X.com Cookie
当系统成功抓取 X.com (Twitter) 的社团推文或单条推文后，MUST 自动提取 Playwright 浏览器上下文的最新 Cookie 列表，并持久化写入到配置的 JSON 文件中，以实现 Cookie 会话（如 `ct0` 令牌等）的自动续期与维护。

#### Scenario: 成功抓取推文后自动覆盖保存
- **WHEN** 爬取或同步推文操作成功执行，抓取到了有效的推文数据，且配置文件或参数中配置了有效的 `cookies_file` (如 `data/twitter_cookies.json`)
- **THEN** 系统从当前的 Playwright `BrowserContext` 中获取所有的 Cookie 列表，并将其以 JSON 格式覆盖写回到 `cookies_file` 对应路径。

#### Scenario: 抓取失败或遇到登录重定向时不执行回写
- **WHEN** 爬取或同步推文操作失败，或者遇到被重定向至登录页、网络中断、被封禁等非成功抓取状态
- **THEN** 系统 SHALL 停止回写操作，保持原 `cookies_file` 的内容完整，防止用失效或空的会话覆盖掉原有的有效 Cookie。

#### Scenario: 未指定 cookies_file 时忽略回写
- **WHEN** 配置文件或环境变量中未指定 `cookies_file` (仅指定了 `cookie_string` 字符串，或者未提供任何凭证)
- **THEN** 系统 SHALL 仅在内存中使用 Session Context 进行抓取，在会话结束后直接退出，不做任何文件回写操作。

