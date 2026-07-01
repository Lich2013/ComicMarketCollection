import os
import tempfile
import sqlite3
import pytest
from src.db import init_db, get_db_connection
from src.circle_tagger import run_circle_tagging

def test_circle_ip_tagger_and_propagation():
    # 1. Setup mock SQLite database
    db_fd, db_path = tempfile.mkstemp()
    try:
        # Initialize tables & view (Tests Task 1.1)
        init_db(db_path)
        
        # 2. Insert mock circles mimicking C108 physical layout
        conn = get_db_connection(db_path)
        cursor = conn.cursor()
        
        circles_data = [
            # ID, Name, Author, Genre, Description, Hall, Day, Block, Space
            (1001, "Alluvial Comet", "藤川フレ", "ゲーム(ネット・ソーシャル)", "", "西", "土", "め", "01a"),
            (1002, "金星航天局", "ウェルト", "ゲーム(ネット・ソーシャル)", "イラスト本と手作りグッズです", "西", "土", "め", "01b"),
            (1003, "こはくきつね", "浅井ガミ", "ゲーム(ネット・ソーシャル)", "ブルーアーカイブやアークナイツなどのイラスト本を出します", "西", "土", "め", "02b"), # Seed 1
            (1004, "わるいこだれだ", "棉きのし", "ゲーム(ネット・ソーシャル)", "", "西", "土", "め", "03b"),
            (1005, "はちみつ☆サワークリーム", "夜月", "ゲーム(ネット・ソーシャル)", "【アークナイツ エンドフィールド】今度はアークナイツで参加します", "西", "土", "め", "06b"), # Seed 2
            (1006, "ぷにぷに亭", "うろこ", "ゲーム(ネット・ソーシャル)", "アークナイツ、エンドフィールド合同イラスト集", "西", "土", "め", "09a"), # Seed 3
            (1007, "techicoo", "远田", "オリジナル雑貨", "装画メインのオリジナル作品集", "西", "土", "め", "15a"), # Non-matching out-of-range booth
            (1008, "ギア工房", "兼志谷", "アリス・ギア・アイギス", "新刊あります", "西", "土", "め", "20a") # New Seed 5 (via genre)
        ]
        
        cursor.executemany("""
            INSERT INTO circles (id, name, author, genre, description, hall, day, block, space)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, circles_data)
        
        # Insert a mock good for testing goods-based seed tagging
        # Circle 1002 has empty description but let's say we parsed Arknights goods for it
        cursor.execute("""
            INSERT INTO catalogs (id, circle_id, tweet_id, tweet_url, status)
            VALUES (1, 1002, 'tweet123', 'https://twitter.com/1', 'processed')
        """)
        cursor.execute("""
            INSERT INTO goods (circle_id, catalog_id, name, type, price)
            VALUES (1002, 1, 'アークナイツ アーミヤアクキー', 'グッズ', 500)
        """) # Seed 4 (via goods)
        
        conn.commit()
        conn.close()
        
        # 3. Run the circle tagger pipeline
        success = run_circle_tagging(db_path=db_path)
        assert success is True
        
        # 4. Assert correctness
        conn = get_db_connection(db_path)
        cursor = conn.cursor()
        
        # Check total tags written (Seeds + Propagated)
        cursor.execute("SELECT COUNT(*) FROM circle_ip_tags")
        # 1002 (明日方舟 - goods), 1003 (明日方舟 - keyword), 1003 (蔚蓝档案 - keyword)
        # 1005 (明日方舟 - keyword), 1006 (明日方舟 - keyword) = 5 seed tags
        # 1008 (爱丽丝机甲 - genre matching) = 1 seed tag
        # 1001 (明日方舟 - spatial), 1004 (明日方舟 - spatial) = 2 propagated tags
        # Total expected tags = 8
        assert cursor.fetchone()[0] == 8
        
        # Query using view (Tests Task 1.1 View behavior)
        cursor.execute("""
            SELECT circle_name, space, ip_tag, confidence, tag_source 
            FROM v_circles_with_ip_tags 
            ORDER BY space, ip_tag
        """)
        rows = cursor.fetchall()
        
        # 1001 (01a): spatial tag
        assert rows[0]["space"] == "01a"
        assert rows[0]["ip_tag"] == "明日方舟"
        assert 0.3 <= rows[0]["confidence"] <= 1.0
        assert rows[0]["tag_source"] == "spatial"
        
        # 1002 (01b): goods seed tag
        assert rows[1]["space"] == "01b"
        assert rows[1]["ip_tag"] == "明日方舟"
        assert rows[1]["confidence"] == 1.0
        assert rows[1]["tag_source"] == "goods"
        
        # 1003 (02b): keyword seed tag
        assert rows[2]["space"] == "02b"
        assert rows[2]["ip_tag"] == "明日方舟"
        assert rows[2]["confidence"] == 1.0
        assert rows[2]["tag_source"] == "keyword"
        
        # 1007 (15a): no tag
        assert len(rows) == 9
        assert rows[7]["space"] == "15a"
        assert rows[7]["ip_tag"] is None
        
        # 1008 (20a): new seed tag (爱丽丝机甲)
        assert rows[8]["space"] == "20a"
        assert rows[8]["ip_tag"] == "爱丽丝机甲"
        assert rows[8]["confidence"] == 1.0
        assert rows[8]["tag_source"] == "keyword"
        
        conn.close()
        
        # 5. Verify Idempotency (ON CONFLICT REPLACE)
        success_retry = run_circle_tagging(db_path=db_path)
        assert success_retry is True
        
    finally:
        os.close(db_fd)
        os.remove(db_path)
