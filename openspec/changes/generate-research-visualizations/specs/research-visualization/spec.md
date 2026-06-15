## ADDED Requirements

### Requirement: 自动生成静态图表资源
系统 SHALL 支持根据同人数据分析大盘自动编译并生成五套设计蓝图对应的静态图表。这些图表包括：
- **题材分布与偏离度气泡图 (DBI Bubble Chart)**：横轴表示大盘受众占比，纵轴表示同人偏离度指数，气泡大小代表实际社团数。
- **社媒采纳三环维恩图 (Social Venn Diagram)**：展示 X 绑定率、Pixiv 绑定率以及双向绑定的交集重合度。
- **展位物理热力分布图 (Booth Spatial Heatmap)**：按展馆网格和位置渲染社团密度及拥堵阻尼节点。
- **简介高频词云图 (Description Word Cloud)**：根据 TF-IDF 权重渲染同人热词的大小与分色展示。
- **中日双城同人生态倾向对比雷达图 (Radar & SDI Charts)**：展示中日展会五个核心指标轴（集中度、小说占比、无料占比、O2O 预约率、双日重合度）的横向与纵向对比。

生成的图表文件 MUST 统一保存为 PNG 静态格式，存放在 `research/images/` 目录下。

#### Scenario: 成功编译生成所有静态图片
- **WHEN** 可视化引擎执行图表编译任务
- **THEN** 系统在 `research/images/` 目录下成功生成并写入 `dbi_bubble_chart.png`、`social_venn_diagram.png`、`booth_heatmap.png`、`description_wordcloud.png` 以及 `radar_ecology_comparison.png` 文件，且图片排版渲染无中文字符乱码

### Requirement: 报告图表自动物理嵌入
系统 SHALL 在编译生成最新的同人分析 Markdown 研究报告时，自动以标准图片语法物理嵌入上述图表。
- 词云图和社交维恩图 MUST 嵌入在 [research/semantic_description.md](file:///Users/lich/work/comicMarketCollection/research/semantic_description.md) 的相应位置。
- 题材分布气泡图、展馆空间热力图及生态雷达图 MUST 嵌入在 [research/comiket_vs_comicup_multi_era_study.md](file:///Users/lich/work/comicMarketCollection/research/comiket_vs_comicup_multi_era_study.md) 的相应位置。

#### Scenario: 重构报告模板并嵌入图片链接
- **WHEN** 渲染研究报告模板
- **THEN** 编译产出的 Markdown 报告包含 `![Description Word Cloud](images/description_wordcloud.png)` 等图片引用，在 Markdown 阅读器中可直接渲染呈现

### Requirement: 命令行入口及任务联动
系统 SHALL 提供独立参数以支持可视化任务的单独调度，同时与主力分析指令（`--analyze-semantics` 和 `--analyze-multi-era`）实现强联动。当运行这些分析指令时，可视化图表 MUST 自动刷新并写入以确保数据与图片内容绝对一致。

#### Scenario: 运行分析参数时自动触发图表刷新
- **WHEN** 用户在命令行执行 `python main.py --analyze-semantics`
- **THEN** 系统先计算文本计量指标，写入 `data/semantic_metrics.json` 缓存，随后自动重新编译生成 `description_wordcloud.png` 并重构 `research/semantic_description.md`，使之包含最新的统计数据与对应的最新词云图
