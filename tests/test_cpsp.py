import os
import json
import tempfile
import sqlite3
import pytest
from src.cpsp_importer import import_cpsp_dataset

def test_cpsp_import():
    # 1. Create temporary directory for mock JSON files
    with tempfile.TemporaryDirectory() as tmpdir:
        # Write mock json data
        mock_data = {
            "isSuccess": True,
            "result": {
                "total": 1,
                "list": [
                    {
                        "doujinshiId": 1221406,
                        "doujinshiName": "图奈《黎明将至》场限版",
                        "themeAlias": "苏丹的游戏",
                        "tag": "图奈|阿尔图",
                        "type": "漫画",
                        "sellStatus": "仅供现场",
                        "hotCount": 8111,
                        "circleID": 7582,
                        "circleName": "烤画组",
                        "eventList": [
                            {
                                "positionName": "苗圃教育从娃娃抓起",
                                "position": "叁M65叁M66",
                                "eventName": "COMICUP SHANGHAI PLUS"
                            }
                        ]
                    }
                ]
            }
        }
        
        with open(os.path.join(tmpdir, "day1-36-1.json"), "w", encoding="utf-8") as f:
            json.dump(mock_data, f)
            
        # 2. Setup mock sqlite database
        db_fd, db_path = tempfile.mkstemp()
        try:
            # Import dataset
            success = import_cpsp_dataset(tmpdir, db_path=db_path)
            assert success is True
            
            # Check db entries
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM cpsp_products")
            assert cursor.fetchone()[0] == 1
            
            cursor.execute("SELECT COUNT(*) FROM cpsp_circles")
            assert cursor.fetchone()[0] == 1
            
            cursor.execute("SELECT name, theme_alias, type, sell_status, hot_count, tags, circle_id FROM cpsp_products WHERE doujinshi_id = 1221406")
            row = cursor.fetchone()
            assert row[0] == "图奈《黎明将至》场限版"
            assert row[1] == "苏丹的游戏"
            assert row[2] == "漫画"
            assert row[3] == "仅供现场"
            assert row[4] == 8111
            assert row[5] == "图奈|阿尔图"
            assert row[6] == 7582
            
            cursor.execute("SELECT name, position_name, position FROM cpsp_circles WHERE circle_id = 7582")
            row = cursor.fetchone()
            assert row[0] == "烤画组"
            assert row[1] == "苗圃教育从娃娃抓起"
            assert row[2] == "叁M65叁M66"
            
            conn.close()
            
            # Test idempotency (should overwrite/not fail)
            success_retry = import_cpsp_dataset(tmpdir, db_path=db_path)
            assert success_retry is True
            
        finally:
            os.close(db_fd)
            os.remove(db_path)
