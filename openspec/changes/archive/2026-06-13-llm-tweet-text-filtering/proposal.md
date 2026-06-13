## Why

目前系统中对 X (Twitter) 推文的过滤仅依赖基于关键词和展位号的静态匹配（`is_potential_catalog`）。这导致许多非品书的日常推文（例如提及“本次没有品书，抱歉”或包含其他关键字的普通插画）被误判为潜在品书并下载，产生了大量数据库噪点与图片文件冗余。

此外，未经过滤的图片直接送入后续的多模态大模型进行商品提取（`--extract-goods`），不仅增加了处理时间，也产生了许多无效的、昂贵的多模态 API 费用。通过引入轻量级的文本 LLM 预过滤层，可以用极低的成本和带宽阻断不相关的日常推文，使数据库与多模态识别更加精准和高效。

## What Changes

- **新增配置选项**：在 `config.yaml` 中新增 `tweet_analysis` 配置项，允许用户独立开启或关闭文本分析过滤，独立指定 OpenAI 兼容格式（OpenAPI 格式）的 API Key、API Base URL 和 Model Name（例如对接 DeepSeek、Qwen 或本地 Ollama），并且在缺省时自动回退复用主 OpenAI 配置。
- **引入 LLM 文本过滤逻辑**：在推文图片下载与数据库保存之前，针对通过关键词初筛的推文文本，调用指定的 LLM 进行意图分析，判定其是否为真正的品书或新刊宣发推文。
- **剔除噪点推文**：如果 LLM 分析判定非品书推文，则直接跳过其图片下载与落库，防止噪点进入数据库。
- **兼容手动指定单推导入**：对于用户使用 `--tweet-url` 明确指定导入的单条推文链接，默认跳过此项 LLM 文本过滤，直接进行抓取并导入。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `catalog-sync`: 在原本的推文获取与校验流程中，增加可选的文本 LLM 意图识别过滤步骤。只有通过关键词初筛且通过 LLM 文本分析的推文，系统才会被允许下载图片和在 `catalogs` 表中记录。

## Impact

- `src/twitter_sync.py`: 增加调用文本 LLM 分析过滤的函数及集成逻辑。
- `config.yaml` / `src/config.py`: 增加 `tweet_analysis` 的定义、解析与智能回退配置逻辑。
- `main.py`: 保持原有的命令行调用逻辑，单条链接导入 (`--tweet-url`) 依然正常绕过预过滤直接落库。
