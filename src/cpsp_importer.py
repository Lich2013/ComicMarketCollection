import os
import json
import sqlite3
from src.db import get_db_connection, init_db
from src.cp31_importer import normalize_theme

def import_cpsp_dataset(base_dir: str, db_path: str = "data/comic_market.db") -> bool:
    """导入 CPSP 的数据包至 SQLite 数据库中"""
    # 确保数据库表已初始化
    init_db(db_path)
    
    if not os.path.exists(base_dir):
        print(f"Error: CPSP directory not found: {base_dir}")
        return False

    unique_products = {}
    unique_circles = {}
    
    print(f"Scanning CPSP JSON files from: {base_dir}...")
    for filename in os.listdir(base_dir):
        if not filename.endswith(".json"):
            continue
        filepath = os.path.join(base_dir, filename)
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
                            "day_label": "D1", # CPSP dataset is day1-only
                            "circle_id": item.get("circleID") or item.get("circleId"),
                            "tags": item.get("tag") or ""
                        }
                    
                    # 记录唯一社团
                    circle_id = item.get("circleID") or item.get("circleId")
                    if circle_id:
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

    print(f"Extracted {len(unique_products)} unique CPSP products, {len(unique_circles)} unique CPSP circles.")
    if not unique_products:
        print("No valid products found to import.")
        return False

    # 导入数据库
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    
    circle_query = """
        INSERT OR REPLACE INTO cpsp_circles (circle_id, name, position_name, position)
        VALUES (:circle_id, :name, :position_name, :position)
    """
    
    product_query = """
        INSERT OR REPLACE INTO cpsp_products (doujinshi_id, name, theme_alias, type, sell_status, hot_count, day_label, circle_id, tags)
        VALUES (:doujinshi_id, :name, :theme_alias, :type, :sell_status, :hot_count, :day_label, :circle_id, :tags)
    """
    
    try:
        cursor.executemany(circle_query, list(unique_circles.values()))
        cursor.executemany(product_query, list(unique_products.values()))
        conn.commit()
        print(f"Successfully imported {len(unique_circles)} circles and {len(unique_products)} products into CPSP tables.")
        return True
    except sqlite3.Error as e:
        print(f"Database insertion failed: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()
