# genre-distribution-analysis Specification

## Purpose
TBD - created by archiving change research-genre-distribution. Update Purpose after archive.
## Requirements
### Requirement: 题材分布与大盘偏离度统计
系统 MUST 支持从 `circles` 表中统计各个题材（`genre`）的整体比例、周六/周日的排程分布、东馆/西馆/南馆的空间分布，并结合预配置的大众受众热度基线，计算每个题材的“同人偏离度指数 (DBI)”。

#### Scenario: 成功执行题材分析并导出
- **WHEN** 用户通过命令行运行分析指令，指定了输出 JSON 路径，且数据库连接正常
- **THEN** 系统对社团元数据进行聚合计算，成功推导出全局大盘题材排行、时间/空间分布矩阵以及各题材的 DBI 指数，并将格式化后的 JSON 报告写入目标路径

#### Scenario: 目标保存路径无效
- **WHEN** 用户指定的输出路径所在目录不存在且系统无法自动创建，或没有写权限
- **THEN** 系统抛出 IOException 或友好错误提示，并以非零错误码退出程序，不损坏现有数据库

