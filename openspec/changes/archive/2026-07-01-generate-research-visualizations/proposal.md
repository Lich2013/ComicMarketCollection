## Why

当前同人创作生态和文本计量研究报告中的所有图表仅以 Markdown 文本表格和设计蓝图形式存在，对于非技术读者而言阅读门槛高，缺乏直观的视觉呈现。
通过引入自动化的图表编译与生成管线，将数据转化为直观的题材分布气泡图、社媒采纳维恩图、展位空间热力图、简介词云以及中日生态对比雷达图，并将其物理生成并嵌入到 Markdown 报告中，能够大幅提升研究的易读性、学术表现力及严谨度。

## What Changes

- 在 `pyproject.toml` 中新增 `matplotlib`、`seaborn`、`wordcloud` 和 `matplotlib-inline` 依赖项（或视情况而定）。
- 新建可视化图表生成模块 [src/visualizer.py](file:///Users/lich/work/comicMarketCollection/src/visualizer.py)，实现五大设计蓝图对应的图表编译与渲染逻辑，输出为 PNG 静态图片并存储在 `research/images/` 目录下。
- 升级分析命令的报告渲染模板，将生成的 PNG 图表文件以 `![caption](path)` 形式自动物理嵌入到 [research/semantic_description.md](file:///Users/lich/work/comicMarketCollection/research/semantic_description.md) 和 [research/comiket_vs_comicup_multi_era_study.md](file:///Users/lich/work/comicMarketCollection/research/comiket_vs_comicup_multi_era_study.md) 等文档的相应章节。
- 在 `main.py` 中引入 `--generate-charts` 命令行参数用以独立调用图表渲染，并确保在执行 `--analyze-multi-era` 和 `--analyze-semantics` 时自动联动更新图表，保持图文口径一致。

## Capabilities

### New Capabilities
- `research-visualization`: 提供基于同人展会分析数据的静态图表自动生成、保存及 Markdown 报告图表嵌入的一体化管道能力。

### Modified Capabilities
（无）

## Impact

- **系统依赖**：新增 `matplotlib`、`seaborn`、`wordcloud` 绘图库，可能需要中文字体库（如 `wqy-microhei` 或使用系统默认中文字体避免中文字符乱码乱码）。
- **命令行工具**：在 `main.py` 中引入新的命令行参数入口。
- **文件存储**：将在 `research/images/` 物理生成 5-6 张静态图片资产。
