## ADDED Requirements

### Requirement: 同步社团基本信息与展位分布
系统 MUST 支持从 WebCatalog (circle.ms) 拉取参展社团的基本信息（如 ID、名称、作者、类别、展馆、天数、区域、摊位号、Twitter / Pixiv URL、Circle Cut URL 等）并存储到本地数据库中。

#### Scenario: 成功拉取并保存社团信息
- **WHEN** 执行社团同步命令并且提供有效的 WebCatalog 会话 Cookie 与 Day/Hall 列表
- **THEN** 系统下载社团数据，解析展位和主页链接，并将其保存/更新至本地 SQLite 数据库中

#### Scenario: 增量更新已存在的社团
- **WHEN** 拉取到的社团 ID 在数据库中已存在且信息有更新
- **THEN** 系统更新该社团在数据库中的字段，同时保留最新更新时间，避免重复插入

### Requirement: 保存会话凭证与配置
系统 MUST 允许通过配置文件或环境变量提供 `webcatalog-free.circle.ms` 的身份验证 Headers (如 Cookie 等) 以通过接口验证。

#### Scenario: 缺少身份验证凭证时报错
- **WHEN** 配置文件或环境变量中没有提供有效的 Cookie / Headers 并执行同步
- **THEN** 系统应当给出明确的错误提示并退出
