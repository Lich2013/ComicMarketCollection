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
系统 MUST 支持在 `config.yaml` 中配置 `image_recognition` 段落，定义 `provider` 为 `openai` 或 `cmd`，并支持配置命令行模板 `command_template`、超时时间 `timeout` 限制，以及是否开启可选的文本 API 格式化规整 fallback 选项。此外，在 `image_recognition.cmd` 下，系统 MUST 支持可选的预压缩配置段落，包含 `compress`（是否启用压缩）、`max_size`（限制最大像素边长）及 `quality`（JPEG 压缩质量）。

#### Scenario: 成功加载命令行图像识别配置
- **WHEN** 配置文件中将 `image_recognition.provider` 设置为 `"cmd"`，且提供了 `command_template`
- **THEN** 系统成功解析并加载该配置，在提取图像时能够将 `{image_path}`、`{abs_image_path}`、`{circle_name}` 和 `{circle_author}` 替换为当前待处理品书的信息

#### Scenario: 成功加载预压缩配置选项
- **WHEN** 配置文件中配置了 `image_recognition.cmd.compress` 为 `true` 并指定了 `max_size` 与 `quality` 属性
- **THEN** 系统加载这三个配置值，若部分配置值缺失，系统能够使用对应的默认值（如 `compress=false`，`max_size=1500`，`quality=85`）补充

### Requirement: 命令行识别图片预压缩与临时文件清理
当配置启用预压缩（`compress` 为 `true`）且图像识别引擎为 `cmd` 时，系统 MUST 在调用外部命令行工具前对品书图片进行降维和质量降级处理。系统 MUST 自动生成一个 JPEG 临时文件，并在命令行执行完毕后（无论成功或失败）自动删除该临时文件，确保不会遗留垃圾文件。

#### Scenario: 成功执行图片预压缩并清理临时文件
- **WHEN** 图片识别引擎为 `"cmd"` 且 `compress` 配置为 `true`，系统触发提取制品逻辑时
- **THEN** 系统根据 `max_size` 与 `quality` 对原始图片进行等比缩放和质量压缩，生成临时 JPEG 图片，将其绝对路径替换入命令行模板参数并执行，执行完毕后在 `finally` 块中自动删除该临时图片

#### Scenario: 压缩图片不具有明显体积优势时自动回退使用原图
- **WHEN** 触发预压缩后，生成的临时 JPEG 文件大小大于或等于原始图片大小的 90%
- **THEN** 系统自动删除临时图片文件，并回退为使用原始图片路径进行命令行参数替换与识别，确保不越压越大

