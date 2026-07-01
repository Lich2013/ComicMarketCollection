## Why

针对当前一维线性滑动窗口打标模型在展会真实场景下的核心物理限制（例如无法感知隔通道/背靠背物理邻域的种子、无法在长空白区域内衰减传播、对弱势二创 IP 存在“绝育”效应以及不支持多 IP 百货摊标签），本项目拟升级现有的打标与检索体系，通过引入二维欧式展位坐标映射、带阻尼衰减的多标签半监督标签传播算法（2D-LPA），以及最近邻二维最优化路径规划，全面提高打标召回率、多标签精度以及逛展路线的物理实用价值。

## What Changes

- **二维展馆几何化映射**：为所有社团展位基于其日期、展馆、排和空间号映射为统一的 $(X, Y)$ 二维物理坐标。
- **空间图网格（Adjacency Graph）构建**：采用 $k$-最近邻（$k$-NN）或半径阈值法自动将物理上左右相邻、背靠背、跨过道面对面的展位连接成带权重的无向边。
- **带衰减的多标签 LPA 打标**：将单一字符串标签升级为多维概率向量（支持复合 IP），允许 0.8 的标签按阻尼系数（Damping Factor）向外迭代传播，打破硬性阈值断流。
- **二维空间最优化逛展路线**：废除按 Block 字母升序的简单排序，引入二维物理坐标及贪心最近邻算法串联路径，生成顺路无折返的逛展物理路线。

## Capabilities

### New Capabilities
- `spatial-lpa-tagging`: 基于展位二维物理坐标构图的带衰减多标签半监督标签传播打标能力。
- `optimal-booth-routing`: 基于二维空间欧氏几何的最优逛展物理路线生成与规划能力。

### Modified Capabilities
<!-- No modified capabilities needed as this introduces new core algorithms and route solver -->

## Impact

- **物理位置解析模块**：新增 `src/spatial_mapper.py` 用于摊位坐标映射。
- **图网格拓扑与传播算法**：新增 `src/graph_builder.py` 与 `src/label_propagator.py` 负责 LPA 构图和迭代运算。
- **自动打标流水线**：重构 `src/circle_tagger.py`，调用新的 LPA 二维传播模块替换原有的一维滑动窗口和纯度校验。
- **物理路线检索模块**：重构 `main.py` 中的 `--search-ip` 逻辑，使用 TSP/最近邻路线规划器重新排列路线图输出。
