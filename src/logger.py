"""
日志系统配置
"""
from loguru import logger
from pathlib import Path
from config.app import LOG_CONFIG, PROJECT_ROOT, log_dir

# 配置日志格式
logger.remove()  # 移除默认的 handler

# 添加控制台输出
logger.add(
    sink=lambda msg: print(msg, end=''),
    format=LOG_CONFIG['format'],
    level=LOG_CONFIG['level'],
    colorize=True
)

# 添加日志文件
logger.add(
    sink=Path(log_dir) / 'app.log',
    format=LOG_CONFIG['format'],
    level=LOG_CONFIG['level'],
    rotation='500 MB',  # 每 500MB 滚动
    retention='10 days',  # 保留 10 天
    encoding='utf-8'
)

# 添加错误日志文件
logger.add(
    sink=Path(log_dir) / 'error.log',
    format=LOG_CONFIG['format'],
    level='ERROR',
    rotation='500 MB',
    retention='10 days',
    encoding='utf-8'
)

__all__ = ['logger']
