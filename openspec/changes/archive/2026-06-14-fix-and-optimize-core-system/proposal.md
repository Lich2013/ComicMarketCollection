## Why

当前系统的核心模块（配置、数据库、Playwright 爬虫、LLM 制品提取）在经过代码评审（Code Review）后发现了若干稳定性和性能方面的不合理之处：
1. **配置智能回退覆盖 Bug**：当 `tweet_analysis.api_key` 为空时，回退策略会覆盖用户在 `tweet_analysis` 里单独定制的 `base_url` 和 `model`。
2. **SQLite 兼容性隐患**：数据库操作 `save_catalog` 强依赖于 SQLite 3.35.0+ 版本的 `RETURNING` 语法。在低于此版本的 SQLite 环境中会直接语法报错，且 Catch 块中的降级逻辑由于没有重新执行 Insert 操作而导致数据丢失。
3. **Twitter Scraper 性能与泄露风险**：
   - Playwright 浏览器实例/上下文初始化在 try 块外部，一旦创建 page/context 失败会发生浏览器进程泄露。
   - 抓取主页时固定无条件滚动 10 次（每次等待 2.5s，共 25s），对高频推主无法在已经加载到历史日期阈值以下时提前退出，极度耗时。
   - 推文抓取的时间限制（2026-06-01）硬编码在代码中，不便于未来展会的复用与扩展。
4. **LLM 提取兼容性不足**：多模态制品提取使用 `client.beta.chat.completions.parse` 强类型约束，导致使用非 OpenAI 官方的第三方 API 中转端（如 DeepSeek 等）时发生报错崩溃。

本次变更旨在修复以上所有不合理的设计，提升系统的稳定性、兼容性与采集性能。

## What Changes

- **配置模块优化**：
  - 修改 `src/config.py` 中的 `load_config` 回退逻辑，改为按字段独立回退（`api_key`, `base_url`, `model`），避免覆盖已有的局部自定义配置。
- **数据库兼容性修复**：
  - 优化 `src/db.py` 中的 `save_catalog`，捕获不支持 `RETURNING` 子句的语法错误。当发生错误时，使用不带 `RETURNING id` 的标准语句进行插入和更新，并使用 `SELECT` 查询重新获取生成的自增 ID。
- **X 抓取性能提升与防泄露**：
  - 重构 `src/twitter_sync.py` 中的 Playwright 初始化，将所有可能抛出异常的初始化阶段放入 `try...finally` 块，确保 `browser.close()` 绝对会被执行，防范 Chromium 僵尸进程泄露。
  - 将时间阈值（原本硬编码的 `2026-06-01`）配置化。在 `config.yaml` 中新增可选参数 `twitter.since_date`，并在 `src/config.py` 与 `src/twitter_sync.py` 中支持读取该配置（若未配置则根据规则动态计算或 fallback）。
  - 优化滚动逻辑，在每次滚动后通过当前 API 返回的推文时间判定，若已越过时间阈值则提早 break 退出滚动，避免不必要的等待。
- **LLM 提取鲁棒性**：
  - 在 `src/goods_extractor.py` 的多模态解析中增加兼容性 fallback。如果 `client.beta.chat.completions.parse` 调用失败，则降级为使用常规的 JSON 模式 `response_format={"type": "json_object"}`，并利用 Pydantic 模型的 `model_validate_json` 方式进行反序列化，以完美支持第三方 OpenAI 兼容端。

## Capabilities

### New Capabilities
无

### Modified Capabilities
- `catalog-sync`: 将硬编码的推文时间校验阈值修改为支持配置化（从配置文件的 `twitter.since_date` 动态读取），并支持抓取过程中若推文时间已超出阈值则自动中止滚动，提升采集速度。

## Impact

- 影响文件：
  - `config.yaml.example` / `config.yaml`（新增配置项 `since_date`）
  - `src/config.py`（优化回退机制，解析 `since_date`）
  - `src/db.py`（优化 SQLite RETURNING 降级处理）
  - `src/twitter_sync.py`（修复 Playwright 进程泄漏，优化滚动早期退出，时间阈值配置化）
  - `src/goods_extractor.py`（增加 OpenAI 兼容端 structured output Fallback）
- 不会对数据库表结构造成任何 Breaking Change。
