## ADDED Requirements

### Requirement: 自动生成多展期双城对比研究报告
系统必须根据计算出的多展期联合指标，在 `research/` 目录下动态生成正式报告 `research/comiket_vs_comicup_multi_era_study.md`。
该报告必须包含以下核心章节：
1. **日本本土对比**：C107 与 C108 规模、大类题材排布、$CR_{10}$ 集中度以及空间莫兰自相关等时序稳定性分析。
2. **中国本土对比**：CPSP 与 CP31 在周边清洗过滤后的书刊级大盘比对、心愿单 Real-time DBI（阐述供需时滞与经济学蛛网效应）、无料占比（验证礼物经济的常量稳定性）以及双日/空间微观主题街区隔离效能比对。
3. **中日横向倾向性对比**：
   - 组织逻辑对比（Demographics 受众市集 vs. IP 叙事主题专区）。
   - 创作倾向性对比（Pixiv 驱动的视觉画师文化 vs. 网文 LOFTER 驱动的“文笔画笔平权”女性向同人小说文化）。
   - 集中度对比（Comiket 中度寡占型 vs. Comicup 极长尾超去中心化）。
   - 流通形式对比（现场即时物理结清 vs. 数字 App 两栖预约核销）。
   - 社交资本对比（商业合同买卖交易 vs. “无料物理交换”非商业互惠 Gifts 经济）。

#### Scenario: 成功写入中日多期对比报告
- **WHEN** 多期统计分析完成后触发报告生成时
- **THEN** 系统自动在 `research/comiket_vs_comicup_multi_era_study.md` 中输出格式排版规范、包含洗牌后指标比对及 Mermaid 流程图的深度学术研究报告
