import os
import pytest
from src.db import (
    init_db, save_circle, get_all_circles, save_catalog, 
    get_pending_catalogs, update_catalog_status, save_goods, 
    get_db_connection, get_filtered_circle_ids
)
from src.circle_sync import extract_twitter_username
from src.twitter_sync import is_potential_catalog, parse_cookie_string

TEST_DB_PATH = "data/test_comic_market.db"

@pytest.fixture(autouse=True)
def setup_and_teardown():
    # 清理已存在的测试数据库
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)
    
    # 初始化
    init_db(TEST_DB_PATH)
    
    yield
    
    # 清理
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)

def test_save_and_get_circle():
    circle_data = {
        "id": 12345,
        "name": "Test Circle",
        "author": "Test Author",
        "genre": "Original",
        "description": "Test Description",
        "hall": "e123",
        "day": "Day1",
        "block": "A",
        "space": "01a",
        "twitter_url": "https://twitter.com/test",
        "twitter_username": "test",
        "pixiv_url": "https://pixiv.net/test",
        "circle_cut_url": "https://circle.ms/cut.png"
    }
    
    # 保存社团
    save_circle(circle_data, db_path=TEST_DB_PATH)
    
    # 读取社团
    circles = get_all_circles(db_path=TEST_DB_PATH)
    assert len(circles) == 1
    assert circles[0]["name"] == "Test Circle"
    assert circles[0]["twitter_username"] == "test"
    
    # 测试更新 (On Conflict Do Update)
    circle_data["name"] = "Updated Name"
    save_circle(circle_data, db_path=TEST_DB_PATH)
    
    circles = get_all_circles(db_path=TEST_DB_PATH)
    assert len(circles) == 1
    assert circles[0]["name"] == "Updated Name"

def test_save_catalog_and_status():
    circle_data = {
        "id": 999,
        "name": "Another Circle",
        "author": "Another Author",
        "genre": "Original",
        "description": "",
        "hall": "e7",
        "day": "Day2",
        "block": "B",
        "space": "02b",
        "twitter_url": "https://twitter.com/another",
        "twitter_username": "another",
        "pixiv_url": "",
        "circle_cut_url": ""
    }
    save_circle(circle_data, db_path=TEST_DB_PATH)
    
    catalog_data = {
        "circle_id": 999,
        "tweet_id": "tweet123",
        "tweet_url": "https://twitter.com/another/status/tweet123",
        "tweet_text": "Here is our C107 catalog!",
        "image_path": "data/images/999/catalog.jpg",
        "status": "pending"
    }
    
    # 保存品书
    cat_id = save_catalog(catalog_data, db_path=TEST_DB_PATH)
    assert cat_id is not None
    
    # 查询待处理
    pending = get_pending_catalogs(db_path=TEST_DB_PATH)
    assert len(pending) == 1
    assert pending[0]["tweet_id"] == "tweet123"
    assert pending[0]["circle_name"] == "Another Circle"
    
    # 更新状态为已处理
    update_catalog_status(cat_id, "processed", db_path=TEST_DB_PATH)
    
    # 再次查询待处理，应当为空
    pending = get_pending_catalogs(db_path=TEST_DB_PATH)
    assert len(pending) == 0

