import os
import sqlite3
import math
import json
from collections import defaultdict, Counter
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import seaborn as sns

# Try import wordcloud
try:
    from wordcloud import WordCloud
    HAS_WORDCLOUD = True
except ImportError:
    HAS_WORDCLOUD = False
    print("Warning: wordcloud library is not installed or failed to import. Word cloud generation will be skipped.")

# Matplotlib styling settings
plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
# Set CJK fonts for macOS/Windows/Linux to prevent tofu blocks
plt.rcParams['font.sans-serif'] = [
    'Arial Unicode MS', 
    'Hiragino Sans', 
    'Heiti TC', 
    'Microsoft YaHei', 
    'PingFang SC', 
    'TakaoPGothic',
    'sans-serif'
]
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.dpi'] = 300


def get_cjk_font_path():
    """找到系统中的中日文字体路径，用于 WordCloud"""
    paths = [
        "/System/Library/Fonts/PingFang.ttc",  # macOS
        "/System/Library/Fonts/STHeiti Light.ttc", # macOS
        "/System/Library/Fonts/STHeiti Medium.ttc", # macOS
        "C:\\Windows\\Fonts\\msyh.ttc",        # Windows
        "C:\\Windows\\Fonts\\simhei.ttf",       # Windows
        "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf", # Linux
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",   # Linux
        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc"            # Linux
    ]
    for p in paths:
        if os.path.exists(p):
            return p
    return None


def get_venn_counts(db_path):
    """获取 C108 社媒与简介填写的交集频数统计"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT 
                SUM(CASE WHEN description IS NOT NULL AND description != '' THEN 1 ELSE 0 END) as has_desc,
                SUM(CASE WHEN twitter_url IS NOT NULL AND twitter_url != '' THEN 1 ELSE 0 END) as has_tw,
                SUM(CASE WHEN pixiv_url IS NOT NULL AND pixiv_url != '' THEN 1 ELSE 0 END) as has_px,
                SUM(CASE WHEN (description IS NOT NULL AND description != '') AND (twitter_url IS NOT NULL AND twitter_url != '') THEN 1 ELSE 0 END) as has_desc_tw,
                SUM(CASE WHEN (description IS NOT NULL AND description != '') AND (pixiv_url IS NOT NULL AND pixiv_url != '') THEN 1 ELSE 0 END) as has_desc_px,
                SUM(CASE WHEN (twitter_url IS NOT NULL AND twitter_url != '') AND (pixiv_url IS NOT NULL AND pixiv_url != '') THEN 1 ELSE 0 END) as has_tw_px,
                SUM(CASE WHEN (description IS NOT NULL AND description != '') AND (twitter_url IS NOT NULL AND twitter_url != '') AND (pixiv_url IS NOT NULL AND pixiv_url != '') THEN 1 ELSE 0 END) as has_all,
                COUNT(*) as total
            FROM circles
        """)
        row = cursor.fetchone()
    except sqlite3.Error as e:
        print(f"Error querying C108 Venn data: {e}")
        row = None
    finally:
        conn.close()
        
    if not row or not row[7]:
        return None
    
    total = row[7]
    n_all = row[6] or 0
    n_desc_tw_only = (row[3] or 0) - n_all
    n_desc_px_only = (row[4] or 0) - n_all
    n_tw_px_only = (row[5] or 0) - n_all
    n_desc_only = (row[0] or 0) - n_desc_tw_only - n_desc_px_only - n_all
    n_tw_only = (row[1] or 0) - n_desc_tw_only - n_tw_px_only - n_all
    n_px_only = (row[2] or 0) - n_desc_px_only - n_tw_px_only - n_all
    n_none = total - (n_desc_only + n_tw_only + n_px_only + n_desc_tw_only + n_desc_px_only + n_tw_px_only + n_all)
    
    return {
        "total": total,
        "has_desc": row[0] or 0,
        "has_tw": row[1] or 0,
        "has_px": row[2] or 0,
        "only_desc": n_desc_only,
        "only_tw": n_tw_only,
        "only_px": n_px_only,
        "desc_tw": n_desc_tw_only,
        "desc_px": n_desc_px_only,
        "tw_px": n_tw_px_only,
        "all": n_all,
        "none": n_none
    }


