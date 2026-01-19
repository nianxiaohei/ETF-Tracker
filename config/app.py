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

# ETF 配置（支持多只ETF）
ETF_CONFIG = {
    'SH560050': {
        'code': 'SH560050',
        'name': 'MSCI中国A50ETF',
        'url': 'https://xueqiu.com/S/SH560050'
    },
    'SZ159967': {
        'code': 'SZ159967',
        'name': '创业板成长ETF',
        'url': 'https://xueqiu.com/S/SZ159967'
    },
    'SH513050': {
        'code': 'SH513050',
        'name': '中概互联网ETF易方达',
        'url': 'https://xueqiu.com/S/SH513050'
    },
    'SZ159790': {
        'code': 'SZ159790',
        'name': '碳中和ETF',
        'url': 'https://xueqiu.com/S/SZ159790'
    },
    'SH512010': {
        'code': 'SH512010',
        'name': '医药ETF易方达',
        'url': 'https://xueqiu.com/S/SH512010'
    },
    'SH588300': {
        'code': 'SH588300',
        'name': '双创ETF',
        'url': 'https://xueqiu.com/S/SH588300'
    },
    'SH513100': {
        'code': 'SH513100',
        'name': '纳指ETF',
        'url': 'https://xueqiu.com/S/SH513100'
    },
    'SH513500': {
        'code': 'SH513500',
        'name': '标普500ETF',
        'url': 'https://xueqiu.com/S/SH513500'
    },
    'SH520550': {
        'code': 'SH520550',
        'name': '港股红利低波ETF',
        'url': 'https://xueqiu.com/S/SH520550'
    },
    'SZ159928': {
        'code': 'SZ159928',
        'name': '消费ETF',
        'url': 'https://xueqiu.com/S/SZ159928'
    },
    'SZ159766': {
        'code': 'SZ159766',
        'name': '旅游ETF',
        'url': 'https://xueqiu.com/S/SZ159766'
    },
    'SH513180': {
        'code': 'SH513180',
        'name': '恒生科技指数ETF',
        'url': 'https://xueqiu.com/S/SH513180'
    },
    'SZ159509': {
        'code': 'SZ159509',
        'name': '纳指科技ETF',
        'url': 'https://xueqiu.com/S/SZ159509'
    },
    'SZ159995': {
        'code': 'SZ159995',
        'name': '芯片ETF',
        'url': 'https://xueqiu.com/S/SZ159995'
    },
    'SZ159920': {
        'code': 'SZ159920',
        'name': '恒生ETF',
        'url': 'https://xueqiu.com/S/SZ159920'
    },
    'SH512070': {
        'code': 'SH512070',
        'name': '证券保险ETF易方达',
        'url': 'https://xueqiu.com/S/SH512070'
    }
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
