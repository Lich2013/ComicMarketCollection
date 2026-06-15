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
        
        # 4. 创建 cp31_products 表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cp31_products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                doujinshi_id INTEGER UNIQUE,
                name TEXT NOT NULL,
                theme_alias TEXT,
                type TEXT,
                sell_status TEXT,
                hot_count INTEGER DEFAULT 0,
                day_label TEXT,
                circle_id INTEGER,
                tags TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 5. 创建 cp31_circles 表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cp31_circles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                circle_id INTEGER UNIQUE,
                name TEXT NOT NULL,
                position_name TEXT,
                position TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 6. 创建 c107_circles 表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS c107_circles (
                id INTEGER PRIMARY KEY,
                circle_id INTEGER,
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
        
        # 7. 创建 cpsp_products 表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cpsp_products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                doujinshi_id INTEGER UNIQUE,
                name TEXT NOT NULL,
                theme_alias TEXT,
                type TEXT,
                sell_status TEXT,
                hot_count INTEGER DEFAULT 0,
                day_label TEXT,
                circle_id INTEGER,
                tags TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 8. 创建 cpsp_circles 表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cpsp_circles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                circle_id INTEGER UNIQUE,
                name TEXT NOT NULL,
                position_name TEXT,
                position TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
            # 如果是由于低版本 SQLite 不支持 RETURNING id 语法引起的报错，降级执行无 RETURNING 子句的语句
            try:
                fallback_query = """
                    INSERT INTO catalogs (
                        circle_id, tweet_id, tweet_url, tweet_text, image_path, status, created_at, updated_at
                    ) VALUES (
                        :circle_id, :tweet_id, :tweet_url, :tweet_text, :image_path, :status, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                    )
                    ON CONFLICT(tweet_id) DO UPDATE SET
                        image_path = COALESCE(excluded.image_path, image_path),
                        tweet_text = COALESCE(excluded.tweet_text, tweet_text),
                        updated_at = CURRENT_TIMESTAMP
                """
                cursor.execute(fallback_query, catalog_data)
                conn.commit()
                cursor.execute("SELECT id FROM catalogs WHERE tweet_id = ?", (catalog_data['tweet_id'],))
                row = cursor.fetchone()
                if row:
                    return row[0]
            except Exception:
                pass
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
                SELECT c.*, cir.name as circle_name, cir.author as circle_author 
                FROM catalogs c
                JOIN circles cir ON c.circle_id = cir.id
                WHERE c.status = 'pending' AND c.circle_id IN ({placeholders})
            """
            cursor.execute(query, list(circle_ids))
        else:
            query = """
                SELECT c.*, cir.name as circle_name, cir.author as circle_author 
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


def export_goods_to_csv(
    output_path: str,
    day_list: list[str] = None,
    hall_list: list[str] = None,
    circle_ids: list[int] = None,
    name_query: str = None,
    db_path: str = DEFAULT_DB_PATH
):
    """将商品数据以 UTF-8 with BOM 编码导出为 CSV，以供 Excel 直接打开"""
    import csv
    import os
    
    # 动态筛选社团
    has_filter = any(x is not None for x in [day_list, hall_list, circle_ids, name_query])
    if has_filter:
        target_circle_ids = get_filtered_circle_ids(
            day_list=day_list,
            hall_list=hall_list,
            circle_ids=circle_ids,
            name_query=name_query,
            db_path=db_path
        )
    else:
        target_circle_ids = None

    # 自动创建父级目录
    if os.path.dirname(output_path):
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    headers = ["日期", "场馆", "区域", "摊位号", "社团名", "作者", "类别", "类型", "商品", "数量", "价格", "来源推文", "社交媒体"]

    rows = []
    if target_circle_ids is not None and not target_circle_ids:
        # 有筛选但没有匹配的社团，写表头空表
        pass
    else:
        query = """
            SELECT 
                c.day AS "day",
                c.hall AS "hall",
                c.block AS "block",
                c.space AS "space",
                c.name AS "circle_name",
                c.author AS "circle_author",
                c.genre AS "circle_genre",
                g.type AS "goods_type",
                g.name AS "goods_name",
                1 AS "quantity",
                g.price AS "price",
                cat.tweet_url AS "tweet_url",
                c.twitter_url AS "twitter_url"
            FROM goods g
            JOIN circles c ON g.circle_id = c.id
            LEFT JOIN catalogs cat ON g.catalog_id = cat.id
        """
        params = []
        if target_circle_ids is not None:
            placeholders = ",".join("?" for _ in target_circle_ids)
            query += f" WHERE g.circle_id IN ({placeholders})"
            params.extend(list(target_circle_ids))

        query += " ORDER BY c.day, c.hall, c.block, c.space"

        with get_db_connection(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()

    with open(output_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        for row in rows:
            # 摊位号格式：场馆 + 区域 + 展位号，比如 "东7 A45a"
            hall = row["hall"] or ""
            block = row["block"] or ""
            space = row["space"] or ""
            booth = f"{hall} {block}{space}".strip()

            writer.writerow([
                row["day"],
                row["hall"],
                row["block"],
                booth,
                row["circle_name"],
                row["circle_author"],
                row["circle_genre"],
                row["goods_type"],
                row["goods_name"],
                row["quantity"],
                row["price"],
                row["tweet_url"],
                row["twitter_url"]
            ])
            
    print(f"Successfully exported {len(rows)} goods items to {output_path}")
