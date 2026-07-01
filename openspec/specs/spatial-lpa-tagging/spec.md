# spatial-lpa-tagging Specification

## Purpose
TBD - created by archiving change spatial-lpa-upgrade. Update Purpose after archive.
## Requirements
### Requirement: 展馆摊位物理坐标映射与加权图拓扑构建 (MUST)
系统必须 (MUST) 建立一个能够解析展馆摊位号并映射为二维物理坐标 $(X, Y)$ 的物理模型。
系统必须 (MUST) 基于展位物理间距（如设定半径阈值 $R_{threshold} = 3.5$ 米）构建社团邻接图，自动将同一排相邻、背靠背以及跨通道对面排布的相邻展位连接成无向边，并根据连接类型赋予不同的边权重。

#### Scenario: 展位二维坐标映射与拓扑建图
- **WHEN** 执行自动打标流水线初始化阶段
- **THEN** 数据库中的所有 C108 摊位均被自动映射为绝对物理坐标，并在内存中构建出以社团为节点、物理相邻边为带权重边的邻接拓扑图。

### Requirement: 带阻尼衰减的多标签半监督标签传播 (MUST)
系统必须 (MUST) 实现连续多标签 LPA 传播模型，将社团的 IP 标记由单一字符串转为多维概率向量（如 `[p_方舟, p_星铁, p_其他]`）。
系统必须 (MUST) 以固定的阻尼系数 $\alpha \in [0.5, 0.7]$ 进行半监督标签迭代传播，在保证原始种子（置信度 1.0）概率锚定不变的前提下，使 IP 概率向外衰减传递。
系统必须 (MUST) 过滤出概率大于设定阈值（如 $p \ge 0.3$）的 IP 标签并将其以多标签形式保存到 `circle_ip_tags` 表中。

#### Scenario: 标签迭代传播与多标签过滤保存
- **WHEN** 运行图打标推理算法
- **THEN** 算法根据二维图的边权重完成 3-5 次的标签迭代扩散，并在遇到长空白带或异种 IP 交叉带时自动阻尼衰减，最终过滤输出多个概率及格的 IP 并写入数据库。

