## 1. Setup & Config

- [x] 1.1 安装/配置 python 依赖，在 `pyproject.toml` 中添加 `langfuse>=2.57.0`，并使用 `uv` 刷新依赖。
- [x] 1.2 在 `config.yaml` 和 `config.yaml.example` 中增加 `langfuse` 配置节点（包括 `enabled`、`host`、`public_key`、`secret_key` 等）。
- [x] 1.3 在 `src/config.py` 中更新配置读取和环境变量映射逻辑，并添加默认生成配置方法（包含 `langfuse` 节点）。

## 2. Observability Utility

- [x] 2.1 创建 `src/utils/observability.py` 模块，包含 `init_observability(config)` 连通性自检方法及 `get_openai_client(api_key, base_url)`。
- [x] 2.2 实现该模块中的异常防御保护和降级日志，确保在 `langfuse` 依赖包不存在或网络不通时能静默降级，不阻断运行。

## 3. Client Integration

- [x] 3.1 修改 `src/twitter_sync.py` 中的 LLM 客户端初始化，使用 `get_openai_client` 包装器。
- [x] 3.2 修改 `src/goods_extractor.py` 中的 LLM 客户端初始化，替换为 `get_openai_client` 包装器。
- [x] 3.3 修改 `main.py` 入口，在启动时调用 `init_observability(config)` 进行初始化自检。

## 4. Verification & Testing

- [x] 4.1 运行单元测试，确保基本流程没有因为 `langfuse` 的引入而损坏。
- [x] 4.2 运行命令行推文分析与品书提取任务，测试连通及降级场景下的控制台日志输出。
- [x] 4.3 验证大语言模型调用的 Trace 上报正常，包含 Prompt/Completion Token 计数和延迟监控。
