## Context

当前系统能够采集并使用 LLM 解析品书生成结构化的商品记录，但该数据留在 SQLite 数据库中。为了满足用户线下逛展的便利性，设计一套可以从命令行工具中触发的商品导出方案，根据物理路线优化的顺序将商品导出为 CSV 格式文件，便于用户使用 Excel、WPS 等软件进行展示和管理。

## Goals / Non-Goals

**Goals:**
- 提供命令行 `--export-goods <csv_path>` 接口。
- 支持全套原有的社团过滤规则（`--days`, `--halls`, `--circle-ids`, `--circle-name`）。
- 导出的 CSV 文件包含日期、场馆、区域、摊位号、社团名、作者、类别 (genre)、类型、商品、数量、价格、来源推文、社交媒体链接。
- CSV 记录的物理顺序按 `Day -> Hall -> Block -> Space` 排序。
- 保证导出的文件在 Excel 等软件中打开时，中日文字符不发生乱码。

**Non-Goals:**
- 不支持直接导出 `.xlsx` 格式，以避免引入 pandas / openpyxl 等重度外部依赖。使用标准库的 CSV 写入并带上 UTF-8 BOM 即可满足兼容性。

## Decisions

### 1. 数据库多表联合查询设计
商品数据分散在多张表中，我们将通过 SQL `JOIN` 进行联查。
- 查询 SQL 设计：
  ```sql
  SELECT 
      c.day AS "day",
      c.hall AS "hall",
      c.block AS "block",
      c.space AS "space",
      c.name AS "circle_name",
      c.author AS "circle_author",
      c.genre AS "circle_genre",
      g.type AS "goods_type",
      g.name AS "goods_name",
      1 AS "quantity",
      g.price AS "price",
      cat.tweet_url AS "tweet_url",
      c.twitter_url AS "twitter_url"
  FROM goods g
  JOIN circles c ON g.circle_id = c.id
  LEFT JOIN catalogs cat ON g.catalog_id = cat.id
  ```
- 关联关系：
  - `goods` 表通过 `circle_id` 强关联 `circles`。
  - `goods` 表通过 `catalog_id` 弱关联 `catalogs`（使用 `LEFT JOIN`，保证即使推文已被清理，商品记录仍可导出）。
- 排序规则：`ORDER BY c.day, c.hall, c.block, c.space`，实现展会天数、展馆、排号和展位号的递增排序，形成逛展最优路线。

### 2. 复用过滤参数
直接复用 `src/db.py` 中已实现的 `get_filtered_circle_ids` 方法。
- 若用户通过命令行传入了过滤参数，先通过 `get_filtered_circle_ids` 获取符合条件的社团 ID 集合 `target_circle_ids`。
- SQL 查询中追加条件 `WHERE g.circle_id IN ({placeholders})` 进行范围过滤。
- 若过滤后的社团 ID 集合为空，则直接写入包含表头的空 CSV 文件，避免执行无效 SQL。

### 3. CSV 编码设计
采用 Python 的内置 `csv` 库，文件写入时显式指定 `encoding="utf-8-sig"`。
- `utf-8-sig` 会在文件头部写入 UTF-8 BOM (`\xef\xbb\xbf`)。
- 这是 Windows 平台 Excel 识别 UTF-8 编码的黄金标准，能彻底杜绝双击打开 CSV 时日文（如 `お品書き`）和中文乱码的问题。

## Risks / Trade-offs

- **[Risk]** 用户输入的导出路径中，其父级文件夹不存在。
  - **[Mitigation]** 在写入 CSV 前，使用 `os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)` 自动创建不存在的父级目录。
- **[Risk]** 商品价格或名称中可能包含逗号 `,` 或换行符等。
  - **[Mitigation]** 使用标准库 `csv.writer`，它会自动为包含特殊字符的文本加上双引号包裹，确保 CSV 格式不会错乱。
