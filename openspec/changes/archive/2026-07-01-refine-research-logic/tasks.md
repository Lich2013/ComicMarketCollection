## 1. 题材分类归一化与数据计算

- [x] 1.1 在 `src/multi_era_analyzer.py` 中实现超级题材映射字典（10 大 Super-Genres）与分类转换函数
- [x] 1.2 升级 `get_comiket_era_stats` 和 `get_comicup_era_stats`，计算对齐尺度下的 Super-CR5 / Super-CR10 集中度数据并返回
- [x] 1.3 升级 `generate_multi_era_report` 渲染模板，新增“3.1.1 题材分类粒度归一化对齐分析（超级题材）”小节，展现 Super-CR5 / Super-CR10 比较表格与学术结论
- [x] 1.4 在多展期对比研究报告模板中，补齐从 Comiket 描述文本中提取出的小说提及率实证数据（5.4%）作为跨国对比支撑

## 2. 复现脚本与方法论报告升级

- [x] 2.1 升级 `research/scripts/chi_square_test.py` 卡方检验脚本，引入内置 `math` 库，动态计算并打印 Cramér's V 效应量
- [x] 2.2 升级 `research/social_media_adoption.md` 社交平台采纳报告中的卡方检验章节，合入关于 Cramér's V 效应量强弱的统计学论述
- [x] 2.3 升级 `research/audience_baseline_methodology.md`，在方法论章节末尾增设大盘基线扰动敏感度分析表格，列明不同扰动等级（±10%, ±20%, ±30%）下的分类翻转率及对边界题材（VTuber 等）的稳定性警告

## 3. 学术措辞规范与因果解释去包装

- [x] 3.1 升级 `research/booth_density.md` 空间分析报告，增设 Moran's I 计算中邻接矩阵定义的学术自反性限制性说明（防范循环论证误解）
- [x] 3.2 升级 `research/comiket_vs_comicup_multi_era_study.md` 联合对比报告及各单篇研究报告，将“稳定性”用词降级为“初步一致性”；将排球少年的供求失衡修正为“生产时滞与供给响应时延假说”，并对齐剧场版上映热度暴涨背景
- [x] 3.3 升级 `research/genre_distribution.md` 题材分布报告，对赛马娘版权政策规制、碧蓝档案人设留白等因果逻辑推断增设“推测性解释”的显式免责标示
- [x] 3.4 升级 `research/comiket_vs_comicup_multi_era_study.md` 联合对比报告及相关文档（如 `research/README.md`），在方法论与局限性声明中明确补充中日两展“偏离度”指标在分子（社团 vs 制品）与分母（外部大盘 MAU 基线 vs 现场心愿单）统计口径上的本质差异及不可直接定量对比的局限性说明


## 4. 单元测试与大盘功能验证

- [x] 4.1 更新 `tests/test_multi_era.py` 单元测试，补充对 Super-Genres 集中度对比内容以及 Comiket 侧小说提及率渲染结果 of 断言校验
- [x] 4.2 运行整个单元测试套件 `PYTHONPATH=. uv run pytest`，确保 34 个测试 100% 成功通过
- [x] 4.3 运行 `PYTHONPATH=. uv run python main.py --analyze-multi-era` 重新渲染生成多期学术报告，验证格式排版完全正确
- [x] 4.4 运行 `uv run --with pandas --with scipy research/scripts/chi_square_test.py` 验证卡方检验及效应量输出正确
