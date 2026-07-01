## Context

当前同人创作生态和文本计量研究报告（如 `research/semantic_description.md` 和 `research/comiket_vs_comicup_multi_era_study.md`）已具备详实的数据表格与推断统计学检验（如卡方检验、z 检验和 Moran's I 空间自相关），但缺乏直观的视觉呈现。为了进一步降低非技术读者的阅读门槛，提升学术报告的表现力，本项目提出引入自动化的图表编译与生成管线。

系统需要支持自动生成题材分布与偏离度气泡图、社媒采纳三环维恩图、展位物理热力分布图、简介高频词云图以及中日双城生态倾向对比雷达图这五大核心图表。图表需物理生成为 PNG 文件存放在 `research/images/` 目录下，并自动物理嵌入到对应的 Markdown 报告中。

## Goals / Non-Goals

**Goals:**
- **自动化图表编译管线**：新建 `src/visualizer.py` 模块，能从数据库或分析计算的中间状态（`stats`）中提取并渲染五大图表。
- **高鲁棒的字体与样式保障**：图表需具备学术级的高 DPI 和美观配色，且必须支持中日语字符渲染，避免出现“豆腐块”乱码。
- **物理嵌入与强联动**：在运行 `--analyze-semantics` 和 `--analyze-multi-era` 时，自动生成对应的图表并嵌入到 Markdown 报告文件的特定位置，确保图文口径绝对一致。
- **独立调用能力**：命令行新增 `--generate-charts` 参数，支持在不重新执行耗时的文本分词与统计分析时，直接基于现有数据或缓存生成最新的图表。

**Non-Goals:**
- **动态交互式图表开发**：不引入基于 JS（如 ECharts、D3.js）的动态前端交互图表，仅专注于高质量的静态 PNG 图表，以保持 Markdown 报告的可移植性。
- **大规模 3D 展位三维建模**：热力图仅进行二维网格和宏观街区的热度分布展示，不进行展位三维立体管线设计。

## Decisions

### 1. 技术选型与依赖引入
- **决策**：使用 `matplotlib` + `seaborn` + `wordcloud` 组合。
- **理由**：
  - `matplotlib` 是 Python 可视化的基石，能实现极高自由度的定制（如雷达图的极坐标投影、维恩图的自定义圆绘制）。
  - `seaborn` 提供优美且学术风的默认色板和简便的二维密度/热力图绘制 API。
  - `wordcloud` 能直接输入词语权重字典，配合日语/中文字体渲染高频词云。
- **备选方案**：引入 `matplotlib-venn` 库绘制维恩图。因该库依赖第三方 C 库，在部分环境下安装复杂，且仅能用于维恩图，因此弃用，转为在 `matplotlib` 中手动绘制 overlapping circles，以降低依赖风险。

### 2. 字体与多语言乱码防护机制
- **决策**：在绘图逻辑初始化时，动态检测并配置 matplotlib 的中日文字体设置。
- **理由**：
  - macOS 环境下默认自带 `'Arial Unicode MS'`, `'Hiragino Sans'`, `'Heiti TC'` 等支持中日语的字体。
  - 在代码中使用以下初始化逻辑：
    ```python
    import matplotlib.pyplot as plt
    plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'Hiragino Sans', 'Heiti TC', 'sans-serif']
    plt.rcParams['axes.unicode_minus'] = False
    ```
  - 对于 `wordcloud`，由于它不支持 matplotlib 的全局 rc 字体配置，必须显式传入 `font_path`。逻辑中应查找系统常见的 TrueType 字体文件（如 macOS 下的 `"/System/Library/Fonts/PingFang.ttc"` 或系统内置日语中文字体），确保词云图正常渲染。

### 3. 五大图表的数据提取与绘制逻辑
- **气泡图 (DBI Bubble Chart)**：
  - 数据：来自 CP31 的 `dbi_rankings`（包含 `supply_percentage`, `demand_percentage`, `dbi`, `count`）。
  - 绘制：X 轴为 `demand_percentage`（反映受众需求占比），Y 轴为 `dbi`（反映供求偏离度）。气泡大小 `s` 正比于制品数量 `count`。添加 $Y = 1.0$ 的平衡虚线。利用 `plt.annotate` 对排名前 10 的重点题材进行标注。
