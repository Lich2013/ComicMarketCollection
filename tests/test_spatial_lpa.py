import pytest
from src.spatial_mapper import get_booth_coords
from src.graph_builder import build_spatial_graph, calculate_distance
from src.label_propagator import run_label_propagation
from src.route_solver import solve_greedy_route, get_hall_entrance

def test_spatial_coords_mapping():
    # 1. 正常网格映射验证
    # data/layout_grid_c108.json 中定義了 東馆 Ｈ X=35.0
    # a面偏移 -0.5, b面偏移 +0.5
    coord_12a = get_booth_coords("東", "Ｈ", "12a")
    assert coord_12a == (34.5, 18.0)
    
    coord_12b = get_booth_coords("東", "Ｈ", "12b")
    assert coord_12b == (35.5, 18.0)
    
    # 2. 备用哈希映射 (Fallback) 验证，确保没有配置的 Block 也能稳定输出不报错且幂等
    coord_fallback_1 = get_booth_coords("東", "Ｚ", "01a")
    coord_fallback_2 = get_booth_coords("東", "Ｚ", "01a")
    assert coord_fallback_1 == coord_fallback_2
    assert coord_fallback_1[0] > 0.0
    assert coord_fallback_1[1] == 1.5

def test_graph_builder_and_weighting():
    # 模拟 3 个社团物理布局
    # 1001 与 1002 在东馆 H 排 12，且是背靠背关系（a面与b面），物理间距 1.0 米
    # 1003 在东馆 H 排 13a，物理距离 1001 为 1.5 米，距离 1002 为 1.8 米
    # 1004 在西馆 む排 01a (不同展馆，绝对不连通)
    circles = [
        {"id": 1001, "day": "日", "hall": "東", "block": "Ｈ", "space": "12a"},
        {"id": 1002, "day": "日", "hall": "東", "block": "Ｈ", "space": "12b"},
        {"id": 1003, "day": "日", "hall": "東", "block": "Ｈ", "space": "13a"},
        {"id": 1004, "day": "日", "hall": "西", "block": "む", "space": "01a"}
    ]
    
    graph = build_spatial_graph(circles)
    
    # 验证 1004 没有邻居
    assert len(graph[1004]) == 0
    
    # 验证 1001 与 1002（背靠背）连通且权重为 1.0 (因为 same_block=True, d<=1.1)
    neighbors_1001 = {nb: w for nb, w in graph[1001]}
    assert 1002 in neighbors_1001
    assert neighbors_1001[1002] == 1.0
    
    # 验证 1001 与 1003 (左右相邻) 连通且权重为 0.7 (d=1.5, same_block=True)
    assert 1003 in neighbors_1001
    assert round(neighbors_1001[1003], 1) == 0.7

def test_lpa_damping_and_anchoring():
    # 构建包含 4 个节点的简单链式图 (1001 --- 1002 --- 1003 --- 1004)
    # 1001 和 1004 为已标记种子，1002 和 1003 为未知节点
    adjacency_list = {
        1001: [(1002, 1.0)],
        1002: [(1001, 1.0), (1003, 1.0)],
        1003: [(1002, 1.0), (1004, 1.0)],
        1004: [(1003, 1.0)]
    }
    
    seeds = {
        1001: {"明日方舟": 1.0},
        1004: {"蔚蓝档案": 1.0}
    }
    
    all_ids = [1001, 1002, 1003, 1004]
    
    # 执行 LPA
    results = run_label_propagation(
        adjacency_list=adjacency_list,
        seeds=seeds,
        all_circle_ids=all_ids,
        alpha=0.6,
        max_iter=5
    )
    
    # 1. 验证种子节点 1001 和 1004 锚定效应，概率仍为 1.0
    assert results[1001]["明日方舟"] == 1.0
    assert results[1004]["蔚蓝档案"] == 1.0
    
    # 2. 验证未知节点 1002 融合了 1001 的能量，发生概率衰减
    assert "明日方舟" in results[1002]
    # 概率应当在 (0, 1.0) 之间且偏向邻居 1001
    assert 0.1 < results[1002]["明日方舟"] < 1.0

def test_greedy_routing_path():
    # 模拟打标输出的无序摊位
    # 展馆入口设在 (50.0, 0.0) (东馆大门)
    # 三个摊位物理坐标：
    # c_far: (80.0, 50.0) -> 最远
    # c_mid: (40.0, 10.0) -> 较近
    # c_near: (52.0, 3.0) -> 最近
    circles = [
        {"circle_id": 1, "day": "日", "hall": "東", "block": "Ｈ", "space": "30a"}, # 远
        {"circle_id": 2, "day": "日", "hall": "東", "block": "Ｈ", "space": "06a"}, # 中
        {"circle_id": 3, "day": "日", "hall": "東", "block": "Ｈ", "space": "02a"}, # 近
    ]
    
    # 物理最优解应当是：近 -> 中 -> 远
    optimized = solve_greedy_route(circles)
    
    assert len(optimized) == 3
    # 按从大门出发最近邻排序
    assert optimized[0]["circle_id"] == 3 # 02a
    assert optimized[1]["circle_id"] == 2 # 06a
    assert optimized[2]["circle_id"] == 1 # 30a
