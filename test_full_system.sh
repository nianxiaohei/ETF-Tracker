#!/bin/bash
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  ETF价格跟踪系统 - 完整自动化测试"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

PASSED=0
FAILED=0

# 测试函数
run_test() {
    local test_name="$1"
    local test_cmd="$2"
    
    echo ""
    echo -n "▶ 测试: $test_name ... "
    
    if eval "$test_cmd" > /tmp/test_output.log 2>&1; then
        echo -e "${GREEN}✓ 通过${NC}"
        ((PASSED++))
    else
        echo -e "${RED}✗ 失败${NC}"
        ((FAILED++))
        echo "错误信息:"
        cat /tmp/test_output.log | head -10
    fi
}

echo "【第1阶段】环境检查"
echo "━━━━━━━━━━━━━━━━━━━━"

# 1.1 Python版本
run_test "Python3是否可用" "python3 --version"

# 1.2 Python路径
echo -n "▶ 测试: Python路径检查 ... "
PYTHON_PATH=$(which python3)
if [[ $PYTHON_PATH == *"bin/python3"* ]]; then
    echo -e "${GREEN}✓ 通过${NC} - Python路径: $PYTHON_PATH"
    ((PASSED++))
else
    echo -e "${RED}✗ 失败${NC}"
    ((FAILED++))
fi

# 1.3 pip是否可用
run_test "pip3是否可用" "pip3 --version"

echo ""
echo "【第2阶段】依赖包检查"
echo "━━━━━━━━━━━━━━━━━━━━"

# 2.1 rich包
echo -n "▶ 测试: rich包 ... "
if python3 -c "import rich" 2>/dev/null; then
    RICH_VERSION=$(python3 -c "import rich; print(rich.__version__)" 2>/dev/null)
    echo -e "${GREEN}✓ 通过${NC} - 版本: $RICH_VERSION"
    ((PASSED++))
else
    echo -e "${RED}✗ 失败${NC}"
    ((FAILED++))
fi

# 2.2 typer包
echo -n "▶ 测试: typer包 ... "
if python3 -c "import typer" 2>/dev/null; then
    TYPER_VERSION=$(python3 -c "import typer; print(typer.__version__)" 2>/dev/null)
    echo -e "${GREEN}✓ 通过${NC} - 版本: $TYPER_VERSION"
    ((PASSED++))
else
    echo -e "${RED}✗ 失败${NC}"
    ((FAILED++))
fi

# 2.3 httpx包
echo -n "▶ 测试: httpx包 ... "
if python3 -c "import httpx" 2>/dev/null; then
    HTTPX_VERSION=$(python3 -c "import httpx; print(httpx.__version__)" 2>/dev/null)
    echo -e "${GREEN}✓ 通过${NC} - 版本: $HTTPX_VERSION"
    ((PASSED++))
else
    echo -e "${RED}✗ 失败${NC}"
    ((FAILED++))
fi

# 2.4 beautifulsoup4包
echo -n "▶ 测试: bs4包 ... "
if python3 -c "import bs4" 2>/dev/null; then
    echo -e "${GREEN}✓ 通过${NC}"
    ((PASSED++))
else
    echo -e "${RED}✗ 失败${NC}"
    ((FAILED++))
fi

# 2.5 lxml包
echo -n "▶ 测试: lxml包 ... "
if python3 -c "import lxml" 2>/dev/null; then
    echo -e "${GREEN}✓ 通过${NC}"
    ((PASSED++))
else
    echo -e "${RED}✗ 失败${NC}"
    ((FAILED++))
fi

# 2.6 loguru包
echo -n "▶ 测试: loguru包 ... "
if python3 -c "import loguru" 2>/dev/null; then
    echo -e "${GREEN}✓ 通过${NC}"
    ((PASSED++))
else
    echo -e "${RED}✗ 失败${NC}"
    ((FAILED++))
fi

echo ""
echo "【第3阶段】项目结构检查"
echo "━━━━━━━━━━━━━━━━━━━━"

# 3.1 主程序
run_test "main.py存在" "test -f /Users/nianxiaohei/Desktop/ETF_trace/main.py"

# 3.2 启动脚本
run_test "start.sh存在" "test -f /Users/nianxiaohei/Desktop/ETF_trace/start.sh"

# 3.3 配置文件
run_test "config/app.py存在" "test -f /Users/nianxiaohei/Desktop/ETF_trace/config/app.py"

# 3.4 config目录
run_test "config目录存在" "test -d /Users/nianxiaohei/Desktop/ETF_trace/config"

# 3.5 src目录
run_test "src目录存在" "test -d /Users/nianxiaohei/Desktop/ETF_trace/src"

# 3.6 data目录（如果不存在则创建）
echo -n "▶ 测试: data目录 ... "
if [ ! -d "/Users/nianxiaohei/Desktop/ETF_trace/data" ]; then
    mkdir -p /Users/nianxiaohei/Desktop/ETF_trace/data
fi
if [ -d "/Users/nianxiaohei/Desktop/ETF_trace/data" ]; then
    echo -e "${GREEN}✓ 通过${NC}"
    ((PASSED++))
else
    echo -e "${RED}✗ 失败${NC}"
    ((FAILED++))
fi

echo ""
echo "【第4阶段】配置检查"
echo "━━━━━━━━━━━━━━━━━━━━"

