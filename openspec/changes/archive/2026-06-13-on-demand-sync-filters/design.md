## Context

随着展会社团增多，全量同步 X 推文和进行 GPT 识别需要花费大量的网络请求和 API 额度，无法快速调试某几个特定社团。我们需要实现多维度按需过滤（支持 ID 列表、名称、天数和场馆）。

## Goals / Non-Goals

**Goals:**
- 在 `main.py` 层面实现推文同步与制品提取的筛选参数配置。
- 在 `src/db.py` 层面设计通用的条件组合过滤器函数，获取匹配的社团 ID 集合。
- 确保推文同步爬虫和 LLM 提取端都能无缝接收并应用过滤后的社团范围。

**Non-Goals:**
- 本次变更仅涉及按条件过滤部分，不改变底层的 Playwright 爬虫细节或 GPT 识别 Schema。

## Decisions

### 1. 命令行筛选参数统合
- **Decision**: 在 `main.py` 的 argparse 中，将现有的 `--days` 和 `--halls` 扩展为同步和提取的共有参数，并新增两个参数：
  - `--circle-ids`: 用逗号隔开的社团 ID 串。
  - `--circle-name`: 用于模糊查找社团或作者名。
- **Rationale**: 这样用户可以使用同样的参数组合过滤全部流程（如 `--days Day2 --halls e7 --sync-circles` 或 `--days Day2 --halls e7 --fetch-tweets` 等）。

### 2. 数据库级通用筛选
- **Decision**: 在 `src/db.py` 中编写 `get_filtered_circle_ids` 辅助函数。该函数接收 `day_list`, `hall_list`, `circle_ids`, `name_query` 等参数，组装带占位符的参数化 SQL（防止 SQL 注入），并返回符合条件的 `circle_id` 集合。
- **Rationale**: 统一在数据库层处理筛选能够避免在 Python 代码中遍历海量社团记录，提高运行速度。

### 3. 多接口调用适配
- **Decision**:
  - `sync_all_circles_twitter(db_path, day_list, hall_list, circle_ids, name_query)`: 调用上述 DB 筛选，若用户传入了任何过滤参数，只遍历在匹配 ID 集合中的社团进行 X 爬取。
  - `process_pending_catalogs(db_path, day_list, hall_list, circle_ids, name_query)`: 同样获取匹配 ID 集合，只拉取 `circle_id IN (matched_ids)` 的 pending 状态品书记录进行 LLM 识别。

---

## Risks / Trade-offs

- **[Risk] 用户过滤输入格式不正确导致报错**
  - **Mitigation**: 在参数处理时，对 `--circle-ids` 进行类型转换与校验（非整数或解析失败时给出清晰的错误提示）。
