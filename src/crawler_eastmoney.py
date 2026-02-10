"""
东方财富数据采集模块
使用东方财富API获取ETF价格
"""
import asyncio
import time
import httpx
import json
from datetime import datetime
from typing import Dict, Optional, Tuple
from src.logger import logger
from config.app import HTTP_CONFIG, ETF_CONFIG


class EastMoneyCrawler:
    """东方财富爬虫类"""

    def __init__(self):
        self.base_url = "https://push2.eastmoney.com/api/qt/stock/get"
        self.timeout = HTTP_CONFIG['timeout']
        self.delay = HTTP_CONFIG['delay']
        self.headers = {
            'User-Agent': HTTP_CONFIG['user_agent'],
            'Accept': 'application/json',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        }

    def _get_market_code(self, etf_code: str) -> str:
        """
        根据ETF代码前缀获取市场代码

        参数:
            etf_code: ETF代码（如 SZ159915, SH510300, SCHD）

        返回:
            东方财富市场代码（0=深圳，1=上海，107=美股）
        """
        if etf_code.startswith('SZ') or etf_code.startswith('sz'):
            return '0'  # 深圳市场
        elif etf_code.startswith('SH') or etf_code.startswith('sh'):
            return '1'  # 上海市场
        else:
            # 美股ETF（代码不以SZ/SH开头）
            # 从ETF列表中检查是否为美股
            try:
                from src.storage import etf_list_storage
                all_etfs = etf_list_storage.get_all_etfs()
                if etf_code in all_etfs:
                    # 从ETF信息中获取市场组别
                    etf_info = all_etfs[etf_code]
                    group = etf_info.get('group', '')
                    # 如果是美股，使用107市场代码
                    if group == '美股':
                        return '107'
            except:
                pass

            # 如果不在列表中，检查是否为常见的美股ETF格式（纯字母）
            import re
            if re.match(r'^[A-Z]+$', etf_code.upper()):
                return '107'  # 默认为美股

            return '0'  # 默认为A股深圳市场

    def _get_etf_name(self, etf_code: str) -> str:
        """
        获取ETF名称

        参数:
            etf_code: ETF代码

        返回:
            ETF名称
        """
        # 从缓存或配置中获取名称
        if etf_code in ETF_CONFIG:
            return ETF_CONFIG[etf_code]['name']

        # 如果不在默认配置中，尝试从csv文件获取
        try:
            from src.storage import etf_list_storage
            all_etfs = etf_list_storage.get_all_etfs()
            if etf_code in all_etfs:
                return all_etfs[etf_code]['name']
        except:
            pass

        # Fallback：使用代码作为名称
        return etf_code

    async def fetch_price_async(self, etf_code: str) -> Optional[Tuple[float, str]]:
        """
        异步获取ETF价格（使用东方财富API）

        参数:
            etf_code: ETF代码（如SZ159915）

        返回:
            (价格, ETF名称)元组，失败返回None
        """
        logger.info(f"开始获取 {etf_code} 的价格（东方财富）")

        # 获取市场代码
        market_code = self._get_market_code(etf_code)
        # 去掉前缀，获取纯代码（仅A股需要去掉SZ/SH前缀，美股代码保持不变）
        if etf_code.startswith(('SZ', 'sz', 'SH', 'sh')):
            pure_code = etf_code[2:]  # 去掉前缀，如SZ159915 -> 159915
        else:
            pure_code = etf_code  # 美股ETF保持原样，如SCHD

        params = {
            'secid': f'{market_code}.{pure_code}',
            'fields': 'f43,f57,f58,f107,f60,f116,f117,f73,f59,f46,f44,f45,f47,f48,f50,f51,f52,f55,f62,f164,f165,f166,f167,f168,f169,f170,f171,f172,f173,f257,f258'
        }

        try:
            # 添加延迟，避免触发频率限制
            await asyncio.sleep(self.delay)

            async with httpx.AsyncClient(timeout=self.timeout, headers=self.headers) as client:
                logger.info(f"正在请求东方财富API: {self.base_url}?secid={params['secid']}")
                response = await client.get(self.base_url, params=params)
                response.raise_for_status()

                data = response.json()
                logger.info(f"API请求成功，状态码: {response.status_code}")

                # 解析价格数据
                price = self._parse_price_from_api(data, etf_code)

                if price is not None:
                    etf_name = self._get_etf_name(etf_code)
                    logger.info(f"成功从东方财富获取 {etf_code} 价格: {price}")
                    return (price, etf_name)
                else:
                    logger.error(f"从东方财富API响应中解析价格失败")
                    return None

        except httpx.HTTPStatusError as e:
            logger.error(f"东方财富API HTTP错误: {e.response.status_code} - {e.response.text[:200]}")
            return None
        except httpx.RequestError as e:
            logger.error(f"东方财富API请求错误: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"东方财富API响应JSON解析失败: {e}")
            return None
        except Exception as e:
            logger.error(f"东方财富API请求未知错误: {e}")
            return None

    def _parse_price_from_api(self, data: Dict, etf_code: str) -> Optional[float]:
        """
        从东方财富API响应中解析价格

        参数:
            data: API返回的JSON数据
            etf_code: ETF代码（用于调试）

        返回:
            价格（浮点数）或None
        """
        try:
            # 检查响应码
            rc_code = data.get('rc')
            if rc_code != 0:
                error_msg = data.get('rtmessage', '未知错误')
                logger.error(f"东方财富API返回错误: {rc_code} - {error_msg}")
                return None

            # 获取行情数据
            result = data.get('data')
            if not result:
                logger.error(f"东方财富API响应中没有data数据")
                # 保存调试信息
                with open(f'debug_eastmoney_{etf_code}.json', 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                logger.info(f"已保存调试文件: debug_eastmoney_{etf_code}.json")
                return None

            # 获取当前价格 (f43字段)
            # 东方财富的价格字段是整数，需要除以1000
            current_price_raw = result.get('f43')
            if current_price_raw is None or current_price_raw == '-':
                logger.error(f"没有f43字段(当前价格): {result}")
                return None

            # 转换为浮点数（除以1000）
            price = float(current_price_raw) / 1000.0

            # 验证价格范围
            if 0.01 <= price <= 10000:
                logger.debug(f"从东方财富API解析价格: {price}")
                return price
            else:
                logger.error(f"价格超出合理范围: {price}")
                return None

        except (ValueError, TypeError, AttributeError) as e:
            logger.error(f"解析东方财富价格时出错: {e}")
            logger.error(f"响应数据: {data}")
            return None

    def fetch_price_sync(self, etf_code: str) -> Optional[Tuple[float, str]]:
        """
        同步获取ETF价格（使用东方财富API）

        参数:
            etf_code: ETF代码

        返回:
            (价格, ETF名称)元组，失败返回None
        """
        logger.info(f"开始同步获取 {etf_code} 的价格（东方财富）")

        # 简单延迟
        time.sleep(self.delay)

        # 获取市场代码和纯代码（仅A股需要去掉SZ/SH前缀，美股代码保持不变）
        market_code = self._get_market_code(etf_code)
        if etf_code.startswith(('SZ', 'sz', 'SH', 'sh')):
            pure_code = etf_code[2:]  # 去掉前缀，如SZ159915 -> 159915
        else:
            pure_code = etf_code  # 美股ETF保持原样，如SCHD

        params = {
            'secid': f'{market_code}.{pure_code}',
            'fields': 'f43,f57,f58,f107,f60,f116,f117,f73,f59,f46,f44,f45,f47,f48,f50,f51,f52,f55,f62,f164,f165,f166,f167,f168,f169,f170,f171,f172,f173,f257,f258'
        }

        try:
            with httpx.Client(timeout=self.timeout, headers=self.headers) as client:
                url_with_params = f"{self.base_url}?secid={params['secid']}"
                logger.info(f"正在请求东方财富API: {url_with_params}")
                response = client.get(self.base_url, params=params)
                response.raise_for_status()

                data = response.json()

                # 解析价格数据
                price = self._parse_price_from_api(data, etf_code)
                if price is not None:
                    etf_name = self._get_etf_name(etf_code)
                    logger.info(f"成功从东方财富获取 {etf_code} 价格: {price}")
                    return (price, etf_name)
                else:
                    logger.error(f"从东方财富API响应中解析价格失败")
                    return None

        except Exception as e:
            logger.error(f"东方财富API请求失败: {e}")
            # 尝试获取错误详情
            try:
                if 'response' in locals():
                    logger.error(f"响应内容: {response.text[:200]}")
            except:
                pass
            return None


def test_eastmoney_crawler():
    """测试东方财富爬虫"""
    print("测试东方财富API爬虫...\n")

    crawler = EastMoneyCrawler()

    # 测试几个ETF
    test_codes = ['SZ159915', 'SH510300', 'SZ159967']

    for code in test_codes:
        print(f"\n--- 测试 {code} ---")
        result = crawler.fetch_price_sync(code)

        if result:
            price, name = result
            print(f"✓ 成功获取价格: {name} - {price}元")
        else:
            print(f"✗ 获取价格失败: {code}")

    return True


__all__ = ['EastMoneyCrawler']


if __name__ == '__main__':
    test_eastmoney_crawler()
