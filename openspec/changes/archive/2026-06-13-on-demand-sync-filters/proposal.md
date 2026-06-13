## Why

目前同步 X (Twitter) 推文与多模态 GPT 提取制品信息是针对所有活跃社团和待处理品书进行的。在社团基数庞大时，全量抓取和解析会带来极高的网络请求数和 LLM API 账单开销，同时也使得调试和个别社团信息的按需更新变得非常困难。因此，系统需要引入更细粒度的同步与提取过滤逻辑，允许用户在同步推文和提取制品时，指定特定的社团（通过 ID、名称、场馆或参展天数进行筛选）。

## What Changes

- 在 `main.py` 的 CLI 参数中，为 `--fetch-tweets` 和 `--extract-goods` 命令添加可选的过滤筛选参数（如 `--circle-ids`、`--circle-name`、`--days` 和 `--halls`）。
- 在 `src/db.py` 中新增多维度社团筛选逻辑函数，支持按上述参数筛选社团。
- 修改 `src/twitter_sync.py` 的 `sync_all_circles_twitter` 流程，仅抓取符合筛选条件的社团推文。
- 修改 `src/goods_extractor.py` 的 `process_pending_catalogs` 流程，仅解析符合筛选条件的社团推文品书图片。

## Capabilities

### New Capabilities

<!-- 无新增 Capability -->

### Modified Capabilities

- `catalog-sync`: 调整 X 推文同步流程以支持按指定 ID、社团名称、日期及展馆进行按需过滤同步。
- `goods-extractor`: 调整 LLM 制品提取流程以支持按指定 ID、社团名称、日期及展馆过滤待处理品书进行按需提取。

## Impact

- 涉及 `main.py` CLI 接口的参数共享与分发。
- 修改 `src/db.py` 数据库查询逻辑，提供条件组合查询。
- 调整 `src/twitter_sync.py` 和 `src/goods_extractor.py` 的遍历筛选流程。
