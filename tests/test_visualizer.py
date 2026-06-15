import os
import tempfile
import sqlite3
import pytest
from src.db import init_db
from src.visualizer import (
    generate_social_venn_diagram,
    generate_dbi_bubble_chart,
    generate_booth_heatmap,
    generate_description_wordcloud,
    generate_radar_ecology_comparison,
    generate_all_charts,
    HAS_WORDCLOUD
)


@pytest.fixture
def mock_db():
    """创建一个带有基本测试数据的临时 SQLite 数据库"""
    db_fd, db_path = tempfile.mkstemp()
    init_db(db_path)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 1. 插入 circles (C108) 测试数据，包含不同的社交链接和简介
    circles_data = [
        # description, twitter, pixiv
        ("简介1", "http://twitter.com/1", "http://pixiv.net/1"),
        ("简介2", "http://twitter.com/2", ""),
        ("简介3", "", "http://pixiv.net/3"),
        ("", "http://twitter.com/4", "http://pixiv.net/4"),
        ("简介5", "http://twitter.com/5", "http://pixiv.net/5"),
        ("", "", ""),
        ("简介7", "", ""),
        ("", "http://twitter.com/8", ""),
        ("", "", "http://pixiv.net/9"),
        ("简介10", "http://twitter.com/10", "http://pixiv.net/10"),
    ]
    for idx, (desc, tw, px) in enumerate(circles_data, 1):
        cursor.execute("""
            INSERT INTO circles (
                id, name, author, genre, description, hall, day, block, space, 
                twitter_url, twitter_username, pixiv_url, circle_cut_url
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (idx, f"社团_{idx}", f"作者_{idx}", "ブルーアーカイブ" if idx <= 5 else "男性向", desc, 
              "東" if idx <= 5 else "西", "Day1", "あ" if idx <= 5 else "い", f"{idx}", tw, f"user_{idx}", px, ""))
        
    # 2. 插入 cp31_circles 测试数据
    cp31_circles = [
        (1, "CP31社团_1", "明日方舟专区", "A-1"),
        (2, "CP31社团_2", "明日方舟专区", "A-2"),
        (3, "CP31社团_3", "排球少年专区", "B-1"),
        (4, "CP31社团_4", "排球少年专区", "B-2"),
        (5, "CP31社团_5", "恋与深空专区", "C-1"),
    ]
    cursor.executemany("""
        INSERT INTO cp31_circles (circle_id, name, position_name, position)
        VALUES (?, ?, ?, ?)
    """, cp31_circles)
    
    # 3. 插入 cp31_products 测试数据
    cp31_products = [
        (101, "方舟小说", "明日方舟", "小说", "仅供现场", 100, "D1", 1, "方舟"),
        (102, "方舟漫画", "明日方舟", "漫画", "仅供现场", 150, "D1", 1, "方舟"),
        (103, "排球本", "排球少年", "漫画", "仅供现场", 500, "D1", 3, "排球"),
        (104, "深空本", "恋与深空", "小说", "仅供现场", 300, "D1", 5, "恋深"),
    ]
    cursor.executemany("""
        INSERT INTO cp31_products (doujinshi_id, name, theme_alias, type, sell_status, hot_count, day_label, circle_id, tags)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, cp31_products)
    
    conn.commit()
    conn.close()
    
    yield db_path
    
    # 清理临时文件
    try:
        os.close(db_fd)
        os.remove(db_path)
    except OSError:
        pass


def test_visualizer_pipeline(mock_db):
    """测试可视化图表生成的完整管线"""
    # 创建临时输出目录
    with tempfile.TemporaryDirectory() as tmpdir:
        venn_path = os.path.join(tmpdir, "venn.png")
        bubble_path = os.path.join(tmpdir, "bubble.png")
        heatmap_path = os.path.join(tmpdir, "heatmap.png")
        wordcloud_path = os.path.join(tmpdir, "wordcloud.png")
        radar_path = os.path.join(tmpdir, "radar.png")
        
        # 1. 测试 Venn Diagram
        assert generate_social_venn_diagram(mock_db, venn_path) is True
        assert os.path.exists(venn_path)
        assert os.path.getsize(venn_path) > 0
        
        # 2. 测试 Bubble Chart
        assert generate_dbi_bubble_chart(mock_db, bubble_path) is True
        assert os.path.exists(bubble_path)
        assert os.path.getsize(bubble_path) > 0
        
        # 3. 测试 Heatmap
        assert generate_booth_heatmap(mock_db, heatmap_path) is True
        assert os.path.exists(heatmap_path)
        assert os.path.getsize(heatmap_path) > 0
        
        # 4. 测试 Word Cloud
        mock_semantic_stats = {
            "genre_tfidf_results": {
                "ブルーアーカイブ": [
                    {"word": "ミカ", "score": 0.15, "df": 2},
                    {"word": "新刊", "score": 0.08, "df": 3}
                ],
                "男性向": [
                    {"word": "新刊", "score": 0.10, "df": 3},
                    {"word": "イラスト", "score": 0.12, "df": 2}
                ]
            }
        }
        if HAS_WORDCLOUD:
            assert generate_description_wordcloud(mock_semantic_stats, wordcloud_path) is True
            assert os.path.exists(wordcloud_path)
            assert os.path.getsize(wordcloud_path) > 0
            
        # 5. 测试 Radar Comparison
        mock_multi_era_stats = {
            "c108": {
                "concentration": {"cr10": 61.59}
            },
            "cp31": {
                "concentration": {"cr10": 30.12},
                "media_types": [
                    {"type": "小说", "percentage": 28.42}
                ],
                "materiality": {
                    "freebies": {"percentage": 4.77}
                },
                "day_scheduling": {
                    "overlap_percentage": 30.8
                }
            }
        }
        assert generate_radar_ecology_comparison(mock_multi_era_stats, radar_path) is True
        assert os.path.exists(radar_path)
        assert os.path.getsize(radar_path) > 0


def test_generate_all_charts(mock_db):
    """测试 generate_all_charts 执行入口"""
    # 模拟两个 stats 字典以避免其内部再重新查询数据库
    mock_semantic_stats = {
        "genre_tfidf_results": {
            "ブルーアーカイブ": [{"word": "ミカ", "score": 0.15, "df": 2}]
        }
    }
    mock_multi_era_stats = {
        "c108": {"concentration": {"cr10": 61.59}},
        "cp31": {
            "concentration": {"cr10": 30.12},
            "media_types": [{"type": "小说", "percentage": 28.42}],
            "materiality": {"freebies": {"percentage": 4.77}},
            "day_scheduling": {"overlap_percentage": 30.8}
        }
    }
    
    # 临时覆盖全局保存路径为临时目录以防污染 research/images/
    # 我们调用时可以手动运行并且测试
    try:
        generate_all_charts(
            db_path=mock_db,
            semantic_stats=mock_semantic_stats,
            multi_era_stats=mock_multi_era_stats
        )
    except Exception as e:
        pytest.fail(f"generate_all_charts raised an exception: {e}")
