import os
import sqlite3
from collections import Counter, defaultdict

# Aligned Super-Genre baseline (aggregated from AUDIENCE_POPULARITY_BASELINE)
SUPER_GENRE_BASELINES = {
    '1. 男性向与成人向 (Male-oriented & R-18)': 11.5, # 男性向 10.0 + ギャルゲー 1.5
    '2. 手游与网络社交游戏 (Mobile & Social Games)': 24.0, # 网游 12.0 + 蓝闪 4.0 + 赛马娘 5.0 + 型月 3.0
    '3. 传统动漫与小说二创 (Anime, Manga & Novel Fan Clubs)': 6.0, # 动漫其他 6.0 (不含未观测FC)
    '4. 同人游戏与单机/桌游 (Indie Games, Console & Tabletop Games)': 1.5, # 东方 1.5 (不含未观测RPG)
    '5. 虚拟主播 (VTubers)': 8.0, # VTuber 8.0
    '6. 原创漫画与插画 (Original Manga & Illustration)': 4.0, # 创作少年 4.0
    '7. 原创周边与手工 (Original Merchandise & Crafts)': 2.5, # 原创杂货 2.5
    '8. 铁道/军事/旅行与评论情报 (Specialized Hobbies & Information)': 3.5, # 评论情报 1.5 + 铁道军事 2.0
    '9. 角色扮演 (Cosplay)': 5.0, # コスプレ 5.0
    '10. 声优与偶像企划 (Idol & Media Projects)': 3.5 # 偶像大师 3.5 (不含LoveLive)
}

def map_comiket_to_super(genre):
    if not genre:
        return '其他/未分类 (Others)'
    genre = genre.strip()
    if genre in ['男性向', 'ギャルゲー']:
        return '1. 男性向与成人向 (Male-oriented & R-18)'
    elif genre in ['ゲーム(ネット・ソーシャル)', 'ブルーアーカイブ', 'ウマ娘', 'TYPE-MOON', '艦これ', 'アズールレーン', 'ゲーム(恋愛・ソーシャル女性向)']:
        return '2. 手游与网络社交游戏 (Mobile & Social Games)'
    elif genre in ['アニメ(その他)', 'アニメ(少女)', 'FC(少年)', 'FC(少女・青年)', 'FC(ジャンプその他)', 'FC(小説)', 'ガンダム', 'ガルパン', '刀剣乱舞', 'TV・映画・芸能・特撮']:
        return '3. 传统动漫与小说二创 (Anime, Manga & Novel Fan Clubs)'
    elif genre in ['同人ソフト', 'ゲーム(その他)', 'ゲーム(電源不要)', 'スクウェア・エニックス(RPG)', 'ゲーム(RPG)', '東方Project']:
        return '4. 同人游戏与单机/桌游 (Indie Games, Console & Tabletop Games)'
    elif genre in ['VTuber']:
        return '5. 虚拟主播 (VTubers)'
    elif genre in ['創作(少年)', '創作(少女)', '創作(JUNE/BL)']:
        return '6. 原创漫画与插画 (Original Manga & Illustration)'
    elif genre in ['オリジナル雑貨', 'デジタル(その他)']:
        return '7. 原创周边与手工 (Original Merchandise & Crafts)'
    elif genre in ['鉄道・旅行・メカミリ', '評論・情報', '歴史・創作(文芸・小説)']:
        return '8. 铁道/军事/旅行与评论情报 (Specialized Hobbies & Information)'
    elif genre in ['コスプレ']:
        return '9. 角色扮演 (Cosplay)'
    elif genre in ['アイドルマスター', 'ラブライブ！']:
        return '10. 声优与偶像企划 (Idol & Media Projects)'
    return '其他/未分类 (Others)'

