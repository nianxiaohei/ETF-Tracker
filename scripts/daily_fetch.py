#!/usr/bin/env python3
"""
每日价格采集脚本
用于 macOS launchd 定时任务
"""
import sys
import os
from pathlib import Path
from datetime import datetime

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.logger import logger
from src.crawler import XueqiuCrawler
from src.storage import price_storage
from config.app import ETF_CONFIG


def is_trading_day() -> bool:
    """
    判断今天是否为交易日
    规则：周一至周五（1-5），周六周日（6-7）为非交易日
    """
    weekday = datetime.now().weekday()  # 0=周一, 6=周日
    is_weekday = 0 <= weekday <= 4  # 周一到周五

    if not is_weekday:
        logger.info(f"今天是周末（weekday={weekday+1}），不采集价格")
        return False

    return True


def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("开始执行每日价格采集任务")
    logger.info(f"执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 判断是否为交易日
    if not is_trading_day():
        logger.info("今日不是交易日，任务结束")
        logger.info("=" * 60)
        return

    try:
        # 获取 ETF 代码
        etf_code = ETF_CONFIG['code']
        etf_name = ETF_CONFIG['name']

        logger.info(f"ETF 代码: {etf_code}")
        logger.info(f"ETF 名称: {etf_name}")

        # 获取价格
        crawler = XueqiuCrawler()
        result = crawler.fetch_price_sync(etf_code)

        if not result:
            logger.error("获取价格失败")
            sys.exit(1)

        price, name = result
        logger.info(f"成功获取价格: {price} 元")

        # 保存到历史记录
        price_record = price_storage.add_price_record(etf_code, name, price)
        logger.info(f"价格已保存到历史记录: {price_record['record_time']}")

        logger.info("任务执行成功")

    except Exception as e:
        logger.error(f"任务执行失败: {e}")
        logger.exception(e)
        sys.exit(1)

    finally:
        logger.info("=" * 60)


if __name__ == '__main__':
    main()
