import math
from src.spatial_mapper import get_booth_coords

def calculate_distance(p1: tuple[float, float], p2: tuple[float, float]) -> float:
    return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)

def get_edge_weight(d: float, same_block: bool) -> float:
    """
    根据二维物理距离和排布类型确定边权重
    - d <= 1.1: 紧邻 (同一排的左右紧邻或背靠背)
    - 1.1 < d <= 2.2: 中邻 (跨通道面对面或斜对角邻居)
    - 2.2 < d <= 3.5: 远邻 (同区域内较远的展位)
    """
    if d > 3.5:
        return 0.0
    
    if d <= 1.1:
        return 1.0 if same_block else 0.8
    elif d <= 2.2:
        return 0.7 if same_block else 0.6
    else:
        return 0.5 if same_block else 0.4

def build_spatial_graph(circles: list[dict]) -> dict[int, list[tuple[int, float]]]:
    """
    为社团列表构建加权无向图邻接表。
    只有在同一天和同一个场馆 (day, hall) 的社团才在图网络中可能连通。
    返回: dict, circle_id -> list of (neighbor_circle_id, weight)
    """
    # 1. 按照 (day, hall) 分组以缩减计算量并保证空间物理隔离
    groups = {}
    for c in circles:
        key = (c.get("day"), c.get("hall"))
        if key not in groups:
            groups[key] = []
        groups[key].append(c)
        
    # 计算每个社团的二维坐标并缓存
    coords = {}
    for c in circles:
        cid = c["id"]
        coords[cid] = get_booth_coords(c.get("hall"), c.get("block"), c.get("space"))
        
    adjacency_list = {c["id"]: [] for c in circles}
    
    # 2. 在每个独立空间组内计算两两之间的物理距离并连边
    for key, group_circles in groups.items():
        n = len(group_circles)
        for i in range(n):
            c1 = group_circles[i]
            cid1 = c1["id"]
            coord1 = coords[cid1]
            block1 = c1.get("block")
            
            for j in range(i + 1, n):
                c2 = group_circles[j]
                cid2 = c2["id"]
                coord2 = coords[cid2]
                block2 = c2.get("block")
                
                # 计算欧氏物理距离
                d = calculate_distance(coord1, coord2)
                if d <= 3.5:
                    same_block = (block1 == block2)
                    weight = get_edge_weight(d, same_block)
                    if weight > 0:
                        adjacency_list[cid1].append((cid2, weight))
                        adjacency_list[cid2].append((cid1, weight))
                        
    return adjacency_list
