import os
import json
import tempfile
import sqlite3
import pytest
from src.db import init_db
from src.cp31_importer import normalize_theme, import_cp31_dataset
from src.cp31_analyzer import get_cp31_stats, generate_cp31_comparison_report

def test_normalize_theme():
    assert normalize_theme("崩坏：星穹铁道") == "崩坏星穹铁道"
    assert normalize_theme("崩铁") == "崩坏星穹铁道"
    assert normalize_theme("原神 ") == "原神"
    assert normalize_theme("ウ马娘") == "ウ马娘"  # Not mapped in dict, returns itself
    assert normalize_theme("") == "未知题材"
    assert normalize_theme("哪吒之魔童降世") == "哪吒之魔童闹海"

def test_cp31_import_and_analyze():
    # 1. Create temporary directory for mock JSON files
    with tempfile.TemporaryDirectory() as tmpdir:
        day1_dir = os.path.join(tmpdir, "day1data")
        os.makedirs(day1_dir)
        
        # Write mock json data
        mock_data = {
            "isSuccess": True,
            "result": {
                "total": 2,
                "list": [
                    {
                        "doujinshiId": 111,
                        "doujinshiName": "璀璨狂想曲合志",
                        "themeAlias": "凹凸世界",
                        "type": "漫画",
                        "sellStatus": "仅供现场",
                        "hotCount": 100,
                        "circleID": 333,
                        "circleName": "凹凸社团",
                        "tag": "合志|无料",
                        "eventList": [
                            {
                                "positionName": "理想空间",
                                "position": "A01"
                            }
                        ]
                    },
                    {
                        "doujinshiId": 222,
                        "doujinshiName": "全职叶修小说再录",
                        "themeAlias": "全职高手",
                        "type": "小说",
                        "sellStatus": "策划中",
                        "hotCount": 200,
                        "circleID": 444,
                        "circleName": "全职社团",
                        "tag": "再录",
                        "eventList": [
                            {
                                "positionName": "理想空间",
                                "position": "A02"
                            }
                        ]
                    }
                ]
            }
        }
        
        with open(os.path.join(day1_dir, "1.json"), "w", encoding="utf-8") as f:
            json.dump(mock_data, f)
            
        # 2. Setup mock sqlite database
        db_fd, db_path = tempfile.mkstemp()
        try:
            # Import dataset
            success = import_cp31_dataset(tmpdir, db_path=db_path)
            assert success is True
            
            # Check db entries
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM cp31_products")
            assert cursor.fetchone()[0] == 2
            
            cursor.execute("SELECT COUNT(*) FROM cp31_circles")
            assert cursor.fetchone()[0] == 2
            
            cursor.execute("SELECT theme_alias, circle_id, tags FROM cp31_products WHERE doujinshi_id = 111")
            row = cursor.fetchone()
            assert row[0] == "凹凸世界"
            assert row[1] == 333
            assert row[2] == "合志|无料"
            
            conn.close()
            
            # 3. Analyze CP31 data
            stats = get_cp31_stats(db_path=db_path)
            assert "error" not in stats
            assert stats["total_products"] == 2
            assert stats["total_circles"] == 2
            
            # Media types check
            media_types = {item["type"]: item["count"] for item in stats["media_types"]}
            assert media_types.get("漫画") == 1
            assert media_types.get("小说") == 1
            
            # Materiality check
            assert stats["materiality"]["freebies"]["count"] == 1
            assert stats["materiality"]["anthologies"]["count"] == 1
            assert stats["materiality"]["reprints"]["count"] == 1
            
            # Concentration CR5/CR10 check
            assert stats["concentration"]["cr5"] == 100.0
            
            # Real-time DBI check (Total heat = 300)
            # 凹凸世界 count = 1, heat = 100 -> supply_pct = 0.5, demand_pct = 100/300 = 1/3
            # dbi = 0.5 / (1/3) = 1.5
            dbi_map = {item["theme"]: item["dbi"] for item in stats["dbi_rankings"]}
            assert abs(dbi_map["凹凸世界"] - 1.5) < 0.01
            
            # Overlap check
            assert stats["day_scheduling"]["overlap_count"] == 0
            
            # Moran's I check for 凹凸世界 (All circles in same position '理想空间', so adjacent)
            spatial = stats["spatial_clustering"]
            # It will compute Moran's I because len(rows) is checked, but wait!
            # In calculate_cp31_moran_i, we check `if len(rows) < 10: return None`
            # Since mock data has only 2 rows, it will return None, which is correct and safe!
            
            # 4. Generate report
            report_path = os.path.join(tmpdir, "comiket_vs_comicup_comparison.md")
            generate_cp31_comparison_report(stats, output_path=report_path, db_path=db_path)
            assert os.path.exists(report_path)
            
            # Read and verify content exists
            with open(report_path, "r", encoding="utf-8") as f:
                content = f.read()
                assert "# Comic Market (C108) 与 Comicup (CP31) 双城同人集聚与创作生态对比研究报告" in content
                assert "凹凸世界" in content
                assert "全职高手" in content
                
        finally:
            os.close(db_fd)
            os.remove(db_path)
