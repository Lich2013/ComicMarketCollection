import re
import collections
from src.db import get_db_connection, save_circle_ip_tags, DEFAULT_DB_PATH
from src.graph_builder import build_spatial_graph
from src.label_propagator import run_label_propagation
from src.config import load_config

# 默认支持的核心 IP 极其正则匹配规则
DEFAULT_IP_RULES = {
    "明日方舟": r"アークナイツ|arknights|明日方舟|エンドフィールド|endfield|アザゼル|ライン生命|バベル|バグパイプ|エイヤフィヤトラ",
    "蔚蓝档案": r"ブルーアーカイブ|ブルアカ|blue\s*archive|キヴォトス|アビドス|トリニティ|ゲヘナ|ミレニアム|シャーレ",
    "原神": r"原神|genshin|テイワット|パイモン|モンド|璃月|稲妻|スメール|フォンテーヌ|ナタ|スネージナヤ",
    "崩坏：星穹铁道": r"崩壊スターレイル|スターレイル|star\s*rail|星穹铁道|ピノコニー|ベロブルグ|仙舟|開拓者",
    "碧蓝航线": r"アズールレーン|アズレン|azur\s*lane|碧蓝航线",
    "Fate": r"fate|fgo|grand\s*order|サーヴァント|聖杯戦争|カルデア|型月|type-moon",
    "东方Project": r"東方project|東方プロジェクト|霊夢|魔理沙|幻想郷",
    "排球少年": r"ハイキュー|haikyu|排球少年|烏野|青葉城西|音駒|梟谷|指宿|稲荷崎",
    "代号鸢": r"代号鸢|ラブアンドディープスペース",
    "恋与深空": r"恋と深空|love\s*and\s*deepspace|恋与深空|セイヤ|ホツマ|黎深|沈星回",
    "鸣潮": r"鳴潮|めいちょう|wuthering\s*waves|鸣潮|漂泊者|今汐|長離|忌炎|秧秧",
    "绝区零": r"ゼンレスゾーンゼロ|ゼンゼロ|zenless\s*zone\s*zero|绝区零|zzz|新エリー都",
    "VTuber": r"vtuber|バーチャルyoutuber|ホロライブ|hololive|にじさんじ|nijisanji|ぶいすぽ|vspo|のりプロ|ななしいんく|あおぎり高校|ホロスターズ|holostars",
    "偶像大师": r"アイドルマスター|imas|ミリマス|デレマス|シャニマス|シャイニーカラーズ|ミリオンライブ|デレステ|天海春香|星井美希|如月千早|島村卯月|渋谷凛|本田未央|宮本フレデリカ|櫻木真乃|風野灯織|八宮めぐる",
    "Love Live!": r"ラブライブ|lovelive|μ's|aqours|虹ヶ咲|虹ヶ咲学園|liella|蓮ノ空|高坂穂乃果|園田海未|南ことり|高海千歌|桜内梨子|渡辺曜|上原歩梦|中須かすみ|桜坂しずく|澁谷かのん|唐可可|嵐千砂都|日野下花帆|乙宗梢|村野さやか",
    "舰队Collection": r"艦これ|艦隊これくしょん|kancolle|提督|吹雪|赤城|加賀|金剛|島風|大和|榛名|霧島|比叡",
    "刀剑乱舞": r"刀剣乱舞|とうらぶ|touran|審神者|三日月宗近|加州清光|大和守安定|鶴丸国永|山姥切国広|へし切長谷部|一期一振|薬研藤四郎",
    "赛马娘": r"ウマ娘|プリティーダービー|umamusume|トレーナー|スペシャルウィーク|サイレンススズカ|トウカイテイオー|メジロマックイーン|ゴールドシップ|ライスシャワー|ミホノブルボン|キタサンブラック|サトノダイヤモンド",
    "高达": r"ガンダム|gundam|モビルスーツ|アムロ|シャア|カミーユ|ジュドー|キラ・ヤマト|アスラン|シン・アスカ|刹那|スレッタ|ミオリネ",
    "少女与战车": r"ガルパン|ガールズ＆パンツァー|girls\s*und\s*panzer|西住みほ|武部沙織|五十鈴華|秋山優花里|冷泉麻子|大洗女子|黒森峰|聖グロリアーナ|サンダース|アンツィオ|プラウダ|知波単|継続高校",
    "崩坏3": r"崩壊3rd|崩壊学園|崩坏3|崩坏学学园|honkai\s*impact|キアナ|芽衣|ブローニャ",
    "世界计划": r"プロジェクトセカイ|プロセカ|project\s*sekai|初音ミク|カラフルステージ|鏡音リン|鏡音レン|巡音ルカ|宵崎奏",
    "碧蓝幻想": r"グランブルーファンタジー|グラブル|granblue\s*fantasy|gbf|ルリア|グラン|ジータ|ビィ|騎空士",
    "公主连结": r"プリンセスコネクト|プリコネ|princess\s*connect|コッコロ|ペコリーヌ|キャル|美食殿",
    "影之诗": r"シャドウバース|シャドバ|shadowverse|アリサ|ローウェン|ルナ|worlds\s*beyond",
    "少女前线": r"ドールズフロントライン|ドルフロ|少女前線|少女前线|ニューラルクラウド|云图计划|エクシリウム|m4a1|girls\s*frontline",
    "胜利女神：妮姬": r"勝利の女神|nikke|ニケ|胜利女神|メガニケ|カウンターズ",
    "白猫Project": r"白猫プロジェクト|白猫|shironeko|キャトラ|アイリス",
    "智龙迷城": r"パズル＆ドラゴンズ|パズドラ|puzzle\s*(and|&)\s*dragons",
    "怪物弹珠": r"モンスターストライク|モンスト|monster\s*strike",
    "战斗女子高校": r"バトルガールハイスクール|バトガ|battle\s*girl\s*high\s*school|星守|星月みき",
    "SHOW BY ROCK!!": r"show\s*by\s*rock|sbr|ショウバイロック|プラズマジカ|シンガンクリムゾンズ",
    "恶魔72": r"メギド72|メギド|megido\s*72|ソロモン|シバの女王",
    "八月的棒球甜心": r"八月のシンデレラナイン|ハチナイ|cinderella\s*nine|有原翼",
    "女友伴身边": r"ガールフレンド\(仮\)|ガールフレンド\(♪\)|gf\(仮\)|椎名心実|クロエ・ルメール",
    "拉拉魔法": r"ららマジ|lalamagi|器楽部",
    "合奏女孩": r"あんさんぶるガールズ|あんガル|ensemble\s*girls",
    "CUE!": r"cue\s*!|キュー\s*!",
    "天华百剑": r"天華百剣|tenka\s*hyakken|巫剣",
    "御城Project": r"御城プロジェクト|城プロ|oshiro\s*project|殿|千狐",
    "俺塔": r"俺タワー|おれタワー|ore\s*tower|建姫|オヤカタ",
    "战舰少女R": r"戦艦少女|战舰少女|warship\s*girls|提督|レキシントン",
    "Last Origin": r"ラストオリジン|last\s*origin|ラスオリ|司令官",
    "灰烬战线": r"アッシュアームズ|ash\s*arms|代理人|エージェント",
    "海豚波浪": r"ドルフィンウェーブ|ドルウェブ|dolphin\s*wave|コーチ|咲宮入華|都条みちる",
    "位置游戏": r"ingress|駅メモ|ステーションメモリーズ|位置ゲー|位置ゲーム",
    "第五人格": r"identityv|identity\s*v|第五人格|荘園|サバイバー|ハンター",
    "英雄联盟": r"リーグ・オブ・レジェンズ|league\s*of\s*legends|lol|エルオーエル|サモナーズリフト|ルーンテラ",
    "Compass": r"コンパス|戦闘摂理解析システム|#コンパス|compass",
    "爱丽丝机甲": r"アリス・ギア・アイギス|アリスギア|alice\s*gear\s*aegis|比良坂夜露|兼志谷シタラ|百科文嘉|成子坂製作所",
    "梦幻之星": r"phantasy\s*star|pso|pso2|ngs|ニュージェネシス|ファンタシースターオンライン|ファンタシースターポータブル|ファンタシースターユニバース",
    "仙境传说": r"ragnarok|ラグナロクオンライン|ラグナロクマスターズ|ラグマス|仙境传说",
    "其他手机网页社交网游": r"→その他\s*携帯・スマホ・WEB・ソーシャルゲーム・ネトゲー|携帯・スマホ・WEB・ソーシャルゲーム・ネトゲー|ソーシャルゲーム|携帯ゲーム|スマホゲーム|ネトゲー|ネットゲーム|webゲーム",
    "MOBA": r"→MOBA|moba|マルチプレイヤーオンラインバトルアリーナ|dota|honor\s*of\s*kings",
    "MO_MMO": r"→MO・MMO|mmo|mmorpg|morpg|ネットゲーム|メイプルストーリー|マビノギ|黒い砂漠|ff14|ファイナルファンタジーxiv",
    "HoYoverse其他": r"→その他HoYoverse作品|hoyoverse|mihoyo|ホヨバース|米哈游",
    "Yostar其他": r"→その他Yostar作品|yostar|ヨースター|悠星"
}

