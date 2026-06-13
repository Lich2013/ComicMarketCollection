## Context

目前，CM (Comic Market) 的参展信息分布在 `circle.ms` WebCatalog 平台，而具体的同人制品图（品书）多发布于创作者的 X (Twitter) 个人主页上。这些数据难以统一检索和整理。本项目提供一套基于 Python 的本地化命令行工具，利用 SQLite 存储，结合 Playwright 模拟浏览器抓取 X.com 推文图片，并通过多模态大语言模型（LLM）结构化提取同人制品信息。

## Goals / Non-Goals

**Goals:**
- 提供从 `circle.ms` 获取社团与展位映射关系并保存至 SQLite 的功能（复用/参考 `c107` 实现）。
- 提供基于 Playwright (支持 Cookie 注入) 抓取指定社团 X 推文及下载品书图片到本地的功能。
- 提供使用多模态 LLM 进行品书制品（名称、价格、类型）结构化提取，并保存回数据库的功能。
- 提供命令行接口，可灵活、按需运行同步与解析任务。

**Non-Goals:**
- 不提供复杂的 Web 页面展示（目前仅为命令行工具 + 本地 SQLite 数据库）。
- 不支持自动登录 X.com 以防账号被封风控。用户需要手动提供 Cookie 信息。
- 优先支持 X (Twitter) 品书抓取，Pixiv 等其他平台的品书抓取暂不在本次范围。

## Decisions

### 1. 数据库选型：SQLite
- **Rationale**: 整个系统是个人运行的本地工具，数据量属于千级到万级规模，SQLite 零配置、单文件，且读写极快，符合按需更新和本地检索的定位。

### 2. X.com 推文抓取：Playwright 注入已登录 Cookie
- **Rationale**: 官方 API 价格过高且权限有限，未登录状态下 X.com 拒绝大部分访问。使用 Playwright 配合用户导出的 X.com Cookie 是目前最稳妥、开发成本最低的爬虫方案。
- **Alternatives Considered**: 
  - Nitter 等第三方反向代理：极不稳定，随时可能失效。
  - 手动保存图片导入：作为降级备用方案（支持通过 CLI 手动导入图片解析）。

### 3. 品书提取：多模态 LLM + Structured Outputs (JSON Schema)
- **Rationale**: 品书排版复杂，传统的 OCR 结合规则提取难以应对花哨的排版和多变的价格表达。通过多模态 LLM（如 Gemini/GPT-4o-mini）以 JSON Schema 约束形式返回制品列表，能保证极高的开发效率与准确率。

---

## Risks / Trade-offs

- **[Risk] X.com 频繁抓取导致 Cookie 失效或账号被限**
  - **Mitigation**: 爬取时增加随机延迟（如 2-5 秒）；支持局部或单社团同步；允许用户手动下载品书图片并使用命令行直接触发 LLM 识别，绕过爬虫。
- **[Risk] LLM 提取价格或名称不准确**
  - **Mitigation**: 在商品表中保留 LLM 的原始 `raw_json` 供排查。精心设计 System Prompt，提供 JPY 金额提取范例。
- **[Risk] WebCatalog 凭证过期**
  - **Mitigation**: 配置文件中包含 `HEADERS`（主要是 Cookie 字段），由用户在浏览器中获取并填入配置文件中。
