## 1. 依赖配置与命令行接口集成

- [x] 1.1 在 `pyproject.toml` 中配置 `matplotlib`、`seaborn` 和 `wordcloud` 依赖
- [x] 1.2 扩展 `main.py` 命令行参数，新增独立控制参数 `--generate-charts`
- [x] 1.3 在 `main.py` 中引入对应的逻辑分支调用，能够触发完整图表生成与保存管线

## 2. 可视化绘制模块实现

- [x] 2.1 创建 `src/visualizer.py` 并初始化 matplotlib 全局字体及 DPI 配置（支持中日文字体渲染）
- [x] 2.2 实现题材分布与偏离度气泡图渲染函数 `generate_dbi_bubble_chart`
- [x] 2.3 实现社媒采纳维恩图手动圆弧渲染函数 `generate_social_venn_diagram`
- [x] 2.4 实现展位物理热力分布图渲染函数 `generate_booth_heatmap`
- [x] 2.5 实现简介高频词云图渲染函数 `generate_description_wordcloud`
- [x] 2.6 实现中日生态倾向对比雷达图渲染函数 `generate_radar_ecology_comparison`
- [x] 2.7 实现一键式整合生成入口函数 `generate_all_charts`

## 3. 分析报告模板修改与自动化钩子联动

- [x] 3.1 修改 `src/semantic_analyzer.py` 中的报告模板，自动物理嵌入词云图与维恩图
- [x] 3.2 修改 `src/multi_era_analyzer.py` 中的报告模板，自动物理嵌入气泡图、展位空间热力图与对比雷达图
- [x] 3.3 在 `main.py` 的语义分析分支（`--analyze-semantics`）中引入可视化更新回调
- [x] 3.4 在 `main.py` 的多展期联合分析分支（`--analyze-multi-era`）中引入可视化更新回调

## 4. 测试与验证

- [x] 4.1 编写单元测试验证 `src/visualizer.py` 的数据提取与各图表生成逻辑不抛出异常
- [x] 4.2 运行图表生成管线，验证 `research/images/` 目录下成功物理保存 5 张 PNG 静态图表
- [x] 4.3 验证生成的 Markdown 报告中均包含了正确格式 of 的图表引用，并在阅读器中能正常展现且无乱码
