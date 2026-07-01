## MODIFIED Requirements

### Requirement: LLM 多模态品书提取与分类
系统 MUST 支持根据配置动态选择图像识别后端（OpenAI API 或自定义命令行工具），对待处理（pending）状态的品书（支持包含逗号分隔的多张图片）进行识别。系统 MUST 对提取出的数据进行强容错清洗与模糊映射归一化处理（包括名称、类型、价格与是否为套装），并将规整后的同人制品信息存入数据库。当选择 OpenAI 图像识别后端或启用文本规整兜底时，若 Langfuse 链路追踪已激活，系统 MUST 对对应的 LLM 调用进行追踪和上报。

#### Scenario: 成功解析品书并入库
- **WHEN** 对处于 `pending` 状态的品书进行解析，如果该品书包含多图（以逗号分隔），系统在 Python 内部逐一循环每张图片，分别调用已配置的图像识别后端进行单图识别，然后将所有图片的识别结果在 Python 端合并并过滤去重
- **THEN** 系统成功获取合法的商品列表后，在 `goods` 表中为该社团插入提取出的合并后的商品信息，并将对应的品书记录 `status` 更新为 `processed`

#### Scenario: 忽略非品书图片
- **WHEN** 图像识别后端对输入的所有图片判定均不属于品书或不包含任何同人制品及价格信息，或数据清洗后未得到任何合法商品项
- **THEN** 系统不插入任何商品数据，并将对应的品书记录 `status` 更新为 `ignored`


### Requirement: 可插拔图像识别引擎配置加载
系统 MUST 支持在 `config.yaml` 中配置 `image_recognition` 段落，定义 `provider` 为 `openai` 或 `cmd`，并支持配置命令行模板 `command_template`、超时时间 `timeout` 限制，以及是否开启可选的文本 API 格式化规整 fallback 选项。

#### Scenario: 成功加载命令行图像识别配置
- **WHEN** 配置文件中将 `image_recognition.provider` 设置为 `"cmd"`，且提供了 `command_template`
- **THEN** 系统成功解析并加载该配置，在串行处理每个单独的图片文件时，能够正确将 `{image_path}`、`{abs_image_path}`、`{circle_name}` 和 `{circle_author}` 替换为当前单张图片路径和相关社团信息传给命令行调用

