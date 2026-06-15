## 1. 报告模板升级与数据清洗整合

- [x] 1.1 在 `src/multi_era_analyzer.py` 的 `generate_multi_era_report` 函数中合入静态科学论证背景段落（说明为什么选择 CP31 而非 CP32 作为对比基准）
- [x] 1.2 在 `generate_multi_era_report` 中合入数据集映射规格与对照表
- [x] 1.3 实现安全的文件清理逻辑，支持删除已完成归一化的 `research/comiket_vs_comicup.md` 和 `research/comiket_vs_comicup_comparison.md` 冗余文档

## 2. 单元测试与大盘功能验证

- [x] 2.1 修改 `tests/test_multi_era.py` 中 `test_report_generation` 单元测试，补充对科学论证背景、映射对照表内容以及冗余文件清理逻辑的断言校验
- [x] 2.2 运行整个单元测试套件，验证测试 100% 通过且无功能回归
- [x] 2.3 执行 CLI 命令 `PYTHONPATH=. uv run python main.py --analyze-multi-era`，验证生成的合并报告格式正确，且原冗余文件被正确删除
