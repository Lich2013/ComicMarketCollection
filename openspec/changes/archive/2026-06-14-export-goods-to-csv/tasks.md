## 1. 数据库逻辑实现

- [x] 1.1 在 src/db.py 中新增 export_goods_to_csv 函数，实现多表联查及带有 BOM (utf-8-sig) 的 CSV 文件生成
- [x] 1.2 支持传入动态过滤参数（天数、场馆、社团 ID 列表、名称），复用现有过滤机制，在 SQL 中动态添加 WHERE 条件

## 2. 命令行入口集成

- [x] 2.1 修改 main.py，在 ArgumentParser 中新增 --export-goods 参数定义，支持指定导出目标路径
- [x] 2.2 在 main.py 中集成调用逻辑，当指定该参数时提取所有过滤参数并调用 db.py 的导出方法

## 3. 测试与验证

- [x] 3.1 在 tests/ 中添加单元测试，模拟商品和社团数据并验证全量导出、条件筛选导出及无匹配时空表导出的正确性
- [x] 3.2 运行所有单元测试（PYTHONPATH=. uv run pytest）并确保全部通过
