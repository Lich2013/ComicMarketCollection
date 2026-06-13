## 1. 基础配置与数据库初始化

- [x] 1.1 配置 `pyproject.toml` 中的依赖，引入 playwright, requests, openai, pillow 等库。
- [x] 1.2 创建数据库模块 `src/db.py`，编写 SQLite 表结构初始化代码（包含 `circles`、`catalogs`、`goods` 三张表）。
- [x] 1.3 编写数据库常用 CRUD 辅助函数，确保支持按需更新（如 `INSERT OR REPLACE`）。

## 2. WebCatalog 同步模块实现

- [x] 2.1 编写 `src/circle_sync.py`，读取配置文件中的 auth Headers 抓取 map 信息（获取 table IDs）。
- [x] 2.2 编写 `src/circle_sync.py` 详情抓取函数，解析社团名、作者、展位位置和 Twitter / Pixiv 链接，并写入 `circles` 表。

## 3. X (Twitter) 推文与品书抓取模块实现

- [x] 3.1 编写 `src/twitter_sync.py`，配置 Playwright 使用配置的 Cookie 模拟登录并访问社团 Twitter 页面。
- [x] 3.2 实现提取推文正文与多媒体图片逻辑，过滤可能是品书的推文图片并下载到本地指定目录（如 `data/images`）。
- [x] 3.3 将下载的图片记录及推文信息写入 `catalogs` 表中，默认状态为 `pending`。

## 4. LLM 品书制品提取模块实现

- [x] 4.1 编写 `src/goods_extractor.py`，配置 OpenAI 客户端/Agents SDK 以支持多模态请求。
- [x] 4.2 编写品书图像提取提示词及 Structured Output JSON Schema 结构。
- [x] 4.3 实现扫描 `pending` 状态的品书记录，调用 LLM 进行制品名称、类型、价格提取并写入 `goods` 表，同时更新推文状态。

## 5. 命令行工具与入口整合

- [x] 5.1 整合 `main.py`，使用 `argparse` 设计统一命令行参数（如 `--sync-circles`, `--fetch-tweets`, `--extract-goods`）。
- [x] 5.2 编写示例配置文件（如 `config.yaml` 或 `.env.example`）用于存储 X.com 和 WebCatalog 的 Cookie/Credentials。

## 6. 测试与验证

- [x] 6.1 编写测试脚本验证 SQLite 读写及状态更新的正确性。
- [x] 6.2 进行端到端的模拟/手动测试，验证品书多模态识别与解析的准确性。
