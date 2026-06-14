## Context

目前，系统通过 `since_date` 设定了推文同步的起始时间边界。但是，系统并不支持设置推文同步的截止时间边界（上限）。在实际参展信息归纳和采集过程中，用户可能需要对推文在某个具体时间节点之后的内容进行屏蔽/过滤（例如只同步截止至展前准备的 "2026.06.05 0点"）。

## Goals / Non-Goals

**Goals:**
- 在配置文件中引入 `until_date` 选项，支持灵活配置推文的截止时间边界。
- 修改推文爬取与过滤模块，丢弃发布时间晚于 `until_date` 的推文（支持 API 拦截及 DOM 备份解析分支）。
- 维持系统的高可靠性，增加对输入日期的健壮解析与 Fallback 策略。

**Non-Goals:**
- 手动导入的单条推文链接（通过 `--tweet-url`）不需要受该时间范围过滤机制约束。

## Decisions

### 1. 配置项设计
在 `config.yaml` / `config.yaml.example` 的 `twitter` 节点下新增可选配置项 `until_date`：
- 配置默认值为 `"2026-06-05"`。
- 在 `src/config.py` 中解析它，支持读取环境变量 `TWITTER_UNTIL_DATE`。
- 如果用户未配置或置空，系统在代码中将默认 fallback 到 `"2026-06-05"`（以完美契合“最多到 2026.06.05 0点”的要求）。

### 2. 带时区的日期比对与解析
X.com 返回的推文时间 `created_at` 是带有时区信息的（例如带有 `+0000`）。为了确保比对时不会因为“带时区”与“无时区”的对象直接比对而抛出 `TypeError`，需要确保构建的时间阈值 `until_threshold` 也是 timezone-aware 的。
- 解析逻辑为：
  ```python
  if "T" in until_date:
      until_threshold = datetime.fromisoformat(until_date)
  else:
      until_threshold = datetime.fromisoformat(f"{until_date}T00:00:00+00:00")
  ```
- 这样解析出来的对象自带 `+00:00` 时区，能直接与经过 `datetime.strptime(created_at, "%a %b %d %H:%M:%S %z %Y")` 得到的 `tweet_date` 进行大小比较。

### 3. 推文遍历时的过滤策略
由于 Twitter 个人主页推文是由新到旧（降序）排列：
- 看到发布时间晚于 `until_threshold` 的推文时：应当执行 `continue` 跳过，因为需要继续向下检索，直到发现更旧的、落入目标区间范围的推文。
- 看到发布时间早于 `date_threshold` (`since_date`) 的推文时：应当执行 `break` 提前终止，因为接下来的推文只会更旧，无需继续做无用功。

## Risks / Trade-offs

- **[Risk]** 用户配置了格式非法的日期字符串（例如 `"2026/06/05"` 或非日期文本）。
  - **[Mitigation]** 在 `src/twitter_sync.py` 的日期解析处采用 `try...except` 包裹，一旦捕获异常，立刻自动 fallback 到默认截止时间 `"2026-06-05T00:00:00+00:00"`，避免程序崩溃。
- **[Risk]** 置顶推文的时间较旧但可能仍需保留。
  - **[Mitigation]** 在过滤时，明确区分普通推文和置顶推文的时限控制。对于置顶推文，即使其时间早于 `since_date`，根据系统已有策略可能可以保留，但如果置顶推文的时间晚于 `until_threshold`（比如是展会很久之后又发的无关内容），则仍然过滤掉。
