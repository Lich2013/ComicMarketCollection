## Why

系统已扩充了日本 C107（2025.12）和中国 CPSP（2025.10）历史数据。为了最大化挖掘跨展期同人生态演进规律，系统需要构建一个多展期联合分析引擎，通过纵向时序演变与横向中日倾向性对比，生成高学术严谨性的双城同人集聚研究报告。

## What Changes

- **多展期联合计算引擎**：新建 `src/multi_era_analyzer.py`，实现四大展期大盘规模、排名前十题材分布、集中度（$CR_5$/$CR_{10}$）、CPSP/CP31 意愿供需（Real-time DBI，其中 CPSP 自动排除低成本平面周边纸胶带及色纸的干扰）以及 Global Moran's I 空间自相关指数的时序联合计算。
- **研究报告自动生成**：自动在 `research/` 目录下生成深度学术报告 `research/comiket_vs_comicup_multi_era_study.md`，并在报告中完整阐述日本本土对比（C107 vs C108）、中国本土对比（CPSP vs CP31）以及中日横向倾向性对比（组织逻辑、性别受众、流通O2O与礼物经济交换）。
- **命令行工具参数扩充**：在 `main.py` 中新增 `--analyze-multi-era` 参数，一键触发计算与报告输出。
- **单元测试保障**：编写对应的单元测试，验证各量化指标联合计算的准确性。

## Capabilities

### New Capabilities
- `multi-era-comparative-analysis`: 联合 C107、C108、CPSP、CP31 核心媒介数据进行规模、题材、集中度、供需偏离度与空间自相关的联合分析。
- `multi-era-comparison-report`: 自动将多展期计算指标及 Mermaid 流程图结构化输出至研究报告中。

### Modified Capabilities
<!-- 空 -->

## Impact

* **分析与文档 (`research/`)**：在 `research/` 目录下新增 `comiket_vs_comicup_multi_era_study.md` 多期对比研究报告。
* **命令行接口 (`main.py`)**：新增 `--analyze-multi-era` 参数用于触发该联合分析流水线。
