import os
import json
import tempfile
import sqlite3
import pytest
from src.c107_importer import import_c107_dataset

def test_c107_import():
    # 1. Create temporary directory for mock JSON files
    with tempfile.TemporaryDirectory() as tmpdir:
        tables_dir = os.path.join(tmpdir, "tables")
        os.makedirs(tables_dir)
        
        # Write mock json data
        mock_data = {
            "Id": 22000003,
            "CircleId": 10486131,
            "Name": "ごまんどる",
            "Author": "ずんべらぼん子",
            "IsReject": False,
            "Hall": "東",
            "Day": "水",
            "Block": "Ｃ",
            "Space": "26a",
            "Genre": "男性向",
            "CircleCutUrls": [
                "/Spa/CachedImage/22000003/1/4d315cca-2d22-4ba3-8f97-591d92120883/3967235873626"
            ],
            "PixivUrl": "https://www.pixiv.net/member.php?id=2212458",
            "TwitterUrl": "https://twitter.com/mugi_humi",
            "Description": "テスト説明"
        }
        
        with open(os.path.join(tables_dir, "22000003.json"), "w", encoding="utf-8") as f:
            json.dump(mock_data, f)
            
        # 2. Setup mock sqlite database
        db_fd, db_path = tempfile.mkstemp()
        try:
            # Import dataset
            success = import_c107_dataset(tmpdir, db_path=db_path)
            assert success is True
            
            # Check db entries
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM c107_circles")
            assert cursor.fetchone()[0] == 1
            
            cursor.execute("SELECT name, author, genre, twitter_username, circle_cut_url FROM c107_circles WHERE id = 22000003")
            row = cursor.fetchone()
            assert row[0] == "ごまんどる"
            assert row[1] == "ずんべらぼん子"
            assert row[2] == "男性向"
            assert row[3] == "mugi_humi"
            assert row[4] == "https://webcatalog.circle.ms/Spa/CachedImage/22000003/1/4d315cca-2d22-4ba3-8f97-591d92120883/3967235873626"
            
            conn.close()
            
            # Test idempotency (should overwrite/not fail)
            success_retry = import_c107_dataset(tmpdir, db_path=db_path)
            assert success_retry is True
            
        finally:
            os.close(db_fd)
            os.remove(db_path)
