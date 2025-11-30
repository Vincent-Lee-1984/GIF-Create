@echo off
cd /d "%~dp0"

REM 1. 检查是否存在 .venv，不存在则创建
if not exist .venv (
    echo Creating virtual environment...
    python -m venv .venv
)

REM 2. 激活环境并安装依赖
call .venv\Scripts\activate
echo Installing requirements...
python -m pip install -r requirements.txt

REM 3. 启动应用
echo Starting Streamlit app...
python -m streamlit run app.py
pause