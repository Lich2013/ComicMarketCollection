import math
from src.spatial_mapper import get_booth_coords

def get_hall_entrance(hall: str) -> tuple[float, float]:
    """获取场馆主入口坐标，用作最近邻路径规划的起始锚点，默认 (0.0, 0.0)"""
    hall_str = str(hall or "")
    if "東" in hall_str:
        return (50.0, 0.0)
    elif "西" in hall_str:
        return (40.0, 0.0)
    elif "南" in hall_str:
        return (45.0, 0.0)
    return (0.0, 0.0)

def calculate_distance(p1: tuple[float, float], p2: tuple[float, float]) -> float:
    return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)

def solve_greedy_route(circles: list[dict]) -> list[dict]:
    """
    对社团数据进行最近邻 (Nearest Neighbor) 二维物理路径解算。
    1. 按 (day, hall) 大维度进行分组并拓扑排序 (如土曜日 -> 日曜日)。
    2. 在每个独立的天数-场馆内，从大门入口出发，贪心选择距离当前点最近的未访问展位。
    """
    if not circles:
        return []
        
    # 1. 按照 (day, hall) 大维度进行合理分组
    groups = {}
    for c in circles:
        key = (c.get("day"), c.get("hall"))
        if key not in groups:
            groups[key] = []
        groups[key].append(c)
        
    # 宏观参展日程排序: 土 (Day1) -> 日 (Day2) -> 其它
    def day_hall_sort_key(k):
        day_str = str(k[0] or "")
        hall_str = str(k[1] or "")
        day_rank = 1 if "土" in day_str else 2 if "日" in day_str else 3
        return (day_rank, hall_str)
        
    sorted_keys = sorted(groups.keys(), key=day_hall_sort_key)
    optimized_circles = []
    
    # 2. 在每一天每一馆中，使用 Nearest Neighbor 贪心算法排线
    for key in sorted_keys:
        day, hall = key
        group_circles = list(groups[key])
        
        # 缓存每个社团的二维几何坐标
        coords = {}
        for idx, c in enumerate(group_circles):
            coords[idx] = get_booth_coords(c.get("hall"), c.get("block"), c.get("space"))
            
        current_pos = get_hall_entrance(hall)
        unvisited = [(idx, c) for idx, c in enumerate(group_circles)]
        
        while unvisited:
            best_idx_in_unvisited = 0
            best_dist = float("inf")
            
            for index, (orig_idx, c) in enumerate(unvisited):
                c_coord = coords[orig_idx]
                d = calculate_distance(current_pos, c_coord)
                if d < best_dist:
                    best_dist = d
                    best_idx_in_unvisited = index
                    
            # 抽出该社团并更新当前坐标
            orig_idx, next_c = unvisited.pop(best_idx_in_unvisited)
            optimized_circles.append(next_c)
            current_pos = coords[orig_idx]
            
    return optimized_circles
