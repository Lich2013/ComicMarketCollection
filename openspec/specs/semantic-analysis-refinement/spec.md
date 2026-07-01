# semantic-analysis-refinement Specification

## Purpose
TBD - created by archiving change refine-semantic-description. Update Purpose after archive.
## Requirements
### Requirement: 日语分词与 TF-IDF 特征词排序 (Japanese Tokenization & TF-IDF Extraction)
系统在生成文本分析报告或执行语义分析时，MUST 引入 `sudachipy` 并配置为 Split Mode C（以完整合并复合词），对 C108 与 C107 的社团简介文本进行分词与过滤。系统 SHALL 对名词、动词、形容词计算其全局 IDF 权重，并按文档频率排序，筛选出 8 大主力题材下平均 TF-IDF 权重前 8 名的核心特异性特征词（过滤停用词与数值）。

#### Scenario: 成功计算并排序 TF-IDF 特征词
- **WHEN** 执行简介文本计量分析并生成报告时
- **THEN** 系统能够为不同题材提取出其最具代表性的垂直特征词（例如东方 Project 的 `アレンジ` 与 `cd`；Cosplay 区的 `rom` 与 `グラビア`；评论情报区的 `レシピ`；铁道区的 `旅行記`），并且全局高频词（`イラスト`、`新刊`）的权重被合理拉低。

### Requirement: 精准 IP 角色提及量化与清洗 (Character Mentions & Regex Cleaning)
系统在统计主力题材（如《碧蓝档案》、《东方Project》、VTuber、偶像大师、赛马娘等）的角色提及情况时，MUST 使用排除性的正则表达式，清洗并纠正子串匹配带来的假阳性统计噪音。

#### Scenario: 角色词频统计成功排除干扰
- **WHEN** 统计《碧蓝档案》题材下阿露 (アル) 角色提及率时
- **THEN** 阿露的提及数能够成功排除 `アクリル` (亚克力) 和 `オリジナル` (原创) 的假阳性干扰，使统计频次处于真实的角色提及区间内。

### Requirement: 题材填写率与引流行为分析 (Fill Rates & Social Redirection)
系统 MUST 分题材统计 C108 简介填写率，并对简介填写状态（有简介 vs 无简介）与社团的原生 Twitter/Pixiv 账号绑定率进行交叉统计，量化引流活跃度与宣发意愿的关联性。

#### Scenario: 填写率与社媒绑定交叉统计成功
- **WHEN** 进行大盘简介覆盖率统计时
- **THEN** 系统能够输出不同题材的填写率差异排行（例如硬核考据题材 70%+ vs 动漫游戏/Cosplay 50%+），且输出结果表明有简介社团的 Twitter 绑定率明显高于无简介社团。

### Requirement: 卡方独立性检验与效应量测算 (Chi-Square & Cramér's V)
系统在分析题材大类与受众内容消费标签（R18分级、周边Goods、小说Novel）的绑定关系时，MUST 构建交叉列联表，并执行卡方独立性检验（Chi-Square Test），同时动态计算并输出 Cramér's V 效应量以度量现实关联强度。

#### Scenario: 卡方检验与效应量输出
- **WHEN** 对题材与内容标签进行独立性原假设检验时
- **THEN** 系统能够正确计算并输出卡方统计量、自由度、p值以及 Cramér's V 效应量，并自动根据效应量强度给出学术性强弱关联判定。

### Requirement: C107 vs C108 纵向时序漂移计算 (Longitudinal Text Drift)
系统 MUST 对 C107 与 C108 的有简介社团词频进行大盘比例级双期比对，计算其时序波动差异，以科学评估同人生态在大盘指标上的平稳性。

#### Scenario: 时序漂移验证大盘平稳性
- **WHEN** 比对冬夏两期核心关键词占比时
- **THEN** 报告中能够准确显示各项核心主题词（插画、周边、小说、R18、新刊等）的占比差异低于 $\pm 0.5\%$。

