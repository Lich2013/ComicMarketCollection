import os
import tempfile
import sqlite3
import json
import pytest
from src.db import init_db
from src.semantic_analyzer import run_semantic_analysis, generate_semantic_report

@pytest.fixture
def mock_db():
    """创建一个带有测试数据的临时 SQLite 数据库"""
    db_fd, db_path = tempfile.mkstemp()
    init_db(db_path)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 1. 插入 C108 (circles) 题材描述测试数据
    # 题材包括: 'ブルーアーカイブ', '東方Project', 'VTuber', '男性向', '評論・情報', 'コスプレ', '鉄道・旅行・メカミリ', 'アイドルマスター'
    circles_data = [
        # ID, Name, Author, Genre, Description, Hall, Day, Block, Space, Twitter, Twitter_Username, Pixiv, Circle_Cut
        (1, "社团1", "作者1", "ブルーアーカイブ", "新刊はミカ中心の小説本です。アルも出ます。", "東", "Day1", "A", "01a", "http://twitter/1", "user1", "http://pixiv/1", ""),
        (2, "社团2", "作者2", "ブルーアーカイブ", "アクリルキーホルダーとアクスタ、既刊コハル本あります。", "東", "Day1", "A", "01b", "", "", "http://pixiv/2", ""),
        (3, "社团3", "作者3", "東方Project", "霊梦与魔理沙的新刊。レイムイラスト。", "東", "Day1", "B", "02a", "http://twitter/3", "user3", "", ""),
        (4, "社团4", "作者4", "VTuber", "すいせいとぺこらのグッズを頒布します。", "東", "Day1", "C", "03a", "http://twitter/4", "user4", "http://pixiv/4", ""),
        (5, "社团5", "作者5", "男性向", "R18のCG集とアクリルグッズ。成人向新刊。", "西", "Day2", "D", "04a", "http://twitter/5", "user5", "http://pixiv/5", ""),
        (6, "社团6", "作者6", "評論・情報", "鉄道の歴史に関する評論誌、既刊。小説ではありません。", "西", "Day2", "E", "05a", "", "", "", ""),
        (7, "社团7", "作者7", "コスプレ", "コスプレROMと写真集を頒布します。", "南", "Day2", "F", "06a", "http://twitter/7", "user7", "http://pixiv/7", ""),
        (8, "社团8", "作者8", "鉄道・旅行・メカミリ", "旅行記と新刊。グッズもあります。", "東", "Day1", "G", "07a", "", "", "", ""),
        (9, "社团9", "作者9", "アイドルマスター", "学マス新刊小説。シンデレラガールズデレマス本。", "東", "Day1", "H", "08a", "http://twitter/9", "user9", "http://pixiv/9", ""),
        (10, "社团10", "作者10", "ブルーアーカイブ", "空白简介测试", "東", "Day1", "A", "09a", "", "", "", "")
    ]
    cursor.executemany("""
        INSERT INTO circles (
            id, name, author, genre, description, hall, day, block, space, 
            twitter_url, twitter_username, pixiv_url, circle_cut_url
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, circles_data)
    
    # 2. 插入 C107 (c107_circles) 测试数据
    c107_data = [
        # ID, Circle_ID, Name, Author, Genre, Description, Hall, Day, Block, Space, Twitter, Twitter_Username, Pixiv, Circle_Cut
        (1, 101, "C107社团1", "作者1", "ブルーアーカイブ", "ミカの新刊と小説。", "東", "Day1", "A", "01a", "", "", "", ""),
        (2, 102, "C107社团2", "作者2", "東方Project", "霊夢のイラストとグッズ。", "東", "Day1", "B", "02a", "", "", "", ""),
        (3, 103, "C107社团3", "作者3", "男性向", "R-18新刊と既刊。", "西", "Day2", "D", "04a", "", "", "", "")
    ]
    cursor.executemany("""
        INSERT INTO c107_circles (
            id, circle_id, name, author, genre, description, hall, day, block, space, 
            twitter_url, twitter_username, pixiv_url, circle_cut_url
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, c107_data)
    
    conn.commit()
    conn.close()
    
    yield db_path
    
    # 清理
    os.close(db_fd)
    if os.path.exists(db_path):
        os.remove(db_path)
    # 额外清理临时缓存文件
    cache_path = "data/semantic_metrics.json"
    if os.path.exists(cache_path):
        try:
            os.remove(cache_path)
        except Exception:
            pass

def test_run_semantic_analysis(mock_db):
    stats = run_semantic_analysis(mock_db)
    
    # 验证基础元数据统计
    assert stats["total_c108"] == 10
    assert stats["filled_count_c108"] == 10
    assert stats["fill_rate"] == 100.0
    assert stats["avg_len"] > 0
    assert stats["n_c107"] == 3
    
    # 验证社交绑定交叉率
    social_corr = stats["social_corr"]
    assert "desc_filled" in social_corr
    assert "desc_empty" in social_corr
    assert social_corr["desc_filled"]["total"] == 10
    assert social_corr["desc_filled"]["twitter_pct"] == 60.0 # 6 out of 10
    assert social_corr["desc_filled"]["pixiv_pct"] == 60.0   # 6 out of 10
    
    # 验证社交绑定卡方检验 (Task 5.4)
    assert "social_chi2" in stats
    assert "twitter" in stats["social_chi2"]
    assert "pixiv" in stats["social_chi2"]
    assert "chi2" in stats["social_chi2"]["twitter"]
    assert "p_value" in stats["social_chi2"]["twitter"]
    assert "cramers_v" in stats["social_chi2"]["twitter"]
    
    # 验证 TF-IDF
    tfidf = stats["genre_tfidf_results"]
    assert "ブルーアーカイブ" in tfidf
    assert "東方Project" in tfidf
    
    # 验证精确 IP 角色提及过滤
    # "ミカ" 应该被成功匹配
    char_mentions = stats["character_mentions"]
    assert "ブルーアーカイブ" in char_mentions
    ba_rankings = dict(char_mentions["ブルーアーカイブ"]["rankings"])
    assert ba_rankings["ミカ (弥香)"]["count"] == 1
    # "アル" 应为 1 (不匹配 アクリル)
    assert ba_rankings["アル (阿露)"]["count"] == 1
    
    # 验证卡方检验与效应量计算
    chi_results = stats["chi_results"]
    assert "has_r18" in chi_results
    assert "has_goods" in chi_results
    assert "has_novel" in chi_results
    
    # 验证时序漂移结果
    drift = stats["drift_results"]
    assert len(drift) > 0
    # 验证 z 检验结果 (Task 5.4)
    assert "z_stat" in drift[0]
    assert "p_value" in drift[0]
    assert "sig_drift" in drift[0]
    
    # 验证本地 JSON 缓存的生成
    cache_path = "data/semantic_metrics.json"
    assert os.path.exists(cache_path)
    with open(cache_path, "r", encoding="utf-8") as f:
        cache_data = json.load(f)
        assert "c108_novel_pct" in cache_data

def test_generate_semantic_report(mock_db):
    stats = run_semantic_analysis(mock_db)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        report_path = os.path.join(tmpdir, "test_semantic_report.md")
        generate_semantic_report(stats, report_path)
        
        assert os.path.exists(report_path)
        with open(report_path, "r", encoding="utf-8") as f:
            content = f.read()
            # 校验包含核心章节与特定词汇
            assert "摘要" in content
            assert "简介文本元数据概况与社媒绑定相关性" in content
            assert "基于 SudachiPy + TF-IDF" in content
            assert "垂直 IP 与精准正则角色提及度分析" in content
            assert "题材 × 内容倾向卡方检验与效应量测算" in content
            assert "时序纵向漂移分析" in content
            assert "数据质量局限性声明" in content
            # 校验新增的检验指标与陈述 (Task 5.4)
            assert "卡方独立性检验结果" in content
            assert "z 检验 p 值" in content
            assert "复合名词过度拆分偏误" in content
            assert "弥香" in content
