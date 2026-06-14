## Context

当前系统在执行推文分类分析与品书同人制品多模态提取时会调用 OpenAI 或兼容 LLM 接口。当前的架构中直接使用了原生的 `openai.OpenAI` 客户端，缺乏调用链路追踪和性能监控。本项目需要接入 Langfuse 链路追踪系统，以非侵入式的方式，对 LLM 的调用请求进行捕获和监控，上报输入、输出、Token 统计、耗时和异常，并保证在 Langfuse 服务不可用时，系统能自动、无感地降级为原生调用。

## Goals / Non-Goals

**Goals:**
- 在 `config.yaml` / `config.yaml.example` 中增加 `langfuse` 配置节点。
- 实现 `src/utils/observability.py` 用以加载配置、执行 Langfuse 连通性自检 (`lf.auth_check()`)，并维护全局激活状态。
- 提供 `get_openai_client` 包装器：当链路追踪激活时返回 `langfuse.openai.OpenAI`，降级时返回原生的 `openai.OpenAI`。
- 修改 `src/twitter_sync.py` 和 `src/goods_extractor.py` 中的 `OpenAI` 客户端初始化逻辑，使用该包装器。
- 修改 `main.py`，在 CLI 启动时自动执行可观测性初始化与自检。

**Non-Goals:**
- 不使用 `openinference-instrumentation-openai-agents` 等针对 Agents 框架的插桩库（因为本项目非 Agent SDK 架构，只需监控标准 OpenAI 客户端调用即可）。
- 不对除 LLM 调用之外的数据库读写或网络请求（如 Playwright 抓取过程）进行复杂的 OpenTelemetry 追踪。

## Decisions

### 1. 使用 `langfuse.openai` 装饰包装器作为 Drop-in 替代
- **设计选择**：将所有 LLM 客户端初始化代码由直接使用 `from openai import OpenAI` 替换为 `src.utils.observability.get_openai_client`。
- **原因**：`langfuse.openai` 封装了标准的 `OpenAI` 客户端，能够自动处理 `chat.completions.create` 的拦截与上报，不需要对业务层的大模型请求代码进行任何修改（如添加修饰器或手动创建 Span），维护成本最低。

### 2. 启动自检与强健的零干扰降级（Zero Interference Degradation）
- **设计选择**：在 CLI 启动时尝试实例化 `Langfuse()` 并调用 `auth_check()` 进行连通性检验。如果发生 `ImportError`（未安装 `langfuse` 包）、网络超时或认证失败，仅在控制台输出警告，将全局追踪标记设为 `False`。
- **原因**：这保证了即使系统没有安装 `langfuse` 依赖，或者本地没有运行自托管的 Langfuse 服务，现有爬虫和提取工具依然可以完全正常地降级运行，绝不因为监控问题阻断用户的实际业务。

### 3. 配置管理的多样性与优先级
- **设计选择**：`langfuse` 配置同时支持 `config.yaml` 文件读取和环境变量（`LANGFUSE_ENABLED`, `LANGFUSE_HOST`, `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`）。环境变量优先级高于配置文件。
- **原因**：这对于 Docker 或 CI 部署以及多用户本地部署环境下的凭证管理非常友好。

## Risks / Trade-offs

- **[Risk] 依赖包缺失导致启动报错** → **[Mitigation]** 在 `src/utils/observability.py` 中对 `import langfuse` 使用 `try-except ImportError` 保护。若导入失败，友好提示并标记未启用。
- **[Risk] 网络阻塞导致 `auth_check()` 卡住启动** → **[Mitigation]** `Langfuse().auth_check()` 自带网络超时设置，即使不可达也会在数秒内返回。在设计中，自检过程使用 try-except 包裹，发生任何超时或连接异常都会迅速降级。
