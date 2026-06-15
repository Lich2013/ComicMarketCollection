## ADDED Requirements

### Requirement: 统一整合双城对比研究报告
系统在执行多期联合分析时，MUST 在生成的 `research/comiket_vs_comicup_multi_era_study.md` 报告中，包含静态论证背景（选用 CP31 而非 CP32 的基准说明）与中日数据映射对照表，并在成功生成报告后，自动删除 `research/comiket_vs_comicup.md` 和 `research/comiket_vs_comicup_comparison.md` 文件。

#### Scenario: 成功生成整合报告并清理冗余文件
- **WHEN** 执行 `--analyze-multi-era` 参数触发计算分析时
- **THEN** 系统动态生成完整的包含引言、方法论、时序对比、倾向性对比及结论的学术报告，同时物理删除冗余文档 `research/comiket_vs_comicup.md` 和 `research/comiket_vs_comicup_comparison.md`
