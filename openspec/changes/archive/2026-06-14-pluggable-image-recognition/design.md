## Context

当前系统中，`src/goods_extractor.py` 内的品书商品提取功能（`extract_goods_from_catalog`）硬编码依赖了 OpenAI 多模态 API。由于多模态 API 对大图片的输入处理计费较高，这使得用户在使用该系统时面临较高的 API 开销。此外，很多用户本地具备运行多模态本地模型或使用本地命令行工具（如 `agy`、`codex`）的能力，系统应允许灵活配置这些工具作为品书解析引擎。

## Goals / Non-Goals

**Goals:**

- **可配置化引擎**：支持通过 `config.yaml` 灵活选择 `openai` API 或 `cmd` 自定义命令行识别后端。
- **高强度的容错解析**：针对命令行输出的不可靠性（包含多余文本、键值混乱、数据类型畸形），构建多层防御解析器，支持模糊键名映射、数字和布尔类型强制转换。
- **无缝向后兼容**：若用户配置文件未更新或未配置 `image_recognition`，系统默认无缝回退到已有的 OpenAI API 调用方式。
- **模块化重构**：将识别底层逻辑（API 与 CLI 识别）与数据入库/格式化业务逻辑分离开来，提升代码的 DRY 水平和可维护性。

**Non-Goals:**

- **不提供命令行工具自身的安装**：用户需自行确保配置的本地 CLI 工具（如 `agy`）在运行环境中已正确安装并处于 PATH 中。
- **不改变数据库结构**：不修改现有的数据库表设计，保证新提取数据流可以直接落入现有的 `goods` 和 `catalogs` 表中。

## Decisions

### 决策 1：配置文件格式设计
在 `config.yaml` 中新增 `image_recognition` 配置节点。

**方案选型：**
```yaml
image_recognition:
  provider: "cmd"  # 可选: "openai" 或 "cmd"
  cmd:
    command_template: 'agy -p "帮我查看社团 {circle_name}（作者：{circle_author}）的品书图片 {image_path}，提取其中所有的制品，并输出为符合结构的要求。"'
    timeout: 90
    fallback_text_formatter: true  # 当 JSON 无法被普通解析时，是否调用纯文本 API 进行结构化整理
```
并在 `src/config.py` 中增加对该段落的加载，确保支持环境变量 `IMAGE_RECOGNITION_PROVIDER` 等的最高优先级覆盖，以及针对历史配置文件的智能默认值填充（若缺失该配置，则默认 `provider = "openai"`）。

---

### 决策 2：架构模块化重构
将 `src/goods_extractor.py` 中的 `extract_goods_from_catalog` 重构为高层分发器与数据归一化后处理器。

**实现方式：**
- `extract_goods_via_openai(catalog, openai_config)`：专门负责多模态图片编码、API 请求与解析。
- `extract_goods_via_cmd(catalog, cmd_config)`：专门负责变量替换、命令行调用执行、超时控制。
- `extract_goods_from_catalog(catalog, config)`：主分发函数，获取中间统一结构后，执行入库字典的拼装和类型格式化。

这样设计能最大化复用入库前的清洗与校验逻辑。

---

### 决策 3：渐进式降级与模糊纠错解析器
外部命令行工具生成的 JSON 约束力弱。我们设计如下三道防线处理输出：

- **防线 1：JSON 正则截取 + 模糊键名映射**：
  使用 `re.search(r"({.*})", output, re.DOTALL)` 提取最外层大括号。然后定义同义词表（如 `title` 映射为 `name`，`cost` 映射为 `price`），并将 `"1000円"`、`"¥1000"` 等脏数据清洗为纯整数。
- **防线 2：Markdown 列表正则匹配**：
  如果 CLI 工具没有输出 JSON，只输出了 `- 新刊 A 1000円` 这类列表，通过 Python 正则逐行匹配提取。
- **防线 3：廉价文本 API 结构化规整 fallback**：
  如果上述均失败且开启了 fallback，则将 CLI 输出文本送入廉价的纯文本 LLM（如 GPT-4o-mini，比多模态图片 API 便宜很多），使用 System Prompt 要求其将其转化为严格的商品 JSON 列表。

---

### 决策 4：安全的进程控制
执行本地命令行使用 Python 的 `subprocess.run(shell=True, capture_output=True, text=True, timeout=timeout)`，并在 `TimeoutExpired` 异常时进行友好捕获，避免整个提取流程因某张图片处理卡死。

## Risks / Trade-offs

- **[Risk]**：Shell 注入风险。如果社团名或图片路径含有恶意 Shell 字符，直接用 `shell=True` 执行命令可能被攻击。
  - **Mitigation**：对传入的模板变量进行安全过滤，例如使用 `shlex.quote()` 转义 `{image_path}`、`{circle_name}` 等变量，或者使用参数列表来传递。但在 Windows 或某些环境下 Shell 表达式较复杂，我们将对变量值采用 `shlex` 进行严格的转义过滤后再格式化。
- **[Risk]**：本地模型不稳定或速度慢，导致商品处理进度延时。
  - **Mitigation**：可以通过在主命令中设置适当的 `timeout`，对超时任务打上 `failed` 状态并跳过，不影响后续品书的提取。