def map_comicup_to_super(theme):
    if not theme:
        return '其他/未分类 (Others)'
    theme = theme.strip()
    
    mobile_games = {
        "明日方舟", "原神", "崩坏星穹铁道", "代号鸢", "恋与深空", "光与夜之恋", 
        "无期迷途", "战双帕弥什", "第五人格", "阴阳师", "碧蓝航线", "重返未来1999", 
        "少女前线", "闪耀暖暖", "奇迹暖暖", "恋与制作人", "深空之眼", "崩坏3", 
        "白夜极光", "蔚蓝档案", "赛马娘", "Fate", "FGO", "Fate/Grand Order", 
        "以闪亮之名", "新世界狂欢", "世界计划 缤纷舞台", "世界计划", "PJSK", "pjsk",
        "刀剑乱舞", "刀剑乱舞-ONLINE-", "剑网3", "剑侠情缘", "时空中的绘旅人", 
        "未定事件簿", "忘川风华录", "燕云十六声", "食物语", "逆水寒", "天下3"
    }
    
    media_clubs = {
        "排球少年", "全职高手", "哪吒之魔童闹海", "银魂", "盗墓笔记", "诡秘之主", 
        "名侦探柯南", "黑塔利亚", "蓝色监狱", "文豪野犬", "天官赐福", "魔道祖师", 
        "哈利波特", "咒术回战", "凹凸世界", "夏目友人帐", "罗小黑战记", "火影忍者", 
        "海贼王", "死神", "鬼灭之刃", "进击的巨人", "吉卜力", "名侦探柯南", "头七怪谈",
        "诡秘之主", "迷宫饭", "黑塔利亚", "蓝色监狱", "天官赐福", "人渣反派自救系统",
        "二哈和他的白猫师尊", "杀破狼", "默读", "魔道祖师", "轻小说", "漫威", "DC",
        "特摄", "假面骑士", "奥特曼", "金光布袋戏", "霹雳布袋戏", "失忆投捕", 
        "变形金刚", "全知读者视角", "雄狮少年", "雄狮少年2", "龙族", "灌篮高手", 
        "石纪元", "家庭教师", "家庭教师reborn", "异形舞台", "时光代理人", 
        "双城之战", "钻石王牌", "庆余年", "灵能百分百", "名侦探柯南", "排球"
    }
    
    indie_console = {
        "东方Project", "东方project", "塞尔达传说", "宝可梦", "怪物猎人", 
        "艾尔登法环", "双人成行", "星露谷物语", "Minecraft", "MC", "我的世界", 
        "只狼", "黑神话悟空", "空洞骑士", "极乐迪斯科", "女神异闻录", "P5", "P5R",
        "饥荒", "泰拉瑞亚", "逆转裁判", "弹丸论破", "杀戮尖塔", "Undertale", "deltarune",
        "只狼：影逝二度", "生化危机", "法环", "魂系", "最终幻想", "女神异闻录5",
        "女神异闻录4", "女神异闻录3", "最终幻想7", "最终幻想14", "鬼泣"
    }
    
    idols = {
        "偶像梦幻祭", "偶像大师", "LoveLive", "lovelive", "BanG Dream", 
        "bangdream", "歌之王子殿下", "催眠麦克风", "Hypnosis Mic"
    }

    if theme == "原创":
        return '6. 原创漫画与插画 (Original Manga & Illustration)'
    elif theme in ["手作", "手工", "棉花美娃娃", "无属性棉花娃娃", "手工手作"]:
        return '7. 原创周边与手工 (Original Merchandise & Crafts)'
    elif theme in ["VTuber", "vtuber", "hololive", "彩虹社", "A-SOUL", "asoul", "虚拟主播"]:
        return '5. 虚拟主播 (VTubers)'
    elif theme in ["Cosplay", "cosplay", "COS写真", "cos"]:
        return '9. 角色扮演 (Cosplay)'
    elif theme in mobile_games:
        return '2. 手游与网络社交游戏 (Mobile & Social Games)'
    elif theme in media_clubs:
        return '3. 传统动漫与小说二创 (Anime, Manga & Novel Fan Clubs)'
    elif theme in indie_console:
        return '4. 同人游戏与单机/桌游 (Indie Games, Console & Tabletop Games)'
    elif theme in idols:
        return '10. 声优与偶像企划 (Idol & Media Projects)'
    
    theme_lower = theme.lower()
    if any(k in theme_lower for k in ["明日方舟", "原神", "星铁", "崩坏", "深空", "代号鸢", "暖暖", "网易游戏", "腾讯游戏", "手游", "网络游戏", "online", "页游", "绘旅人", "未定", "阴阳师", "重返未来"]):
        return '2. 手游与网络社交游戏 (Mobile & Social Games)'
    if any(k in theme_lower for k in ["排球", "全职", "柯南", "诡秘", "魔道", "天官", "咒术", "防弹", "同人志", "影视", "动漫", "漫画", "小说", "广播剧", "特摄", "剧场版", "变形金刚", "失忆投捕", "全知读者", "雄狮少年", "哈利波特", "魔道祖师", "天官赐福", "黑塔利亚", "jojo", "家庭教师", "名侦探", "金光布袋戏", "霹雳布袋戏"]):
        return '3. 传统动漫与小说二创 (Anime, Manga & Novel Fan Clubs)'
    if any(k in theme_lower for k in ["塞尔达", "马力欧", "任天堂", "steam", "口袋妖怪", "宝可梦", "怪物猎人", "女神异闻录", "最终幻想", "法环", "只狼", "黑神话", "鬼泣", "单机", "主机"]):
        return '4. 同人游戏与单机/桌游 (Indie Games, Console & Tabletop Games)'
    if any(k in theme_lower for k in ["娃娃", "手作", "手工", "棉花娃", "周边", "挂件", "徽章"]):
        return '7. 原创周边与手工 (Original Merchandise & Crafts)'
    if any(k in theme_lower for k in ["原创", "插画", "设计"]):
        return '6. 原创漫画与插画 (Original Manga & Illustration)'
    if any(k in theme_lower for k in ["偶像", "声优", "催麦", "歌王", "lovelive", "bang dream"]):
        return '10. 声优与偶像企划 (Idol & Media Projects)'
        
    return '其他/未分类 (Others)'

