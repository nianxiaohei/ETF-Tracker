#!/bin/bash
# ETF 价格跟踪系统 - 快速启动脚本

echo "=========================================="
echo "ETF 价格跟踪系统 - 安装和配置"
echo "=========================================="
echo ""

# 检查 Python 版本
echo "1. 检查 Python 版本..."
python3 --version
echo ""

# 创建虚拟环境
echo "2. 创建虚拟环境..."
python3 -m venv venv
source venv/bin/activate
echo "✓ 虚拟环境已创建并激活"
echo ""

# 安装依赖
echo "3. 安装依赖库..."
pip install -r requirements.txt
echo "✓ 依赖库安装完成"
echo ""

# 复制配置文件
echo "4. 配置环境变量..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✓ 配置文件已创建 (.env)"
else
    echo "✓ 配置文件已存在 (.env)"
fi
echo ""

# 测试运行
echo "5. 测试运行..."
echo "正在获取 ETF 价格..."
python main.py price
echo ""

# 完成
echo "=========================================="
echo "安装完成！"
echo "=========================================="
echo ""
echo "使用方法:"
echo "  # 激活虚拟环境"
echo "  source venv/bin/activate"
echo ""
echo "  # 分析 ETF"
echo "  python main.py analyze"
echo ""
echo "  # 查看命令帮助"
echo "  python main.py --help"
echo ""
echo "  # 配置定时任务（可选）"
echo "  # 编辑 com.etf.tracker.plist 并替换路径"
echo "  # 然后运行: launchctl load ~/Library/LaunchAgents/com.etf.tracker.plist"
echo ""
echo "查看 README.md 获取更多详细信息"
echo ""
