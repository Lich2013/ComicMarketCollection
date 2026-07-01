## Context

随着对同人集聚与创作生态的研究拓展，需要支持中国 CPSP（2025.10）和日本 C107（2025.12）两个新增数据集。C107 采用分散的单社团 WebCatalog JSON 文件结构，而 CPSP 采用大 JSON 分包接口数据结构，均需要进行结构化解析和批量入库。

## Goals / Non-Goals

**Goals:**
* 在 `data/comic_market.db` 中新建 `c107_circles`、`cpsp_products` 与 `cpsp_circles` 表，物理隔离数据。
* 编写 C107 社团详情 JSON 解析器，扫描指定目录并批量幂等导入社团元数据。
* 编写 CPSP 接口分包 JSON 解析器，抽取制品和社团信息，复用题材清洗与去重逻辑后批量幂等导入。
* 在 `main.py` 的 CLI 中支持对应的命令行参数调用，并补充完备的单元测试。

**Non-Goals:**
* 不对 C108 和 CP31 的原有数据表结构与数据记录进行侵入性改动。
* 本阶段暂不在 CLI 中挂载 C107 和 CPSP 的统计分析及对比报告输出逻辑，仅实现清洗与数据落库。

## Decisions

### 1. 数据库独立分表设计 (Table Isolation)
*   **决策**：为 C107 和 CPSP 数据建立独立的主表（`c107_circles`、`cpsp_products`、`cpsp_circles`）。
*   **理由**：C107 属于 Comiket 系列，其 CircleId 与 C108 的 ID 系统存在冲突风险；CPSP 与 CP31 同属 Comicup，但展期和主键系统独立。分表设计能最大限度保证数据隔离，避免覆盖。

### 2. IP 题材标准化清洗逻辑复用 (Theme Normalization Reuse)
*   **决策**：CPSP 数据导入时，直接复用 `src/cp31_importer.py` 中的 `normalize_theme` 函数。
*   **理由**：中日同人题材的译名及拼写习惯基本一致，复用已有的归一化逻辑，不仅能保持题材比对口径完全一致，还能减少开发成本，防止清洗词典分支发散。

## Risks / Trade-offs

*   **[风险]** CPSP 数据包中存在空包或异常分包（如 65 字节的空文件 `day1-36-178.json` 只有 `{"isSuccess":true,"result":{"total":0,"list":[]}}`）。
    *   *缓解方案*：在解析 `cpsp` 文件读取 `result.list` 时，增加严格的类型和空值判断保护（如使用 `data.get("result", {}).get("list", [])`），防止抛出 Key/Attribute 异常。
*   **[风险]** C107 详情包中存在 TwitterUrl 格式非标或缺失。
    *   *缓解方案*：使用已有的 `extract_twitter_username` 精准提取并进行 `None` 容错。
