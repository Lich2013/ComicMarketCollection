import os
import sqlite3
from collections import defaultdict

def calculate_comiket_moran_i(db_path: str, table_name: str, target_genre: str) -> tuple:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    query = f"""
        SELECT id, hall, block, space, genre 
        FROM {table_name}
        WHERE hall IS NOT NULL AND hall != '' 
          AND block IS NOT NULL AND block != ''
          AND space IS NOT NULL AND space != ''
          AND genre IS NOT NULL AND genre != ''
    """
    try:
        cursor.execute(query)
        rows = cursor.fetchall()
    except sqlite3.Error as e:
        print(f"Error querying {table_name}: {e}")
        conn.close()
        return None
    finally:
        conn.close()
        
    if not rows:
        return None
        
    circles = []
    z = []
    
    for r_id, hall, block, space_str, genre in rows:
        try:
            space_num = int(''.join(filter(str.isdigit, str(space_str))))
        except ValueError:
            space_num = 1
            
        is_target = 1 if (genre == target_genre or target_genre in genre) else 0
        circles.append({
            "id": r_id,
            "hall": hall,
            "block": block,
            "space": space_num,
            "is_target": is_target
        })
        z.append(is_target)
        
    N = len(circles)
    if N < 10:
        return None
        
    z_bar = sum(z) / N
    
    spatial_groups = defaultdict(list)
    for idx, c in enumerate(circles):
        key = (c["hall"], c["block"])
        spatial_groups[key].append(idx)
        
    numerator = 0.0
    W = 0.0
    
    for (hall, block), indices in spatial_groups.items():
        n_grp = len(indices)
        for i in range(n_grp):
            idx_i = indices[i]
            c_i = circles[idx_i]
            z_i_diff = c_i["is_target"] - z_bar
            
            for j in range(i + 1, n_grp):
                idx_j = indices[j]
                c_j = circles[idx_j]
                
                if abs(c_i["space"] - c_j["space"]) <= 3:
                    w_ij = 1.0
                    z_j_diff = c_j["is_target"] - z_bar
                    
                    numerator += 2 * w_ij * z_i_diff * z_j_diff
                    W += 2 * w_ij
                    
    denominator = sum((val - z_bar) ** 2 for val in z)
    if denominator == 0 or W == 0:
        return 0.0, -1.0 / (N - 1), N, 0.0
        
    moran_i = (N / W) * (numerator / denominator)
    e_i = -1.0 / (N - 1)
    return moran_i, e_i, N, W


def calculate_comicup_moran_i(
    db_path: str, 
    circles_table: str, 
    products_table: str, 
    target_theme: str, 
    filter_types: list = None
) -> tuple:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    filter_sql = ""
    params = [target_theme]
    if filter_types:
        placeholders = ",".join("?" for _ in filter_types)
        filter_sql = f"AND type NOT IN ({placeholders})"
        params.extend(filter_types)
        
    product_query = f"""
        SELECT DISTINCT circle_id 
        FROM {products_table} 
        WHERE theme_alias = ?
        {filter_sql}
    """
    try:
        cursor.execute(product_query, params)
        theme_circle_ids = {row[0] for row in cursor.fetchall() if row[0] is not None}
    except sqlite3.Error as e:
        print(f"Error querying products for Moran I: {e}")
        conn.close()
        return None

    circle_query = f"""
        SELECT circle_id, position_name 
        FROM {circles_table} 
        WHERE position_name IS NOT NULL AND position_name != ''
    """
    try:
        cursor.execute(circle_query)
        rows = cursor.fetchall()
    except sqlite3.Error as e:
        print(f"Error querying circles for Moran I: {e}")
        conn.close()
        return None
    finally:
        conn.close()
        
    if len(rows) < 10:
        return None
        
    circles = []
    z = []
    for row in rows:
        c_id, pos_name = row[0], row[1]
        val = 1 if c_id in theme_circle_ids else 0
        circles.append({
            "circle_id": c_id,
            "position_name": pos_name,
            "val": val
        })
        z.append(val)
        
    N = len(circles)
    z_bar = sum(z) / N
    
    street_groups = defaultdict(list)
    for idx, c in enumerate(circles):
        street_groups[c["position_name"]].append(idx)
        
    numerator = 0.0
    W = 0.0
    
    for street, indices in street_groups.items():
        n_grp = len(indices)
        if n_grp < 2:
            continue
        for i in range(n_grp):
            idx_i = indices[i]
            c_i = circles[idx_i]
            z_i_diff = c_i["val"] - z_bar
            
            for j in range(i + 1, n_grp):
                idx_j = indices[j]
                c_j = circles[idx_j]
                
                w_ij = 1.0
                z_j_diff = c_j["val"] - z_bar
                
                numerator += 2 * w_ij * z_i_diff * z_j_diff
                W += 2 * w_ij
                
    denominator = sum((val - z_bar) ** 2 for val in z)
    if denominator == 0 or W == 0:
        return 0.0, -1.0 / (N - 1), N, 0.0
        
    moran_i = (N / W) * (numerator / denominator)
    e_i = -1.0 / (N - 1)
    return moran_i, e_i, N, W


def main():
    db_path = "data/comic_market.db"
    if not os.path.exists(db_path):
        print(f"错误: 数据库文件不存在。请在项目根目录下运行。当前路径: {db_path}")
        return
        
    print("=== Comiket & Comicup 题材空间自相关 Moran's I 复现计算 ===")
    
    # 1. Comiket 107
    print("\n--- Comiket 107 (C107) ---")
    c107_genres = ["ブルーアーカイブ", "男性向", "鉄道・旅行・メカミリ", "コスプレ"]
    for g in c107_genres:
        res = calculate_comiket_moran_i(db_path, "c107_circles", g)
        if res:
            moran_i, expected, n, w = res
            print(f"题材: {g} | Moran's I: {moran_i:.6f} | E(I): {expected:.6f} | N: {n}")
            
    # 2. Comiket 108
    print("\n--- Comiket 108 (C108) ---")
    c108_genres = ["ブルーアーカイブ", "男性向", "鉄道・旅行・メカミリ", "コスプレ"]
    for g in c108_genres:
        res = calculate_comiket_moran_i(db_path, "circles", g)
        if res:
            moran_i, expected, n, w = res
            print(f"题材: {g} | Moran's I: {moran_i:.6f} | E(I): {expected:.6f} | N: {n}")
            
    # 3. Comicup Special (CPSP)
    print("\n--- Comicup Special (CPSP) - 过滤色纸/胶带后 ---")
    cpsp_themes = ["明日方舟", "排球少年", "代号鸢", "原神", "恋与深空", "原创"]
    for t in cpsp_themes:
        res = calculate_comicup_moran_i(db_path, "cpsp_circles", "cpsp_products", t, ["色纸", "纸胶带"])
        if res:
            moran_i, expected, n, w = res
            print(f"题材: {t} | Moran's I: {moran_i:.6f} | E(I): {expected:.6f} | N: {n}")
            
    # 4. Comicup 31 (CP31)
    print("\n--- Comicup 31 (CP31) ---")
    cp31_themes = ["明日方舟", "排球少年", "代号鸢", "原神", "恋与深空", "原创"]
    for t in cp31_themes:
        res = calculate_comicup_moran_i(db_path, "cp31_circles", "cp31_products", t)
        if res:
            moran_i, expected, n, w = res
            print(f"题材: {t} | Moran's I: {moran_i:.6f} | E(I): {expected:.6f} | N: {n}")

if __name__ == "__main__":
    main()