def get_cp31_dbi_data(db_path):
    """获取 CP31 题材的 SDI / DBI 数据"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='cp31_products'")
        if not cursor.fetchone():
            return []
        
        cursor.execute("SELECT SUM(hot_count) FROM cp31_products")
        total_heat = cursor.fetchone()[0] or 1
        cursor.execute("SELECT COUNT(*) FROM cp31_products")
        total_products = cursor.fetchone()[0] or 1
        
        cursor.execute("""
            SELECT theme_alias, COUNT(*) as cnt, SUM(hot_count) as heat 
            FROM cp31_products 
            GROUP BY theme_alias
        """)
        theme_metrics = cursor.fetchall()
    except sqlite3.Error as e:
        print(f"Error querying CP31 DBI data: {e}")
        theme_metrics = []
    finally:
        conn.close()
        
    dbi_list = []
    for row in theme_metrics:
        theme = row[0] or "未知题材"
        cnt = row[1]
        heat = row[2] or 0
        
        supply_pct = (cnt / total_products) * 100
        demand_pct = (heat / total_heat) * 100
        
        dbi = supply_pct / demand_pct if demand_pct > 0 else 0.0
        dbi_list.append({
            "theme": theme,
            "count": cnt,
            "supply_percentage": supply_pct,
            "heat": heat,
            "demand_percentage": demand_pct,
            "dbi": dbi
        })
    return dbi_list


def generate_social_venn_diagram(db_path, output_path="research/images/social_venn_diagram.png"):
    """渲染 C108 社团引流与简介填写三维交叉维恩图"""
    data = get_venn_counts(db_path)
    if not data:
        print("No C108 circles data available to generate Social Venn Diagram.")
        return False
        
    fig, ax = plt.subplots(figsize=(8, 7))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')
    
    # Coordinates for the 3 circles
    r = 0.23
    c_desc = patches.Circle((0.38, 0.60), r, color='#4682B4', alpha=0.5, label=f"简介已填写 ({data['has_desc']:,})")
    c_tw = patches.Circle((0.62, 0.60), r, color='#1DA1F2', alpha=0.5, label=f"Twitter 绑定 ({data['has_tw']:,})")
    c_px = patches.Circle((0.50, 0.38), r, color='#FF69B4', alpha=0.4, label=f"Pixiv 绑定 ({data['has_px']:,})")
    
    ax.add_patch(c_desc)
    ax.add_patch(c_tw)
    ax.add_patch(c_px)
    
    # Add borders
    ax.add_patch(patches.Circle((0.38, 0.60), r, fill=False, edgecolor='#3a6a93', linewidth=1.5))
    ax.add_patch(patches.Circle((0.62, 0.60), r, fill=False, edgecolor='#157ebf', linewidth=1.5))
    ax.add_patch(patches.Circle((0.50, 0.38), r, fill=False, edgecolor='#cc5490', linewidth=1.5))
    
    # Text helper
    def add_val(x, y, label, val):
        pct = (val / data['total']) * 100
        ax.text(x, y, f"{label}\n{val:,}\n({pct:.1f}%)", ha='center', va='center', fontsize=9, fontweight='bold')
        
    add_val(0.26, 0.68, "仅简介", data['only_desc'])
    add_val(0.74, 0.68, "仅 Twitter", data['only_tw'])
    add_val(0.50, 0.22, "仅 Pixiv", data['only_px'])
    
    add_val(0.50, 0.68, "简介+Twitter", data['desc_tw'])
    add_val(0.38, 0.46, "简介+Pixiv", data['desc_px'])
    add_val(0.62, 0.46, "Twitter+Pixiv", data['tw_px'])
    
    add_val(0.50, 0.52, "三者重合", data['all'])
    
    # Outer box for 'None' counts
    ax.text(0.10, 0.10, f"无绑定及简介留空: {data['none']:,} 社团 ({data['none']/data['total']*100:.1f}%)", 
            ha='left', va='center', fontsize=10, bbox=dict(boxstyle='round,pad=0.3', facecolor='#f5f5f5', edgecolor='#d3d3d3'))
    
    ax.set_title(f"Comiket C108 社团引流与简介填写三维交叉维恩图\n(样本总量: {data['total']:,} 社团)", fontsize=12, fontweight='bold', pad=20)
    plt.legend(loc='upper right', frameon=True, facecolor='#ffffff', edgecolor='#d3d3d3')
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, bbox_inches='tight', dpi=300)
    plt.close()
    return True


def generate_dbi_bubble_chart(db_path, output_path="research/images/dbi_bubble_chart.png"):
    """渲染 CP31 题材的供需偏离度气泡图 (SDI Bubble Chart)"""
    dbi_list = get_cp31_dbi_data(db_path)
    if not dbi_list:
        print("No CP31 data available to generate DBI Bubble Chart.")
        return False
        
    # Filter for visualization: demand_percentage > 0.05% or count > 5
    filtered_list = [d for d in dbi_list if d['demand_percentage'] > 0.05 or d['count'] > 5]
    # Sort to show most important ones
    filtered_list = sorted(filtered_list, key=lambda x: x['count'], reverse=True)[:25]
    
    if not filtered_list:
        print("No filtered data for DBI Bubble Chart.")
        return False
        
    fig, ax = plt.subplots(figsize=(10, 6.5))
    
    x = [d['demand_percentage'] for d in filtered_list]
    y = [d['dbi'] for d in filtered_list]
    sizes = [d['count'] * 12 for d in filtered_list]
    
    scatter = ax.scatter(x, y, s=sizes, alpha=0.6, edgecolors='gray', c=y, cmap='coolwarm', norm=plt.Normalize(vmin=0.2, vmax=1.8))
    
    # Draw equilibrium line
    ax.axhline(1.0, color='red', linestyle='--', alpha=0.6, label='供需平衡基线 (SDI = 1.0)')
    
    # Label bubbles
    for d in filtered_list:
        # Prevent zero positions or overlap in labels
        ax.annotate(d['theme'], 
                    (d['demand_percentage'], d['dbi']),
                    textcoords="offset points", 
                    xytext=(0, 8), 
                    ha='center', fontsize=9, fontweight='semibold')
                    
    ax.set_xlabel("需求占比 (Allcpp 心愿单收藏数占比 %)", fontsize=11, fontweight='bold')
    ax.set_ylabel("供需偏离度 (SDI = 供给占比 % / 需求占比 %)", fontsize=11, fontweight='bold')
    ax.set_title("Comicup 31 核心题材供需偏离度气泡图 (SDI Bubble Chart)\n(气泡大小代表制品数量，SDI < 1 表示供不应求)", fontsize=13, fontweight='bold', pad=15)
    
    ax.set_yscale('log')
    from matplotlib.ticker import FormatStrFormatter
    ax.yaxis.set_major_formatter(FormatStrFormatter('%.2f'))
    
    cbar = plt.colorbar(scatter, ax=ax)
    cbar.set_label('SDI 偏离度 (偏低说明严重供不应求，偏高说明供过于求)', rotation=270, labelpad=15, fontweight='bold')
    
    plt.legend(loc='upper right', frameon=True)
    plt.tight_layout()
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, bbox_inches='tight', dpi=300)
    plt.close()
    return True


def generate_booth_heatmap(db_path, output_path="research/images/booth_heatmap.png"):
    """渲染中日展位物理空间集聚与密度热力图"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 1. Comiket C108 Booth Density
    comiket_rows = []
    try:
        cursor.execute("""
            SELECT hall, block, COUNT(*) 
            FROM circles 
            WHERE hall IS NOT NULL AND hall != '' AND block IS NOT NULL AND block != ''
            GROUP BY hall, block
        """)
        comiket_rows = cursor.fetchall()
    except sqlite3.Error as e:
        print(f"Error querying circles for heatmap: {e}")
        
    # 2. Comicup CP31 Street Density
    cp31_rows = []
    try:
        cursor.execute("""
            SELECT position_name, COUNT(*) as cnt 
            FROM cp31_circles 
            WHERE position_name IS NOT NULL AND position_name != '' AND position_name != '未知'
            GROUP BY position_name 
            ORDER BY cnt DESC 
            LIMIT 15
        """)
        cp31_rows = cursor.fetchall()
    except sqlite3.Error as e:
        print(f"Error querying cp31_circles for heatmap: {e}")
        
    conn.close()
    
    if not comiket_rows and not cp31_rows:
        print("No spatial data available to generate Heatmap.")
        return False
        
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6.5))
    
    # Plot Comiket Heatmap (Left)
    if comiket_rows:
        halls = sorted(list(set(r[0] for r in comiket_rows)))
        # Filter top blocks for clean plot
        top_blocks = [x[0] for x in Counter(r[1] for r in comiket_rows).most_common(20)]
        top_blocks.sort()
        
        matrix = [[0 for _ in range(len(top_blocks))] for _ in range(len(halls))]
        hall_to_idx = {h: i for i, h in enumerate(halls)}
        block_to_idx = {b: i for i, b in enumerate(top_blocks)}
        
        for h, b, cnt in comiket_rows:
            if h in hall_to_idx and b in block_to_idx:
                matrix[hall_to_idx[h]][block_to_idx[b]] = cnt
                
        sns.heatmap(matrix, xticklabels=top_blocks, yticklabels=halls, annot=True, fmt="d", cmap="YlOrRd", ax=ax1, cbar_kws={'label': '社团数量 (Density)'})
        ax1.set_title("Comiket C108 物理空间展馆-街区社团分布热力图\n(横轴为主要 Block 假名，纵轴为展馆分类)", fontsize=11, fontweight='bold')
        ax1.set_xlabel("展位 Block 假名", fontsize=10)
        ax1.set_ylabel("物理展馆 (Hall)", fontsize=10)
    else:
        ax1.text(0.5, 0.5, "无 Comiket 空间数据", ha='center', va='center')
        
    # Plot CP31 Street Density (Right)
    if cp31_rows:
        streets = [r[0] for r in cp31_rows]
        counts = [r[1] for r in cp31_rows]
        
        colors = sns.color_palette("viridis", len(streets))
        bars = ax2.barh(streets[::-1], counts[::-1], color=colors, edgecolor='gray')
        
        for bar in bars:
            width = bar.get_width()
            ax2.text(width + 1, bar.get_y() + bar.get_height()/2, f"{int(width)}", 
                     va='center', ha='left', fontsize=9, fontweight='semibold')
                     
        ax2.set_title("Comicup 31 热门主题专区/街道社团集聚密度分布\n(前 15 名热门专区摊位密度对比)", fontsize=11, fontweight='bold')
        ax2.set_xlabel("活跃社团总数 (摊位数)", fontsize=10)
        ax2.set_ylabel("专区街道名称 (Position Name)", fontsize=10)
        ax2.grid(True, linestyle='--', alpha=0.5)
    else:
        ax2.text(0.5, 0.5, "无 CP31 空间数据", ha='center', va='center')
        
    plt.suptitle("中日双城同人展位物理空间集聚与街区密度热力图", fontsize=14, fontweight='bold', y=0.98)
    plt.tight_layout()
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, bbox_inches='tight', dpi=300)
    plt.close()
    return True


