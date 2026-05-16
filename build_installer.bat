@echo off
chcp 65001 >nul
echo ====================================
echo   MT任务助手 - 构建安装程序
echo ====================================
echo.

REM 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python，请先安装 Python 3.8+
    pause
    exit /b 1
)

REM 安装依赖
echo [1/3] 安装依赖...
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple pyinstaller -q
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt -q

REM 清理旧文件
echo [2/3] 清理旧构建文件...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

REM 构建
echo [3/3] 构建可执行文件...
pyinstaller mt_task_assistant.spec --noconfirm

if errorlevel 1 (
    echo.
    echo [错误] 构建失败！
    pause
    exit /b 1
)

echo.
echo ====================================
echo   构建完成！
echo   输出目录: dist\MT任务助手\
echo ====================================
pause
