# goods-extractor Specification

## Purpose
TBD - created by archiving change collect-comic-market-data. Update Purpose after archive.
## Requirements
### Requirement: LLM 多模态品书提取与分类
系统 MUST 支持根据配置动态选择图像识别后端（OpenAI API 或自定义命令行工具），对待处理（pending）状态的品书图片进行识别。系统 MUST 对提取出的数据进行强容错清洗与模糊映射归一化处理（包括名称、类型、价格与是否为套装），并将规整后的同人制品信息存入数据库。当选择 OpenAI 图像识别后端或启用文本规整兜底时，若 Langfuse 链路追踪已激活，系统 MUST 对对应的 LLM 调用进行追踪和上报。

#### Scenario: 成功解析品书并入库
- **WHEN** 对处于 `pending` 状态的品书图片调用已配置的图像识别后端（API或命令行）进行解析，且后端返回提取出的制品文本或 JSON
- **THEN** 系统将提取结果进行键名映射与数据类型纠错，成功获取合法的制品列表后，在 `goods` 表中为该社团插入提取出的商品信息，并将对应的品书记录 `status` 更新为 `processed`

#### Scenario: 忽略非品书图片
- **WHEN** 图像识别后端判定该图片不属于品书或不包含任何同人制品及价格信息，或数据清洗后未得到任何合法商品项
- **THEN** 系统不插入任何商品数据，并将对应的品书记录 `status` 更新为 `ignored`

### Requirement: 按需更新命令行工具
系统 MUST 提供统一的命令行工具（CLI），允许用户通过不同参数分别执行同步社团、抓取品书图片和提取制品数据等操作。同时，同步推文与提取制品指令 MUST 支持根据用户提供的条件（社团 ID、名称、参展日期及展馆）仅对指定的社团数据进行按需处理。

#### Scenario: 执行同步社团指令
- **WHEN** 用户运行命令并指定同步社团参数（如 `--sync-circles`）
- **THEN** 系统开始拉取并同步 WebCatalog 社团信息

#### Scenario: 执行提取制品指令
- **WHEN** 用户运行命令并指定提取制品参数（如 `--extract-goods`）
- **THEN** 系统扫描数据库中所有 `pending` 状态的品书并调用 LLM 进行解析

### Requirement: 可插拔图像识别引擎配置加载
系统 MUST 支持在 `config.yaml` 中配置 `image_recognition` 段落，定义 `provider` 为 `openai` 或 `cmd`，并支持配置命令行模板 `command_template`、超时时间 `timeout` 限制，以及是否开启可选的文本 API 格式化规整 fallback 选项。

#### Scenario: 成功加载命令行图像识别配置
- **WHEN** 配置文件中将 `image_recognition.provider` 设置为 `"cmd"`，且提供了 `command_template`
- **THEN** 系统成功解析并加载该配置，在提取图像时能够将 `{image_path}`、`{abs_image_path}`、`{circle_name}` 和 `{circle_author}` 替换为当前待处理品书的信息

