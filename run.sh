#!/bin/bash

# 1. 获取脚本所在目录，确保在项目根目录运行
cd "$(dirname "$0")"

# 2. 检查是否存在 .venv 虚拟环境，不存在则创建
if [ ! -d ".venv" ]; then
    echo "正在创建虚拟环境..."
    python3 -m venv .venv
fi

# 3. 激活虚拟环境
source .venv/bin/activate

# 4. 升级 pip (可选，但推荐)
python -m pip install --upgrade pip

# 5. 安装/更新依赖
echo "正在检查并安装依赖..."
python -m pip install -r requirements.txt

# 6. 启动 Streamlit
echo "正在启动应用..."
python -m streamlit run app.py
