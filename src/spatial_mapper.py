import os
import json

LAYOUT_GRID_PATH = os.path.join("data", "layout_grid_c108.json")

# 预加载布局配置
_layout_grid = {}
if os.path.exists(LAYOUT_GRID_PATH):
    try:
        with open(LAYOUT_GRID_PATH, "r", encoding="utf-8") as f:
            _layout_grid = json.load(f)
    except Exception as e:
        print(f"Warning: Failed to load layout grid config: {e}")

def get_space_num(space_str: str) -> int:
    """提取摊位物理数字。如 '24a' -> 24，'01b' -> 1"""
    if not space_str:
        return 0
    digits = "".join(filter(str.isdigit, str(space_str)))
    return int(digits) if digits else 0

def get_booth_coords(hall: str, block: str, space: str) -> tuple[float, float]:
    """
    根据展馆、排和摊位号计算二维物理坐标 (X, Y)
    - X 轴：排的基准线位置。若是 a 面，则向左偏移 0.5 米；若是 b 面，则向右偏移 0.5 米。
    - Y 轴：空间号数字 * 摊位宽度 (默认为 1.5 米)。
    - Fallback 机制：如果 hall/block 不在配置中，使用哈希映射生成基准 X。
    """
    hall_str = str(hall or "")
    block_str = str(block or "")
    space_str = str(space or "")
    
    # 1. 确定基准 X
    base_x = None
    if hall_str in _layout_grid and block_str in _layout_grid[hall_str]:
        base_x = _layout_grid[hall_str][block_str].get("x")
    
    if base_x is None:
        # Fallback 机制：对 block 字符进行哈希映射，确保相同的 block 有相同的基准 X
        hall_offset = sum(ord(c) for c in hall_str) % 3 * 50.0
        block_char = block_str[0] if block_str else 'A'
        base_x = hall_offset + (ord(block_char) - ord('A') + 1) * 15.0
        
    # 2. X 轴精细偏移 (a面 vs b面)
    # 背靠背排布下，a面朝向一侧，b面朝向另一侧
    is_a_face = space_str.endswith("a")
    x = base_x - 0.5 if is_a_face else base_x + 0.5
    
    # 3. Y 轴坐标
    # 假设每个摊位宽度为 1.5 米
    space_num = get_space_num(space_str)
    y = space_num * 1.5
    
    return (float(x), float(y))
