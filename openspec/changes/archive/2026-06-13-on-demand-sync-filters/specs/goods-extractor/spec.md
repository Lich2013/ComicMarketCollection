## MODIFIED Requirements

### Requirement: 按需更新命令行工具
系统 MUST 提供统一的命令行工具（CLI），允许用户通过不同参数分别执行同步社团、抓取品书图片和提取制品数据等操作。同时，同步推文与提取制品指令 MUST 支持根据用户提供的条件（社团 ID、名称、参展日期及展馆）仅对指定的社团数据进行按需处理。

#### Scenario: 执行同步社团指令
- **WHEN** 用户运行命令并指定同步社团参数（如 `--sync-circles`）
- **THEN** 系统开始拉取并同步 WebCatalog 社团信息

#### Scenario: 执行提取制品指令
- **WHEN** 用户运行命令并指定提取制品参数（如 `--extract-goods`）
- **THEN** 系统扫描数据库中所有 `pending` 状态的品书并调用 LLM 进行解析
