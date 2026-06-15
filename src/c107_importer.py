import os
import json
import sqlite3
from src.db import get_db_connection, init_db
from src.circle_sync import extract_twitter_username

def import_c107_dataset(base_dir: str, db_path: str = "data/comic_market.db") -> bool:
    """导入 C107 的 WebCatalog 社团数据包至 SQLite 数据库中"""
    # 确保数据库表已初始化
    init_db(db_path)
    
    tables_dir = os.path.join(base_dir, "tables")
    if not os.path.exists(tables_dir):
        # 兼容性处理：如果直接传入了 tables 目录，或者 tables 在其它子路径中
        if base_dir.endswith("tables"):
            tables_dir = base_dir
        else:
            print(f"Error: tables subdirectory not found in {base_dir}")
            return False

    unique_circles = {}
    
    print(f"Scanning C107 JSON files from: {tables_dir}...")
    for filename in os.listdir(tables_dir):
        if not filename.endswith(".json"):
            continue
        filepath = os.path.join(tables_dir, filename)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                if not isinstance(data, dict) or "Id" not in data:
                    continue
                
                tid = data.get("Id")
                
                # 提取 Cut URL
                cut_urls = data.get("CircleCutUrls") or []
                circle_cut_url = None
                if cut_urls and cut_urls[0]:
                    circle_cut_url = "https://webcatalog.circle.ms" + cut_urls[0]
                
                twitter_url = data.get("TwitterUrl")
                twitter_username = extract_twitter_username(twitter_url)
                
                # 记录唯一社团
                unique_circles[tid] = {
                    "id": tid,
                    "circle_id": data.get("CircleId"),
                    "name": data.get("Name") or "未名社团",
                    "author": data.get("Author"),
                    "genre": data.get("Genre"),
                    "description": data.get("Description"),
                    "hall": data.get("Hall"),
                    "day": data.get("Day"),
                    "block": data.get("Block"),
                    "space": data.get("Space"),
                    "twitter_url": twitter_url,
                    "twitter_username": twitter_username,
                    "pixiv_url": data.get("PixivUrl"),
                    "circle_cut_url": circle_cut_url
                }
        except Exception as e:
            print(f"Error parsing file {filename}: {e}")

    print(f"Extracted {len(unique_circles)} unique C107 circles.")
    if not unique_circles:
        print("No valid circles found to import.")
        return False

    # 导入数据库
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    
    query = """
        INSERT OR REPLACE INTO c107_circles (
            id, circle_id, name, author, genre, description, hall, day, block, space, 
            twitter_url, twitter_username, pixiv_url, circle_cut_url
        ) VALUES (
            :id, :circle_id, :name, :author, :genre, :description, :hall, :day, :block, :space, 
            :twitter_url, :twitter_username, :pixiv_url, :circle_cut_url
        )
    """
    
    try:
        cursor.executemany(query, list(unique_circles.values()))
        conn.commit()
        print(f"Successfully imported {len(unique_circles)} circles into c107_circles table.")
        return True
    except sqlite3.Error as e:
        print(f"Database insertion failed: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()
