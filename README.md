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
- `OPENAI_API_KEY`: OpenAI API Key。
- `OPENAI_BASE_URL`: OpenAI 接口的基础 URL。
- `OPENAI_MODEL`: OpenAI 使用的多模态模型（默认：`gpt-4o-mini`）。

---

## 🛠️ 命令行参数说明 (CLI)

可以使用 `uv run main.py -h` 查看完整命令行帮助。

### 1. 同步社团与展位信息
从 WebCatalog 爬取展位及社团详情，并写入本地 SQLite：
```bash
# 同步全部场馆与参展天（较慢，默认启用断点续传跳过已同步社团）
uv run main.py --sync-circles

# 限制特定日期和场馆（推荐，如同步 Day2 的东7厅）
uv run main.py --sync-circles --days Day2 --halls e7

# 强制重新抓取并更新已存在的社团详情（覆盖已有数据）
uv run main.py --sync-circles --days Day2 --halls e7 --force
```
> **提示**：为避免被 WebCatalog 封禁，此过程在单次循环请求中默认设置了 `0.5秒` 的安全延迟（Sleep）。默认只做增量/断点续传抓取，只有传入 `--force` 时才会强制发送请求覆盖更新已有社团。


### 2. 同步 X (Twitter) 推文及品书图
本项目采用 Playwright 拦截 X.com 的 GraphQL API 接口，内置敏感内容警告自动点击绕过、置顶推文（`TimelinePinEntry`）解析、以及自转发推文媒体与正文提取逻辑（自转自动寻找原推 `retweeted_status_result`）。同时内置 500 条解析安全上限以防止内存或性能过载。

支持两种同步方式：
- **方式一：批量增量同步**
  为当前数据库中保存了 X (Twitter) 用户名的社团抓取最新推文，提取符合条件的品书图片至本地 `data/images/{circle_id}/`，初始状态为 `pending`：
  ```bash
  uv run main.py --fetch-tweets
  ```
- **方式二：指定单条博文链接同步**
  手动指定一条 X 博文链接。系统会自动提取链接中的用户名并与数据库中的社团进行智能匹配关联（或通过 `--circle-ids` 强制关联指定社团），抓取并提取该博文中的品书图片：
  ```bash
  # 自动匹配社团并导入
  uv run main.py --tweet-url https://x.com/nekomata/status/2062809125718016071
  
  # 手动强制关联指定的社团 ID
  uv run main.py --tweet-url https://x.com/nekomata/status/2062809125718016071 --circle-ids 23003977
  ```

### 3. 多模态 GPT 提取制品信息
扫描 `pending` 状态下的推文品书图片，发送给 GPT 进行 OCR 及结构化识别，解析出同人制品名称、类型、价格并存入 `goods` 数据表，然后将该品书状态更新为 `processed`：
```bash
uv run main.py --extract-goods
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
