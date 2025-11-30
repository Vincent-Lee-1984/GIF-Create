# GIF-Create 项目说明

- 使用 `matplotlib` 3D 与 `imageio` 生成演示 GIF，展示从“设定目标”到“识别分割”再到“生成 3D 模型”的三阶段动画流程。
- 运行后在当前目录生成 `sam3d_fixed_compressed.gif`，尺寸约 300×300 像素、透明背景、LZW 压缩、15 FPS。

**项目亮点**
- 自动中文字体配置，跨平台兼容（Windows/macOS/Linux）。
- 三种几何体：立方体、金字塔、六边棱柱；相机视角与旋转平滑过渡。
- 叠加 UI 文本与描边效果，保证小尺寸下可读性。
- 无界面渲染，通过内存缓冲捕获帧，避免“残影”。

**环境依赖**
- Python 3.8 及以上版本（建议 3.10+）。
- 依赖包来源于 `requirements.txt`：
  - `numpy`
  - `matplotlib`
  - `imageio`
  - `pillow`

**在 macOS 安装**
- 推荐使用虚拟环境：
  - `python3 -m venv .venv`
  - `source .venv/bin/activate`
- 安装依赖：
  - `pip install -r requirements.txt`

**运行**
- 执行：
  - `python main.py`
- 输出：当前目录生成 `sam3d_fixed_compressed.gif`。

**文件结构**
- `main.py`：主程序，负责构建 3D 场景、时间线与 GIF 导出。
- `requirements.txt`：依赖列表。

**核心流程概述**
- 字体配置（自动选择平台字体，确保中文显示）：
  - macOS 优先 `Arial Unicode MS`、`PingFang SC`、`Heiti TC`。
- 场景几何：
  - 立方体、金字塔、六边棱柱的顶点与面片构造。
- 动画阶段：
  - 阶段 1（0–35%）：展示“建模目标”输入，三几何体均为初始配色。
  - 阶段 2（35–55%）：突出立方体，其余几何体淡出。
  - 阶段 3（55–100%）：立方体保持高亮并做 360° 旋转。
- UI 叠加：
  - 标题、提示文本、光标闪烁；描边提升对比度。
- 渲染与导出：
  - 画布 `3x3` 英寸、`100 dpi`，总帧数 `60`（约 4 秒 @ 15 FPS），透明背景；`imageio.mimsave` 导出 GIF。

**参数与自定义**
- 目标字符串：修改 `TARGET_STR` 可替换演示目标文本。
- 画布尺寸与 DPI：调整 `plt.figure(figsize=(w, h), dpi=...)` 控制输出分辨率。
- 帧数与时长：
  - `TOTAL_FRAMES` 控制总帧数；`duration=4.0 / TOTAL_FRAMES` 控制每帧时长（总时长约 4 秒）。
- 颜色与线宽：
  - 初始与高亮配色、描边颜色、`linewidths` 可根据品牌风格调整。
- 几何体参数：
  - 修改 `get_cube`、`get_pyramid`、`get_prism` 的中心与尺寸实现不同场景布局。

**常见问题与解决**
- 中文字体缺失：
  - 若 macOS 无法显示中文，可安装 `PingFang SC` 或手动设置 `plt.rcParams['font.sans-serif']`。
- Matplotlib 后端问题：
  - 本项目不依赖交互式后端；若遇到 GUI 警告，可忽略或使用非交互式环境运行。
- GIF 文件过大：
  - 降低 `dpi` 或减少帧数；或增大 `optimize=True` 的压缩效果。

**扩展建议**
- 导出 MP4：使用 `imageio.v3` 或 `matplotlib.animation` 导出 `mp4`，适合社交平台分享。
- 场景主题：可将 `ACTIVE_COLOR` 替换为品牌主色，并调整 UI 文本与布局。

**许可证**
- 未明确指定许可证；如需开源分发，建议补充许可证文件（如 MIT 或 Apache-2.0）。

