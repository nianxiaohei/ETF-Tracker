#!/bin/bash
# ETF 价格跟踪系统 - 快速启动脚本

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# 检查虚拟环境是否存在
if [ ! -d "venv" ]; then
    echo "⚠️  虚拟环境不存在，正在创建..."
    python3 -m venv venv
    echo "✓ 虚拟环境创建完成"
fi

# 激活虚拟环境
echo "🔧 激活虚拟环境..."
source venv/bin/activate

# 检查依赖是否安装
if ! python -c "import typer" 2>/dev/null; then
    echo "⚠️  依赖未安装，正在安装..."
    pip install -r requirements.txt
    echo "✓ 依赖安装完成"
fi

# 显示菜单
echo ""
echo "=========================================="
echo "  ETF 价格跟踪系统"
echo "=========================================="
echo ""
echo "请选择操作："
echo "  1) 获取当前价格"
echo "  2) 分析 ETF（交互式）"
echo "  3) 分析 ETF（指定参数）"
echo "  4) 获取并保存价格"
echo "  5) 查看价格历史"
echo "  6) 查看交易记录"
echo "  7) 查看帮助"
echo "  0) 退出"
echo ""
read -p "请输入选项 [0-7]: " choice

case $choice in
    1)
        echo ""
        python main.py price
        ;;
    2)
        echo ""
        python main.py analyze
        ;;
    3)
        read -p "请输入交易价格: " price
        read -p "请输入交易数量: " quantity
        echo ""
        python main.py analyze --price "$price" --quantity "$quantity"
        ;;
    4)
        echo ""
        python main.py fetch
        ;;
    5)
        echo ""
        python main.py history
        ;;
    6)
        echo ""
        python main.py list
        ;;
    7)
        echo ""
        python main.py --help
        ;;
    0)
        echo "退出"
        exit 0
        ;;
    *)
        echo "无效选项"
        exit 1
        ;;
esac

echo ""
echo "=========================================="
echo "操作完成！"
echo "=========================================="
