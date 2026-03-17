"""
ETF数据源管理器
支持多数据源自动切换：腾讯财经 -> 东方财富
"""
import time
from typing import Optional, Tuple
from src.logger import logger
from src.crawler_tencent import TencentCrawler
from src.crawler_eastmoney import EastMoneyCrawler


class ETFDataSourceManager:
    """ETF数据源管理器，支持多数据源自动切换"""

    def __init__(self):
        self.tencent_crawler = TencentCrawler()
        self.eastmoney_crawler = EastMoneyCrawler()
        self.primary_source = 'tencent'  # 主数据源
        self.fallback_enabled = True  # 启用备用数据源

    def fetch_price(self, etf_code: str, use_fallback: bool = True) -> Optional[Tuple[float, str]]:
        """
        获取ETF价格，自动切换数据源

        参数:
            etf_code: ETF代码
            use_fallback: 是否使用备用数据源

        返回:
            (价格, 名称) 或 None
        """
        # 尝试主数据源（腾讯财经）
        if self.primary_source == 'tencent':
            result = self._try_tencent(etf_code)
            if result is not None:
                return result

            # 主数据源失败，尝试备用数据源
            if use_fallback and self.fallback_enabled:
                logger.warning("腾讯财经API失败，尝试东方财富备用数据源...")
                result = self._try_eastmoney(etf_code)
                if result is not None:
                    return result

            return None
        else:
            # 尝试东方财富
            result = self._try_eastmoney(etf_code)
            if result is not None:
                return result

            # 备用数据源失败，尝试主数据源
            if use_fallback and self.fallback_enabled:
                logger.warning("东方财富API失败，尝试腾讯财经备用数据源...")
                result = self._try_tencent(etf_code)
                if result is not None:
                    return result

            return None

    def _try_tencent(self, etf_code: str) -> Optional[Tuple[float, str]]:
        """尝试从腾讯财经获取数据"""
        try:
            logger.debug(f"尝试从腾讯财经获取 {etf_code} 价格")
            return self.tencent_crawler.fetch_price_sync(etf_code)
        except Exception as e:
            logger.error(f"腾讯财经获取 {etf_code} 失败: {e}")
            return None

    def _try_eastmoney(self, etf_code: str) -> Optional[Tuple[float, str]]:
        """尝试从东方财富获取数据"""
        try:
            logger.debug(f"尝试从东方财富获取 {etf_code} 价格")
            return self.eastmoney_crawler.fetch_price_sync(etf_code)
        except Exception as e:
            logger.error(f"东方财富获取 {etf_code} 失败: {e}")
            return None

    def fetch_price_with_source(self, etf_code: str) -> Tuple[Optional[Tuple[float, str]], str]:
        """
        获取ETF价格，同时返回使用的数据源

        返回:
            ((价格, 名称), 数据源名称) 或 (None, 数据源名称)
        """
        # 尝试腾讯财经
        result = self._try_tencent(etf_code)
        if result is not None:
            return (result, 'tencent')

        # 尝试东方财富
        if self.fallback_enabled:
            result = self._try_eastmoney(etf_code)
            if result is not None:
                return (result, 'eastmoney')

        return (None, 'none')


# 全局实例
data_source_manager = ETFDataSourceManager()


def fetch_etf_price(etf_code: str) -> Optional[Tuple[float, str]]:
    """
    获取ETF价格的便捷函数

    参数:
        etf_code: ETF代码

    返回:
        (价格, 名称) 或 None
    """
    return data_source_manager.fetch_price(etf_code)


__all__ = ['ETFDataSourceManager', 'data_source_manager', 'fetch_etf_price']
