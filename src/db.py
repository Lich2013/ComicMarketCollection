import os
import sqlite3
from datetime import datetime

DEFAULT_DB_PATH = "data/comic_market.db"

def get_db_connection(db_path: str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """获取数据库连接，并确保父目录存在"""
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(db_path: str = DEFAULT_DB_PATH):
    """初始化数据库表结构"""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        
        # 1. 创建 circles 表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS circles (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                author TEXT,
                genre TEXT,
                description TEXT,
                hall TEXT,
                day TEXT,
                block TEXT,
                space TEXT,
                twitter_url TEXT,
                twitter_username TEXT,
                pixiv_url TEXT,
                circle_cut_url TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 2. 创建 catalogs 表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS catalogs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                circle_id INTEGER,
                tweet_id TEXT UNIQUE,
                tweet_url TEXT,
                tweet_text TEXT,
                image_path TEXT,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (circle_id) REFERENCES circles (id) ON DELETE CASCADE
            )
        """)
        
        # 3. 创建 goods 表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS goods (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                circle_id INTEGER,
                catalog_id INTEGER,
                name TEXT NOT NULL,
                type TEXT,
                price INTEGER,
                is_set INTEGER DEFAULT 0,
                raw_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (circle_id) REFERENCES circles (id) ON DELETE CASCADE,
                FOREIGN KEY (catalog_id) REFERENCES catalogs (id) ON DELETE CASCADE
            )
        """)
        
        conn.commit()

# --- CRUD 辅助函数 ---

def save_circle(circle_data: dict, db_path: str = DEFAULT_DB_PATH):
    """插入或更新社团数据"""
    query = """
        INSERT INTO circles (
            id, name, author, genre, description, hall, day, block, space, 
            twitter_url, twitter_username, pixiv_url, circle_cut_url, updated_at
        ) VALUES (
            :id, :name, :author, :genre, :description, :hall, :day, :block, :space, 
            :twitter_url, :twitter_username, :pixiv_url, :circle_cut_url, CURRENT_TIMESTAMP
        )
        ON CONFLICT(id) DO UPDATE SET
            name = excluded.name,
            author = excluded.author,
            genre = excluded.genre,
            description = excluded.description,
            hall = excluded.hall,
            day = excluded.day,
            block = excluded.block,
            space = excluded.space,
            twitter_url = excluded.twitter_url,
            twitter_username = excluded.twitter_username,
            pixiv_url = excluded.pixiv_url,
            circle_cut_url = excluded.circle_cut_url,
            updated_at = CURRENT_TIMESTAMP
    """
    with get_db_connection(db_path) as conn:
        conn.execute(query, circle_data)
        conn.commit()

def get_all_circles(db_path: str = DEFAULT_DB_PATH) -> list:
    """获取所有社团信息"""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM circles")
        return [dict(row) for row in cursor.fetchall()]

def get_existing_circle_ids(db_path: str = DEFAULT_DB_PATH) -> set[int]:
    """获取数据库中已同步的所有社团 ID 集合"""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM circles")
        return {row[0] for row in cursor.fetchall()}


def save_catalog(catalog_data: dict, db_path: str = DEFAULT_DB_PATH) -> int:
    """保存或更新品书推文记录，并返回记录 ID"""
    query = """
        INSERT INTO catalogs (
            circle_id, tweet_id, tweet_url, tweet_text, image_path, status, created_at, updated_at
        ) VALUES (
            :circle_id, :tweet_id, :tweet_url, :tweet_text, :image_path, :status, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
        )
        ON CONFLICT(tweet_id) DO UPDATE SET
            image_path = COALESCE(excluded.image_path, image_path),
            tweet_text = COALESCE(excluded.tweet_text, tweet_text),
            updated_at = CURRENT_TIMESTAMP
        RETURNING id
    """
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(query, catalog_data)
            row = cursor.fetchone()
            conn.commit()
            if row:
                return row[0]
        except sqlite3.Error as e:
            # 如果 RETURNING id 不支持或者冲突，尝试直接查询
            cursor.execute("SELECT id FROM catalogs WHERE tweet_id = ?", (catalog_data['tweet_id'],))
            row = cursor.fetchone()
            if row:
                return row[0]
            raise e
        # 兜底查询
        cursor.execute("SELECT id FROM catalogs WHERE tweet_id = ?", (catalog_data['tweet_id'],))
        row = cursor.fetchone()
        return row[0] if row else None

def get_pending_catalogs(db_path: str = DEFAULT_DB_PATH, circle_ids: set[int] = None) -> list:
    """获取待处理 (pending) 状态的品书，支持按社团 ID 集合筛选"""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        if circle_ids is not None:
            if not circle_ids:
                return []
            placeholders = ",".join("?" for _ in circle_ids)
            query = f"""
                SELECT c.*, cir.name as circle_name 
                FROM catalogs c
                JOIN circles cir ON c.circle_id = cir.id
                WHERE c.status = 'pending' AND c.circle_id IN ({placeholders})
            """
            cursor.execute(query, list(circle_ids))
        else:
            query = """
                SELECT c.*, cir.name as circle_name 
                FROM catalogs c
                JOIN circles cir ON c.circle_id = cir.id
                WHERE c.status = 'pending'
            """
            cursor.execute(query)
        return [dict(row) for row in cursor.fetchall()]

def get_filtered_circle_ids(
    day_list: list[str] = None, 
    hall_list: list[str] = None, 
    circle_ids: list[int] = None, 
    name_query: str = None, 
    db_path: str = DEFAULT_DB_PATH
) -> set[int]:
    """多条件动态筛选社团，返回匹配的社团 ID 集合"""
    query = "SELECT id FROM circles WHERE 1=1"
    params = []
    
    if day_list:
        placeholders = ",".join("?" for _ in day_list)
        query += f" AND day IN ({placeholders})"
        params.extend(day_list)
        
    if hall_list:
        placeholders = ",".join("?" for _ in hall_list)
        query += f" AND hall IN ({placeholders})"
        params.extend(hall_list)
        
    if circle_ids:
        placeholders = ",".join("?" for _ in circle_ids)
        query += f" AND id IN ({placeholders})"
        params.extend(circle_ids)
        
    if name_query:
        query += " AND (name LIKE ? OR author LIKE ?)"
        params.extend([f"%{name_query}%", f"%{name_query}%"])
        
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        return {row[0] for row in cursor.fetchall()}


def update_catalog_status(catalog_id: int, status: str, db_path: str = DEFAULT_DB_PATH):
    """更新品书的状态"""
    with get_db_connection(db_path) as conn:
        conn.execute("""
            UPDATE catalogs 
            SET status = ?, updated_at = CURRENT_TIMESTAMP 
            WHERE id = ?
        """, (status, catalog_id))
        conn.commit()

def save_goods(goods_list: list[dict], db_path: str = DEFAULT_DB_PATH):
    """批量保存商品制品记录"""
    query = """
        INSERT INTO goods (circle_id, catalog_id, name, type, price, is_set, raw_json)
        VALUES (:circle_id, :catalog_id, :name, :type, :price, :is_set, :raw_json)
    """
    with get_db_connection(db_path) as conn:
        conn.executemany(query, goods_list)
        conn.commit()