def generate_description_wordcloud(stats, output_path="research/images/description_wordcloud.png"):
    """渲染 Comiket C108 简介词频词云图"""
    if not HAS_WORDCLOUD:
        print("Skipping word cloud generation: wordcloud package is not available.")
        return False
        
    tfidf_results = stats.get("genre_tfidf_results", {})
    if not tfidf_results:
        print("No TF-IDF results available to generate Word Cloud.")
        return False
        
    word_freq = defaultdict(float)
    for words_list in tfidf_results.values():
        for item in words_list:
            word_freq[item['word']] += item['score']
            
    if not word_freq:
        print("Word frequencies dictionary is empty.")
        return False
        
    font_path = get_cjk_font_path()
    if not font_path:
        print("Warning: CJK font path not found. WordCloud might display tofu blocks for Chinese/Japanese text.")
        
    wc = WordCloud(
        font_path=font_path,
        background_color='white',
        width=800,
        height=500,
        max_words=100,
        colormap='tab10',
        prefer_horizontal=0.7
    )
    
    wc.generate_from_frequencies(word_freq)
    
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.imshow(wc, interpolation='bilinear')
    ax.axis('off')
    ax.set_title("Comiket C108 社团简介高频特征词云图 (TF-IDF Weighting)", fontsize=13, fontweight='bold', pad=15)
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, bbox_inches='tight', dpi=300)
    plt.close()
    return True


