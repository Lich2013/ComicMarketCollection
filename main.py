import sys
import argparse
from src.db import init_db
from src.config import load_config, write_default_config
from src.circle_sync import sync_circles_data
from src.twitter_sync import sync_all_circles_twitter, sync_single_tweet
from src.goods_extractor import process_pending_catalogs

def main():
    parser = argparse.ArgumentParser(
        description="Comic Market Collection System - 获取 CM 创作者/社团、同人制品及摊位信息的命令行工具"
    )
    
    parser.add_argument(
        "--init-db", 
        action="store_true", 
        help="初始化/创建 SQLite 数据库表结构"
    )
    parser.add_argument(
        "--write-config", 
        action="store_true", 
        help="在当前目录下生成默认的 config.yaml 配置文件模板"
    )
    parser.add_argument(
        "--sync-circles", 
        action="store_true", 
        help="从 WebCatalog 同步社团与展位信息"
    )
    parser.add_argument(
        "--fetch-tweets", 
        action="store_true", 
        help="使用 Playwright 抓取社团的 X (Twitter) 推文及品书图片"
    )
    parser.add_argument(
        "--extract-goods", 
        action="store_true", 
        help="使用 OpenAI 多模态模型解析待处理 (pending) 品书图片中的同人制品信息"
    )
    parser.add_argument(
        "--days", 
        type=str, 
        help="限制同步的参展天，多个天数用逗号隔开 (如: Day1,Day2)"
    )
    parser.add_argument(
        "--halls", 
        type=str, 
        help="限制同步的场馆，多个场馆用逗号隔开 (如: e123,s12)"
    )
    parser.add_argument(
        "--circle-ids",
        type=str,
        help="限制同步的社团 ID，多个 ID 用逗号隔开 (如: 123,456)"
    )
    parser.add_argument(
        "--circle-name",
        type=str,
        help="限制同步的社团或作者名，进行模糊匹配"
    )
    parser.add_argument(
        "--tweet-url",
        type=str,
        help="手动指定同步单条 X (Twitter) 博文链接，自动提取品书图文"
    )
    parser.add_argument(
        "--db-path", 
        type=str, 
        default="data/comic_market.db",
        help="自定义 SQLite 数据库路径 (默认: data/comic_market.db)"
    )
    parser.add_argument(
        "--export-goods",
        type=str,
        help="导出解析到的商品数据为 CSV 文件 (如: data/goods.csv)"
    )
    parser.add_argument(
        "--analyze-genres",
        type=str,
        help="统计分析社团题材与受众偏离度分布并导出为 JSON (如: data/genre_analysis.json)"
    )
    parser.add_argument(
        "--import-cp31",
        type=str,
        help="导入 CP31 day1/day2 原始 JSON 数据包文件夹 (如: /Users/lich/Downloads/cpp)"
    )
    parser.add_argument(
        "--import-c107",
        type=str,
        help="导入 C107 原始 JSON 数据包文件夹 (如: /Users/lich/work/c107/data/2025-12-20)"
    )
    parser.add_argument(
        "--import-cpsp",
        type=str,
        help="导入 CPSP 原始 JSON 数据包文件夹 (如: /Users/lich/Downloads/cpp/cpsp)"
    )
    parser.add_argument(
        "--analyze-cp31",
        action="store_true",
        help="执行 CP31 与 Comiket (C108) 的多维度比较分析并生成研究报告"
    )
    parser.add_argument(
        "--analyze-multi-era",
        action="store_true",
        help="执行 C107、C108、CPSP、CP31 的多展期联合比较分析并自动生成研究报告"
    )
    parser.add_argument(
        "--analyze-semantics",
        action="store_true",
        help="执行社团简介语义特征分析并自动生成研究报告"
    )
    parser.add_argument(
        "--force", 
        action="store_true", 
        help="强制更新，即使数据已在数据库中存在也不跳过"
    )
    parser.add_argument(
        "--generate-charts",
        action="store_true",
        help="编译生成并输出五个主要设计蓝图的可视化静态图表到 research/images/ 目录"
    )
    
    args = parser.parse_args()
    
    # 没有任何参数时，显示帮助并退出
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)
        
    # 1. 写入默认配置模板
    if args.write_config:
        print("Generating default config.yaml template...")
        write_default_config()
        print("Done. Please edit config.yaml to configure your cookies and API keys.")
        sys.exit(0)
        
    # 加载配置并初始化可观测性
    config = load_config()
    from src.utils.observability import init_observability
    init_observability(config)
        
    # 2. 初始化数据库
    if args.init_db:
        print(f"Initializing database at {args.db_path}...")
        init_db(args.db_path)
        print("Database initialized successfully.")
        
    # 3. 同步社团信息
    if args.sync_circles:
        # 首先保证数据库已初始化
        init_db(args.db_path)
        
        day_list = [x.strip() for x in args.days.split(",") if x.strip()] if args.days else None
        hall_list = [x.strip() for x in args.halls.split(",") if x.strip()] if args.halls else None
        
        print("Starting Circle & Booth sync...")
        sync_circles_data(day_list=day_list, hall_list=hall_list, db_path=args.db_path, force=args.force)
        
    # 4. 同步 X 推文和图片
    if args.fetch_tweets:
        init_db(args.db_path)
        
        day_list = [x.strip() for x in args.days.split(",") if x.strip()] if args.days else None
        hall_list = [x.strip() for x in args.halls.split(",") if x.strip()] if args.halls else None
        circle_ids = None
        if args.circle_ids:
            try:
                circle_ids = [int(x.strip()) for x in args.circle_ids.split(",") if x.strip()]
            except ValueError:
                print("Error: --circle-ids must be a comma-separated list of integers.", file=sys.stderr)
                sys.exit(1)
        circle_name = args.circle_name
        
        print("Starting Twitter scraper...")
        sync_all_circles_twitter(
            db_path=args.db_path,
            day_list=day_list,
            hall_list=hall_list,
            circle_ids=circle_ids,
            name_query=circle_name
        )
        
    # 4.5 同步单条 X 推文
    if args.tweet_url:
        init_db(args.db_path)
        target_circle_id = None
        if args.circle_ids:
            try:
                target_circle_id = int(args.circle_ids.split(",")[0])
            except ValueError:
                print("Error: --circle-ids must be a valid integer when used with --tweet-url.", file=sys.stderr)
                sys.exit(1)
        print(f"Starting single tweet sync for URL: {args.tweet_url}...")
        success = sync_single_tweet(args.tweet_url, circle_id=target_circle_id, db_path=args.db_path)
        if success:
            print("Single tweet sync finished successfully.")
        else:
            print("Single tweet sync failed.")
            sys.exit(1)
            
    # 5. LLM 提取制品
    if args.extract_goods:
        init_db(args.db_path)
        
        day_list = [x.strip() for x in args.days.split(",") if x.strip()] if args.days else None
        hall_list = [x.strip() for x in args.halls.split(",") if x.strip()] if args.halls else None
        circle_ids = None
        if args.circle_ids:
            try:
                circle_ids = [int(x.strip()) for x in args.circle_ids.split(",") if x.strip()]
            except ValueError:
                print("Error: --circle-ids must be a comma-separated list of integers.", file=sys.stderr)
                sys.exit(1)
        circle_name = args.circle_name
        
        print("Starting LLM goods extraction...")
        process_pending_catalogs(
            db_path=args.db_path,
            day_list=day_list,
            hall_list=hall_list,
            circle_ids=circle_ids,
            name_query=circle_name
        )

    # 6. 导出商品至 CSV
    if args.export_goods:
        init_db(args.db_path)
        
        day_list = [x.strip() for x in args.days.split(",") if x.strip()] if args.days else None
        hall_list = [x.strip() for x in args.halls.split(",") if x.strip()] if args.halls else None
        circle_ids = None
        if args.circle_ids:
            try:
                circle_ids = [int(x.strip()) for x in args.circle_ids.split(",") if x.strip()]
            except ValueError:
                print("Error: --circle-ids must be a comma-separated list of integers.", file=sys.stderr)
                sys.exit(1)
        circle_name = args.circle_name
        
        print(f"Starting goods export to: {args.export_goods}...")
        from src.db import export_goods_to_csv
        export_goods_to_csv(
            output_path=args.export_goods,
            day_list=day_list,
            hall_list=hall_list,
            circle_ids=circle_ids,
            name_query=circle_name,
            db_path=args.db_path
        )

    # 7. 题材及受众分析统计
    if args.analyze_genres:
        init_db(args.db_path)
        print(f"Starting genre & audience analysis, exporting to: {args.analyze_genres}...")
        from src.analytics import calculate_genre_distribution
        calculate_genre_distribution(db_path=args.db_path, output_path=args.analyze_genres)

    # 8. 导入 CP31 数据
    if args.import_cp31:
        print(f"Starting CP31 data import from directory: {args.import_cp31}...")
        from src.cp31_importer import import_cp31_dataset
        import_cp31_dataset(args.import_cp31, db_path=args.db_path)

    # 8.1 导入 C107 数据
    if args.import_c107:
        print(f"Starting C107 data import from directory: {args.import_c107}...")
        from src.c107_importer import import_c107_dataset
        import_c107_dataset(args.import_c107, db_path=args.db_path)

    # 8.2 导入 CPSP 数据
    if args.import_cpsp:
        print(f"Starting CPSP data import from directory: {args.import_cpsp}...")
        from src.cpsp_importer import import_cpsp_dataset
        import_cpsp_dataset(args.import_cpsp, db_path=args.db_path)

    # 9. 分析 CP31 数据并生成中日对比报告
    if args.analyze_cp31:
        print("Starting CP31 comparative analysis and report generation...")
        from src.cp31_analyzer import get_cp31_stats, generate_cp31_comparison_report
        stats = get_cp31_stats(db_path=args.db_path)
        if "error" in stats:
            print(f"Error: {stats['error']}")
            sys.exit(1)
        generate_cp31_comparison_report(stats, db_path=args.db_path)

    # 10. 执行多展期联合比较分析并生成研究报告
    if args.analyze_multi_era:
        print("Starting multi-era comparative analysis and report generation...")
        from src.multi_era_analyzer import run_multi_era_analysis, generate_multi_era_report
        try:
            stats = run_multi_era_analysis(db_path=args.db_path)
            generate_multi_era_report(stats, output_path="research/comiket_vs_comicup_multi_era_study.md")
            print("Auto-generating/updating charts for multi-era study...")
            from src.visualizer import generate_all_charts
            generate_all_charts(db_path=args.db_path, multi_era_stats=stats)
        except Exception as e:
            print(f"Error during multi-era analysis: {e}")
            sys.exit(1)

    # 11. 执行社团简介语义特征分析并自动生成研究报告
    if args.analyze_semantics:
        print("Starting circle description semantic analysis and report generation...")
        from src.semantic_analyzer import run_semantic_analysis, generate_semantic_report
        try:
            stats = run_semantic_analysis(db_path=args.db_path)
            generate_semantic_report(stats, output_path="research/semantic_description.md")
            print("Auto-generating/updating charts for semantic analysis...")
            from src.visualizer import generate_all_charts
            generate_all_charts(db_path=args.db_path, semantic_stats=stats)
        except Exception as e:
            print(f"Error during semantic analysis: {e}")
            sys.exit(1)

    # 12. 独立调用图表生成
    if args.generate_charts:
        print("Starting static visualization charts generation...")
        from src.visualizer import generate_all_charts
        try:
            generate_all_charts(db_path=args.db_path)
            print("Successfully completed charts generation.")
        except Exception as e:
            print(f"Error generating charts: {e}")
            sys.exit(1)

if __name__ == "__main__":
    main()
