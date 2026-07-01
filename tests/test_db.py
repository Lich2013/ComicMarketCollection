import os
import pytest
from src.db import (
    init_db, save_circle, get_all_circles, save_catalog, 
    get_pending_catalogs, update_catalog_status, save_goods, 
    get_db_connection, get_filtered_circle_ids, get_circle
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

def test_get_circle():
    # Test non-existing circle
    assert get_circle(99999, db_path=TEST_DB_PATH) is None

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
    
    save_circle(circle_data, db_path=TEST_DB_PATH)
    res = get_circle(12345, db_path=TEST_DB_PATH)
    assert res is not None
    assert res["name"] == "Test Circle"
    assert res["author"] == "Test Author"

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

def test_save_catalog_on_conflict_update():
    # 验证 ON CONFLICT DO UPDATE 行为
    circle_data = {
        "id": 777,
        "name": "De-dup Circle",
        "author": "Author D",
        "genre": "Original",
        "description": "",
        "hall": "e7",
        "day": "Day2",
        "block": "B",
        "space": "02b",
        "twitter_url": "https://twitter.com/dedup",
        "twitter_username": "dedup",
        "pixiv_url": "",
        "circle_cut_url": ""
    }
    save_circle(circle_data, db_path=TEST_DB_PATH)
    
    # 第一次保存，status = 'pending'
    catalog_data_1 = {
        "circle_id": 777,
        "tweet_id": "1800000000000000000",
        "tweet_url": "https://twitter.com/dedup/status/1800000000000000000",
        "tweet_text": "Original text C107 お品書き",
        "image_path": "data/images/777/image_0.jpg,data/images/777/image_1.jpg",
        "status": "pending"
    }
    save_catalog(catalog_data_1, db_path=TEST_DB_PATH)
    
    # 验证已保存
    pending = get_pending_catalogs(db_path=TEST_DB_PATH)
    assert len(pending) == 1
    assert pending[0]["tweet_id"] == "1800000000000000000"
    assert pending[0]["tweet_text"] == "Original text C107 お品書き"
    assert pending[0]["image_path"] == "data/images/777/image_0.jpg,data/images/777/image_1.jpg"
    
    # 模拟第二次保存（自转归一化后重新导入），文字略有更新，状态依然为 pending 覆盖
    catalog_data_2 = {
        "circle_id": 777,
        "tweet_id": "1800000000000000000",
        "tweet_url": "https://twitter.com/dedup/status/1800000000000000000",
        "tweet_text": "Original text C107 お品書き (Updated)",
        "image_path": "data/images/777/image_0_new.jpg,data/images/777/image_1_new.jpg",
        "status": "pending"
    }
    save_catalog(catalog_data_2, db_path=TEST_DB_PATH)
    
    # 验证只有一条记录，且字段被成功更新
    pending = get_pending_catalogs(db_path=TEST_DB_PATH)
    assert len(pending) == 1
    assert pending[0]["tweet_id"] == "1800000000000000000"
    assert pending[0]["tweet_text"] == "Original text C107 お品書き (Updated)"
    assert pending[0]["image_path"] == "data/images/777/image_0_new.jpg,data/images/777/image_1_new.jpg"

def test_scrape_twitter_profile_retweet_deduplication():
    from unittest.mock import patch, MagicMock
    
    mock_playwright = MagicMock()
    mock_browser = mock_playwright.chromium.launch.return_value
    mock_context = mock_browser.new_context.return_value
    mock_page = mock_context.new_page.return_value
    
    # 拦截 page.on("response", callback)
    registered_callbacks = []
    def mock_on(event_name, callback):
        if event_name == "response":
            registered_callbacks.append(callback)
            
    mock_page.on.side_effect = mock_on
    
    # 当 page.goto 被调用时，模拟触发 response 监听器
    def mock_goto(url, *args, **kwargs):
        # 构造自转推文的 GraphQL 响应
        mock_payload = {
            "data": {
                "user": {
                    "result": {
                        "timeline": {
                            "timeline": {
                                "instructions": [
                                    {
                                        "type": "TimelineAddEntries",
                                        "entries": [
                                            {
                                                "entryId": "tweet-1800000000000000001",
                                                "content": {
                                                    "entryType": "TimelineTimelineItem",
                                                    "itemContent": {
                                                        "itemType": "TimelineTweet",
                                                        "tweet_results": {
                                                            "result": {
                                                                "__typename": "Tweet",
                                                                "rest_id": "1800000000000000001",
                                                                "legacy": {
                                                                    "created_at": "Sat Jun 13 12:00:00 +0000 2026",
                                                                    "full_text": "RT @test_user: original text",
                                                                    "retweeted_status_result": {
                                                                        "result": {
                                                                            "__typename": "Tweet",
                                                                            "rest_id": "1800000000000000000",
                                                                            "legacy": {
                                                                                "created_at": "Sat Jun 06 12:00:00 +0000 2026",
                                                                                "full_text": "original text #品书",
                                                                                "extended_entities": {
                                                                                    "media": [
                                                                                        {
                                                                                            "type": "photo",
                                                                                            "media_url_https": "https://pbs.twimg.com/media/photo1.jpg"
                                                                                        }
                                                                                    ]
                                                                                }
                                                                            }
                                                                        }
                                                                    }
                                                                }
                                                            }
                                                        }
                                                    }
                                                }
                                            }
                                        ]
                                    }
                                ]
                            }
                        }
                    }
                }
            }
        }
        
        mock_response = MagicMock()
        mock_response.url = "https://x.com/i/api/graphql/.../UserTweets"
        mock_response.json.return_value = mock_payload
        
        for cb in registered_callbacks:
            cb(mock_response)
            
    mock_page.goto.side_effect = mock_goto
    mock_page.locator.return_value.first.is_visible.return_value = False
    
    # mock sync_playwright Context Manager
    with patch("src.twitter_sync.sync_playwright") as mock_sync_pw:
        mock_sync_pw.return_value.__enter__.return_value = mock_playwright
        
        # 执行抓取
        from src.twitter_sync import scrape_twitter_profile
        tweets = scrape_twitter_profile("test_user", cookies=None, max_tweets=5, until_date="2026-06-15")
        
        # 验证是否成功归一化为原推 ID
        assert len(tweets) == 1
        assert tweets[0]["tweet_id"] == "1800000000000000000"
        assert tweets[0]["tweet_url"] == "https://x.com/test_user/status/1800000000000000000"
        assert tweets[0]["tweet_text"] == "original text #品书"
        assert tweets[0]["image_urls"] == ["https://pbs.twimg.com/media/photo1.jpg"]


def test_config_tweet_analysis_granular_fallback():
    from src.config import load_config
    import tempfile
    
    config_content = """
openai:
  api_key: "main-key"
  base_url: "main-url"
  model: "main-model"
tweet_analysis:
  enabled: true
  model: "deepseek-v4-flash"
  base_url: "https://api.deepseek.com/v1"
"""
    with tempfile.NamedTemporaryFile("w", delete=False) as temp_f:
        temp_f.write(config_content)
        temp_f_path = temp_f.name
        
    try:
        config = load_config(temp_f_path)
        assert config["tweet_analysis"]["enabled"] is True
        # api_key should fallback to main key
        assert config["tweet_analysis"]["api_key"] == "main-key"
        # model and base_url should keep custom values and NOT fallback
        assert config["tweet_analysis"]["model"] == "deepseek-v4-flash"
        assert config["tweet_analysis"]["base_url"] == "https://api.deepseek.com/v1"
    finally:
        import os
        if os.path.exists(temp_f_path):
            os.remove(temp_f_path)


def test_save_catalog_sqlite_fallback():
    from unittest.mock import patch
    import sqlite3
    from src.db import get_db_connection
    
    class MockCursor:
        def __init__(self, real_cursor):
            self.real_cursor = real_cursor
            
        def execute(self, sql, params=None):
            if isinstance(sql, str) and "RETURNING id" in sql:
                raise sqlite3.OperationalError("near \"RETURNING\": syntax error (mocked)")
            if params is not None:
                return self.real_cursor.execute(sql, params)
            return self.real_cursor.execute(sql)
            
        def fetchone(self):
            return self.real_cursor.fetchone()
            
        def fetchall(self):
            return self.real_cursor.fetchall()
            
        def __getattr__(self, name):
            return getattr(self.real_cursor, name)
            
    class MockConnection:
        def __init__(self, real_conn):
            self.real_conn = real_conn
            
        def cursor(self):
            return MockCursor(self.real_conn.cursor())
            
        def commit(self):
            return self.real_conn.commit()
            
        def execute(self, sql, params=None):
            if isinstance(sql, str) and "RETURNING id" in sql:
                raise sqlite3.OperationalError("near \"RETURNING\": syntax error (mocked)")
            if params is not None:
                return self.real_conn.execute(sql, params)
            return self.real_conn.execute(sql)
            
        def __enter__(self):
            return self
            
        def __exit__(self, exc_type, exc_val, exc_tb):
            return self.real_conn.__exit__(exc_type, exc_val, exc_tb)
            
        def __getattr__(self, name):
            return getattr(self.real_conn, name)

    original_get_db_connection = get_db_connection
    
    def mock_get_db_connection(db_path=TEST_DB_PATH):
        real_conn = original_get_db_connection(db_path)
        return MockConnection(real_conn)
        
    circle_data = {
        "id": 555,
        "name": "Fallback Circle",
        "author": "Author F",
        "genre": "Original",
        "description": "",
        "hall": "e7",
        "day": "Day2",
        "block": "B",
        "space": "02b",
        "twitter_url": "https://twitter.com/fallback",
        "twitter_username": "fallback",
        "pixiv_url": "",
        "circle_cut_url": ""
    }
    save_circle(circle_data, db_path=TEST_DB_PATH)
    
    catalog_data = {
        "circle_id": 555,
        "tweet_id": "fallback_tweet",
        "tweet_url": "https://twitter.com/fallback/status/fallback_tweet",
        "tweet_text": "Here is our catalog!",
        "image_path": "data/images/555/catalog.jpg",
        "status": "pending"
    }
    
    with patch("src.db.get_db_connection", mock_get_db_connection):
        cat_id = save_catalog(catalog_data, db_path=TEST_DB_PATH)
        assert cat_id is not None
        
    # Verify it was successfully saved
    pending = get_pending_catalogs(db_path=TEST_DB_PATH)
    assert len(pending) == 1
    assert pending[0]["tweet_id"] == "fallback_tweet"


def test_scrape_twitter_profile_until_date_filtering():
    from unittest.mock import patch, MagicMock
    from src.twitter_sync import scrape_twitter_profile
    
    mock_playwright = MagicMock()
    mock_browser = mock_playwright.chromium.launch.return_value
    mock_context = mock_browser.new_context.return_value
    mock_page = mock_context.new_page.return_value
    
    registered_callbacks = []
    def mock_on(event_name, callback):
        if event_name == "response":
            registered_callbacks.append(callback)
            
    mock_page.on.side_effect = mock_on
    
    def mock_goto(url, *args, **kwargs):
        # 构造带有不同发布时间的 GraphQL 响应
        mock_payload = {
            "data": {
                "user": {
                    "result": {
                        "timeline": {
                            "timeline": {
                                "instructions": [
                                    {
                                        "type": "TimelineAddEntries",
                                        "entries": [
                                            {
                                                "entryId": "tweet-1800000000000000001",
                                                "content": {
                                                    "entryType": "TimelineTimelineItem",
                                                    "itemContent": {
                                                        "itemType": "TimelineTweet",
                                                        "tweet_results": {
                                                            "result": {
                                                                "__typename": "Tweet",
                                                                "rest_id": "1800000000000000001",
                                                                "legacy": {
                                                                    "created_at": "Sat Jun 06 12:00:00 +0000 2026",
                                                                    "full_text": "C108お品書き 较新推文",
                                                                    "extended_entities": {
                                                                        "media": [{"type": "photo", "media_url_https": "https://pbs.twimg.com/media/photo1.jpg"}]
                                                                    }
                                                                }
                                                            }
                                                        }
                                                    }
                                                }
                                            },
                                            {
                                                "entryId": "tweet-1800000000000000002",
                                                "content": {
                                                    "entryType": "TimelineTimelineItem",
                                                    "itemContent": {
                                                        "itemType": "TimelineTweet",
                                                        "tweet_results": {
                                                            "result": {
                                                                "__typename": "Tweet",
                                                                "rest_id": "1800000000000000002",
                                                                "legacy": {
                                                                    "created_at": "Wed Jun 03 12:00:00 +0000 2026",
                                                                    "full_text": "C108お品書き 目标区间推文",
                                                                    "extended_entities": {
                                                                        "media": [{"type": "photo", "media_url_https": "https://pbs.twimg.com/media/photo2.jpg"}]
                                                                    }
                                                                }
                                                            }
                                                        }
                                                    }
                                                }
                                            },
                                            {
                                                "entryId": "tweet-1800000000000000003",
                                                "content": {
                                                    "entryType": "TimelineTimelineItem",
                                                    "itemContent": {
                                                        "itemType": "TimelineTweet",
                                                        "tweet_results": {
                                                            "result": {
                                                                "__typename": "Tweet",
                                                                "rest_id": "1800000000000000003",
                                                                "legacy": {
                                                                    "created_at": "Sat May 30 12:00:00 +0000 2026",
                                                                    "full_text": "C107お品書き 较旧推文",
                                                                    "extended_entities": {
                                                                        "media": [{"type": "photo", "media_url_https": "https://pbs.twimg.com/media/photo3.jpg"}]
                                                                    }
                                                                }
                                                            }
                                                        }
                                                    }
                                                }
                                            }
                                        ]
                                    }
                                ]
                            }
                        }
                    }
                }
            }
        }
        
        mock_response = MagicMock()
        mock_response.url = "https://x.com/i/api/graphql/.../UserTweets"
        mock_response.json.return_value = mock_payload
        
        for cb in registered_callbacks:
            cb(mock_response)
            
    mock_page.goto.side_effect = mock_goto
    mock_page.locator.return_value.first.is_visible.return_value = False
    
    with patch("src.twitter_sync.sync_playwright") as mock_sync_pw:
        mock_sync_pw.return_value.__enter__.return_value = mock_playwright
        
        # 1. 抓取：指定区间在 2026-06-01 到 2026-06-05 之间
        tweets = scrape_twitter_profile("test_user", cookies=None, max_tweets=5, since_date="2026-06-01", until_date="2026-06-05")
        
        # 只有中间的那一条（Wed Jun 03 12:00:00 +0000 2026）应该被保存
        assert len(tweets) == 1
        assert tweets[0]["tweet_id"] == "1800000000000000002"
        assert tweets[0]["tweet_text"] == "C108お品書き 目标区间推文"


def test_export_goods_to_csv():
    import tempfile
    import csv
    from src.db import export_goods_to_csv
    
    # 1. 插入测试数据
    c1 = {
        "id": 101, "name": "Circle A", "author": "Author A", "genre": "Original",
        "description": "", "hall": "East 1", "day": "Day1", "block": "A", "space": "01a",
        "twitter_url": "https://twitter.com/circlea", "twitter_username": "a", "pixiv_url": "", "circle_cut_url": ""
    }
    c2 = {
        "id": 102, "name": "Circle B", "author": "Author B", "genre": "VTuber",
        "description": "", "hall": "West 1", "day": "Day2", "block": "B", "space": "02b",
        "twitter_url": "https://twitter.com/circleb", "twitter_username": "b", "pixiv_url": "", "circle_cut_url": ""
    }
    save_circle(c1, db_path=TEST_DB_PATH)
    save_circle(c2, db_path=TEST_DB_PATH)
    
    cat1 = {
        "circle_id": 101, "tweet_id": "t1", "tweet_url": "https://x.com/a/status/t1", "tweet_text": "C108新刊",
        "image_path": "path1", "status": "processed"
    }
    cat2 = {
        "circle_id": 102, "tweet_id": "t2", "tweet_url": "https://x.com/b/status/t2", "tweet_text": "C108周边",
        "image_path": "path2", "status": "processed"
    }
    cat1_id = save_catalog(cat1, db_path=TEST_DB_PATH)
    cat2_id = save_catalog(cat2, db_path=TEST_DB_PATH)
    
    goods = [
        {
            "circle_id": 101,
            "catalog_id": cat1_id,
            "name": "Goods A1",
            "type": "新刊",
            "price": 1000,
            "is_set": 0,
            "raw_json": "{}"
        },
        {
            "circle_id": 102,
            "catalog_id": cat2_id,
            "name": "Goods B1",
            "type": "周边",
            "price": 500,
            "is_set": 1,
            "raw_json": "{}"
        }
    ]
    save_goods(goods, db_path=TEST_DB_PATH)
    
    with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".csv") as temp_csv:
        temp_csv_path = temp_csv.name
        
    try:
        # 2. 全量导出验证
        export_goods_to_csv(temp_csv_path, db_path=TEST_DB_PATH)
        
        # 校验带 BOM 的 UTF-8 编码
        with open(temp_csv_path, "r", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            headers = next(reader)
            assert headers == ["日期", "场馆", "区域", "摊位号", "社团名", "作者", "类别", "细分IP", "类型", "商品", "数量", "价格", "来源推文", "社交媒体"]
            
            rows = list(reader)
            assert len(rows) == 2
            
            # 第一行 (Circle A - Day1)
            assert rows[0][0] == "Day1"
            assert rows[0][1] == "East 1"
            assert rows[0][2] == "A"
            assert rows[0][3] == "East 1 A01a"  # 拼接摊位号
            assert rows[0][4] == "Circle A"
            assert rows[0][5] == "Author A"
            assert rows[0][6] == "Original"      # 类别 (genre)
            assert rows[0][7] == ""              # 细分IP (空)
            assert rows[0][8] == "新刊"          # 类型
            assert rows[0][9] == "Goods A1"      # 商品
            assert rows[0][10] == "1"            # 数量
            assert rows[0][11] == "1000"         # 价格
            assert rows[0][12] == "https://x.com/a/status/t1"
            assert rows[0][13] == "https://twitter.com/circlea"
            
        # 3. 按条件筛选导出验证 (只导出 Day2)
        export_goods_to_csv(temp_csv_path, day_list=["Day2"], db_path=TEST_DB_PATH)
        with open(temp_csv_path, "r", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            next(reader) # skip headers
            rows = list(reader)
            assert len(rows) == 1
            assert rows[0][4] == "Circle B"
            assert rows[0][6] == "VTuber"
            
        # 4. 无匹配条件导出验证
        export_goods_to_csv(temp_csv_path, day_list=["Day3"], db_path=TEST_DB_PATH)
        with open(temp_csv_path, "r", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            next(reader)
            rows = list(reader)
            assert len(rows) == 0
            
    finally:
        import os
        if os.path.exists(temp_csv_path):
            os.remove(temp_csv_path)


def test_export_goods_to_csv_with_multiple_catalogs():
    import tempfile
    import csv
    from src.db import export_goods_to_csv
    
    # 1. 写入测试社团
    c1 = {
        "id": 201, "name": "Circle Merge", "author": "Author M", "genre": "Original",
        "description": "", "hall": "East 1", "day": "Day1", "block": "A", "space": "01a",
        "twitter_url": "https://twitter.com/circlemerge", "twitter_username": "merge", "pixiv_url": "", "circle_cut_url": ""
    }
    save_circle(c1, db_path=TEST_DB_PATH)
    
    # 2. 写入两个不同的品书推文
    # 推文 1 (较旧): tweet_id = "1000000000000000001"
    cat1 = {
        "circle_id": 201, "tweet_id": "1000000000000000001", "tweet_url": "https://x.com/merge/status/1000000000000000001", "tweet_text": "品书第一弹",
        "image_path": "path1", "status": "processed"
    }
    # 推文 2 (较新): tweet_id = "1000000000000000002"
    cat2 = {
        "circle_id": 201, "tweet_id": "1000000000000000002", "tweet_url": "https://x.com/merge/status/1000000000000000002", "tweet_text": "品书第二弹",
        "image_path": "path2", "status": "processed"
    }
    cat1_id = save_catalog(cat1, db_path=TEST_DB_PATH)
    cat2_id = save_catalog(cat2, db_path=TEST_DB_PATH)
    
    # 3. 写入商品
    # 推文 1 关联的商品：商品 A (1000円)，商品 B (500円)
    # 推文 2 关联的商品：商品 A (1200円，涨价)，商品 C (800円，追加周边)
    goods = [
        {
            "circle_id": 201, "catalog_id": cat1_id, "name": "商品 A", "type": "新刊", "price": 1000, "is_set": 0, "raw_json": "{}"
        },
        {
            "circle_id": 201, "catalog_id": cat1_id, "name": "商品 B", "type": "既刊", "price": 500, "is_set": 0, "raw_json": "{}"
        },
        {
            "circle_id": 201, "catalog_id": cat2_id, "name": "商品 A", "type": "新刊", "price": 1200, "is_set": 0, "raw_json": "{}"
        },
        {
            "circle_id": 201, "catalog_id": cat2_id, "name": "商品 C", "type": "周边", "price": 800, "is_set": 0, "raw_json": "{}"
        }
    ]
    save_goods(goods, db_path=TEST_DB_PATH)
    
    with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".csv") as temp_csv:
        temp_csv_path = temp_csv.name
        
    try:
        # 4. 执行导出并验证结果
        export_goods_to_csv(temp_csv_path, db_path=TEST_DB_PATH)
        
        with open(temp_csv_path, "r", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            headers = next(reader)
            rows = list(reader)
            
            # 应仅包含商品 A (最新版 1200円)、商品 B (500円)、商品 C (800円)
            assert len(rows) == 3
            
            # 把每一行映射为 name -> price 的字典，以便断言
            goods_dict = {row[9]: int(row[11]) for row in rows}
            
            assert "商品 A" in goods_dict
            assert goods_dict["商品 A"] == 1200  # 取最新的推文 2 价格
            
            assert "商品 B" in goods_dict
            assert goods_dict["商品 B"] == 500   # 保留推文 1 中的商品 B
            
            assert "商品 C" in goods_dict
            assert goods_dict["商品 C"] == 800   # 保留推文 2 中的商品 C
            
    finally:
        import os
        if os.path.exists(temp_csv_path):
            os.remove(temp_csv_path)






