## 1. 基础计算引擎设计与实现 (src/multi_era_analyzer.py)

- [x] 1.1 实现 Comiket (C107/C108) 的数据读取与大盘规模统计方法（社团数、大类题材排行及占比）
- [x] 1.2 实现 Comicup (CPSP/CP31) 的数据清洗与过滤逻辑，支持在统计 CPSP 时排除 `['色纸', '纸胶带']` 类型的平面周边，并计算大盘基础指标
- [x] 1.3 实现题材集中度 ($CR_5$ 与 $CR_{10}$) 计算及 Bain 市场结构判定逻辑（支持四展的统一计算）
- [x] 1.4 实现 CPSP 与 CP31 基于 `hotCount` 的意愿供需偏离度 (Real-time DBI) 排序与计算
- [x] 1.5 提取无料、合志、再录、突发等特殊属性的占比分析方法
- [x] 1.6 实现 Comiket 的 Global Moran's I 空间自相关计算逻辑 (同一 hall/block, space 差 <= 3)
- [x] 1.7 实现 Comicup 的 Global Moran's I 空间自相关计算逻辑 (同一 position_name)
- [x] 1.8 编写统一的主计算流，输出结构化数据用于报告渲染

## 2. 学术研究报告自动生成

- [x] 2.1 设计学术报告渲染模版，包含日本本土时序对比（C107 vs C108）、中国本土时序对比（CPSP vs CP31）以及中日横向倾向性深度比对（组织逻辑、创作倾向、集中度、流通通路、礼物经济）
- [x] 2.2 实现 `generate_multi_era_report(stats, output_path)` 函数，将多展期计算结果格式化输出为 `research/comiket_vs_comicup_multi_era_study.md` 研究报告，并在其中嵌入相关的 Mermaid 流程图（包含两栖流通漏斗、双日题材调度对比等）

## 3. 命令行接口扩展与单元测试

- [x] 3.1 修改 `main.py`，新增 `--analyze-multi-era` 参数，并在解析该参数时调用联合计算引擎及报告生成流水线
- [x] 3.2 在 `tests/` 下编写针对多展期计算引擎的单元测试，并在 `data/test_comic_market.db` 中进行测试数据隔离与清理，防止污染生产库
- [x] 3.3 运行单元测试并运行完整命令行参数测试，验证报告是否正确写入 `research/comiket_vs_comicup_multi_era_study.md`
