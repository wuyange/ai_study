@echo off
chcp 65001 >nul
echo ========================================
echo    AI 聊天系统 - 环境配置
echo ========================================
echo.

echo [步骤 1/5] 配置后端环境
echo ========================================
cd backend

echo 创建 Python 虚拟环境...
if exist venv (
    echo ✓ 虚拟环境已存在，跳过创建
) else (
    python -m venv venv
    if errorlevel 1 (
        echo ✗ 创建虚拟环境失败，请检查 Python 是否正确安装
        pause
        exit /b 1
    )
    echo ✓ 虚拟环境创建完成
)

echo.
echo 激活虚拟环境...
call venv\Scripts\activate
echo ✓ 虚拟环境已激活

echo.
echo [步骤 2/5] 升级 pip（使用清华镜像）
echo ========================================
python -m pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple
echo ✓ pip 升级完成

echo.
echo [步骤 3/5] 安装 Python 依赖（使用清华镜像）
echo ========================================
echo 这可能需要几分钟，请耐心等待...
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
if errorlevel 1 (
    echo.
    echo ✗ 依赖安装失败，尝试使用阿里云镜像重试...
    pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/
    if errorlevel 1 (
        echo ✗ 依赖安装失败
        pause
        exit /b 1
    )
)
echo ✓ 基础依赖安装完成

echo.
echo [步骤 4/5] 安装 AutoGen（使用清华镜像）
echo ========================================
echo 正在安装 AutoGen，这可能需要几分钟...
pip install autogen-agentchat autogen-ext[openai] -i https://pypi.tuna.tsinghua.edu.cn/simple
if errorlevel 1 (
    echo.
    echo ✗ AutoGen 安装失败，尝试使用阿里云镜像重试...
    pip install autogen-agentchat autogen-ext[openai] -i https://mirrors.aliyun.com/pypi/simple/
    if errorlevel 1 (
        echo ✗ AutoGen 安装失败
        pause
        exit /b 1
    )
)
echo ✓ AutoGen 安装完成

echo.
echo 配置环境变量...
if exist env.example (
    if not exist .env (
        copy env.example .env
        echo ✓ 已创建 .env 文件
    ) else (
        echo ✓ .env 文件已存在，跳过创建
    )
) else (
    echo ✗ 未找到 env.example 文件
)

cd ..

echo.
echo [步骤 5/5] 配置前端环境
echo ========================================

REM 检查 npm 是否安装
where npm >nul 2>&1
if errorlevel 1 (
    echo.
    echo ⚠️  警告：未检测到 Node.js/npm
    echo.
    echo Node.js 下载地址：https://nodejs.org/
    echo 建议下载 LTS 长期支持版本
    echo.
    echo 您可以：
    echo 1. 现在下载安装 Node.js，然后重新运行此脚本
    echo 2. 跳过前端安装，只使用后端 API（按任意键继续）
    echo.
    pause
    echo.
    echo 跳过前端安装...
    goto :skip_frontend
)

cd frontend

echo 检测到 npm，正在安装依赖...
echo 使用淘宝镜像加速...
call npm install --legacy-peer-deps --registry=https://registry.npmmirror.com
if errorlevel 1 (
    echo.
    echo ✗ 前端依赖安装失败，尝试使用默认源重试...
    call npm install --legacy-peer-deps
    if errorlevel 1 (
        echo ✗ 前端依赖安装失败
        cd ..
        goto :skip_frontend
    )
)
echo ✓ 前端依赖安装完成
cd ..

:skip_frontend

echo.
echo ========================================
echo    ✓ 环境配置完成！
echo ========================================
echo.
echo 后续步骤：
echo 1. 编辑 backend\.env 文件，填入您的 OpenAI API Key
echo    OPENAI_API_KEY=sk-your-actual-api-key-here
echo.
echo 2. 运行 start_all.bat 启动完整系统
echo.
echo 3. 在浏览器访问 http://localhost:3000
echo.
echo ========================================
echo.

pause

