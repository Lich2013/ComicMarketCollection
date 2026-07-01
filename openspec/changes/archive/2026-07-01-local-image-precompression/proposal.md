## Why

在当前的图像识别系统中，尤其是使用本地命令行识别（`provider: "cmd"`，如自定义的 `agy` 引擎）时，系统直接将本地的原始高清大图（通常由 Twitter 抓取，体积在 1MB 至 4.5MB 以上，分辨率通常超过 3000px）路径传递给命令行。由于本地视觉大模型（VLM）在读取、加载和处理这种超大高分辨率图像时，存在显著的性能开销，容易导致 GPU 显存溢出（OOM）或极长的时间延迟。而在 API 模式下，直接传递超大原图也伴随着较高的 Token 消费与网络传输时间。

为了降低本地识别时的硬件开销、加速推理速度并防止因图片过大引发的程序中断，我们需要在调用识别后端前引入可选的本地图片预压缩与尺寸缩放机制，在保证 OCR 文字可读性的前提下显著降低图片体积。

## What Changes

- **配置扩展**：在 `config.yaml` 的 `image_recognition.cmd` 下，增加可选的预压缩相关配置项：`compress`（是否启用压缩，布尔值）、`max_size`（限制最大边长，整数像素）和 `quality`（JPEG 质量百分比，整数）。
- **预处理流程集成**：在 `goods_extractor.py` 的命令行识别（`extract_goods_via_cmd`）流程前，检查如果启用了 `compress` 选项，则在本地动态生成一个降采样和 JPEG 降质压缩后的临时图片，将命令行参数占位符 `{image_path}` 和 `{abs_image_path}` 替换为此临时图片路径。
- **临时生命周期管理**：在命令行任务执行完成后（无论成功或失败），系统必须确保自动清理并删除生成的临时图片文件。
- **原有归档不改变**：保存在 `data/images/` 中的原始品书大图文件保持原封不动，不受预压缩临时机制的影响，以备后续其他高清查看需求。

## Capabilities

### New Capabilities
<!-- 无新增的 spec 级别独立功能，仅修改现有提取器的行为 -->

### Modified Capabilities
- `goods-extractor`: 增强可插拔图像识别配置与运行场景，在运行自定义命令行识别前，支持可选的本地图片预压缩处理，自动使用临时压缩图进行识别并保障临时文件的生命周期。

## Impact

- **`config.yaml` & `src/config.py`**：新增 `image_recognition.cmd.compress`、`image_recognition.cmd.max_size`、`image_recognition.cmd.quality` 等配置的加载 and 默认值定义（默认 `compress = false` 保持向后兼容）。
- **`src/goods_extractor.py`**：在 `extract_goods_via_cmd` 方法中增加基于 `PIL` 的图片缩放压缩与临时文件管理逻辑。
- **网络与文件系统**：会在 `data/images/` 目录下（例如 `data/images/tmp/`）动态读写临时 JPEG 文件。
