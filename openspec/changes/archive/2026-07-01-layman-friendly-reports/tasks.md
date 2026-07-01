## 1. 准备与基准对齐

- [x] 1.1 确认 `research/` 目录下全部五个研究报告的原始路径与备份
- [x] 1.2 确认所有 LaTeX 公式、Mermaid 拓扑图、PNG 图片的链接路径，确保不被遗漏或损毁

## 2. 报告文本通俗化重构与公式拆解

- [x] 2.1 重构 `research/genre_distribution.md`（题材与类型分布分析报告），对 $CR_n$、贝恩市场集中度分类、DBI 和区位商 $LQ$ 等公式应用四层渐进解释
- [x] 2.2 重构 `research/social_media_adoption.md`（社交媒体采纳率分析报告），对双平台采纳率公式、卡方独立性检验期望频数 $E_{ij}$ 及 $\chi^2$ 统计量进行四层渐进式拆解
- [x] 2.3 重构 `research/booth_density.md`（展位密度分析报告），对街区题材纯度 $\text{Purity}$、全局莫兰指数 Moran's I、壁圈判定 $\text{IsWall}$、2D 平面映射及步行距离惩罚公式进行四层渐进式拆解
- [x] 2.4 重构 `research/semantic_description.md`（简介文本计量特征提取报告），对 Cramér's V 效应量公式（予以补充）、卡方检验结果、z 检验公式（予以展示）进行四层渐进式拆解
- [x] 2.5 重构 `research/comiket_vs_comicup_multi_era_study.md`（中日双城生态多展期对比研究报告），对多期 SDI、Moran's I 等公式应用四层渐进解释，并优化对比表格和分析的通俗度

## 3. 验证与发布

- [x] 3.1 校验重构后的五篇 Markdown 报告是否通过 MathJax 或 LaTeX 标准公式渲染校验
- [x] 3.2 校验重构后的报告中的全部原始统计数据与原版是否完全一致（未被误删改）
- [x] 3.3 检查所有图片、链接及 Mermaid 拓扑图在 markdown 中的渲染效果，确认无死链或格式崩溃