- **社媒维恩图 (Social Venn Diagram)**：
  - 数据：通过 SQL 统计 C108 中同时包含或部分包含 `has_desc`, `has_twitter`, `has_pixiv` 的社团组合频数。
  - 绘制：在 matplotlib 中计算 3 个相交圆的圆心位置（如 Left(0.35, 0.6), Right(0.65, 0.6), Bottom(0.5, 0.35)，半径均设为 0.25）。用 `matplotlib.patches.Circle` 绘制半透明圆，并在各重合区域叠加文本标注绝对数与百分比。
- **展位物理热力图 (Booth Spatial Heatmap)**：
  - 数据：
    - Comiket (C108)：X 轴为 Block（A-Z），Y 轴为 Hall（E1-6, W1-2, S1-2），网格内数值为社团密度。
    - Comicup (CP31)：提取排名前 15 的街区专区（`position_name`），计算其社团数或制品数密度。
  - 绘制：在一个画布的左右子图中，左图用 `sns.heatmap` 绘制 Comiket 的展馆-街区热力方阵；右图绘制 Comicup 主力街区密度的水平色带条形热力图。
- **简介词云图 (Description Word Cloud)**：
  - 数据：从语义分析输出的 `genre_tfidf_results` 中汇总全局词汇的平均 TF-IDF 权重，或过滤特定停用词后进行全局词频/权重统计。
  - 绘制：使用 `wordcloud.WordCloud().generate_from_frequencies(tfidf_dict)`，选用系统支持的中日文字体。
- **对比雷达图 (Radar Comparison)**：
  - 数据：横向对比 C108 与 CP31 的五个生态指标：CR10 集中度、文本小说比、无料占比、O2O 数字化率、双日重合度。
  - 绘制：利用极坐标 `subplot(111, projection='polar')`，计算五个维度标准化后的多边形并填充半透明对比色。

### 4. Markdown 自动嵌入设计
- **决策**：修改报告生成函数 `generate_semantic_report` 和 `generate_multi_era_report`，在渲染模板的指定章节自动插入 Markdown 图片引用语法。
- **理由**：
  - 确保每次执行分析更新数据时，Markdown 报告中不仅数据表格得到更新，引用的图片物理文件也同步刷新，且路径使用相对路径 `images/xxxx.png`，确保任何 Markdown 渲染器或本地预览均能正常加载。

## Risks / Trade-offs

- **[Risk] 中日语字符在无对应字体的系统环境（如没有 Arial Unicode MS 的精简 Linux Docker）中运行时渲染为“豆腐块”**
  - **Mitigation**：代码中建立多级的字体查找降级链（包含 macOS, Windows, Linux 常见中日文字体名称），如最终都未找到，则尝试读取 Python 系统环境中自带的 `DejaVuSans.ttf` 并打印警告信息。
- **[Risk] WordCloud 依赖的 wordcloud 库在某些 Python 3.12+ 环境下可能需要 C 编译器才能从源码编译构建**
  - **Mitigation**：在 `pyproject.toml` 中使用标准的 `wordcloud` 依赖。若用户环境无法成功安装 `wordcloud`，在 `src/visualizer.py` 中引入 `import wordcloud` 时使用 `try-except` 捕获异常，并在导入失败时仅打印警告并跳过词云图生成，而不阻断其他四个基于 matplotlib 纯 Python 图表的编译，保证系统整体的弹性。
- **[Risk] 二维展位热力图中，Comiket 展位位置数据的 block 字符和 space 数字格式不规整**
  - **Mitigation**：在 `visualizer.py` 中对 `hall` 和 `block` 进行严格的正则过滤与清洗，对于不合规的位置映射到“未知”网格，避免程序崩溃。
