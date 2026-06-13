## Why

目前需要方便地获取 Comic Market (CM) 创作者/社团的摊位分布、同人制品以及价格等信息，用于个人收藏、购买规划或市场调研。这些信息目前分布在 WebCatalog (circle.ms) 以及 X (Twitter) 等平台上，且制品信息大多以图片（品书）形式发布，难以直接检索和分析。因此，本变更旨在建立一个本地工具，自动抓取社团展位、获取 X 上的品书、并通过多模态 LLM 识别提取同人制品的结构化数据，存储在 SQLite 中以供检索与更新。

## What Changes

- 提供抓取 WebCatalog 展位和社团信息的 Python 脚本，支持写入 SQLite。
- 提供 X (Twitter) 推文及品书图片获取功能，支持按需同步。
- 提供基于多模态 LLM（使用 OpenAI Agents SDK 兼容 API/Gemini 等）的图片识别模块，可从品书图片中结构化提取同人制品的名称、类型、价格和套装信息。
- 提供命令行工具（CLI），支持对展位、品书和制品信息的按需同步与增量更新。

## Capabilities

### New Capabilities

- `circle-sync`: 同步 WebCatalog 上的社团基本信息和展位分布到本地数据库。
- `catalog-sync`: 获取社团发布的 X 推文和品书图片，并下载到本地存储。
- `goods-extractor`: 使用多模态 LLM 解析品书图片中的制品，将其结构化并保存至数据库。

### Modified Capabilities

<!-- 无现有 Capability 修改 -->

## Impact

- **数据存储**：新建本地 SQLite 数据库文件保存社团、推文和同人制品信息。
- **第三方依赖**：引入 Playwright 用于推文抓取，引入 openai SDK/Gemini SDK 用于 LLM 多模态调用。
- **新增模块**：新增 `src/` 下的数据抓取、LLM 识别、数据库交互和 CLI 入口模块。
