# Comic Market Collection System

本项目是一套简易、按需运行的 Comic Market (CM) 同人参展信息、推文品书（Catalog）以及制品提取的本地数据同步工具。

## ⚙️ 技术栈

- **Python 3.11+**
- **uv** (项目与依赖依赖管理)
- **Playwright** (自动化模拟抓取 X.com 推文及图片)
- **SQLite** (本地轻量级数据库存储)
- **OpenAI SDK** (集成 GPT-4o-mini 多模态多模功能进行品书提取)

---

## 📂 项目结构

```text
├── config.yaml             # 本地配置文件（管理 Cookie 和 API 金钥，首次运行可生成）
├── main.py                 # 命令行接口入口
├── pyproject.toml          # 项目信息与依赖项
├── src/
│   ├── config.py           # 配置文件解析模块
│   ├── db.py               # SQLite 数据库连接及 CRUD 辅助函数
│   ├── circle_sync.py      # WebCatalog 展位及社团数据同步器
│   ├── twitter_sync.py     # Playwright 推文及品书图片抓取器
│   └── goods_extractor.py  # GPT 多模态品书同人制品结构化提取器
└── tests/
    └── test_db.py          # 数据库逻辑单元测试
```

---

## 🚀 快速开始与安装

### 1. 安装依赖并初始化浏览器环境

确保您的系统已安装 `uv`，然后在项目根目录下运行：

```bash
# 同步安装所有 Python 依赖
uv sync

# 安装 Playwright 的 Chromium 浏览器内核
uv run playwright install chromium
```

### 2. 生成并修改本地配置文件

运行以下命令，在项目根目录生成 `config.yaml` 模板文件：

```bash
uv run main.py --write-config
```

