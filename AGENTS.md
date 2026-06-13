# Agent Developer Handbook (AGENTS.md)

本文件记录了本项目的核心设计决策、避坑指南、关键实现模式以及需要特别注意的“潜规则”。请后续接手的 AI 助手在开发和修改代码前务必仔细阅读此文档。

---

## 1. X.com (Twitter) Cookie 智能加载机制
用户提供 X.com Cookie 的方式可能有多种，为了最大程度提升用户体验，系统已实现自适应解析：
* **普通 Cookie 字符串（关键点）**：
  - 用户通常直接从浏览器中复制形如 `auth_token=xxx; ct0=yyy;` 的原始字符串。
  - 字符串中可能包含 JSON 格式的子串（例如 `g_state={"i_l":0,...}`）。在 YAML 中，这些大括号和引号容易引起解析错误。
  - **避坑要求**：在 `config.yaml` 中，Cookie 字符串必须使用块格式指示符 `|`（Block Scalar）进行多行/原始定义，或者用双引号包裹；同时，`src/twitter_sync.py` 中的 `parse_cookie_string` 需要能完美容错，剥离并解析所有的 `name=value` 键值对。
* **文件自适应读取**：
  - 如果用户将 Cookie 存储在文件中，程序会自动检测文件内容：如果是 `[` 开头，则当作 JSON 数组载入；否则直接当作普通字符串解析。

---

## 2. Playwright API 拦截与绕过机制 (重中之重)
X.com 对爬虫的检测与限制极其严格，必须遵循以下反爬与绕过机制：

### 2.1 Stealth 伪装
- 启动 Chromium 时，必须添加 `--disable-blink-features=AutomationControlled` 参数。
- 新建页面后，必须注入 JavaScript 屏蔽 `navigator.webdriver` 标识：
  ```python
  page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
  ```

### 2.2 敏感内容确认框（物理穿透点击）
- X.com 上许多画师的个人主页带有成人/敏感内容警告（Sensitive Profile Warning）。
- 页面会使用一个覆盖层阻挡事件分发，直接定位按钮并点击可能会抛出 `intercepted pointer events` 错误。
- **解决方案**：在定位到 `"View profile"` 或 `"プロフィールを表示する"` 后，必须使用强制点击模式 `btn.click(force=True)` 强行物理穿透，促使 X 加载 GraphQL 数据。

### 2.3 GraphQL 拦截与解析路径
- 批量抓取用户主页时，拦截 `UserTweets` 或 `UserTweetsAndReplies` 请求；单推同步时，拦截 `TweetDetail` 请求。
- **置顶推文 (`TimelinePinEntry`)**：置顶推文存储在 `TimelinePinEntry` 指令中（而非 `TimelineAddEntries`）。解析器需要同时提取两种指令的 entry。
- **自转/转发媒体提取 (`retweeted_status_result`)**：如果推文为转发或自转，外部 `legacy` 属性不包含图片列表。必须从 `retweeted_status_result` 内部的 `result` 或是 `tweet -> legacy` 中提取原始的 `extended_entities` 与 `full_text`，否则自转的品书图文将无法被捕获。
- **500 条上限安全阀**：为了在极端刷屏情况下保护系统性能与内存，API 拦截解析中内置了 `500` 条匹配上限。

---

## 3. 按需同步与过滤参数组合
为减少网络和数据库开销，所有同步命令（推文同步、LLM 解析）均支持多维度参数搭配：
- `--days`: 参展天数（如 `Day1,Day2`）。
- `--halls`: 场馆名称（如 `e7,s12`）。
- `--circle-ids`: 社团 ID。
- `--circle-name`: 社团名或作者名（模糊匹配）。
- `--tweet-url`: 单条推文链接手动导入（此时会自动提取链接中的用户名关联社团）。

---

## 4. 数据库持久化规范
- 默认数据库路径为 `data/comic_market.db`。
- 本地图片必须以 `data/images/{circle_id}/{filename}` 相对路径存放。
- 推文品书的状态流转为：`pending`（待处理） -> `processed`（解析成功）/ `failed`（解析失败）/ `ignored`（被忽略）。
- 单元测试运行在 `data/test_comic_market.db` 中，测试完成后会自动清理。不要将测试数据混入生产数据库。

---

## 5. 推文文本 LLM 预分析过滤机制
为了剔除日常非品书（但意外匹配了关键词）的噪点推文以省去多模态模型 OCR 费用，系统支持在推文入库前进行纯文本大模型过滤：
- **配置文件**：通过 `config.yaml` 中的 `tweet_analysis` 段落控制其独立凭证。
- **智能回退加载**：若用户未指定独立的 `api_key`，系统会在 `src/config.py` 加载时自动复用主 `openai` 参数，实现低成本无缝开启。
- **意图分析函数**：通过 `src/twitter_sync.py` 的 `analyze_tweet_text_with_llm` 对博文内容进行语义意图提取，要求返回标准的 JSON 数据，对三方模型可能包装的 Markdown 代码块标记（```json）具有极强的正则表达式剥离清洗鲁棒性，并在 API 遇到任何网络异常或故障时默认返回 `True` 放行，防错漏抓。
- **手动导入免过滤**：手动导入单推链接（`--tweet-url`）将自动绕过文本大模型的预分析阶段。

