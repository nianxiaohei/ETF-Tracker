#!/bin/bash
echo "开始安装依赖包到系统Python..."
echo ""
echo "这将安装 rich, httpx, beautifulsoup4, lxml 等包"
echo "到系统的site-packages目录"
echo ""

# 使用系统Python的pip安装
/usr/bin/pip3 install -q rich typer httpx beautifulsoup4 lxml loguru

echo "✅ 依赖安装完成！"
echo ""
echo "现在可以直接运行程序："
echo ""
echo "  cd /Users/nianxiaohei/Desktop/ETF_trace"
echo "  python3 main.py"
echo ""
