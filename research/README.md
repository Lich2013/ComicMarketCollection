# Comic Market 数据分析与研究中心 (Research Hub)

本目录用于存放关于 Comic Market 收集数据的多维度数据分析与规格设计研究。我们通过对社团元数据、推文品书信息以及提取出来的制品数据进行建模与挖掘，提炼展会的深度洞察。

## 研究课题索引

### 1. [题材与类型分布分析 (Genre & Theme Distribution)](file:///Users/lich/work/comicMarketCollection/research/genre_distribution.md)
* **目标**：挖掘 Comiket 在不同日期（Day1/Day2）、不同场馆的题材分布格局。
* **主要指标**：题材热度排行、跨馆题材流向、时空分布矩阵。
* **数据基线说明**：[Comic Market 大众受众热度基线估算说明书](file:///Users/lich/work/comicMarketCollection/research/audience_baseline_methodology.md)（说明了同人偏离度指数 DBI 计算所使用的大盘受众热度分母数据来源与校准方法）。

### 2. [社交媒体与平台采纳率分析 (Social Media & Platform Adoption)](file:///Users/lich/work/comicMarketCollection/research/social_media_adoption.md)
* **目标**：分析创作者对 Twitter (X) 和 Pixiv 等主流网络平台的采纳率与偏好差异。
* **主要指标**：X 绑定率、Pixiv 覆盖率、不同题材（Genre）的平台偏好交叉分析、社交影响力气泡图数据源。

### 3. [展位排布与物理密度分析 (Booth Spatial & Density Analysis)](file:///Users/lich/work/comicMarketCollection/research/booth_density.md)
* **目标**：基于场馆地理坐标和展位号（Hall, Block, Space），分析社团的物理排布特征。
* **主要指标**：壁圈（壁サークル）大盘识别、题材空间聚集度指数（同人街纯度）、步行路线热图规划。

### 4. [社团简介文本计量与特征提取报告 (Circle Descriptions Semantic Metrics)](file:///Users/lich/work/comicMarketCollection/research/semantic_description.md)
* **目标**：利用 SudachiPy (SplitMode.C) 日语分词与分题材 TF-IDF 特征提取，深度分析本届 Comiket 创作者简介中的核心主题与特定 IP 明星角色提及度，并通过卡方独立性检验量化题材与内容倾向的相关性。
* **主要指标**：分题材 TF-IDF 特征词、IP 角色提及正则洗白率（排除子串干扰）、简介填写率与社交媒体绑定率交叉分析、题材与内容标签（R18、周边、小说）的卡方独立性检验（Cramér's V 效应量）及 C107 vs C108 时序纵向漂移。

### 5. [中日双城同人集聚与创作生态多展期对比研究报告 (Comiket vs. Comicup Multi-Era Comparative Study)](file:///Users/lich/work/comicMarketCollection/research/comiket_vs_comicup_multi_era_study.md)
* **目标**：对比日本 Comiket（C107 vs C108）与中国 Comicup（CPSP vs CP31）在清洗周边干扰后的宏观与微观创作生态的时序与倾向性演进。
* **主要指标**：大盘规模、市场集中度（CR5/CR10）、媒介类型分布（小说/漫画占比）、特殊属性（无料礼物经济占比）、心愿单供需偏离度（SDI）以及展位专区莫兰指数（Moran's I）。

---

## 二、 运行与分析规格

各子研究文件内定义了相应的**分析规格 (Specification)**、可执行的 **Python 复现脚本** 及独立 **SQL 查询文件**。这些设计将作为未来实现可视化大屏、分析导出脚本或研究报告的参考规格。

*   卡方独立性检验复现命令：
    ```bash
    uv run --with pandas --with scipy python research/scripts/chi_square_test.py
    ```
*   莫兰指数空间自相关复现命令：
    ```bash
    uv run python research/scripts/moran_i_calculator.py
    ```
*   中日双城多展期对比分析与报告生成复现命令：
    ```bash
    PYTHONPATH=. uv run python main.py --analyze-multi-era
    ```

---

## 三、 数据可视化设计蓝图与一句话核心结论 (Visualization Blueprints & Takeaways)

为降低非技术读者的阅读门槛，本研究中心规划了以下五套数据大屏/图表可视化方案（⚠️ **注：所有可视化图表目前处于规划开发中，此处仅作为设计蓝图与规范定义**），并提取了各报告的一句话核心研究发现：

### 1. 题材分布与 DBI 偏离度大屏 (Genre & DBI Bubble Chart)
*   **一句话核心结论**：**《碧蓝档案》是本届 Comiket 绝对的二创人气之王（同人偏离度 DBI 为 1.91，远超受众声量），而《赛马娘》虽讨论度极高但受官方二创规制限制，创作热度意外遇冷（DBI 仅 0.58）。**
*   **可视化方案**：
    *   **散点气泡图**：横坐标为大众受众大盘比例 ($P_g$)，纵坐标为同人偏离度 ($DBI$)。气泡大小代表 Comiket 实际注册社团数 ($C_g$)。
    *   **象限划分**：
        *   第一象限（双高明星区）：碧蓝档案、男性向（高大众声量，极强二创供给）。
        *   第二象限（垂直硬核区）：评论情报、铁道军事（大众极小众，但圈内创作者拥有爆表偏向度）。
        *   第四象限（偏消费规制区）：赛马娘、网络手游、VTuber（受众规模庞大，但二创转化比例偏低）。

### 2. 创作者社交媒体采纳维恩图 (Social Media Adoption Venn Diagram)
*   **一句话核心结论**：**Comiket 创作者高度依赖社交网络（整体绑定率超 80%），但平台偏好因题材形态发生极端分化，Cosplay 圈几乎 100% 极化于 Twitter (X) 而彻底抛弃了 Pixiv。**
*   **可视化方案**：
    *   **三环维恩图 (Venn Diagram)**：展示 $Circles_{\text{Total}}$，$Circles_{\text{Twitter}}$ 与 $Circles_{\text{Pixiv}}$ 的交集比例（47.66% 双向绑定）。
    *   **题材侧向对比堆叠条形图**：展示不同题材（如 Cosplay、插画、评论情报）中 `Both` / `X_Only` / `Pixiv_Only` / `None` 四种状态的相对占比，直观呈现不同题材的传播媒介差异。

### 3. 展位排布与物理流动热力图 (Booth Spatial & Density Heatmap)
*   **一句话核心结论**：**Comiket 摊位分配具有极强的“空间连排高度聚焦”特征，蓝闪、男性向等形成纯度达 100% 的超级街区，构成局部巨大的人流拥堵阻尼。**
*   **可视化方案**：
    *   **二维展馆平面热力图**：根据 Big Sight 东、西、南馆平面图纸建立网格，将每 2.0m x 2.0m 网格内同一题材的社团密集度进行彩色渲染（从冷色蓝到暖色红）。
    *   **排队阻尼节点标记**：对 `IsWall`（壁圈）摊位标以闪烁图标，代表高时空队列等待代价，在导航中指示动态避让。

### 4. 简介文本高频关键词云 (Description Word Cloud)
*   **一句话核心结论**：**同人市场是典型的“新刊（新发表书籍）”与“精美视觉制品（插画与挂件周边）”双轮驱动的即时消费生态。**
*   **可视化方案**：
    *   **分色词云图**：以 TF-IDF 权重渲染词语大小，剔除噪音。“イラスト (插画)”与“既刊”/“新刊”使用暖色系，“グッズ (周边)”与“アクリル (亚克力)”使用冷色系，直观展示创作者出摊时的主要贩售产品类型分布。

### 5. 中日双城同人生态倾向性对比图谱 (Comiket vs. Comicup Multi-Era Comparative Chart)
*   **一句话核心结论**：**Comiket 属于高度集中的“古典契约范式”（CR10达61%），物理现场现金结清；而 Comicup 则展现出“两栖长尾去中心化范式”（CR10仅30%），由心愿单 O2O 预约核销与无料礼物经济互惠所驱动。**
*   **可视化方案**：
    *   **中日特性雷达图**：展示中日展会在五个核心轴度上的对比（集中度 CR10、小说/文本占比、无料/礼物经济占比、O2O预约率、双日题材重合度）。
    *   **供需偏离蛛网对比图**：横轴展示主力题材，纵轴展示 SDI 偏离度（中日偏离度统计口径对比差异详见多期对比报告附录）。直观表达《排球少年》等热门 IP 在中国 Comicup 展会的供需变化特征与生产时滞。
