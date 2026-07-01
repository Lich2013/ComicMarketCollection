## 1. 数据库扩容设计与建表逻辑实现

- [x] 1.1 在 `src/db.py` 中增加 `c107_circles`、`cpsp_products` 与 `cpsp_circles` 的建表语句，并加入 `init_db` 中
- [x] 1.2 执行本地数据库初始化校验，确保在指定新库路径时能自动创建正确字段的新表

## 2. C107 与 CPSP 导入引擎实现

- [x] 2.1 编写 `src/c107_importer.py`，实现 C107 单个详情 JSON 的读取、Twitter 提取、Cut 图提取与批量 `INSERT OR REPLACE` 逻辑
- [x] 2.2 编写 `src/cpsp_importer.py`，实现 CPSP 大 JSON 分包读取、题材 IP 标准化归一、内存去重及主外键批量导入逻辑

## 3. CLI 命令行参数扩充与业务绑定

- [x] 3.1 在 `main.py` 中扩充 `--import-c107 <dir>` 和 `--import-cpsp <dir>` 参数
- [x] 3.2 挂接并调用对应的导入引擎逻辑，确保从控制台命令可正确触发数据解析导入

## 4. 单元测试与大盘导入验证

- [x] 4.1 编写 `tests/test_c107.py` 与 `tests/test_cpsp.py` 单元测试，验证导入引擎在 Mock JSON 数据环境下的导入完整性与幂等性
- [x] 4.2 运行完整分析链条，物理导入 C107 和 CPSP 大盘真实数据包，并在控制台验证打印的导入总数是否与原始数据符合
- [x] 4.3 运行 `PYTHONPATH=. uv run pytest` 验证全部测试 100% 通过，无回归破坏
