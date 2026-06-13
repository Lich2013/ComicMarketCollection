# goods-extractor Specification

## Purpose
TBD - created by archiving change collect-comic-market-data. Update Purpose after archive.
## Requirements
### Requirement: LLM 多模态品书提取与分类
系统 MUST 支持将本地品书图片送入多模态 LLM 进行识别，结构化地提取出同人制品的名称、类型、价格和是否为套装（Set），并存入数据库。

#### Scenario: 成功解析品书并入库
- **WHEN** 对处于 `pending` 状态的品书图片调用 LLM API 进行解析，且 LLM 成功返回合法的制品列表 JSON
- **THEN** 系统在 `goods` 表中为该社团插入提取出的商品信息，并将对应的品书记录 `status` 更新为 `processed`

#### Scenario: 忽略非品书图片
- **WHEN** LLM 判定该图片不属于品书或不包含任何同人制品及价格信息
- **THEN** 系统不插入任何商品数据，并将对应的品书记录 `status` 更新为 `ignored`

### Requirement: 按需更新命令行工具
系统 MUST 提供统一的命令行工具（CLI），允许用户通过不同参数分别执行同步社团、抓取品书图片和提取制品数据等操作。同时，同步推文与提取制品指令 MUST 支持根据用户提供的条件（社团 ID、名称、参展日期及展馆）仅对指定的社团数据进行按需处理。

#### Scenario: 执行同步社团指令
- **WHEN** 用户运行命令并指定同步社团参数（如 `--sync-circles`）
- **THEN** 系统开始拉取并同步 WebCatalog 社团信息

#### Scenario: 执行提取制品指令
- **WHEN** 用户运行命令并指定提取制品参数（如 `--extract-goods`）
- **THEN** 系统扫描数据库中所有 `pending` 状态的品书并调用 LLM 进行解析

