## Context

在之前的变更中，我们新增了多期计算引擎，并在 `research/comiket_vs_comicup_multi_era_study.md` 下生成了分析大盘指标。然而，项目仍遗留了最初的方法论大纲设计文档 `comiket_vs_comicup.md` 和旧的单期对比报告 `comiket_vs_comicup_comparison.md`。这导致了 `research/` 目录下研究文件分布零散，缺乏自洽和统一性。

## Goals / Non-Goals

**Goals:**
* 将旧有的学术背景论证（选用 CP31 的科学基准）与中日大盘清洗映射表，整合进入 `src/multi_era_analyzer.py` 生成的 Markdown 报告模板中。
* 确保在执行多期联合分析 `--analyze-multi-era` 时，能够自动、安全地清理掉 `comiket_vs_comicup.md` 和 `comiket_vs_comicup_comparison.md` 冗余文档。
* 通过单元测试验证文件的删除与合并报告内容的完整性。

**Non-Goals:**
* 不涉及已有的数据库导入代码（CPSP, C107）的修改。
* 不涉及其他不相关的 `research/` 文档的归并。

## Decisions

### 1. 静态学术段落与映射对照表的注入
我们将在 `src/multi_era_analyzer.py` 的报告渲染模板中直接加入“引言与方法论”章节，将原文档中的文本与映射表格硬编码编排入生成字串中。
* **理由**：同人展大盘映射字段（例如 `themeAlias` 与 `genre`，`hotCount` 等）和学术理由在项目生命周期中属于长期静态常量。将其合入动态报告中可以减少外部文件依赖，生成自包含的完整 PDF/Markdown 学术成果。
* **备选方案**：运行时从外部 `comiket_vs_comicup.md` 读取并用 Regex 提取再合并。这会显著增加读取异常的概率，且一旦外部文件损坏会导致生成程序崩溃。

### 2. 安全的文件清理逻辑
在 `generate_multi_era_report` 生成并保存完多期学术报告后，调用一个安全清理辅助逻辑：
```python
for filepath in ["research/comiket_vs_comicup.md", "research/comiket_vs_comicup_comparison.md"]:
    if os.path.exists(filepath):
        try:
            os.remove(filepath)
            print(f"Removed redundant document: {filepath}")
        except Exception as e:
            print(f"Warning: Failed to remove {filepath}: {e}")
```
* **理由**：直接在生成引擎内部进行自动清理，可以使 CLI 执行 `--analyze-multi-era` 或任何调用报告渲染的操作均触发目录精简，符合规范的单一事实来源（SSOT）设计。
* **备选方案**：在 `main.py` 的 CLI 流程里删除。这会导致测试套件中（测试通常直接调用 `generate_multi_era_report` 绕过 `main.py`）无法覆盖删除逻辑。

### 3. 测试覆盖
在 `tests/test_multi_era.py` 中，编写对删除机制的验证：在临时测试目录中 Mock 出要删除的冗余文件，调用 `generate_multi_era_report` 后，断言这两个 Mock 文件已不存在。

## Risks / Trade-offs

### 1. 本地代码和文件的删除风险
* **Risk**：物理删除文件不可逆，一旦用户在 `comiket_vs_comicup.md` 中保存了其他个人草稿，会被直接清理。
* **Mitigation**：由于这两个文件的所有核心内容已经完整合并到了最终报告模板和 Git 历史中，且删除前会确认最终报告已成功写入磁盘，该风险处于可控范围。
