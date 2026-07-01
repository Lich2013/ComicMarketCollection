## 1. 配置加载扩展

- [x] 1.1 修改 `src/config.py`，在 `image_recognition.cmd` 配置节点下，增加 `compress`、`max_size`、`quality` 属性的解析，并设置后备默认值（`compress = False`, `max_size = 1500`, `quality = 85`）。
- [x] 1.2 更新 `config.yaml.example`，提供新增预压缩配置的示例文档 and 注释说明。
- [x] 1.3 在 `tests/test_goods_extractor.py` 中，增加对新增配置读取与默认值回退逻辑的单元测试。

## 2. 预压缩核心流程与文件生命周期实现

- [x] 2.1 修改 `src/goods_extractor.py` 中的 `extract_goods_via_cmd`，增加配置判断。若 `compress` 为 `true`，使用 Pillow 的 `LANCZOS` 采样对原始图片进行缩放（最大边不超过 `max_size`），并以指定的 `quality` 质量压缩保存为临时 JPEG 图片。
- [x] 2.2 在生成临时图片时，使用时间戳或唯一标识符（如 `tmp_{timestamp}_{filename}.jpg`）命名，保存在 `data/images/tmp/` 目录中，确保多任务并行时文件名无冲突。
- [x] 2.3 在运行外部命令参数替换时，如果启用了压缩，使用生成的临时图片路径替换占位符 `{image_path}` 和 `{abs_image_path}`。
- [x] 2.4 实现图片压缩后的体积对比判定逻辑。若生成的临时图片体积大于或等于原图的 90%，则主动清理该临时文件，并将运行路径切回原图路径，触发回退保护。
- [x] 2.5 在 `extract_goods_via_cmd` 的整个执行逻辑外包裹 `try...finally` 块。在 `finally` 块中通过安全判断（检测文件存在并捕获异常）将生成的临时图片文件彻底清理，确保不遗留任何垃圾临时文件。


## 3. 功能验证与测试

- [x] 3.1 在 `tests/test_goods_extractor.py` 中编写集成测试，模拟开启 `compress` 配置时的 `cmd` 图像识别流程，验证临时文件生成、外部命令路径替换，以及执行完毕后临时文件被成功自动删除。
- [x] 3.2 手动开启 `config.yaml` 中的 `compress` 配置，执行一次本地 `uv run main.py --extract-goods` 命令，观察命令行输出，并验证 `data/images/tmp/` 目录下临时文件在运行前后的创建与销毁。
