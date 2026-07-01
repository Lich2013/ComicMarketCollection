## 1. 物理网格配置与坐标映射模块

- [x] 1.1 创建展位物理网格布局配置文件 `data/layout_grid_c108.json`，定义东、西、南馆主要排（Block）的 X 轴基准线坐标与长度。
- [x] 1.2 新建空间坐标解析器 `src/spatial_mapper.py`，实现 `get_booth_coords(hall, block, space)`，支持提取 space 编号数字作为 Y 坐标以及利用 a/b 面代表的背靠背 X 轴对称偏移。

## 2. 图拓扑网络与多标签 LPA 迭代传播

- [x] 2.1 新建图网络构建模块 `src/graph_builder.py`，实现基于二维欧氏距离阈值（如 $d \le 3.5$ 米）连接相邻节点，并根据左右、背靠背、跨过道赋予不同边权重。
- [x] 2.2 新建标签传播迭代模块 `src/label_propagator.py`，将打标标签结构向量化（多标签），实现基于归一化度矩阵和阻尼系数 $\alpha$（如 0.6）的半监督 LPA 迭代运算。
- [x] 2.3 重构打标流水线 `src/circle_tagger.py`，将第一步与第二步提取的关键字和商品种子整合为初始向量 $Y$，调用二维 LPA 替换原有的一维滑动窗口和纯度校验，将大于设定概率阈值（如 0.3）的 IP 以多标签形式持久化到 `circle_ip_tags`。

## 3. 最优二维逛展路线生成

- [x] 3.1 新建物理路径规划模块 `src/route_solver.py`，设计贪心最近邻（Greedy Nearest Neighbor）算法，输入展厅入口坐标与打标社团列表，解算出一条最短欧氏几何逛展链条。
- [x] 3.2 重构命令行入口 `main.py` 中的 `--search-ip <ip_name>` 逻辑，调用二维物理路径规划器，对检索到的展位按照最优逛展链条排序输出。

## 4. 验证与单元测试

- [x] 4.1 新增单元测试 `tests/test_spatial_lpa.py`，模拟包含过道、背靠背和长空位等特例展位物理布局，验证 2D-LPA 在边缘纯度、多标签混合和最近邻路径规划上的算法鲁棒性与幂等。
- [x] 4.2 运行项目全部 pytest 套件并手动测试 `main.py --tag-circles` 及 `--search-ip "明日方舟"` 检验输出的可用性。
