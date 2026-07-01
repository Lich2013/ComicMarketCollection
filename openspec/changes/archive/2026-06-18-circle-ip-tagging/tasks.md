## 1. 数据库设计与 CRUD 扩展

- [x] 1.1 在 `src/db.py` 的 `init_db` 函数中，添加创建 `circle_ip_tags` 关系表以及 `v_circles_with_ip_tags` 联表视图的 SQL 语句。
- [x] 1.2 在 `src/db.py` 中，新增 `save_circle_ip_tags(tags: list[dict], db_path: str)` 的批量插入与替换 CRUD 方法。
- [x] 1.3 重构 `src/db.py` 中的 `export_goods_to_csv` 函数，修改 SQL 联表查询并追加导出“细分IP（Sub-IP）”列。

## 2. 打标流水线与物理空间传播算法实现

- [x] 2.1 新建核心打标模块 `src/circle_tagger.py`，实现通过社团名字和简介进行多语言关键字匹配种子点的逻辑。
- [x] 2.2 在 `src/circle_tagger.py` 中，实现通过 `goods` 商品表中已提取的制品名称对社团打上 IP 种子标签的逻辑。
- [x] 2.3 在 `src/circle_tagger.py` 中，实现基于滑动窗口和种子密度检测的物理空间邻域传播打标推理逻辑（置信度设为 0.8，来源为 spatial）。
- [x] 2.4 在 `src/circle_tagger.py` 中，暴露 `run_circle_tagging(db_path: str)` 函数一键集成以上三步打标流水线并将结果持久化。

## 3. 命令行参数集成与逛展路线排序

- [x] 3.1 在 `main.py` 中，集成 `--tag-circles` 一键打标选项，并在逻辑分支中执行打标流水线。
- [x] 3.2 在 `main.py` 中，集成 `--search-ip <ip_name>` 物理路线检索选项，实现从视图关联查询并在控制台按照 `Day -> Hall -> Block -> Space` 排序格式化输出。

## 4. 测试与验证

- [x] 4.1 新建单元测试 `tests/test_circle_tagger.py`，模拟数据库测试数据验证打标、空间传播与视图查询的完整性与幂等性。
- [x] 4.2 运行项目 pytest 全量测试，并执行真实的 `--tag-circles` 以及 `--search-ip "明日方舟"` 进行功能检查。
