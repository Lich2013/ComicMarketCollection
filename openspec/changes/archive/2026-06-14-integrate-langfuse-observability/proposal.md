## Why

目前系统在进行推文预过滤分析（`twitter_sync.py`）以及品书信息提取（`goods_extractor.py`）时，频繁调用大语言模型（LLM）。在开发与运行阶段，由于缺乏统一的可观测性监控，我们难以实时掌握 LLM 调用的延迟、Prompt/Completion Token 消耗、具体开销、以及调用过程中的异常堆栈和上下文信息。

引入 Langfuse 链路追踪可以帮助我们在不破坏现有业务的前提下，对所有大语言模型调用进行全程监控和数据收集。

## What Changes

- **依赖项引入**：添加 `langfuse` 依赖，以支持与 Langfuse 服务的通信。
- **配置项扩展**：在 `config.yaml` / `config.yaml.example` 和 `src/config.py` 中增加对 `langfuse` 配置支持，包含 `enabled`、`host`、`public_key`、`secret_key` 等参数，并支持读取环境变量（`LANGFUSE_ENABLED`, `LANGFUSE_HOST`, `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`）。
- **初始化与自检逻辑**：新建 `src/utils/observability.py`。在应用启动时（或者执行命令时）自检 Langfuse 连通性（`Langfuse().auth_check()`）。如果不可用或未启用，输出警告并平滑降级为原生 `openai` 调用，确保系统运行的健壮性（零干扰降级）。
- **包装器替换**：对 LLM 调用部分进行代码微调，如果 Langfuse 可用，则实例化 `langfuse.openai` 提供的 `OpenAI` 包装器，替代原生的 `openai.OpenAI`。

## Capabilities

### New Capabilities
- `observability-tracing`: 引入 Langfuse 链路追踪系统，支持在系统启动时对本地/自托管/云端 Langfuse 服务进行连通性自检与友好降级；当服务可用时，使用包装器自动捕获并追踪推文分析和品书提取过程中的 LLM 交互详情、输入输出、延迟及 Token 消耗。

### Modified Capabilities
- `goods-extractor`: 在使用 OpenAI 多模态提取品书或在格式化文本兜底解析时，支持将大模型请求通过 Langfuse 可观测性网络进行上报和关联。

## Impact

- **Affected code**: `src/config.py`, `src/twitter_sync.py`, `src/goods_extractor.py`, `main.py`
- **APIs**: OpenAI Chat Completion 调用现在会经过 `langfuse.openai` 代理进行上报（在 Langfuse 连通的情况下）。
- **Dependencies**: 增加 `langfuse` python SDK 依赖。
- **Systems**: 需要连接 Langfuse 服务（例如本地 `http://localhost:3000`），无连接时对系统原有功能没有任何性能和逻辑阻碍。