def test_save_goods():
    circle_data = {
        "id": 888,
        "name": "Goods Circle",
        "author": "Author X",
        "genre": "Original",
        "description": "",
        "hall": "e7",
        "day": "Day2",
        "block": "B",
        "space": "02b",
        "twitter_url": "https://twitter.com/another",
        "twitter_username": "another",
        "pixiv_url": "",
        "circle_cut_url": ""
    }
    save_circle(circle_data, db_path=TEST_DB_PATH)
    
    catalog_data = {
        "circle_id": 888,
        "tweet_id": "tweet888",
        "tweet_url": "https://twitter.com/another/status/tweet888",
        "tweet_text": "Here is our catalog!",
        "image_path": "data/images/888/catalog.jpg",
        "status": "pending"
    }
    cat_id = save_catalog(catalog_data, db_path=TEST_DB_PATH)
    
    goods_list = [
        {
            "circle_id": 888,
            "catalog_id": cat_id,
            "name": "新刊セット",
            "type": "套装",
            "price": 2000,
            "is_set": 1,
            "raw_json": "{}"
        },
        {
            "circle_id": 888,
            "catalog_id": cat_id,
            "name": "アクリルキーホルダー",
            "type": "周边",
            "price": 500,
            "is_set": 0,
            "raw_json": "{}"
        }
    ]
    
    # 保存商品
    save_goods(goods_list, db_path=TEST_DB_PATH)
    
    # 验证数据库中商品存在
    with get_db_connection(TEST_DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM goods WHERE circle_id = 888")
        rows = cursor.fetchall()
        assert len(rows) == 2
        assert rows[0]["name"] == "新刊セット"
        assert rows[0]["price"] == 2000
        assert rows[0]["is_set"] == 1
        assert rows[1]["name"] == "アクリルキーホルダー"
        assert rows[1]["price"] == 500

def test_extract_twitter_username():
    assert extract_twitter_username("https://twitter.com/test_user") == "test_user"
    assert extract_twitter_username("http://x.com/user_123?s=20") == "user_123"
    assert extract_twitter_username("@username") == "username"
    assert extract_twitter_username("just_user") == "just_user"
    assert extract_twitter_username("") is None
    assert extract_twitter_username(None) is None

def test_is_potential_catalog():
    # 测试基本关键字匹配
    assert is_potential_catalog("这是我们的新刊！") is True
    assert is_potential_catalog("お品書きはこちら") is True
    assert is_potential_catalog("今天晚饭吃拉面") is False
    
    # 测试通用 CM / 日期匹配
    assert is_potential_catalog("C108新情報") is True
    assert is_potential_catalog("8/15会去参加コミケ") is True
    assert is_potential_catalog("土曜日はよろしくお願いします") is True
    
    # 测试社团特定匹配
    circle = {
        "name": "キノコの王様",
        "author": "キノキング",
        "hall": "東7",
        "block": "A",
        "space": "45a"
    }
    # 匹配社团名称
    assert is_potential_catalog("キノコの王様的新作", circle) is True
    # 匹配作者名称
    assert is_potential_catalog("キノキング发布了新图", circle) is True
    # 匹配展位号
    assert is_potential_catalog("我们在东7厅A45a", circle) is True
    assert is_potential_catalog("摊位是A-45a", circle) is True
    assert is_potential_catalog("東A 45a", circle) is True
    assert is_potential_catalog("摊位是B-12b", circle) is False

def test_get_filtered_circle_ids_and_pending():
    # 1. 写入测试社团
    c1 = {
        "id": 100, "name": "Circle A", "author": "Author A", "genre": "Original",
        "description": "", "hall": "East 1", "day": "Day1", "block": "A", "space": "01a",
        "twitter_url": "", "twitter_username": "a", "pixiv_url": "", "circle_cut_url": ""
    }
    c2 = {
        "id": 101, "name": "Circle B", "author": "Author B", "genre": "Original",
        "description": "", "hall": "East 2", "day": "Day2", "block": "B", "space": "02b",
        "twitter_url": "", "twitter_username": "b", "pixiv_url": "", "circle_cut_url": ""
    }
    c3 = {
        "id": 102, "name": "Circle C", "author": "Author C", "genre": "Original",
        "description": "", "hall": "West 1", "day": "Day2", "block": "C", "space": "03c",
        "twitter_url": "", "twitter_username": "c", "pixiv_url": "", "circle_cut_url": ""
    }
    save_circle(c1, db_path=TEST_DB_PATH)
    save_circle(c2, db_path=TEST_DB_PATH)
    save_circle(c3, db_path=TEST_DB_PATH)

    # 2. 测试各种单维度过滤
    # 天数过滤
    ids = get_filtered_circle_ids(day_list=["Day2"], db_path=TEST_DB_PATH)
    assert ids == {101, 102}

    # 场馆过滤
    ids = get_filtered_circle_ids(hall_list=["East 2"], db_path=TEST_DB_PATH)
    assert ids == {101}

    # ID 列表过滤
    ids = get_filtered_circle_ids(circle_ids=[100, 102], db_path=TEST_DB_PATH)
    assert ids == {100, 102}

    # 模糊名匹配
    ids = get_filtered_circle_ids(name_query="Circle", db_path=TEST_DB_PATH)
    assert ids == {100, 101, 102}

    # 模糊作者匹配
    ids = get_filtered_circle_ids(name_query="Author B", db_path=TEST_DB_PATH)
    assert ids == {101}

    # 无匹配
    ids = get_filtered_circle_ids(name_query="NonExistent", db_path=TEST_DB_PATH)
    assert ids == set()

    # 3. 测试组合过滤
    ids = get_filtered_circle_ids(
        day_list=["Day2"], 
        hall_list=["East 2", "West 1"], 
        circle_ids=[101], 
        name_query="Circle B", 
        db_path=TEST_DB_PATH
    )
    assert ids == {101}

    # 4. 测试 get_pending_catalogs 的过滤能力
    cat1_data = {
        "circle_id": 100, "tweet_id": "t1", "tweet_url": "", "tweet_text": "text1",
        "image_path": "path1", "status": "pending"
    }
    cat2_data = {
        "circle_id": 101, "tweet_id": "t2", "tweet_url": "", "tweet_text": "text2",
        "image_path": "path2", "status": "pending"
    }
    save_catalog(cat1_data, db_path=TEST_DB_PATH)
    save_catalog(cat2_data, db_path=TEST_DB_PATH)

    # 过滤 100
    pending = get_pending_catalogs(db_path=TEST_DB_PATH, circle_ids={100})
    assert len(pending) == 1
    assert pending[0]["circle_id"] == 100

    # 过滤 101
    pending = get_pending_catalogs(db_path=TEST_DB_PATH, circle_ids={101})
    assert len(pending) == 1
    assert pending[0]["circle_id"] == 101

    # 空集合
    pending = get_pending_catalogs(db_path=TEST_DB_PATH, circle_ids=set())
    assert len(pending) == 0

    # None (全量)
    pending = get_pending_catalogs(db_path=TEST_DB_PATH, circle_ids=None)
    assert len(pending) == 2

def test_parse_cookie_string():
    cookie_str = "auth_token=abcdef123456; ct0=xyz789; guest_id=v1%3A111"
    cookies = parse_cookie_string(cookie_str)
    assert len(cookies) == 3
    
    assert cookies[0]["name"] == "auth_token"
    assert cookies[0]["value"] == "abcdef123456"
    assert cookies[0]["domain"] == ".x.com"
    assert cookies[0]["path"] == "/"
    
    assert cookies[1]["name"] == "ct0"
    assert cookies[1]["value"] == "xyz789"
    
    assert cookies[2]["name"] == "guest_id"
    assert cookies[2]["value"] == "v1%3A111"
    
    # 空字符串测试
    assert parse_cookie_string("") == []
    assert parse_cookie_string(None) == []
    
    # 畸形字符串测试
    bad_cookie = "bad_format; name=value"
    cookies = parse_cookie_string(bad_cookie)
    assert len(cookies) == 1
    assert cookies[0]["name"] == "name"
    assert cookies[0]["value"] == "value"

def test_config_tweet_analysis():
    from src.config import load_config
    import tempfile
    
    # 建立测试用 config 文件
    config_content = """
openai:
  api_key: "main-key"
  base_url: "main-url"
  model: "main-model"
tweet_analysis:
  enabled: true
"""
    with tempfile.NamedTemporaryFile("w", delete=False) as temp_f:
        temp_f.write(config_content)
        temp_f_path = temp_f.name
        
    try:
        config = load_config(temp_f_path)
        assert config["tweet_analysis"]["enabled"] is True
        # 验证智能回退
        assert config["tweet_analysis"]["api_key"] == "main-key"
        assert config["tweet_analysis"]["base_url"] == "main-url"
        assert config["tweet_analysis"]["model"] == "main-model"
    finally:
        import os
        if os.path.exists(temp_f_path):
            os.remove(temp_f_path)


