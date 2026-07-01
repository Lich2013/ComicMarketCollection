## Context

当前的社团简介文本挖掘缺乏科学的计量模型与严谨的因果推论，主要体现在词频统计被高频背景停用词干扰、IP 角色计数因简单的子串碰撞而严重偏离真实值、缺少与社媒链接及大盘填写率的交叉分析，且缺少必要的卡方检验与效应量支撑。本设计旨在在应用层引入日语分词（SudachiPy）和 TF-IDF 加权排序算法，解决角色计数的假阳性碰撞，并引入卡方独立性检验和双期漂移分析。

## Goals / Non-Goals

**Goals:**
*   在 `src/` 目录下新增 [semantic_analyzer.py](file:///Users/lich/work/comicMarketCollection/src/semantic_analyzer.py) 模块，实现 SudachiPy 分词、TF-IDF 权重排序、特定 IP 角色精准正则匹配计数、覆盖率与引流交叉统计，以及题材与核心标签的卡方检验。
*   在 `main.py` 中新增 `--analyze-semantics` 参数，实现一键刷新报告。
*   利用计算结果完全重构 [research/semantic_description.md](file:///Users/lich/work/comicMarketCollection/research/semantic_description.md)。

**Non-Goals:**
*   不改变已有的 SQLite 数据库结构（Schema）。
*   不修改 Comiket 和 Comicup 数据采集爬虫的核心抓取逻辑。

## Decisions

### 决策 1：选择 SudachiPy 作为日语分词器
*   **方案**：引入 `sudachipy` 及其核心词典 `sudachidict_core`，并采用 `SplitMode.C` 进行分词。
*   **理由**：
    *   *Janome*：Janome 是纯 Python 实现，易于安装，但在处理 15,000 条文本时速度过慢，对本项目的分析性能有明显制约。
    *   *MeCab*：MeCab 速度极快，但需要宿主机预先编译安装 `mecab` 系统动态库，会给用户运行测试脚本带来环境摩擦。
    *   *SudachiPy（选择）*：SudachiPy 速度极快，且不需要安装系统级 MeCab，通过 uv 动态引入极为平滑。其 `SplitMode.C`（复合词模式）能够自动将“ブルーアーカイブ”、“同人誌”等复合名词作为一个整体切分出来，大幅减少了自定义字典的维护工作量。

### 决策 2：分析脚本与自动化报告生成架构
*   **方案**：在 `src/semantic_analyzer.py` 中集中实现分析流程。
    *   `run_semantic_analysis(db_path)`：负责从数据库读取简介，调用分词器，计算所有文档的 TF-IDF。接着分题材（8 大题材）过滤得到平均 TF-IDF 前 8 的特异特征词；分题材利用排除性正则统计角色提及率；统计有无简介与原生社媒链接的交叉相关性；对冬夏（C107 vs C108）两期进行漂移对比；并利用 `scipy` 对主力题材与 R18/Goods/Novel 标签进行卡方检验和 Cramér's V 效应量计算。
    *   `generate_semantic_report(stats, output_path)`：将数据渲染填充至报告模板，一键生成 `research/semantic_description.md`。
    *   在 `main.py` 中集成：
        ```python
        parser.add_argument("--analyze-semantics", action="store_true", help="执行社团简介语义特征分析并自动生成研究报告")
        ```
*   **理由**：保持代码高内聚、低耦合，将计算和报告生成逻辑集中于单一文件，并在入口 `main.py` 暴露一键生成通路，便于复现与单元测试。

### 决策 3：IP 角色提及率的多重正则匹配清洗
*   **方案**：对高频冲突词设计前向/后向负性断言。例如，对角色“アル”（阿露），使用正则表达式 `アル(?![(キ)(コ)(カ)(ゲ)(フ)(テ)(ト)(バ)(ビ)(ブ)(ベ)(ボ)(マ)(ミ)(メ)(モ)(ラ)(リ)(ル)(レ)(ロ)(ワ)(ン)(ァ)(ィ)(ゥ)(ェ)(ォ)])` 以排除 `アクリル` (亚克力)、`オリジナル` (原创) 等词汇。
*   **理由**：在日语中，由于没有空格且片假名外来语重合度高，直接子串检索会产生巨大的系统噪音（如将 238 次子串匹配清洗为仅 3 次的阿露提及）。正则排除是一种不需构建庞大停用词库即可在应用层高效洗白关键角色的最佳妥协方案。

### 决策 4：题材与内容倾向的卡方检验与 Cramér's V 效应量计算设计
*   **方案**：选取 7 大主力题材作为自变量，将简介中是否包含 `R18/成人向`、`周边 (Goods)`、`小说 (Novel)` 分别作为三个二分类因变量。构建 $7 \times 2$ 的交叉列联表，使用 `scipy.stats.chi2_contingency` 进行检验，并使用 pandas 动态计算 Cramér's V：
    $$V = \sqrt{\frac{\chi^2}{N \cdot 1}} = \sqrt{\frac{\chi^2}{N}}$$
*   **理由**：在内容偏好判定中，纯统计显著性（p值）易受 15,000 级大样本量的影响而呈现虚假显著。引入 Cramér's V 效应量（由于列联表维度为 $7 \times 2$，自由度 $k = 1$，效应量阈值 $V \ge 0.1$ 为弱，$\ge 0.3$ 为强）能够科学评估关联强度，提供符合学术规范的解释。

## Risks / Trade-offs

*   **[Risk] SudachiPy 词典文件较大 (约 70MB)**
    *   *Mitigation*：`sudachidict_core` 在通过 `uv` 运行或安装时会自动缓存，虽然首次下载需要一定时间，但后续执行是瞬时启动的。在文档中写明下载要求。
*   **[Risk] 新增特定 IP 角色的正则可能不够完备**
    *   *Mitigation*：在代码中编写单元测试，对特殊冲突词语的匹配逻辑进行断言核对，确保过滤正则的精确度。
