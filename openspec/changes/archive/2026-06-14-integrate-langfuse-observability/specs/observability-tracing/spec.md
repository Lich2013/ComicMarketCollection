## ADDED Requirements

### Requirement: 链路追踪配置加载与自检
系统 MUST 支持通过配置文件 `config.yaml`（`langfuse` 节点）或环境变量（`LANGFUSE_ENABLED`, `LANGFUSE_HOST`, `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`）加载 Langfuse 追踪配置，并于系统初始化或命令执行前，对配置的 Langfuse 服务进行连通性自检。

#### Scenario: Langfuse 服务连通成功
- **WHEN** 配置文件或环境变量中的 Langfuse 配置正确，且网络连通，执行 `Langfuse().auth_check()` 返回成功
- **THEN** 系统激活链路追踪模式，在控制台输出成功连接的提示信息，并将后续的 LLM 客户端包装为 Langfuse OpenAI 客户端

#### Scenario: Langfuse 服务未启用或连通失败
- **WHEN** 配置文件中 `langfuse.enabled` 为 `false`，或网络连接超时，或 `Langfuse().auth_check()` 返回失败
- **THEN** 系统在控制台输出降级运行的黄色 Warning 提示，但不抛出异常中断执行，后续 LLM 客户端采用原生 OpenAI 客户端运行

### Requirement: LLM 调用自动插桩与追踪
当系统链路追踪模式成功激活时，系统中的推文大模型预过滤分析与品书信息提取中的所有 LLM（OpenAI 兼容）调用，MUST 自动经过 Langfuse 客户端拦截，向 Langfuse 服务上报调用参数、输入输出、延迟和 Token 使用情况。

#### Scenario: LLM 请求被成功追踪上报
- **WHEN** 链路追踪模式已激活，系统执行品书提取或推文分析大模型调用
- **THEN** LLM 请求正常完成，同时相应的调用链路（Traces/Spans）、模型名称、Token 计数和时延上报至 Langfuse 控制台
