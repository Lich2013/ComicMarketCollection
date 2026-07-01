## ADDED Requirements

### Requirement: 题材分类粒度归一化 (Super-Genre Normalization)
系统在执行多期联合分析时，MUST 将 Comiket 与 Comicup 的题材分类映射为 10 大统一的超级题材 (Super-Genres)，并在报告中展现二者在此对齐维度下的 CR5 和 CR10 集中度对比，以消除原始分类粒度不对齐带来的集中度比较偏差。

#### Scenario: 成功生成超级题材对齐的集中度对比数据
- **WHEN** 运行 `--analyze-multi-era` 参数生成对比报告时
- **THEN** 报告的“集中度结构”章节中 MUST 包含对齐后的 Super-CR5 与 Super-CR10 比较，揭示 Comiket 题材的多样化分布以及 Comicup 在“动漫”与“手游”上的双头高度垄断结构。

### Requirement: DBI 基线敏感度分析 (Sensitivity Analysis)
系统设计的大众受众热度基线方法论报告中，MUST 补充关于基线扰动敏感性的定量测试结果，说明参数在不同扰动级别（±10%, ±20%, ±30%）下边界题材分类结果的翻转率与鲁棒性。

#### Scenario: 方法论文档包含敏感度分析表
- **WHEN** 查阅 `research/audience_baseline_methodology.md` 时
- **THEN** 文档中 MUST 包含一个扰动敏感性表格，列明不同扰动等级下的翻转社团比例与具体的边界 volatile 题材（如 VTuber、男性向等）警戒提示。

### Requirement: 卡方检验效应量计算 (Cramér's V Calculation)
卡方检验复现脚本 `research/scripts/chi_square_test.py` MUST 自动计算并输出 Cramér's V 效应量，同时在社交媒体采纳报告中补充相关效应量的分析，以论证大样本下的统计关联强弱。

#### Scenario: 运行卡方检验脚本输出效应量
- **WHEN** 运行卡方检验复现命令时
- **THEN** 控制台输出除卡方值和 p 值外，MUST 包含计算得出的 Cramér's V 效应量值（约为 0.3056），并提示其处于“强关联区间”。

### Requirement: 规范学术词汇与因果假设去包装
各篇研究报告在论及非直接数据支撑的观点时，MUST 将礼物经济的“稳定性”修正为“初步一致性”，将排球少年的供求失衡修正为“生产时滞与供给响应时延假说”，且将对具体题材 DBI 高低的因果归因（如版权限制、角色设计留白）明确标识为“推测性解释”。

#### Scenario: 校验报告用词符合局限性声明
- **WHEN** 查阅多期联合对比报告或各单篇研究报告时
- **THEN** 报告中对二创机制成因的论断 MUST 明确使用“推测性归因”或“可能解释”等限制词，且无料礼物的论述中 MUST 剔除“稳定性证明”词汇，代之以“初步一致性观察”。

### Requirement: Comiket 描述文本小说提及率实证支撑
系统在进行中日“文画平权”对比时，MUST 通过在 Comiket description 字段进行关键词（小説、ライトノベル）匹配的方式，获得 Comiket 小说提及率的实证占比（约为 5.4%），用于与 Comicup 的小说比例进行同口径对比。

#### Scenario: 联合报告中引用 Comiket 侧小说实证提及率
- **WHEN** 执行分析并生成多展期对比研究报告时
- **THEN** 报告关于“媒介载体”的横向对比段落中 MUST 包含 Comiket 侧描述文本中提取出的小说社团提及率数值，用数据而非纯断言支撑跨国对比。
