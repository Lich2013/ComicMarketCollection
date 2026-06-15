import os
import tempfile
import sqlite3
import pytest
from src.db import init_db
from src.multi_era_analyzer import (
    calculate_comiket_moran_i,
    calculate_comicup_moran_i,
    get_comiket_era_stats,
    get_comicup_era_stats,
    run_multi_era_analysis,
    generate_multi_era_report
)

@pytest.fixture
def mock_db():
    """创建一个带有测试数据的临时 SQLite 数据库"""
    db_fd, db_path = tempfile.mkstemp()
    init_db(db_path)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 1. 插入 C107 测试数据 (>= 10 行以启用 Moran's I 计算)
    # 我们构造聚集的空间结构，前5个社团属于男性向，后5个不是
    c107_data = []
    for i in range(1, 11):
        genre = "男性向" if i <= 5 else "其他题材"
        c107_data.append((
            i, i * 100, f"C107社团_{i}", f"作者_{i}", genre, f"简介_{i}",
            "東", "土", "A", f"{i}a", "http://twitter/i", f"username_{i}", "http://pixiv/i", "http://cut/i"
        ))
    cursor.executemany("""
        INSERT INTO c107_circles (
            id, circle_id, name, author, genre, description, hall, day, block, space, 
            twitter_url, twitter_username, pixiv_url, circle_cut_url
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, c107_data)
    
    # 2. 插入 C108 (circles) 测试数据
    c108_data = []
    for i in range(1, 11):
        genre = "ブルーアーカイブ" if i <= 5 else "其他题材"
        c108_data.append((
            i, f"C108社团_{i}", f"作者_{i}", genre, f"简介_{i}",
            "東", "土", "A", f"{i}a", "http://twitter/i", f"username_{i}", "http://pixiv/i", "http://cut/i"
        ))
    cursor.executemany("""
        INSERT INTO circles (
            id, name, author, genre, description, hall, day, block, space, 
            twitter_url, twitter_username, pixiv_url, circle_cut_url
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, c108_data)
    
    # 3. 插入 CPSP 测试数据 (circles 和 products)
    cpsp_circles = []
    for i in range(1, 11):
        cpsp_circles.append((i, f"CPSP社团_{i}", "明日方舟专区" if i <= 5 else "其他专区", f"A-{i}"))
    cursor.executemany("""
        INSERT INTO cpsp_circles (circle_id, name, position_name, position)
        VALUES (?, ?, ?, ?)
    """, cpsp_circles)
    
    # 插入制品，包含色纸和纸胶带（应被过滤掉）
    cpsp_products = [
        # 明日方舟小说
        (1, "方舟本_1", "明日方舟", "小说", "仅供现场", 100, "D1", 1, "方舟"),
        (2, "方舟本_2", "明日方舟", "小说", "仅供现场", 150, "D1", 2, "方舟"),
        # 明日方舟色纸 (应过滤)
        (3, "方舟色纸", "明日方舟", "色纸", "仅供现场", 80, "D1", 3, "方舟"),
        # 明日方舟纸胶带 (应过滤)
        (4, "方舟纸胶带", "明日方舟", "纸胶带", "仅供现场", 30, "D1", 4, "方舟"),
        # 其他产品
        (5, "手办_1", "原神", "手办", "仅供现场", 400, "D1", 6, "手办"),
        (6, "手办_2", "原神", "手办", "仅供现场", 200, "D1", 7, "手办"),
    ]
    cursor.executemany("""
        INSERT INTO cpsp_products (doujinshi_id, name, theme_alias, type, sell_status, hot_count, day_label, circle_id, tags)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, cpsp_products)
    
    # 4. 插入 CP31 测试数据 (circles 和 products)
    cp31_circles = []
    for i in range(1, 11):
        cp31_circles.append((i, f"CP31社团_{i}", "明日方舟专区" if i <= 5 else "其他专区", f"B-{i}"))
    cursor.executemany("""
        INSERT INTO cp31_circles (circle_id, name, position_name, position)
        VALUES (?, ?, ?, ?)
    """, cp31_circles)
    
    cp31_products = [
        (1, "方舟本_1", "明日方舟", "小说", "仅供现场", 120, "D1", 1, "方舟"),
        (2, "方舟本_2", "明日方舟", "小说", "仅供现场", 130, "D2", 2, "方舟"),
        (3, "原神本", "原神", "漫画", "仅供现场", 300, "D1", 6, "原神"),
    ]
    cursor.executemany("""
        INSERT INTO cp31_products (doujinshi_id, name, theme_alias, type, sell_status, hot_count, day_label, circle_id, tags)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, cp31_products)
    
    conn.commit()
    conn.close()
    
    yield db_path
    
    # 清理
    os.close(db_fd)
    if os.path.exists(db_path):
        os.remove(db_path)


def test_comiket_moran_i_calculation(mock_db):
    # C107 男性向空间自相关计算
    res = calculate_comiket_moran_i(mock_db, "c107_circles", "男性向")
    assert res is not None
    moran_i, expected, n, w = res
    assert n == 10
    assert w > 0
    # 因为 1-5 都是男性向（聚集），所以莫兰指数应该大于 0 （正自相关）
    assert moran_i > expected
    
    # C108 ブルーアーカイブ计算
    res_c108 = calculate_comiket_moran_i(mock_db, "circles", "ブルーアーカイブ")
    assert res_c108 is not None
    assert res_c108[0] > res_c108[1]


def test_comicup_moran_i_calculation(mock_db):
    # CPSP 明日方舟 Moran's I，包含周边过滤 (过滤色纸和纸胶带)
    res_cpsp = calculate_comicup_moran_i(
        mock_db, 
        circles_table="cpsp_circles", 
        products_table="cpsp_products", 
        target_theme="明日方舟", 
        filter_types=["色纸", "纸胶带"]
    )
    assert res_cpsp is not None
    moran_i, expected, n, w = res_cpsp
    assert n == 10
    
    # CP31 明日方舟 Moran's I
    res_cp31 = calculate_comicup_moran_i(
        mock_db, 
        circles_table="cp31_circles", 
        products_table="cp31_products", 
        target_theme="明日方舟"
    )
    assert res_cp31 is not None


def test_get_comiket_era_stats(mock_db):
    stats = get_comiket_era_stats(mock_db, "c107_circles")
    assert stats["total_circles"] == 10
    assert len(stats["top_genres"]) > 0
    assert stats["top_genres"][0]["genre"] == "男性向"
    assert stats["top_genres"][0]["count"] == 5
    assert stats["top_genres"][0]["percentage"] == 50.0
    assert stats["cr5"] == 100.0
    assert stats["cr10"] == 100.0
    assert "super_cr5" in stats
    assert "super_cr10" in stats
    assert stats["super_cr5"] == 100.0
    assert "男性向" in stats["spatial_clustering"]


def test_get_comicup_era_stats_with_filtering(mock_db):
    # 对 CPSP 运行包含过滤逻辑的统计
    stats = get_comicup_era_stats(
        mock_db, 
        circles_table="cpsp_circles", 
        products_table="cpsp_products", 
        filter_types=["色纸", "纸胶带"]
    )
    assert stats["total_circles"] == 10
    # 原始制品共6件，过滤掉色纸和纸胶带后，应只剩4件
    assert stats["total_products"] == 4
    
    # 验证媒介类型分布中不存在色纸和纸胶带
    media_types = [m["type"] for m in stats["media_types"]]
    assert "色纸" not in media_types
    assert "纸胶带" not in media_types
    assert "小说" in media_types
    assert "手办" in media_types
    
    # 验证心愿单 DBI 偏离度计算
    # 过滤后：方舟小说 100+150=250，原手办 400+200=600，总热度=850
    # 方舟制品 2 件，原神 2 件，总制品=4
    # 方舟 DBI = (2/4) / (250/850) = 0.5 * (850/250) = 1.7
    # 原神 DBI = (2/4) / (600/850) = 0.5 * (850/600) = 0.708
    dbi_rankings = {d["theme"]: d["dbi"] for d in stats["dbi_rankings"]}
    assert pytest.approx(dbi_rankings["明日方舟"], 0.01) == 1.7
    assert pytest.approx(dbi_rankings["原神"], 0.01) == 0.708
    
    # 验证超级集中度
    assert "super_cr5" in stats["concentration"]
    assert "super_cr10" in stats["concentration"]
    assert stats["concentration"]["super_cr5"] == 100.0


def test_run_multi_era_analysis(mock_db):
    all_stats = run_multi_era_analysis(mock_db)
    assert "c107" in all_stats
    assert "c108" in all_stats
    assert "cpsp" in all_stats
    assert "cp31" in all_stats
    
    assert all_stats["c107"]["total_circles"] == 10
    assert all_stats["cpsp"]["total_products"] == 4


def test_report_generation(mock_db):
    all_stats = run_multi_era_analysis(mock_db)
    
    # 模拟创建待清理的冗余文档
    file1 = "research/comiket_vs_comicup.md"
    file2 = "research/comiket_vs_comicup_comparison.md"
    
    # 确保目录存在
    os.makedirs("research", exist_ok=True)
    
    # 写入 dummy 内容
    with open(file1, "w", encoding="utf-8") as f:
        f.write("dummy content 1")
    with open(file2, "w", encoding="utf-8") as f:
        f.write("dummy content 2")
        
    assert os.path.exists(file1)
    assert os.path.exists(file2)

    with tempfile.TemporaryDirectory() as tmpdir:
        report_path = os.path.join(tmpdir, "test_report.md")
        generate_multi_era_report(all_stats, report_path)
        
        assert os.path.exists(report_path)
        with open(report_path, "r", encoding="utf-8") as f:
            content = f.read()
            # 校验包含核心章节与特定词汇
            assert "引言与方法论" in content
            assert "科学基准说明" in content
            assert "数据集对应与映射规格" in content
            assert "日本本土时序稳定性分析" in content
            assert "中国本土演进与周边清洗过滤分析" in content
            assert "中日双城同人集聚与创作生态倾向性横向对比" in content
            assert "Moran's I" in content
            assert "贝恩" in content
            assert "供需偏离度" in content
            assert "附录：方法论注意事项与数据局限性声明" in content
            assert "分析单位不对齐说明" in content
            assert "题材分类粒度归一化对齐分析（超级题材）" in content
            assert "Super-CR5" in content
            # Calculate what we expect based on cache file or fallback
            expected_pct = 5.4
            cache_path = "data/semantic_metrics.json"
            if os.path.exists(cache_path):
                try:
                    import json
                    with open(cache_path, "r", encoding="utf-8") as f:
                        expected_pct = json.load(f).get("c108_novel_pct", 5.4)
                except Exception:
                    pass
            assert f"提及率仅为 **{expected_pct:.1f}%**" in content
            assert "中日“偏离度”指标的统计口径不一致" in content
            
        # 校验冗余文件已物理删除
        assert not os.path.exists(file1)
        assert not os.path.exists(file2)
