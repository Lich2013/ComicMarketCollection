## Why

当前系统在同步社团 X (Twitter) 推文时，只支持配置推文抓取的起始日期 `since_date`，不支持截止时间限制。为了支持更加灵活的参展信息归档与数据采集（例如：限制推文同步最多到某个特定的展会准备节点，如 "2026.06.05 0点"），需要支持推文同步的截止时间上限过滤，并将其做成可配置的。

## What Changes

- 在配置文件 `config.yaml` 与 `config.yaml.example` 的 `twitter` 段落中引入可选的 `until_date` 配置项，允许用户指定一个截止日期时间。
- 在 `src/config.py` 中增加对 `until_date`（及环境变量 `TWITTER_UNTIL_DATE`）的解析与回退机制，当未配置时支持默认回退到 `"2026-06-05"` 0点。
- 修改 `src/twitter_sync.py`，使推文抓取过滤（包括 API 拦截与 DOM 备份解析分支）支持 `until_threshold` 校验，丢弃发布时间晚于该阈值的推文。

## Capabilities

### New Capabilities

无

### Modified Capabilities

- `catalog-sync`: 在推文的时间校验规则中，不仅要校验发布日期在 `since_date` 之后，还要过滤掉发布日期在 `until_date` 之后的推文。

## Impact

- 涉及配置文件：`config.yaml` / `config.yaml.example` 增加 `until_date` 配置。
- 涉及配置解析模块：`src/config.py` 会新增字段读取和环境变量映射。
- 涉及同步模块：`src/twitter_sync.py` 中的 `scrape_twitter_profile` 和 `sync_circle_twitter` 方法在过滤和时间边界比较时会使用该阈值。
