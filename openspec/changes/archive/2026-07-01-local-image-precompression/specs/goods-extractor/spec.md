## ADDED Requirements

### Requirement: 命令行识别图片预压缩与临时文件清理
当配置启用预压缩（`compress` 为 `true`）且图像识别引擎为 `cmd` 时，系统 MUST 在调用外部命令行工具前对品书图片进行降维和质量降级处理。系统 MUST 自动生成一个 JPEG 临时文件，并在命令行执行完毕后（无论成功或失败）自动删除该临时文件，确保不会遗留垃圾文件。

#### Scenario: 成功执行图片预压缩并清理临时文件
- **WHEN** 图片识别引擎为 `"cmd"` 且 `compress` 配置为 `true`，系统触发提取制品逻辑时
- **THEN** 系统根据 `max_size` 与 `quality` 对原始图片进行等比缩放和质量压缩，生成临时 JPEG 图片，将其绝对路径替换入命令行模板参数并执行，执行完毕后在 `finally` 块中自动删除该临时图片

#### Scenario: 压缩图片不具有明显体积优势时自动回退使用原图
- **WHEN** 触发预压缩后，生成的临时 JPEG 文件大小大于或等于原始图片大小的 90%
- **THEN** 系统自动删除临时图片文件，并回退为使用原始图片路径进行命令行参数替换与识别，确保不越压越大


## MODIFIED Requirements

### Requirement: 可插拔图像识别引擎配置加载
系统 MUST 支持在 `config.yaml` 中配置 `image_recognition` 段落，定义 `provider` 为 `openai` 或 `cmd`，并支持配置命令行模板 `command_template`、超时时间 `timeout` 限制，以及是否开启可选的文本 API 格式化规整 fallback 选项。此外，在 `image_recognition.cmd` 下，系统 MUST 支持可选的预压缩配置段落，包含 `compress`（是否启用压缩）、`max_size`（限制最大像素边长）及 `quality`（JPEG 压缩质量）。

#### Scenario: 成功加载命令行图像识别配置
- **WHEN** 配置文件中将 `image_recognition.provider` 设置为 `"cmd"`，且提供了 `command_template`
- **THEN** 系统成功解析并加载该配置，在提取图像时能够将 `{image_path}`、`{abs_image_path}`、`{circle_name}` 和 `{circle_author}` 替换为当前待处理品书的信息

#### Scenario: 成功加载预压缩配置选项
- **WHEN** 配置文件中配置了 `image_recognition.cmd.compress` 为 `true` 并指定了 `max_size` 与 `quality` 属性
- **THEN** 系统加载这三个配置值，若部分配置值缺失，系统能够使用对应的默认值（如 `compress=false`，`max_size=1500`，`quality=85`）补充
