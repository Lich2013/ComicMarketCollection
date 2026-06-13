## 1. 配置项更新与加载逻辑

- [x] 1.1 在 `config.yaml` 中新增 `tweet_analysis` 模板配置项（支持设置 `enabled`、`api_key`、`base_url`、`model`）
- [x] 1.2 在 `src/config.py` 中适配配置，并在加载时实现 `tweet_analysis` 的智能回退策略（缺省时自动复用主 `openai` 参数）



## 2. 文本分析大模型接口实现

- [x] 2.1 在 `src/twitter_sync.py` 中编写 `analyze_tweet_text_with_llm(text, circle, analysis_config)` 函数，利用标准 OpenAI 客户端调用指定的大模型
- [x] 2.2 实现对 LLM 返回 of JSON 的解析清洗逻辑（剥离 Markdown 块标签），并编写 `try-except` 异常保护（默认返回 `True` 以保护数据不遗失）


## 3. 推文抓取同步流程集成

- [x] 3.1 修改 `src/twitter_sync.py` 中的 `sync_circle_twitter` 流程，在爬虫抓取完推文列表后，若启用了 `tweet_analysis`，则遍历并调用大模型进行过滤，只保留通过判定的品书推文
- [x] 3.2 验证手动指定单推导入命令 `sync_single_tweet` 中是否不受此 LLM 文本过滤的影响，确保正常导入


## 4. 测试与验证

- [x] 4.1 运行单元测试 `PYTHONPATH=. uv run pytest`，确保原有同步功能完全正常

- [x] 4.2 手动执行抓取命令，对带有明显干扰关键词的日常推文与真实的品书推文进行抓取测试，验证 LLM 预过滤输出的准确性与落库结果

