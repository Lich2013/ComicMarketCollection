import os
import json
import sqlite3
from src.db import get_db_connection, init_db

def normalize_theme(theme: str) -> str:
    """标准化 IP 题材名称，清洗空格、标点及各种拼写变体"""
    if not theme:
        return "未知题材"
    theme = theme.strip()
    # 转换为去除常见标点符号和空格的小写比对字串
    norm = theme.replace("：", "").replace(":", "").replace(" ", "").replace("·", "").lower()
    
    # 常用大门类的合并规则
    if "崩坏星穹铁道" in norm or "星穹铁道" in norm or "崩铁" in norm:
        return "崩坏星穹铁道"
    if "原神" in norm:
        return "原神"
    if "明日方舟" in norm:
        return "明日方舟"
    if "恋与深空" in norm:
        return "恋与深空"
    if "排球少年" in norm:
        return "排球少年"
    if "代号鸢" in norm:
        return "代号鸢"
    if "偶像梦幻祭" in norm:
        return "偶像梦幻祭"
    if "银魂" in norm:
        return "银魂"
    if "盗墓笔记" in norm:
        return "盗墓笔记"
    if "全职高手" in norm:
        return "全职高手"
    if "诡秘之主" in norm:
        return "诡秘之主"
    if "哪吒" in norm:
        return "哪吒之魔童闹海"
    if "迷宫饭" in norm:
        return "迷宫饭"
    if "蓝色监狱" in norm:
        return "蓝色监狱"
    if "凹凸世界" in norm:
        return "凹凸世界"
    if "名侦探柯南" in norm:
        return "名侦探柯南"
    if "光与夜之恋" in norm:
        return "光与夜之恋"
    if "黑塔利亚" in norm:
        return "黑塔利亚"
    
    return theme

def import_cp31_dataset(base_dir: str, db_path: str = "data/comic_market.db"):
    """导入 CP31 day1 和 day2 的数据包至 SQLite 数据库中"""
    # 确保数据库表已初始化
    init_db(db_path)
    
    day1_dir = os.path.join(base_dir, "day1data")
    day2_dir = os.path.join(base_dir, "day2data")
    
    if not os.path.exists(day1_dir) and not os.path.exists(day2_dir):
        # 兼容性处理：如果传入的直接是 day1data 这种子目录，或者包含 day1/day2 子目录
        if os.path.exists(os.path.join(base_dir, "day1")):
            day1_dir = os.path.join(base_dir, "day1")
        if os.path.exists(os.path.join(base_dir, "day2")):
            day2_dir = os.path.join(base_dir, "day2")
            
    # 如果依旧不存在，报错提示
    if not os.path.exists(day1_dir) and not os.path.exists(day2_dir):
        print(f"Error: CP31 day1data/day2data directories not found in {base_dir}")
        return False

    unique_products = {}
    unique_circles = {}
    
    def parse_folder(directory, day_label):
        if not os.path.exists(directory):
            return
        
        for filename in os.listdir(directory):
            if not filename.endswith(".json"):
                continue
            filepath = os.path.join(directory, filename)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if not isinstance(data, dict) or "result" not in data:
                        continue
                    item_list = data["result"].get("list", [])
                    for item in item_list:
                        pid = item.get("doujinshiId")
                        if not pid:
                            continue
                        
                        # 清洗与归一化题材
                        raw_theme = item.get("themeAlias") or "未知题材"
                        clean_theme = normalize_theme(raw_theme)
                        
                        # 记录唯一制品
                        if pid not in unique_products:
                            unique_products[pid] = {
                                "doujinshi_id": pid,
                                "name": item.get("doujinshiName") or "未名制品",
                                "theme_alias": clean_theme,
                                "type": item.get("type") or "未知类型",
                                "sell_status": item.get("sellStatus") or "未知状态",
                                "hot_count": item.get("hotCount") or 0,
                                "day_label": day_label,
                                "circle_id": item.get("circleID"),
                                "tags": item.get("tag") or ""
                            }
                        
                        # 记录唯一社团
                        circle_id = item.get("circleID")
                        if circle_id:
                            # 提取摊位位置信息
                            event_list = item.get("eventList", [])
                            pos_name = ""
                            pos = ""
                            if event_list:
                                pos_name = event_list[0].get("positionName") or ""
                                pos = event_list[0].get("position") or ""
                            
                            if circle_id not in unique_circles:
                                unique_circles[circle_id] = {
                                    "circle_id": circle_id,
                                    "name": item.get("circleName") or "未名社团",
                                    "position_name": pos_name,
                                    "position": pos
                                }
            except Exception as e:
                print(f"Error parsing file {filename}: {e}")

    # 解析双日文件夹
    print("Parsing CP31 JSON files...")
    parse_folder(day1_dir, "D1")
    parse_folder(day2_dir, "D2")
    
    print(f"Extracted {len(unique_products)} unique products, {len(unique_circles)} unique circles.")
    
    # 导入数据库
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    
    # 批量导入 circles
    circle_query = """
        INSERT OR REPLACE INTO cp31_circles (circle_id, name, position_name, position)
        VALUES (:circle_id, :name, :position_name, :position)
    """
    # 批量导入 products
    product_query = """
        INSERT OR REPLACE INTO cp31_products (doujinshi_id, name, theme_alias, type, sell_status, hot_count, day_label, circle_id, tags)
        VALUES (:doujinshi_id, :name, :theme_alias, :type, :sell_status, :hot_count, :day_label, :circle_id, :tags)
    """
    
    try:
        # 执行批量插入
        cursor.executemany(circle_query, list(unique_circles.values()))
        cursor.executemany(product_query, list(unique_products.values()))
        conn.commit()
        print(f"Successfully imported {len(unique_circles)} circles and {len(unique_products)} products into CP31 tables.")
        return True
    except sqlite3.Error as e:
        print(f"Database insertion failed: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()