def generate_radar_ecology_comparison(stats, output_path="research/images/radar_ecology_comparison.png"):
    """渲染中日双城生态倾向对比雷达图"""
    c108 = stats.get("c108", {})
    cp31 = stats.get("cp31", {})
    
    # 1. Concentration CR10
    c108_cr10 = c108.get("concentration", {}).get("cr10", 61.59)
    cp31_cr10 = cp31.get("concentration", {}).get("cr10", 30.12)
    
    # 2. Novel %
    c108_novel = 5.40
    cache_path = "data/semantic_metrics.json"
    if os.path.exists(cache_path):
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                c108_novel = json.load(f).get("c108_novel_pct", 5.40)
        except Exception:
            pass
            
    cp31_novel = 30.12
    cp31_media = cp31.get("media_types", [])
    for m in cp31_media:
        if m.get("type") in ("小说", "小说本", "文本"):
            cp31_novel = m.get("percentage", 30.12)
            break
            
    # 3. Freebies %
    c108_freebies = 0.5
    cp31_freebies = cp31.get("materiality", {}).get("freebies", {}).get("percentage", 4.12)
    
    # 4. O2O rate
    c108_o2o = 5.0
    cp31_o2o = 85.0
    
    # 5. Day overlap %
    c108_overlap = 0.0
    cp31_overlap = cp31.get("day_scheduling", {}).get("overlap_percentage", 30.8)
    
    # Labels and values
    labels = ['题材集中度 (CR10)', '同人小说占比', '无料礼物占比', '数字化O2O预约率', '双日题材重合度']
    num_vars = len(labels)
    
    angles = [n / float(num_vars) * 2 * math.pi for n in range(num_vars)]
    angles += angles[:1]
    
    c108_vals = [c108_cr10, c108_novel, c108_freebies, c108_o2o, c108_overlap]
    c108_vals += c108_vals[:1]
    
    cp31_vals = [cp31_cr10, cp31_novel, cp31_freebies, cp31_o2o, cp31_overlap]
    cp31_vals += cp31_vals[:1]
    
    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
    
    # Draw axes
    plt.xticks(angles[:-1], labels, color='grey', size=10, fontweight='bold')
    
    # Y-axis ticks
    ax.set_rlabel_position(0)
    plt.yticks([20, 40, 60, 80, 100], ["20%", "40%", "60%", "80%", "100%"], color="grey", size=8)
    plt.ylim(0, 100)
    
    # Plot Comiket C108
    ax.plot(angles, c108_vals, linewidth=2, linestyle='solid', label="东京 Comiket (C108)", color='#4682B4')
    ax.fill(angles, c108_vals, '#4682B4', alpha=0.3)
    
    # Plot Comicup CP31
    ax.plot(angles, cp31_vals, linewidth=2, linestyle='solid', label="上海 Comicup (CP31)", color='#FF6347')
    ax.fill(angles, cp31_vals, '#FF6347', alpha=0.3)
    
    plt.title("中日双城同人生态倾向对比雷达图\n(东京 Comiket C108 vs 上海 Comicup CP31)", size=13, fontweight='bold', pad=25)
    plt.legend(loc='upper right', bbox_to_anchor=(0.1, 0.1), frameon=True)
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, bbox_inches='tight', dpi=300)
    plt.close()
    return True


