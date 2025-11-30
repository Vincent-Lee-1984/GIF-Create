# GIF-Create 项目总览（Web + 脚本）

本项目用于生成 3D 技术演示动图，展示“环绕扫描 → 点云 → 建模”的过程。支持两种使用方式：
- 网页端（Streamlit）：交互式输入目标名称，实时生成 GIF 并下载。
- 脚本端（Python 程序）：直接在终端运行，生成离线 GIF 文件。

**亮点**
- 自动中文字体配置，跨平台兼容（Windows/macOS/Linux）。
- 小尺寸透明背景的 GIF，描边 UI 文本保证可读性。
- 使用内存缓冲逐帧渲染，避免“残影”，并保持尺寸稳定。

**当前代码状态**
- 网页入口：`app.py`（推荐）与 `run.py`（等效入口，功能相近）。
- 离线脚本：`main.py`（直接生成 `sam3d_fixed_compressed.gif`）。
- 依赖清单：`requirements.txt`（`streamlit`、`numpy`、`matplotlib`、`imageio`）。

## 快速开始（macOS）

**1. 创建并启用虚拟环境**
- `python3 -m venv .venv`
- `source .venv/bin/activate`

**2. 安装依赖**
- `pip install -r requirements.txt`

**3. 启动网页端（推荐）**
- `python -m streamlit run app.py`
- 访问：`http://localhost:8501/`
- 如你更倾向使用另一个入口：`python -m streamlit run run.py`

提示：如果你的终端提示符同时显示 `(.venv)` 与 `(base)`，建议使用 `python -m streamlit ...` 形式确保调用的是虚拟环境中的解释器。

**4. 生成离线 GIF（脚本端）**
- `python main.py`
- 输出文件：`sam3d_fixed_compressed.gif`（约 300×300 像素、透明背景、15 FPS）。

可选优化（热更新更顺畅）：
- 安装 Xcode Command Line Tools：`xcode-select --install`
- 安装文件监控：`pip install watchdog`

## 使用说明

**网页端工作流**
- 在页面输入“建模目标名称”（如“智能音箱”），选择动画时长，点击“开始生成 GIF”。
- 渲染完成后可预览并下载生成的动图。

**脚本端工作流**
- 直接运行 `main.py`。脚本会在当前目录生成示例 GIF。

## 项目结构
- `app.py`：Streamlit 网页版入口，包含 UI 与逐帧渲染逻辑。
- `run.py`：另一份 Streamlit 入口，界面与逻辑与 `app.py` 类似。
- `main.py`：离线脚本，构建 3D 场景、时间线并导出 GIF。
- `requirements.txt`：依赖列表。
- `.gitignore`：忽略项配置。

## 技术细节（概述）
- 字体配置：根据平台自动选择字体，确保中文正常显示。
  - macOS 优先：`Arial Unicode MS`、`PingFang SC`、`Heiti TC`。
- 场景与动画：
  - 几何体：立方体（示例），并可扩展金字塔/棱柱等。
  - 三阶段时间线：
    - 阶段 1：环绕扫描/输入目标。
    - 阶段 2：稀疏点云到稠密实体的可视化过渡。
    - 阶段 3：高亮实体并进行旋转展示。
- 渲染与导出：
  - 小画布（约 250–300px），透明背景。
  - `imageio.mimsave` 导出 GIF，使用 `optimize=True` 提高压缩效果。

## 参数与自定义
- 目标名称：网页端直接输入；脚本端可修改常量（如 `TARGET_STR`）。
- 输出尺寸：调整 `plt.figure(figsize=(w, h), dpi=...)`。
- 帧数与时长：
  - 网页端：`duration` 与内部 `FPS` 控制总帧数。
  - 脚本端：`TOTAL_FRAMES` 与 `duration=4.0 / TOTAL_FRAMES` 控制时长。
- 视觉风格：
  - 颜色、线宽、描边等均可在样式字典或绘制函数中调整。

## 常见问题
- 文件不存在：若运行 `streamlit run app.py` 报“File does not exist”，请确认文件存在并使用 `python -m streamlit run app.py` 以确保采用虚拟环境中的解释器。
- 中文字体缺失：安装 `PingFang SC` 或在代码中手动设置 `plt.rcParams['font.sans-serif']`。
- 端口占用：默认端口 `8501` 被占用时，可运行 `streamlit run app.py --server.port 8502`。
- GIF 体积偏大：降低 `dpi` 或减少帧数，或保留 `optimize=True`。

## 许可证
- 暂未指定许可证；如需开源分发，建议新增许可证文件（如 MIT 或 Apache-2.0）。

