"""
配置文件管理
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent

# 目录配置
data_dir = os.getenv('DATA_DIR', './data')
log_dir = os.getenv('LOG_DIR', './logs')

# 确保目录存在
Path(data_dir).mkdir(exist_ok=True)
Path(log_dir).mkdir(exist_ok=True)

# ETF 配置
ETF_CONFIG = {
    'code': os.getenv('ETF_CODE', 'SZ159915'),
    'name': os.getenv('ETF_NAME', '创业板ETF易方达')
}

# 文件配置
CSV_FILES = {
    'price_history': os.path.join(data_dir, os.getenv('PRICE_HISTORY_FILE', 'price_history.csv')),
    'user_transactions': os.path.join(data_dir, os.getenv('USER_TRANSACTIONS_FILE', 'user_transactions.csv')),
    'alert_status': os.path.join(data_dir, os.getenv('ALERT_STATUS_FILE', 'alert_status.csv')),
    'alert_history': os.path.join(data_dir, os.getenv('ALERT_HISTORY_FILE', 'alert_history.csv'))
}

# HTTP 配置
HTTP_CONFIG = {
    'user_agent': os.getenv('USER_AGENT', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'),
    'timeout': int(os.getenv('REQUEST_TIMEOUT', '30')),
    'delay': float(os.getenv('REQUEST_DELAY', '1.0'))
}

# 日志配置
LOG_CONFIG = {
    'level': os.getenv('LOG_LEVEL', 'INFO'),
    'format': '<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{module}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>'
}

# 价格计算配置
PRICE_CALCULATION = {
    'calculation_precision': 4,  # 内部计算精度
    'display_precision': 2      # 显示精度
}
