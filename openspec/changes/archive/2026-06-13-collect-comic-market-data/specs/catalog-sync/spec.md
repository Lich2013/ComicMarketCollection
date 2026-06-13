## ADDED Requirements

### Requirement: 获取社团 X (Twitter) 推文及品书图片
系统 MUST 能够根据社团的 Twitter 用户名获取其最近发布的推文，并提取推文中的图片资源保存至本地。

#### Scenario: 成功抓取指定社团的品书推文图片
- **WHEN** 指定一个或多个社团，系统使用 Playwright 模拟浏览器（带有配置好的 X.com Cookie）加载该作者主页并提取推文图片
- **THEN** 系统下载图片到本地指定目录，并在数据库的 `catalogs` 表中记录推文 ID、内容、本地图片路径，初始状态设为 `pending`

#### Scenario: 增量抓取避免重复推文
- **WHEN** 抓取到的推文 ID 在 `catalogs` 表中已经存在
- **THEN** 系统必须跳过该推文的下载与数据库写入，避免重复处理

### Requirement: 推文内容与图片关联管理
系统 MUST 将下载的品书图片与社团 ID、推文 ID 建立明确的外键关联，以方便后续制品提取与查询。

#### Scenario: 品书图片下载并与社团关联成功
- **WHEN** 推文图片成功下载到本地
- **THEN** 系统在 `catalogs` 表中写入对应的 `circle_id`、`tweet_id` 和本地文件路径 `image_path`