def analyze_aligned_dbi():
    db_path = "data/comic_market.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 1. Comiket C108 (Circles): Numerator = Circle Count
    cursor.execute("SELECT genre, COUNT(*) FROM circles GROUP BY genre")
    comiket_raw = cursor.fetchall()
    comiket_super = Counter()
    total_comiket_circles = 0
    for genre, count in comiket_raw:
        if genre:
            super_name = map_comiket_to_super(genre)
            comiket_super[super_name] += count
            total_comiket_circles += count
            
    # 2. Comicup CP31 (Circles): Numerator = Unique Circle Count
    # We assign each circle to a Super-Genre based on its products
    cursor.execute("SELECT circle_id, theme_alias FROM cp31_products")
    products = cursor.fetchall()
    
    circle_themes = defaultdict(list)
    for circle_id, theme in products:
        if circle_id and theme:
            circle_themes[circle_id].append(map_comicup_to_super(theme))
            
    cp31_super = Counter()
    total_cp31_circles = 0
    for circle_id, super_list in circle_themes.items():
        # Vote for the primary Super-Genre of the circle
        primary_super = Counter(super_list).most_common(1)[0][0]
        cp31_super[primary_super] += 1
        total_cp31_circles += 1
        
    conn.close()
    
    print(f"Comiket C108 Total Circles: {total_comiket_circles}")
    print(f"Comicup CP31 Total Circles (mapped): {total_cp31_circles}")
    print("\n" + "="*70 + "\n")
    
    # 3. Print Aligned DBI table
    print(f"{'超级题材 (Super-Genre)':<45} | {'Comiket C108 DBI':<18} | {'Comicup CP31 DBI':<18}")
    print("-" * 90)
    
    for super_name, baseline in SUPER_GENRE_BASELINES.items():
        # Comiket
        c_count = comiket_super.get(super_name, 0)
        c_pct = (c_count / total_comiket_circles) * 100
        c_dbi = c_pct / baseline if baseline > 0 else 0.0
        
        # Comicup
        cp_count = cp31_super.get(super_name, 0)
        cp_pct = (cp_count / total_cp31_circles) * 100
        cp_dbi = cp_pct / baseline if baseline > 0 else 0.0
        
        print(f"{super_name:<45} | {c_dbi:.2f} (占比{c_pct:4.1f}%) | {cp_dbi:.2f} (占比{cp_pct:4.1f}%)")

if __name__ == "__main__":
    analyze_aligned_dbi()