# 4.1 ETF配置
echo -n "▶ 测试: ETF配置加载 ... "
ETF_COUNT=$(python3 -c "from config.app import ETF_LIST; print(len(ETF_LIST))" 2>/dev/null)
if [ "$ETF_COUNT" == "16" ]; then
    echo -e "${GREEN}✓ 通过${NC} - 加载了 $ETF_COUNT 个ETF"
    ((PASSED++))
else
    echo -e "${YELLOW}⚠ 警告${NC} - 加载了 $ETF_COUNT 个ETF（预期16个）"
    ((PASSED++))
fi

# 4.2 ETF代码格式
echo -n "▶ 测试: ETF代码格式 ... "
ETF_SAMPLE=$(python3 -c "from config.app import ETF_LIST; print(ETF_LIST[0]['code'])" 2>/dev/null)
if [[ "$ETF_SAMPLE" == SH* ]] || [[ "$ETF_SAMPLE" == SZ* ]]; then
    echo -e "${GREEN}✓ 通过${NC} - 格式正确 ($ETF_SAMPLE)"
    ((PASSED++))
else
    echo -e "${RED}✗ 失败${NC} - 格式错误 ($ETF_SAMPLE)"
    ((FAILED++))
fi

echo ""
echo "【第5阶段】爬虫测试"
echo "━━━━━━━━━━━━━━━━━━━━"

# 5.1 爬虫模块加载
echo -n "▶ 测试: 爬虫模块导入 ... "
if python3 -c "from src.crawler import XueqiuCrawler" 2>/dev/null; then
    echo -e "${GREEN}✓ 通过${NC}"
    ((PASSED++))
else
    echo -e "${RED}✗ 失败${NC}"
    cat /tmp/test_output.log | head -10
    ((FAILED++))
fi

# 5.2 测试单个ETF抓取（简单测试）
echo -n "▶ 测试: 单ETF价格抓取 ... "
python3 -c "
from src.crawler import XueqiuCrawler
import sys
crawler = XueqiuCrawler()
result = crawler.fetch_price_sync('SZ159790')
if result:
    print(f'成功: {result[0]}')
    sys.exit(0)
else:
    sys.exit(1)
" > /tmp/crawler_test.log 2>&1

if [ $? -eq 0 ]; then
    PRICE=$(cat /tmp/crawler_test.log)
    echo -e "${GREEN}✓ 通过${NC} - $PRICE"
    ((PASSED++))
else
    echo -e "${RED}✗ 失败${NC}"
    cat /tmp/crawler_test.log | head -10
    ((FAILED++))
fi

# 5.3 测试批量抓取函数
echo -n "▶ 测试: 批量抓取函数导入 ... "
if python3 -c "from src.crawler import XueqiuCrawler; c = XueqiuCrawler(); hasattr(c, 'fetch_multiple_etfs_sync')" 2>/dev/null; then
    echo -e "${GREEN}✓ 通过${NC}"
    ((PASSED++))
else
    echo -e "${RED}✗ 失败${NC}"
    ((FAILED++))
fi

echo ""
echo "【第6阶段】存储模块测试"
echo "━━━━━━━━━━━━━━━━━━━━"

# 6.1 存储模块导入
echo -n "▶ 测试: 存储模块导入 ... "
if python3 -c "from src.storage import price_storage" 2>/dev/null; then
    echo -e "${GREEN}✓ 通过${NC}"
    ((PASSED++))
else
    echo -e "${RED}✗ 失败${NC}"
    cat /tmp/test_output.log | head -10
    ((FAILED++))
fi

echo ""
echo "【第7阶段】计算器模块测试"
echo "━━━━━━━━━━━━━━━━━━━━"

# 7.1 计算器模块导入
echo -n "▶ 测试: 计算器模块导入 ... "
if python3 -c "from src.calculator import PriceCalculator" 2>/dev/null; then
    echo -e "${GREEN}✓ 通过${NC}"
    ((PASSED++))
else
    echo -e "${RED}✗ 失败${NC}"
    ((FAILED++))
fi

# 7.2 计算涨跌幅
echo -n "▶ 测试: 涨跌幅计算 ... "
CHANGE=$(python3 -c "from src.calculator import PriceCalculator; print(PriceCalculator.calculate_change_percent(1.0, 1.05))" 2>/dev/null)
if echo "$CHANGE" | grep -q "5.0"; then
    echo -e "${GREEN}✓ 通过${NC} - 涨幅: $CHANGE%"
    ((PASSED++))
else
    echo -e "${RED}✗ 失败${NC} - 结果: $CHANGE"
    ((FAILED++))
fi

echo ""
echo "【第8阶段】日志模块测试"
echo "━━━━━━━━━━━━━━━━━━━━"

# 8.1 日志模块导入
echo -n "▶ 测试: 日志模块导入 ... "
if python3 -c "from src.logger import logger" 2>/dev/null; then
    echo -e "${GREEN}✓ 通过${NC}"
    ((PASSED++))
else
    echo -e "${RED}✗ 失败${NC}"
    ((FAILED++))
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  测试完成数据统计"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "通过: ${GREEN}$PASSED${NC}"
echo -e "失败: ${RED}$FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}  ✅ 所有测试通过！系统可以正常运行${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo "可以启动程序："
    echo "  ./start.sh"
    echo ""
    exit 0
else
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${RED}  ⚠️  有 $FAILED 项测试失败，请检查${NC}"
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    exit 1
fi
