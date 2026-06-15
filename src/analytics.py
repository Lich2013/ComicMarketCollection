import os
import json
import sqlite3
from src.db import DEFAULT_DB_PATH, get_db_connection

# 预设的大众二次元受众热度基线比例 (单位: %)，用于计算同人偏离度 (DBI)
AUDIENCE_POPULARITY_BASELINE = {
    "男性向": 10.0,
    "ブルーアーカイブ": 4.0,
    "ゲーム(ネット・ソーシャル)": 12.0,
    "VTuber": 8.0,
    "鉄道・旅行・メカミリ": 2.0,
    "評論・情報": 1.5,
    "コスプレ": 5.0,
    "創作(少年)": 4.0,
    "アニメ(その他)": 6.0,
    "アイドルマスター": 3.5,
    "オリジナル雑貨": 2.5,
    "ウマ娘": 5.0,
    "TYPE-MOON": 3.0,
    "東方Project": 1.5,
    "ギャルゲー": 1.5
}

def calculate_genre_distribution(db_path: str = DEFAULT_DB_PATH, output_path: str = None) -> dict:
    """
    分析社团题材分布，计算时间（星期）、空间（展馆）矩阵，
    结合大众受众热度基线计算 DBI 偏离度，并将分析报告导出为 JSON。
    """
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Database file not found: {db_path}")

    # 1. 题材大盘统计
    with get_db_connection(db_path) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 统计总社团数（有题材的社团数）
        cursor.execute("SELECT COUNT(*) FROM circles WHERE genre IS NOT NULL AND genre != ''")
        total_circles = cursor.fetchone()[0]
        if total_circles == 0:
            print("No circles with valid genres found in database.")
            return {
                "summary": {"total_circles": 0, "total_genres": 0},
                "global_rank": [],
                "day_comparison": [],
                "hall_matrix": {"East": [], "West": [], "South": []}
            }

        # 各题材总数与比例
        cursor.execute("""
            SELECT genre, COUNT(*) as circle_count
            FROM circles
            WHERE genre IS NOT NULL AND genre != ''
            GROUP BY genre
            ORDER BY circle_count DESC
        """)
        genre_ranks_raw = cursor.fetchall()
        
        # 2. 日期维度（土/日 映射为 Day1/Day2）
        cursor.execute("""
            SELECT 
                genre,
                SUM(CASE WHEN day = '土' THEN 1 ELSE 0 END) as day1_count,
                SUM(CASE WHEN day = '日' THEN 1 ELSE 0 END) as day2_count
            FROM circles
            WHERE genre IS NOT NULL AND genre != ''
            GROUP BY genre
        """)
        day_comparison_raw = {row["genre"]: (row["day1_count"], row["day2_count"]) for row in cursor.fetchall()}

        # 3. 场馆维度（东/西/南）
        cursor.execute("""
            SELECT 
                hall,
                genre,
                COUNT(*) as circle_count
            FROM circles
            WHERE hall IS NOT NULL AND hall != '' AND genre IS NOT NULL AND genre != ''
            GROUP BY hall, genre
            ORDER BY hall, circle_count DESC
        """)
        hall_raw = cursor.fetchall()

    # 整理场馆分布矩阵
    # 映射 hall 的显示名
    hall_mapping = {"東": "East", "西": "West", "南": "South"}
    hall_matrix = {"East": [], "West": [], "South": []}
    for row in hall_raw:
        raw_hall = row["hall"]
        mapped_hall = hall_mapping.get(raw_hall, raw_hall)
        if mapped_hall not in hall_matrix:
            hall_matrix[mapped_hall] = []
        hall_matrix[mapped_hall].append({
            "genre": row["genre"],
            "count": row["circle_count"]
        })

    # 计算全局排行及 DBI
    global_rank = []
    day_comparison = []
    
    # 统计独立题材数量
    total_genres = len(genre_ranks_raw)
    
    for row in genre_ranks_raw:
        genre = row["genre"]
        count = row["circle_count"]
        ratio = round((count * 100.0 / total_circles), 2)
        
        # 计算 DBI (同人偏离度)
        # DBI = Comiket占比 / 大众占比
        # 如果题材在预置基线中，取其值，否则以 Comiket 比例作为基准（使 DBI 默认为 1.0）
        baseline_pct = AUDIENCE_POPULARITY_BASELINE.get(genre, ratio)
        if baseline_pct > 0:
            dbi = round((ratio / baseline_pct), 2)
        else:
            dbi = 1.0
            
        global_rank.append({
            "genre": genre,
            "count": count,
            "ratio": ratio,
            "dbi": dbi,
            "baseline_popularity": baseline_pct
        })
        
        # 整理星期对比
        d1, d2 = day_comparison_raw.get(genre, (0, 0))
        day_comparison.append({
            "genre": genre,
            "day1": d1,
            "day2": d2
        })

    # 4. 构造完整报告
    report = {
      "summary": {
        "total_circles": total_circles,
        "total_genres": total_genres
      },
      "global_rank": global_rank,
      "day_comparison": day_comparison,
      "hall_matrix": hall_matrix
    }

    # 5. 写入本地文件
    if output_path:
        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"Genre & Theme distribution analysis report successfully saved to: {output_path}")

    return report