def run_circle_tagging(db_path: str = DEFAULT_DB_PATH) -> bool:
    """运行自动打标流水线，并在 C108 数据上完成基于 2D-LPA 的 IP 标记与空间传播"""
    print("Initializing 2D spatial LPA tagging pipeline...")
    
    # 动态加载并编译 IP_RULES
    config = load_config()
    config_rules = config.get("ip_rules", {})
    
    # 合并默认规则与用户自定义配置规则
    merged_rules = dict(DEFAULT_IP_RULES)
    merged_rules.update(config_rules)
    
    compiled_ip_rules = {
        ip: re.compile(pattern, re.IGNORECASE)
        for ip, pattern in merged_rules.items()
    }
    
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    
    # 0. 清除旧的 C108 标签数据，以防残留脏数据
    try:
        cursor.execute("DELETE FROM circle_ip_tags WHERE event = 'C108'")
        conn.commit()
    except Exception as e:
        print(f"Warning: Could not clear old C108 tags: {e}")

    # 1. 获取 C108 (circles 表) 的所有社团信息
    try:
        cursor.execute("SELECT id, name, author, genre, day, hall, block, space, description FROM circles")
        circles = [dict(row) for row in cursor.fetchall()]
    except Exception as e:
        print(f"Error querying circles: {e}")
        conn.close()
        return False
        
    if not circles:
        print("No C108 circles found to tag.")
        conn.close()
        return False
        
    print(f"Total circles loaded: {len(circles)}")
    
    # 2. 获取所有的商品数据以辅助打标
    goods_by_circle = collections.defaultdict(list)
    try:
        cursor.execute("SELECT circle_id, name, type FROM goods")
        for row in cursor.fetchall():
            goods_by_circle[row[0]].append(dict(row))
    except Exception as e:
        print(f"Warning: Could not fetch goods data for tagging: {e}")
        
    conn.close()
    
    # 3. 筛选并标注原始种子 (Seeds)
    # 3.1 收集候选种子
    candidate_seeds_by_ip = collections.defaultdict(list)
    seed_source_info = {}  # 缓存种子的打标来源，形如 (circle_id, ip) -> "keyword" / "goods"
    
    for c in circles:
        cid = c["id"]
        text_to_check = f"{c['name'] or ''} {c['author'] or ''} {c['genre'] or ''} {c['description'] or ''}"
        
        matched_ips = set()
        
        # 1) 关键字匹配
        for ip, pattern in compiled_ip_rules.items():
            if pattern.search(text_to_check):
                matched_ips.add(ip)
                seed_source_info[(cid, ip)] = "keyword"
                
        # 2) 商品数据反推
        c_goods = goods_by_circle.get(cid, [])
        for g in c_goods:
            g_text = f"{g['name'] or ''} {g['type'] or ''}"
            for ip, pattern in compiled_ip_rules.items():
                if pattern.search(g_text):
                    matched_ips.add(ip)
                    if (cid, ip) not in seed_source_info:
                        seed_source_info[(cid, ip)] = "goods"
                        
        for ip in matched_ips:
            candidate_seeds_by_ip[ip].append(c)
            
    # 3.2 空间离群过滤 (Spatial Outlier Filtering for clustered IPs)
    # 利用 Comiket 的题材专区聚集排布规律过滤孤立的假阳性种子点
    from src.spatial_mapper import get_booth_coords
    import math
    
    seeds = {}
    for ip, c_list in candidate_seeds_by_ip.items():
        pattern = compiled_ip_rules[ip]
        
        # 如果该 IP 在本届展会中的候选种子总数少于 5，说明是极其小众/长尾的 IP
        # 此时不进行离群过滤，避免误伤孤立但真实的独立摊位
        if len(c_list) < 5:
            for c in c_list:
                cid = c["id"]
                if cid not in seeds:
                    seeds[cid] = {}
                seeds[cid][ip] = 1.0
            continue
            
        # 缓存每个候选摊位的二维物理坐标以加速距离计算
        coords_cache = {}
        for c in c_list:
            coords_cache[c["id"]] = get_booth_coords(c["hall"], c["block"], c["space"])
            
        for c1 in c_list:
            cid1 = c1["id"]
            
            # 规则 A: 如果社团的官方题材 genre 匹配了当前 IP，判定为在专用分区，直接保留
            genre_matches = False
            if c1["genre"] and pattern.search(c1["genre"]):
                genre_matches = True
                
            if genre_matches:
                if cid1 not in seeds:
                    seeds[cid1] = {}
                seeds[cid1][ip] = 1.0
                continue
                
            # 规则 B: 否则（通过描述或商品匹配的非本分区社团），必须在 25.0 米物理半径内
            # 存在至少一个同日、同馆的该 IP 其他候选种子（证明其为专区/相邻集中地带，而非离群大杂烩）
            coord1 = coords_cache[cid1]
            has_neighbor = False
            
            for c2 in c_list:
                cid2 = c2["id"]
                if cid1 == cid2:
                    continue
                # 必须同一天、同一个展馆
                if c1["day"] != c2["day"] or c1["hall"] != c2["hall"]:
                    continue
                    
                coord2 = coords_cache[cid2]
                dx = coord1[0] - coord2[0]
                dy = coord1[1] - coord2[1]
                dist = math.sqrt(dx*dx + dy*dy)
                if dist <= 25.0:
                    has_neighbor = True
                    break
                    
            if has_neighbor:
                if cid1 not in seeds:
                    seeds[cid1] = {}
                seeds[cid1][ip] = 1.0

    seeds_count = len(seeds)
    print(f"Seeds identification complete: {seeds_count} seed circles marked with confidence 1.0.")
    
    # 4. 构建二维展馆物理图网络
    print("Building 2D spatial graph topology...")
    adjacency_list = build_spatial_graph(circles)
    
    # 5. 执行二维标签传播算法 (LPA)
    print("Running Label Propagation (max_iter=5, alpha=0.6)...")
    all_circle_ids = [c["id"] for c in circles]
    propagated_results = run_label_propagation(
        adjacency_list=adjacency_list,
        seeds=seeds,
        all_circle_ids=all_circle_ids,
        alpha=0.6,
        max_iter=5
    )
    
    # 6. 整合结果并持久化写入数据库 (只保留概率 >= 0.3 的标签)
    db_tags = []
    
    for cid in all_circle_ids:
        c_results = propagated_results.get(cid, {})
        for ip, prob in c_results.items():
            # 判断是否是原始种子
            is_original_seed = (cid in seeds and ip in seeds[cid])
            
            if is_original_seed:
                # 原始种子使用固定的 1.0 置信度与原始来源
                db_tags.append({
                    "event": "C108",
                    "circle_id": cid,
                    "ip_tag": ip,
                    "confidence": 1.0,
                    "source": seed_source_info.get((cid, ip), "keyword")
                })
            elif prob >= 0.3:
                # 空间传播的标签，需概率达到 0.3，置信度为其概率值
                db_tags.append({
                    "event": "C108",
                    "circle_id": cid,
                    "ip_tag": ip,
                    "confidence": round(prob, 2),
                    "source": "spatial"
                })
                
    if db_tags:
        print(f"Committing {len(db_tags)} IP tags to DB...")
        save_circle_ip_tags(db_tags, db_path=db_path)
        print("Successfully completed C108 circles IP tagging via 2D-LPA.")
        return True
    else:
        print("No tags generated.")
        return False
