## 1. 配置加载与向后兼容

- [x] 1.1 在 `src/config.py` 中加载 `image_recognition` 配置节点，在缺失时提供默认的 `"openai"` 回退以实现无缝兼容
- [x] 1.2 支持读取环境变量（如 `IMAGE_RECOGNITION_PROVIDER`）以最高优先级覆盖配置
- [x] 1.3 更新 `config.yaml`（及 `config.yaml.example` 模版，并在 `src/config.py` 的 `write_default_config` 中更新），添加注释说明和默认字段


## 2. 图像提取核心逻辑重构

- [x] 2.1 重构 `src/goods_extractor.py` 中的 `extract_goods_from_catalog` 为高层路由分发函数，并将提取后的字段归一化及入库流程抽离为通用的后处理逻辑
- [x] 2.2 抽取原有 OpenAI 视觉 API 调用及 structured outputs 解析逻辑，封装进独立的子函数 `extract_goods_via_openai`
- [x] 2.3 实现子函数 `extract_goods_via_cmd`，根据模板动态替换 `{image_path}`、`{abs_image_path}`、`{circle_name}` 和 `{circle_author}`，支持安全转义处理
- [x] 2.4 使用 `subprocess.run` 并配合配置中的 `timeout` 限制执行自定义命令行，捕获进程执行异常和超时异常
- [x] 2.5 修复 `prompt_template` 中大括号引发的 `format()` 崩溃问题，改用更健壮的 `.replace()` 替换
- [x] 2.6 增加 CLI 运行结果（退出码、标准输出与错误输出）的调试打印


## 3. 强容错数据清洗与解析器

- [x] 3.1 实现 `parse_json_from_stdout`，使用正则表达式和括号扫描，稳健地截取并解析 CLI 标准输出中的 JSON 块
- [x] 3.2 实现模糊键名匹配（同义词转换表）和类型纠错转换逻辑（把非数字符号过滤清洗价格、把各种异形表达转换为 Boolean）
- [x] 3.3 实现 Markdown 正则解析器 `try_parse_markdown_list`，用于从完全不带 JSON 的纯文本 Bullet 列表中正则提取制品与价格
- [x] 3.4 实现可选的 `fallback_text_formatter` 逻辑，当 CLI 无法输出标准的 JSON 结构时，调用纯文本 API 进行低成本格式转换

## 4. 测试与验证

- [x] 4.1 在 `tests/test_db.py` 或新建测试文件中，编写配置加载及智能回退逻辑的单元测试
- [x] 4.2 针对模糊映射、价格清洗、布尔值转换编写多场景输入单元测试
- [x] 4.3 编写测试用例验证 Markdown 正则列表解析与模糊 JSON 提取的健壮性
- [x] 4.4 模拟（Mock）命令行执行，编写对 CLI 品书提取完整调用流的集成测试