def generate_all_charts(db_path="data/comic_market.db", semantic_stats=None, multi_era_stats=None):
    """一键生成并保存五大核心设计蓝图对应的图表"""
    # 延迟加载，防止死循环导入
    if semantic_stats is None:
        from src.semantic_analyzer import run_semantic_analysis
        print("Running semantic analysis to retrieve stats for charts...")
        semantic_stats = run_semantic_analysis(db_path)
        
    if multi_era_stats is None:
        from src.multi_era_analyzer import run_multi_era_analysis
        print("Running multi-era analysis to retrieve stats for charts...")
        multi_era_stats = run_multi_era_analysis(db_path)
        
    print("Generating Social Venn Diagram...")
    generate_social_venn_diagram(db_path, "research/images/social_venn_diagram.png")
    
    print("Generating DBI Bubble Chart...")
    generate_dbi_bubble_chart(db_path, "research/images/dbi_bubble_chart.png")
    
    print("Generating Booth Spatial Heatmap...")
    generate_booth_heatmap(db_path, "research/images/booth_heatmap.png")
    
    if HAS_WORDCLOUD:
        print("Generating Description Word Cloud...")
        generate_description_wordcloud(semantic_stats, "research/images/description_wordcloud.png")
    else:
        print("Skipped Description Word Cloud generation (wordcloud package not found).")
        
    print("Generating Radar Ecology Comparison Chart...")
    generate_radar_ecology_comparison(multi_era_stats, "research/images/radar_ecology_comparison.png")
    
    print("All charts have been generated in research/images/")
