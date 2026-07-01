## 1. 语义分析内核实现与分词计算 (Semantic Analyzer Kernel & Tokenization)

- [x] 1.1 在 `pyproject.toml` 中添加 `sudachipy`、`sudachidict-core`、`pandas` 和 `scipy` 依赖项
- [x] 1.2 在 `src/` 下新建 [semantic_analyzer.py](file:///Users/lich/work/comicMarketCollection/src/semantic_analyzer.py)，编写 SudachiPy 分词与分题材 TF-IDF 特征提取函数（需支持动态 `db_path` 参数）
- [x] 1.3 实现特定 IP 角色词的前向/后向负性断言正则表达式排除匹配与计数逻辑，洗白子串噪音
- [x] 1.4 实现题材与简介填写率的交叉分析，以及简介填写状态与原生社媒链接绑定相关性分析逻辑
- [x] 1.5 引入 scipy 卡方独立性检验（题材大类 × 内容标签）及 Cramér's V 效应量计算逻辑
- [x] 1.6 引入 C107 和 C108 核心词频的占比时序纵向漂移计算逻辑

## 2. 命令行集成与报告渲染模块 (CLI Integration & Report Generation)

- [x] 2.1 编写 `generate_semantic_report(stats, output_path)` 报告生成模板渲染逻辑，输出格式完全对齐新方法论
- [x] 2.2 在 `main.py` 中引入 `--analyze-semantics` 命令行参数并对接语义分析执行入口
- [x] 2.3 在运行生成对比报告时，安全地将计算出的 C108 小说提及率（5.5% 左右）数值与多展期对比模块打通（可通过文件缓存或模块导入），防止跨文档口径不一，并同步更新 `tests/test_multi_era.py` 中对应的测试断言

## 3. 文档体系更新 (Document Updates)

- [x] 3.1 运行分析命令，完全重构 [research/semantic_description.md](file:///Users/lich/work/comicMarketCollection/research/semantic_description.md) 报告，替换所有老旧的模糊统计表格并合入卡方效应量和时序漂移说明
- [x] 3.2 升级 [research/README.md](file:///Users/lich/work/comicMarketCollection/research/README.md) 中的相关指标描述说明

## 4. 单元测试与大盘验证 (Tests & Verifications)

- [x] 4.1 在 `tests/` 中新建测试脚本 `tests/test_semantic_analyzer.py`，编写对 SudachiPy 分词、正则角色过滤、卡方计算和报告渲染模板的单元测试
- [x] 4.2 运行整个单元测试套件 `PYTHONPATH=. uv run pytest`，确保测试通过率 100%
- [x] 4.3 执行 `PYTHONPATH=. uv run python main.py --analyze-semantics`，重新编译生成最新的简介报告，验证格式排版及中日对比小说数据一致性完全正确

## 5. 评审反馈改进 (Peer Review Refinements)

- [x] 5.1 在 `src/semantic_analyzer.py` 中计算社媒绑定相关性的卡方值、p-value 与 Cramér's V 效应量
- [x] 5.2 在 `src/semantic_analyzer.py` 的时序漂移计算中引入两样本比例 z 检验，计算双尾 p-value
- [x] 5.3 在报告渲染模板中补充社媒卡方检验值、明示卡方检验的 7 大自变量题材、合入 z 检验 p 值、增补“复合名词过度拆分”局限性声明，并统一格式化千分位数字
- [x] 5.4 升级单元测试套件 `tests/test_semantic_analyzer.py` 中关于新增检验指标的断言，确保测试通过率 100%
- [x] 5.5 运行重新编译命令编译生成最新的分析报告与多展期报告，验证格式完全正确
