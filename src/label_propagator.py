def run_label_propagation(
    adjacency_list: dict[int, list[tuple[int, float]]],
    seeds: dict[int, dict[str, float]],
    all_circle_ids: list[int],
    alpha: float = 0.6,
    max_iter: int = 5
) -> dict[int, dict[str, float]]:
    """
    运行基于图拓扑的带阻尼多标签半监督传播算法。
    参数:
    - adjacency_list: 图邻接表，circle_id -> list of (neighbor_id, weight)
    - seeds: 种子节点打标，circle_id -> dict of (ip_label -> confidence)
    - all_circle_ids: 全部节点 ID 列表
    - alpha: 阻尼衰减系数
    - max_iter: 最大迭代步数
    返回:
    - propagated_tags: circle_id -> dict of (ip_label -> probability)
    """
    # 1. 收集所有唯一的 IP 标签，建立标签索引
    unique_labels = set()
    for s_tags in seeds.values():
        unique_labels.update(s_tags.keys())
        
    if not unique_labels:
        return {}
        
    labels = sorted(list(unique_labels))
    label_to_idx = {lbl: idx for idx, lbl in enumerate(labels)}
    m = len(labels)
    
    # 2. 初始化概率分布矩阵 F 和种子矩阵 Y
    F = {}
    Y = {}
    for cid in all_circle_ids:
        F[cid] = [0.0] * m
        Y[cid] = [0.0] * m
        
    for cid, tags in seeds.items():
        if cid in Y:
            for ip, conf in tags.items():
                idx = label_to_idx[ip]
                # 初始种子概率设置为置信度 (1.0)
                Y[cid][idx] = float(conf)
                F[cid][idx] = float(conf)
                
    # 3. 计算每个节点的邻边总度数以供归一化
    degrees = {}
    for cid in all_circle_ids:
        neighbors = adjacency_list.get(cid, [])
        degrees[cid] = sum(weight for _, weight in neighbors)
        
    # 4. 迭代标签传播
    for _ in range(max_iter):
        F_new = {}
        for cid in all_circle_ids:
            deg = degrees[cid]
            if deg > 0:
                # 收集邻居概率分布的归一化加权贡献
                temp_vec = [0.0] * m
                for nb_id, weight in adjacency_list.get(cid, []):
                    nb_vec = F[nb_id]
                    for idx in range(m):
                        temp_vec[idx] += (weight / deg) * nb_vec[idx]
                F_new[cid] = temp_vec
            else:
                F_new[cid] = [0.0] * m
                
        # 应用阻尼更新并对种子节点进行锚定复位
        for cid in all_circle_ids:
            is_seed = (cid in seeds)
            if is_seed:
                # 种子节点保持最初火种概率 (1.0) 恒定不变，起约束作用
                F[cid] = list(Y[cid])
            else:
                # 未知节点融合同步过来的邻接概率与初始零分布
                F[cid] = [
                    alpha * F_new[cid][idx] + (1.0 - alpha) * Y[cid][idx]
                    for idx in range(m)
                ]
                
    # 5. 导出非零概率的标签结果
    propagated_tags = {}
    for cid in all_circle_ids:
        c_tags = {}
        for idx, lbl in enumerate(labels):
            prob = F[cid][idx]
            if prob > 0.0:
                c_tags[lbl] = float(prob)
        if c_tags:
            propagated_tags[cid] = c_tags
            
    return propagated_tags
