import os
import json
import pytest
from src.db import init_db, save_circle
from src.analytics import calculate_genre_distribution, AUDIENCE_POPULARITY_BASELINE

TEST_DB_PATH = "data/test_analytics_comic_market.db"
TEST_OUTPUT_PATH = "data/test_genre_analysis.json"

@pytest.fixture(autouse=True)
def setup_and_teardown():
    # Setup: clean up files
    for path in [TEST_DB_PATH, TEST_OUTPUT_PATH]:
        if os.path.exists(path):
            os.remove(path)
            
    yield
    
    # Teardown: clean up files
    for path in [TEST_DB_PATH, TEST_OUTPUT_PATH]:
        if os.path.exists(path):
            os.remove(path)

def test_calculate_genre_distribution_success():
    # Initialize DB
    init_db(TEST_DB_PATH)
    
    # Insert mock circles
    # Total circles with valid genres: 10
    # ブルーアーカイブ: 4 (Saturday/土, East/東)
    # 男性向: 3 (Sunday/日, East/東)
    # VTuber: 2 (Saturday/土, West/西)
    # コスプレ: 1 (Sunday/日, South/南)
    mock_circles = [
        {"id": 1, "name": "C1", "author": "A1", "genre": "ブルーアーカイブ", "day": "土", "hall": "東", "block": "A", "space": "01"},
        {"id": 2, "name": "C2", "author": "A2", "genre": "ブルーアーカイブ", "day": "土", "hall": "東", "block": "A", "space": "02"},
        {"id": 3, "name": "C3", "author": "A3", "genre": "ブルーアーカイブ", "day": "土", "hall": "東", "block": "A", "space": "03"},
        {"id": 4, "name": "C4", "author": "A4", "genre": "ブルーアーカイブ", "day": "土", "hall": "東", "block": "A", "space": "04"},
        
        {"id": 5, "name": "C5", "author": "A5", "genre": "男性向", "day": "日", "hall": "東", "block": "B", "space": "01"},
        {"id": 6, "name": "C6", "author": "A6", "genre": "男性向", "day": "日", "hall": "東", "block": "B", "space": "02"},
        {"id": 7, "name": "C7", "author": "A7", "genre": "男性向", "day": "日", "hall": "東", "block": "B", "space": "03"},
        
        {"id": 8, "name": "C8", "author": "A8", "genre": "VTuber", "day": "土", "hall": "西", "block": "C", "space": "01"},
        {"id": 9, "name": "C9", "author": "A9", "genre": "VTuber", "day": "土", "hall": "西", "block": "C", "space": "02"},
        
        {"id": 10, "name": "C10", "author": "A10", "genre": "コスプレ", "day": "日", "hall": "南", "block": "D", "space": "01"},
    ]
    
    for circle in mock_circles:
        for key in ["description", "twitter_url", "twitter_username", "pixiv_url", "circle_cut_url"]:
            circle[key] = ""
        save_circle(circle, db_path=TEST_DB_PATH)
        
    # Run calculation
    report = calculate_genre_distribution(db_path=TEST_DB_PATH, output_path=TEST_OUTPUT_PATH)
    
    # Assert return structure
    assert report["summary"]["total_circles"] == 10
    assert report["summary"]["total_genres"] == 4
    
    # Global Rank (Ordered descending by circle count)
    ranks = report["global_rank"]
    assert len(ranks) == 4
    assert ranks[0]["genre"] == "ブルーアーカイブ"
    assert ranks[0]["count"] == 4
    assert ranks[0]["ratio"] == 40.0
    # DBI = 40.0 / 4.0 = 10.0
    assert ranks[0]["dbi"] == 10.0
    
    assert ranks[1]["genre"] == "男性向"
    assert ranks[1]["count"] == 3
    assert ranks[1]["ratio"] == 30.0
    # DBI = 30.0 / 10.0 = 3.0
    assert ranks[1]["dbi"] == 3.0
    
    # Day Comparison
    day_comp = report["day_comparison"]
    ba_comp = next(item for item in day_comp if item["genre"] == "ブルーアーカイブ")
    assert ba_comp["day1"] == 4
    assert ba_comp["day2"] == 0
    
    m_comp = next(item for item in day_comp if item["genre"] == "男性向")
    assert m_comp["day1"] == 0
    assert m_comp["day2"] == 3
    
    # Hall Matrix
    halls = report["hall_matrix"]
    assert len(halls["East"]) == 2
    assert len(halls["West"]) == 1
    assert len(halls["South"]) == 1
    
    east_ba = next(item for item in halls["East"] if item["genre"] == "ブルーアーカイブ")
    assert east_ba["count"] == 4
    
    # Output file verification
    assert os.path.exists(TEST_OUTPUT_PATH)
    with open(TEST_OUTPUT_PATH, "r", encoding="utf-8") as f:
        file_report = json.load(f)
    assert file_report["summary"]["total_circles"] == 10
    assert file_report["summary"]["total_genres"] == 4

def test_calculate_genre_distribution_missing_db():
    with pytest.raises(FileNotFoundError):
        calculate_genre_distribution(db_path="non_existent_db_file_123.db")

def test_calculate_genre_distribution_empty_db():
    init_db(TEST_DB_PATH)
    report = calculate_genre_distribution(db_path=TEST_DB_PATH)
    assert report["summary"]["total_circles"] == 0
    assert report["summary"]["total_genres"] == 0
    assert len(report["global_rank"]) == 0
