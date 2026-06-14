## Context

在对 Comic Market Collection System 进行深入的代码评审（Code Review）后，发现了 4 个核心领域的稳定性和性能隐患：
1. **配置覆盖 (Config Override)**: `src/config.py` 中的 `tweet_analysis` 回退策略在 API Key 为空时，使用 `openai` 的值直接覆盖了整个字典块，使得分析专用的模型和基准 URL 无法进行部分自定义。
2. **SQLite RETURNING 兼容性**: `src/db.py` 中使用 `RETURNING id` 子句。若用户的系统 SQLite 库版本低于 3.35.0，会导致插入失败并报错崩溃，且异常捕获后的 fallback 查询没有做重复的插入操作，造成数据丢失。
3. **Playwright 资源泄露与滚动效率低下**:
   - `src/twitter_sync.py` 中的 `browser` 和 `context` 分配在 `try` 块外，如在建 context 或 new page 阶段抛出异常，`finally: browser.close()` 会因为引用或创建阶段错误导致无法执行，从而泄露 Chromium 僵尸进程。
   - 固定 10 次的滚动逻辑每次等待 2.5s，对于大量已抓取且有旧推文的用户，极其消耗不必要的时间。
   - 抓取的起始日期限制硬编码在代码中。
4. **LLM 提取兼容性不足**: `src/goods_extractor.py` 中对于多模态提取依赖于 OpenAI 的 `Structured Outputs` 接口。如果用户配置了兼容 OpenAI 的非官方 API 端（例如 DeepSeek、本地 LLM 中转服务等），调用会发生报错。

## Goals / Non-Goals

**Goals:**
- **精细化回退**: 确保 `tweet_analysis` 与主 `openai` 之间的参数回退精细到字段级别，支持覆盖特定的属性（如 model 或 base_url）。
- **SQLite 版本高兼容性**: 修正 `save_catalog` 中的 RETURNING 退回机制，在遇到 SQL 语法错误时能够成功降级使用标准 `INSERT/UPDATE`，并不丢失数据。
- **Playwright 零泄漏与提速**: 保证无论何时发生意外报错，均能调用 `browser.close()`；推文抓取的滚动行为必须支持“根据最旧推文时间与时间限制（`since_date`）进行比对并提前退出”；`since_date` 需在配置中支持自定义。
- **LLM 提取高兼容性**: 兼容非官方的 OpenAI 兼容网关，在 Structured Output 失败时，无缝回退到 `response_format={"type": "json_object"}` + 客户端 JSON 强类型反序列化。

**Non-Goals:**
- 不改变数据库表结构或表字段设计。
- 不增加除了 `twitter.since_date` 以外的其他复杂配置项。

## Decisions

### 1. 独立配置属性回退
- **设计**: 在 `src/config.py` 的智能回退中，分别对 `api_key`、`base_url`、`model` 执行 `if not analysis.get(field)` 校验，而不是如果 `api_key` 不存在就覆盖整个 `tweet_analysis` 配置段。
- **Rationale**: 允许用户仅在 `config.yaml` 中配置 `tweet_analysis` 的 `model` 或 `base_url`，同时继承主 `openai` 的 `api_key`。

### 2. SQLite RETURNING 兼容性降级
- **设计**:
  - `save_catalog` 中保留 `RETURNING id` 语法为首选。
  - 若执行出错且报错类型是 `sqlite3.Error`，检查错误类型并执行标准不含 `RETURNING` 的降级语句。
  - 降级插入执行完成后，使用 `SELECT id FROM catalogs WHERE tweet_id = ?` 重新取出 ID 供函数返回。
- **Rationale**: 最大限度兼顾高性能新版本与高兼容旧版本 SQLite 的跨平台表现。

### 3. Playwright 零僵尸进程模式与滚动优化
- **防泄漏设计**:
  - 在 `sync_playwright()` 内，将 `browser = None` 定义在 try 外部，`browser = p.chromium.launch(...)` 与之后的 `context` / `page` 初始化全部收入 `try...except...finally` 块中。
  - 在 `finally` 块中增加安全判断：`if browser: browser.close()`。
- **时间限制配置化**:
  - 在 `config.yaml` 的 `twitter` 分支增加可选配置 `since_date: "2026-06-01"`。
  - 在 `src/config.py` 中解析，若为空则在 `src/twitter_sync.py` 中默认 fallback 到 `"2026-06-01"`，以保证向前兼容。
- **滚动提速优化**:
  - 滚动提取主页的过程中，实时解析已捕获的 API Payload 或 DOM 内推文的发布时间。
  - 剔除置顶推文（Pinned Tweet）的影响，获取当前捕获的、非置顶推文中最旧的发布时间。
  - 若该最旧发布时间已小于时间阈值，则立刻执行 `break` 跳出滚动，实现大幅提速。

### 4. LLM 多模态 Structured Output 回退兼容
- **设计**:
  - 正常调用 `client.beta.chat.completions.parse(...)` 进行结构化识别。
  - 捕获任何异常（包括 `AttributeError` 或 API 返回的 400 格式错误），在 `except` 块中调用传统的 `client.chat.completions.create`，将 `response_format` 设为 `{"type": "json_object"}`，并增加 JSON 解析保障。
  - 最终使用 Pydantic 模型的 `CatalogExtraction.model_validate_json(raw_text)` 将其反序列化为相同的模型对象。
- **Rationale**: 保证使用非官方 OpenAI 端时的兼容性，同时保留官方端的高性能结构化返回。

## Risks / Trade-offs

- **[Risk]**: Twitter API 拦截抓取在滚动早期退出时，可能会因为网络延迟等原因导致较新的推文还没来得及加载，从而提前退出导致漏掉一部分推文。
  - **Mitigation**: 限制至少获取到了一定数量的推文或保证首屏已经完全拦截解析后，并且在检查到确实存在若干早于阈值的推文时才进行退出，避免单纯因为加载延迟导致的误判。
- **[Risk]**: 使用 JSON Mode fallback 时，有些模型可能会在生成的 JSON 格式上存在细微偏差，或者由于没用 Structured Output 导致格式不完美匹配 `CatalogExtraction` 的 Schema。
  - **Mitigation**: 充分优化 system prompt，并使用 Pydantic 的容错和字段默认值来应对细微的 JSON 解析异常。