用编辑器打开 `config.yaml` 并填写相应的凭证：
1. **`openai.api_key`**: 填入您的 OpenAI API 金钥。
2. **`webcatalog.cookie`**: 登录 [Comike Web Catalog](https://webcatalog.circle.ms/)，并在浏览器开发者工具中获取当前的 Cookie 字符串填入。
3. **`twitter.cookie_string`** 或 **`twitter.cookies_file`**:
   本项目支持**两种方式**来配置 X.com 的 Cookie 以模拟登录：
   - **方式一（极简，推荐）**：直接在 `config.yaml` 中将浏览器开发者工具（如 Network 面板请求头）中复制的原始 Cookie 字符串（形如 `auth_token=xxx; ct0=yyy;`）黏贴到 `twitter.cookie_string` 中即可。
   - **方式二（JSON 格式文件）**：保持 `cookie_string` 为空，使用 Cookie 导出插件（如 EditThisCookie）将 Cookie 导出为 JSON 格式并存放到 `twitter.cookies_file` 指定的路径（默认 `data/twitter_cookies.json`）下。
   - **方式三（文件内放置普通文本）**：直接将原始的普通 Cookie 字符串写入 `cookies_file` 对应的文件中，程序也会自动检测其非 JSON 格式并进行智能解析加载。

### 3. 使用环境变量进行配置 (可选)

除了使用 `config.yaml` 配置文件之外，本项目的所有配置项均支持通过环境变量直接注入（环境变量优先级最高）：
- `WEBCATALOG_COOKIE`: WebCatalog 的 Cookie 字符串。
- `WEBCATALOG_USER_AGENT`: WebCatalog 访问时使用的 User-Agent。
- `TWITTER_COOKIE_STRING`: X.com 的普通 Cookie 字符串（形如 `auth_token=xxx; ct0=yyy;`）。
- `TWITTER_COOKIES_FILE`: X.com Cookie 的 JSON/文本 文件路径。
- `TWITTER_SINCE_DATE`: X.com 推文同步起始日期限制 (格式: YYYY-MM-DD)。
- `TWITTER_UNTIL_DATE`: X.com 推文同步截止日期限制 (格式: YYYY-MM-DD)。
- `OPENAI_API_KEY`: OpenAI API Key。
- `OPENAI_BASE_URL`: OpenAI 接口的基础 URL。
- `OPENAI_MODEL`: OpenAI 使用的多模态模型（默认：`gpt-4o-mini`）。

---

## 🛠️ 命令行参数说明 (CLI)

可以使用 `uv run main.py -h` 查看完整命令行帮助。

### 1. 基础配置与数据库初始化

* **生成默认配置文件模板**：
  ```bash
  uv run main.py --write-config
  ```
* **手动初始化/创建本地数据库表结构**（支持自定义数据库路径）：
  ```bash
  # 默认在 data/comic_market.db 初始化
  uv run main.py --init-db

  # 指定自定义路径初始化
  uv run main.py --init-db --db-path my_data/custom.db
  ```

---

### 2. 通用筛选与辅助参数

在同步社团、抓取推文或提取制品时，您可以附加以下参数来进行**按需过滤**，以显著减少网络开销与 API 请求费用（均支持与自定义 `--db-path` 搭配使用）：

| 参数名          | 类型   | 说明                                               | 示例                                |
| :-------------- | :----- | :------------------------------------------------- | :---------------------------------- |
| `--days`        | `str`  | 限制参展日期（用逗号隔开）                         | `--days Day1` 或 `--days Day1,Day2` |
| `--halls`       | `str`  | 限制参展场馆（用逗号隔开，不区分大小写）           | `--halls e7` 或 `--halls e7,s12`    |
| `--circle-ids`  | `str`  | 限制社团唯一 ID（用逗号隔开）                      | `--circle-ids 23003977`             |
| `--circle-name` | `str`  | 限制社团名或作者名，进行模糊匹配                   | `--circle-name ねこ`                |
| `--db-path`     | `str`  | 指定 SQLite 数据库文件路径                         | `--db-path data/custom.db`          |
| `--force`       | `bool` | 强制重新同步（即便本地数据库已存在该记录也不跳过） | `--force`                           |

---

### 3. 同步社团与展位信息 (`--sync-circles`)
从 WebCatalog 爬取展位及社团详情，并写入本地 SQLite。默认只做增量/断点续传同步，若本地已同步过该社团则会自动跳过：
```bash
# 同步全部场馆与参展天（由于包含网络延迟防止封禁，较慢）
uv run main.py --sync-circles

# 按需同步：仅同步 Day2 的东7厅 (e7) 展位
uv run main.py --sync-circles --days Day2 --halls e7

# 强制同步：覆盖本地数据库已有的社团详情数据
uv run main.py --sync-circles --days Day2 --halls e7 --force
```
> **提示**：为避免被 WebCatalog 封禁，此过程在单次循环请求中默认设置了 `0.5秒` 的安全延迟（Sleep）。

---

### 4. 同步 X (Twitter) 推文及品书图 (`--fetch-tweets` 或 `--tweet-url`)
本项目采用 Playwright 模拟用户登录，拦截 X.com 的 GraphQL API 接口以结构化抓取博文。
功能内置：敏感内容警告自动点击绕过、置顶推文（`TimelinePinEntry`）解析、自转发推文媒体与正文提取逻辑（自转自动寻找原推 `retweeted_status_result`）以及 500 条解析安全上限以防止内存或性能过载。

* **方式一：批量过滤与按需增量同步** (`--fetch-tweets`)
  为数据库中符合筛选条件的社团抓取最新推文，将符合品书关键字/展位号规则的图片下载至本地 `data/images/{circle_id}/`，并在数据库中写入记录，初始状态计为 `pending`：
  
  ```bash
  # 全量同步所有配置了 Twitter 链接的社团
  uv run main.py --fetch-tweets

  # 按需同步：仅同步 Day1 且在 e7 场馆的社团推文
  uv run main.py --fetch-tweets --days Day1 --halls e7

  # 定向同步：仅同步社团 ID 为 23003977 的推文
  uv run main.py --fetch-tweets --circle-ids 23003977

  # 定向模糊匹配：仅同步社团名/作者名包含“ねこ”的推文
  uv run main.py --fetch-tweets --circle-name ねこ
  ```
  
  > **注意（时间窗口限制）**：批量同步默认仅抓取处于 `since_date`（默认 `2026-06-01`）至 `until_date`（默认 `2026-06-05`）时间范围内的推文。这两个日期可在 `config.yaml` 文件的 `twitter.since_date` 和 `twitter.until_date` 中配置，或通过环境变量覆盖。如果在滚动或数据分析中遇到早于起始时间的非置顶推文，系统会自动提前中止滚动以提升抓取效率。

* **方式二：指定单条博文链接同步** (`--tweet-url`)
  手动输入指定的一条 X 博文链接进行单推同步。系统会自动从 URL 解析出作者用户名并在数据库中智能匹配关联对应的社团，将图片下载至本地并落库为 `pending` 状态：
  
  ```bash
  # 自动匹配数据库社团并导入
  uv run main.py --tweet-url https://x.com/nekomata/status/2062809125718016071

  # 手动强制关联指定的社团 ID（若该作者不在本地 circles 表中时非常有用）
  uv run main.py --tweet-url https://x.com/nekomata/status/2062809125718016071 --circle-ids 23003977
  ```

---

### 5. 品书制品信息结构化提取 (`--extract-goods`)
扫描数据库中处于 `pending` 状态下的推文品书图片，调用识别引擎进行多模态 OCR 及结构化识别，解析出同人制品名称、类型、价格并存入 `goods` 数据表，随后将该品书状态更新为 `processed`。

本项目支持**双识别引擎模式**，可在 `config.yaml` 的 `image_recognition.provider` 中自由切换：
- **`openai` 引擎**：直接调用 OpenAI/GPT-4o-mini 多模态 API 进行智能品书提取（需配置 `openai.api_key`）。
- **`cmd` 引擎**：调用本地自定义命令行图像识别工具（如特定的本地视觉 Agent 命令行， 如codex、agy等），支持自定义参数占位符（如 `{image_path}`, `{prompt}`）、超时控制以及当输出格式非标时调用文本大模型二次规整的容错机制（`fallback_text_formatter`）。

```bash
# 全量解析所有 pending 状态的品书图
uv run main.py --extract-goods

# 按需解析：仅解析 Day2 东7厅 (e7) 的待处理品书
uv run main.py --extract-goods --days Day2 --halls e7

# 定向解析：仅解析社团 ID 为 23003977 的待处理品书
uv run main.py --extract-goods --circle-ids 23003977
```

---

### 6. 导出同人商品数据至 CSV (`--export-goods`)
将本地 SQLite 数据库中提取并解析出的商品数据批量导出为符合 Excel 直接双击打开不乱码格式的 CSV 文件（采用带 BOM 的 UTF-8 编码）。

为了方便现场最顺路地逛展购买，导出的记录将自动按照物理路线最优化排序（`日期` -> `场馆` -> `区域` -> `摊位号` 升序）。

导出的 CSV 包含以下列：`日期`、`场馆`、`区域`、`摊位号`（合并展位信息）、`社团名`、`作者`、`类别` (genre)、`类型`、`商品`、`数量`（默认 `1`）、`价格`、`来源推文`、`社交媒体`。

```bash
# 全量导出所有解析到的商品信息
uv run main.py --export-goods data/shopping_list.csv

# 按需导出：仅导出 Day1 且在东123厅 (e123) 的商品，过滤生成的购买清单
uv run main.py --export-goods data/day1_east123_list.csv --days Day1 --halls e123
```

---

## 🗄️ 数据库设计说明

运行任何同步命令后，系统将自动创建并在本地生成轻量级 SQLite 数据库：`data/comic_market.db`。包含以下三张核心表：

1. **`circles` (社团展位表)**: 包含社团 ID、社团名、作者、类型介绍、展馆、参展天、排、摊位号、Twitter / Pixiv URL 等。
2. **`catalogs` (推文品书表)**: 包含推文 ID、内容、下载的本地图片相对路径以及状态字段 `status` (`pending`, `processed`, `ignored`, `failed`)。
3. **`goods` (同人制品商品表)**: 包含具体制品名称、类型（如：新刊、既刊、周边）、价格（日元）、是否为套装以及对应的社团外键关联。

---

## 🧪 单元测试

运行单元测试以验证本地 SQLite 交互、Twitter 账户提取等核心逻辑：

```bash
PYTHONPATH=. uv run pytest tests/
```
