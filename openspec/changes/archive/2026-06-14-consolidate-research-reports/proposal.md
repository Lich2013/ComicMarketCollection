## Why

当前在 `research/` 目录下散落着三份与 Comiket 和 Comicup 对比相关的文档（`comiket_vs_comicup.md` 映射规范、`comiket_vs_comicup_comparison.md` 单期报告、`comiket_vs_comicup_multi_era_study.md` 多期报告）。这导致了严重的内容重叠（多期报告已覆盖单期报告的全部指标）与定位混淆。

为了提升研究成果的整合度、学术严谨性，以及保持 `research/` 目录的整洁，我们需要将这三份文档合并成一篇统一、自洽且具备完整方法论（包含数据选取逻辑与映射规格表）的多展期双城对比研究报告，并清理多余的过渡性文件。

## What Changes

* **报告内容合并与重组**：更新多期研究报告生成模板，将 `comiket_vs_comicup.md` 中静态的“研究基准与数据选取说明”、“数据集对应与映射规格表”合并进动态生成的 `research/comiket_vs_comicup_multi_era_study.md` 中。
* **清理冗余历史文档**：在分析任务执行后，自动清理/删除已被完全覆盖的 `research/comiket_vs_comicup.md` 和 `research/comiket_vs_comicup_comparison.md` 文件。
* **计算逻辑微调**：对 `src/multi_era_analyzer.py` 的报告渲染模块进行升级，支持包含上述静态学术背景及映射对照表。

## Capabilities

### New Capabilities
- `research-report-consolidation`: 统一整合双城同人生态时序对比报告，清理冗余规格与单期报告。

### Modified Capabilities
<!-- 空 -->

## Impact

* **分析与文档 (`research/`)**：`research/comiket_vs_comicup_multi_era_study.md` 成为唯一的双城同人对比研究成果，其余两份冗余文档被清理。
* **计算模块 (`src/multi_era_analyzer.py`)**：修改 `generate_multi_era_report` 函数模板，合入静态科学论证背景与映射规格表。
