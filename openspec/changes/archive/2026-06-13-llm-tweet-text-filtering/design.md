## Context

当前系统中，`src/twitter_sync.py` 在通过 Playwright 抓取完推文后，直接使用关键词匹配 `is_potential_catalog(text, circle)` 对博文内容进行校验。如果匹配成功，则立即下载推文所包含的图片，并写入本地数据库 `catalogs` 表中。

这导致了以下技术限制与浪费：
1. **关键词匹配局限性**：无法识别语境。例如否定句、日常碎碎念如果带有关键词，都会引发误报，造成大量的冗余图片下载。
2. **多模态费用高昂**：多模态商品 OCR 识别（`--extract-goods`）的 API 费用相对较高。如果推文初筛包含大量非品书噪点，会产生很多不必要的图片 OCR 请求。

## Goals / Non-Goals

**Goals:**
- 实现基于文本 LLM 的预过滤，智能分析博文文本语义，判定是否是真实的品书/新刊宣发推文。
- 提供高度可自定义的 OpenAPI 兼容客户端配置，支持用户灵活切换不同的模型和 API 代理。
- 实现平滑的智能回退策略，如果用户不配置单独的 API Key，自动复用现有的主 `openai` 参数。
- 手动指定单条 URL 导入（`--tweet-url`）时，能自动跳过文本 LLM 分析，以保留用户强行同步的自主权。

**Non-Goals:**
- 不在此预过滤步骤中下载图片或对图片进行多模态分析。
- 不对已存在于数据库中的推文重新进行过滤或状态修正。
- 不改变商品提取（`--extract-goods`）这一后续步骤的多模态逻辑。

## Decisions

### 1. 配置参数与加载回退设计
在 `config.yaml` 中为 `tweet_analysis` 提供独立的 API 凭证及模型配置。如果该项开启，但用户没有独立设置 api_key 等，代码会自动从 `config["openai"]` 中读取参数，实现“零配置”开启：
```python
# 示例加载逻辑
analysis_config = config.get("tweet_analysis", {})
if analysis_config.get("enabled", False):
    api_key = analysis_config.get("api_key") or config["openai"].get("api_key")
    base_url = analysis_config.get("base_url") or config["openai"].get("base_url")
    model = analysis_config.get("model") or config["openai"].get("model")
```
*评估备选*：如果强制用户必须双重配置，会增加配置文件冗余，降低易用性。此回退设计最为顺畅。

### 2. 纯文本大模型接口与 JSON Mode 规范
通过大模型进行文本分类，我们要求返回标准的 JSON 格式，如 `{"is_catalog_announcement": true/false, "reason": "..."}`。
为了保证兼容各类大语言模型（包括某些不完全支持 OpenAI 的 `response_format` JSON 模式的第三方模型或国内大模型），我们：
- 在 System Prompt 中强力申明只返回纯 JSON，不带 markdown 的包裹。
- 在代码中对返回结果进行清洗，如果 LLM 带有了 ```json ... ``` 块包裹，则用正则或字符串分割剥离后，再进行 `json.loads` 解析。
- 在发生异常（如超时、限流、解析失败）时，默认返回 `True`，以确保“宁可错杀、绝不漏抓”的容错性，保护数据完整性。

### 3. 集成点设计 (在 `sync_circle_twitter` 环节)
过滤操作不放在 Playwright 爬虫函数 `scrape_twitter_profile` 内部（为了保持爬虫函数的单一职责和纯粹性），而是在 `sync_circle_twitter` 调用完爬虫得到候选推文列表后，对列表进行循环过滤。这样便于管理数据库事务，且不干扰 DOM 渲染逻辑。

## Risks / Trade-offs

- **[Risk] 大模型请求延迟增加** → 抓取推文时增加了每条推文 1~3 秒的 API 响应时间。
  - *Mitigation*: 只对通过了 `is_potential_catalog` 关键词初筛的推文才调用 LLM 进行深度判断，限制每次同步的 API 请求总数；同时对于无图推文直接在前置过滤跳过，不发送大模型请求。
- **[Risk] 第三方大模型偶尔抽风或超时导致过滤失效** → API 调用失败导致丢失数据。
  - *Mitigation*: 捕获所有 API 异常，在 `try-except` 块中默认回退为 `True`，即一旦报错直接认为通过，保留推文，防止数据丢失。
