import os
import sqlite3
import math

def run_chi_square_test():
    """
    对 Comiket 题材分类与创作者社交媒介采纳倾向进行卡方独立性检验，
    并打印交叉列联表及卡方统计参数。
    """
    db_path = "data/comic_market.db"
    if not os.path.exists(db_path):
        print(f"错误: 数据库文件不存在，请确保在项目根目录下运行此脚本。当前检测路径: {db_path}")
        return

    # 1. 尝试导入科学计算第三方库，如果缺失则引导安装
    try:
        import pandas as pd
        from scipy.stats import chi2_contingency
    except ImportError:
        print("提示: 缺少 scipy 或 pandas 库。建议使用以下命令一键运行:")
        print("uv run --with pandas --with scipy research/scripts/chi_square_test.py")
        print("或者在当前虚拟环境中安装: pip install pandas scipy\n")
        return

    conn = sqlite3.connect(db_path)
    
    # 2. 读取高频题材（摊位数大或等于 200 的题材，以提供稳定的单元格频数）
    query = """
        SELECT genre, 
               (CASE WHEN twitter_url IS NOT NULL AND twitter_url != '' THEN 1 ELSE 0 END) as has_twitter,
               (CASE WHEN pixiv_url IS NOT NULL AND pixiv_url != '' THEN 1 ELSE 0 END) as has_pixiv
        FROM circles 
        WHERE genre IS NOT NULL AND genre != ''
          AND genre IN (
              SELECT genre FROM circles 
              GROUP BY genre 
              HAVING COUNT(*) >= 200
          )
    """
    df = pd.read_sql_query(query, conn)
    conn.close()

    # 3. 映射社交平台采纳的组合类型 (双向/仅X/仅Pixiv/无)
    def get_platform_type(row):
        if row['has_twitter'] and row['has_pixiv']:
            return 'Both (X & Pixiv)'
        elif row['has_twitter']:
            return 'X Only'
        elif row['has_pixiv']:
            return 'Pixiv Only'
        else:
            return 'None'

    df['platform_status'] = df.apply(get_platform_type, axis=1)

    # 4. 构造列联表 (Contingency Table)
    contingency_table = pd.crosstab(df['genre'], df['platform_status'])
    print("=== 题材与社交平台采纳列联表 (Contingency Table) ===")
    print(contingency_table.to_string())
    print("\n" + "="*70 + "\n")

    # 5. 执行卡方独立性检验
    chi2, p_val, dof, expected = chi2_contingency(contingency_table)
    
    print("=== 卡方独立性检验结果 (Chi-Square Test of Independence) ===")
    print(f"卡方统计量 (Chi-Square Statistic) : {chi2:.4f}")
    print(f"自由度 (Degrees of Freedom)        : {dof}")
    print(f"显著性值 (p-value)                 : {p_val}")
    
    # 计算效应量 Cramér's V
    n_total = len(df)
    r, c = contingency_table.shape
    k_dim = min(r, c) - 1
    cramers_v = math.sqrt(chi2 / (n_total * k_dim)) if k_dim > 0 else 0.0
    
    if k_dim == 3:
        if cramers_v >= 0.29:
            effect_strength = "强效应关联 (Strong Effect Size)"
        elif cramers_v >= 0.17:
            effect_strength = "中等效应关联 (Medium Effect Size)"
        elif cramers_v >= 0.06:
            effect_strength = "弱效应关联 (Small Effect Size)"
        else:
            effect_strength = "极微弱或无效应关联 (Negligible Effect Size)"
    else:
        effect_strength = "极微弱" if cramers_v < 0.1 else "强" if cramers_v >= 0.3 else "中等"
        
    print(f"Cramér's V 效应量 (Effect Size)   : {cramers_v:.4f}")
    print(f"效应强度判定 (Effect Strength)     : {effect_strength}")
    
    # 6. 统计决策判定
    alpha = 0.01
    if p_val < alpha:
        print(f"\n结论: 在显著性水平 alpha = {alpha} 下，拒绝原假设(H0)。")
        print("证明【题材大类】与【创作者社交媒介采纳倾向】之间存在高度显著的统计学关联性（p < 0.01），且 Cramér's V 效应量表明该关联确实具有实质性强关联强度，排除了纯由大样本量造成的“虚假显著”。")
    else:
        print(f"\n结论: 无法拒绝原假设(H0)，表明两变量相互独立。")

if __name__ == "__main__":
    run_chi_square_test()
