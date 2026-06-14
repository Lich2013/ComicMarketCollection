## Why

当前系统中的品书图像识别（goods-extractor）硬编码为仅支持 OpenAI 的多模态 API。这导致用户在处理大量品书图片时，必须支付高昂的 API 调用费用，且无法利用本地已有的视觉模型。通过引入可配置的命令行（CLI）图像识别后端（例如本地的 `agy` 或 `codex`），可以使用户自由配置本地或第三方工具进行图片识别，极大地降低开销，并增强了离线和本地化部署的隐私性与灵活性。

## What Changes

- **多后端图像识别机制**：在配置文件中增加 `image_recognition` 选项，允许用户选择 `provider: "openai"`（API模式）或 `provider: "cmd"`（命令行模式）。
- **命令行模板化调用**：支持配置 `command_template` 与 `timeout`，允许通过 `{image_path}`、`{abs_image_path}`、`{circle_name}` 和 `{circle_author}` 等占位符动态构造并执行外部图像识别命令。
- **强容错与数据归一化后处理**：
  - **模糊键名映射**：允许外部 CLI 输出的 JSON 键名不完全匹配（如将 `title` 映射为 `name`，`cost` 映射为 `price`）。
  - **数据类型纠错与清洗**：统一强转价格为整型，布尔值为布尔类型。
  - **Markdown 正则提取**：若命令行工具仅输出 Bullet 点（如 `- 商品 1000円`），系统可使用正则匹配提取结构化数据。
  - **廉价文本 API 规整 fallback**：可选支持将命令行工具输出的非标准/杂乱文本通过廉价的纯文本 API 进行结构化整理。

## Capabilities

### New Capabilities
- 无

### Modified Capabilities
- `goods-extractor`: 扩展制品提取与分类能力，支持除了 OpenAI 多模态 API 之外的本地自定义命令行提取引擎，并引入强容错的数据格式清洗与规整处理。

## Impact

- **配置文件与加载**：修改 `config.yaml` 和 `src/config.py`，新增并适配 `image_recognition` 部分。
- **核心逻辑提取器**：修改 `src/goods_extractor.py`，重构 `extract_goods_from_catalog`，将其拆分为子函数 `extract_goods_via_openai`、`extract_goods_via_cmd` 以及通用的模糊归一化逻辑。
- **测试覆盖**：在测试用例中增加对新配置项加载、模糊键值映射清洗、以及命令行模拟调用的测试验证。
