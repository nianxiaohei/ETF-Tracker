"""
腾讯财经数据采集模块
使用腾讯财经API获取ETF价格
支持美股ETF使用Yahoo Finance作为备用数据源

API文档: https://qt.gtimg.cn/
Yahoo Finance: https://query1.finance.yahoo.com/
"""
import asyncio
import time
import httpx
import json
import ssl
from datetime import datetime
from typing import Dict, Optional, Tuple
from src.logger import logger
from config.app import HTTP_CONFIG, ETF_CONFIG


class TencentCrawler:
    """腾讯财经爬虫类，支持A股和美股ETF"""

    # 美股ETF代码列表（不带SH/SZ前缀）
    US_ETFS = {'USMV', 'VIG', 'VNM', 'SCHD', 'QQQM', 'DXJ', 'VGIT', 'GLDM',
               'VTI', 'QQQ', 'SPY', 'IWM', 'DIA', 'EFA', 'EEM', 'VWO',
               'BND', 'TLT', 'GLD', 'SLV', 'VNQ', 'XLE', 'XLF', 'XLV'}

    def __init__(self):
        self.base_url = "https://qt.gtimg.cn/q"
        self.yahoo_url = "https://query1.finance.yahoo.com/v8/finance/chart"
        self.timeout = HTTP_CONFIG['timeout']
        self.delay = HTTP_CONFIG['delay']
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': '*/*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Referer': 'https://finance.qq.com/',
        }

    def _get_stock_code(self, etf_code: str) -> str:
        """
        根据ETF代码获取腾讯API需要的股票代码

        参数:
            etf_code: ETF代码，如 SH560050, SZ159967, SCHD

        返回:
            腾讯API需要的股票代码，如 sh560050, sz159967
        """
        # 检查是否是美股ETF（不带SH/SZ前缀）
        if etf_code.upper() in self.US_ETFS:
            return None  # 使用Yahoo Finance

        # 去掉前缀，获取纯代码
        pure_code = etf_code[2:] if len(etf_code) > 2 else etf_code

        # 根据前缀判断市场
        if etf_code.startswith('SH'):
            return f'sh{pure_code}'
        elif etf_code.startswith('SZ'):
            return f'sz{pure_code}'
        elif etf_code.startswith('HK'):
            return f'hk{pure_code}'
        else:
            # 默认为上海
            return f'sh{pure_code}'

    def _is_us_etf(self, etf_code: str) -> bool:
        """判断是否是美股ETF"""
        return etf_code.upper() in self.US_ETFS

    def _parse_price_from_response(self, response: str, etf_code: str) -> Optional[Tuple[float, str]]:
        """
        解析腾讯API响应

        响应格式: v_sh560050="1~中国A50ETF汇添富~560050~1.044~1.033~1.028~..."

        字段说明:
        0: 股票代码
        1: 股票名称
        2: 代码(数字)
        3: 当前价格
        4: 昨收价
        5: 开盘价
        ...

        返回:
        (价格, 名称) 或 None
        """
        try:
            # 解析响应格式: v_xxxxx="..."
            if not response or '=' not in response:
                logger.error(f"腾讯API响应格式错误: {response}")
                return None

            # 提取数据部分
            data_part = response.split('=')[1].strip('"; ')
            if not data_part:
                logger.error(f"腾讯API响应数据为空")
                return None

            # 按~分割字段
            fields = data_part.split('~')
            if len(fields) < 4:
                logger.error(f"腾讯API响应字段不足: {fields}")
                return None

            # 获取当前价格 (第4个字段，索引3)
            current_price_str = fields[3]
            if not current_price_str or current_price_str == '-':
                logger.error(f"腾讯API返回价格为空: {fields}")
                return None

            current_price = float(current_price_str)
            name = fields[1] if len(fields) > 1 else etf_code

            return (current_price, name)

        except (ValueError, IndexError) as e:
            logger.error(f"解析腾讯API响应失败: {e}, 响应: {response[:200]}")
            return None
        except Exception as e:
            logger.error(f"解析腾讯API响应未知错误: {e}")
            return None

    def _fetch_from_yahoo(self, etf_code: str) -> Optional[Tuple[float, str]]:
        """
        从Yahoo Finance获取美股ETF价格

        参数:
            etf_code: 美股ETF代码，如 SCHD, QQQM

        返回:
            (价格, 名称) 或 None
        """
        url = f"{self.yahoo_url}/{etf_code.upper()}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        try:
            time.sleep(self.delay)
            response = httpx.get(url, headers=headers, timeout=self.timeout)
            response.raise_for_status()

            data = response.json()

            if 'chart' in data and 'result' in data['chart']:
                results = data['chart']['result']
                if results and len(results) > 0:
                    result = results[0]
                    if 'meta' in result:
                        meta = result['meta']
                        price = meta.get('regularMarketPrice')
                        symbol = meta.get('symbol', etf_code.upper())

                        if price:
                            logger.info(f"成功从Yahoo Finance获取 {etf_code} 价格: {price}")
                            return (price, symbol)

            logger.error(f"Yahoo Finance返回数据格式错误: {data}")
            return None

        except httpx.HTTPStatusError as e:
            logger.error(f"Yahoo Finance HTTP错误: {e.response.status_code}")
            return None
        except httpx.RequestError as e:
            logger.error(f"Yahoo Finance请求错误: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Yahoo Finance JSON解析失败: {e}")
            return None
        except Exception as e:
            logger.error(f"Yahoo Finance请求未知错误: {e}")
            return None

    async def fetch_price_async(self, etf_code: str) -> Optional[Tuple[float, str]]:
        """
        异步获取ETF价格

        参数:
            etf_code: ETF代码，如 SH560050, SCHD

        返回:
            (价格, 名称) 或 None
        """
        # 判断是否是美股ETF
        if self._is_us_etf(etf_code):
            return self._fetch_from_yahoo(etf_code)

        stock_code = self._get_stock_code(etf_code)
        if stock_code is None:
            # 美股ETF
            return self._fetch_from_yahoo(etf_code)

        url = f"{self.base_url}={stock_code}"

        # 异步重试机制
        max_retries = 3
        retry_delay = 1.0

        for attempt in range(max_retries):
            try:
                # 添加延迟，避免触发频率限制
                await asyncio.sleep(self.delay)

                async with httpx.AsyncClient(
                    timeout=httpx.Timeout(self.timeout, connect=10.0),
                    headers=self.headers,
                    http2=False
                ) as client:
                    logger.info(f"正在请求腾讯财经API: {url} (尝试 {attempt + 1}/{max_retries})")
                    response = await client.get(url)
                    response.raise_for_status()

                    # 尝试用GB18030解码（腾讯API返回GB编码）
                    try:
                        text = response.content.decode('GB18030')
                    except UnicodeDecodeError:
                        text = response.text

                    logger.info(f"腾讯API请求成功，状态码: {response.status_code}")

                    # 解析价格数据
                    result = self._parse_price_from_response(text, etf_code)

                    if result is not None:
                        price, name = result
                        logger.info(f"成功从腾讯财经获取 {etf_code} 价格: {price}, 名称: {name}")
                        return (price, name)
                    else:
                        logger.error(f"从腾讯财经API解析价格失败")
                        return None

            except httpx.HTTPStatusError as e:
                logger.error(f"腾讯财经API HTTP错误: {e.response.status_code} - {e.response.text[:200]}")
                if attempt < max_retries - 1:
                    logger.info(f"将在 {retry_delay}秒后重试...")
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    return None
            except httpx.RequestError as e:
                logger.error(f"腾讯财经API请求错误: {e}")
                if attempt < max_retries - 1:
                    logger.info(f"将在 {retry_delay}秒后重试...")
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    return None
            except Exception as e:
                logger.error(f"腾讯财经API请求未知错误: {e}")
                if attempt < max_retries - 1:
                    logger.info(f"将在 {retry_delay}秒后重试...")
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    return None

        return None

    def fetch_price_sync(self, etf_code: str) -> Optional[Tuple[float, str]]:
        """
        同步获取ETF价格

        参数:
            etf_code: ETF代码，如 SH560050, SCHD

        返回:
            (价格, 名称) 或 None
        """
        # 判断是否是美股ETF
        if self._is_us_etf(etf_code):
            return self._fetch_from_yahoo(etf_code)

        stock_code = self._get_stock_code(etf_code)
        if stock_code is None:
            # 美股ETF
            return self._fetch_from_yahoo(etf_code)

        url = f"{self.base_url}={stock_code}"

        # 配置SSL上下文，允许较旧的TLS版本以兼容腾讯API
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = True
        ssl_context.verify_mode = ssl.CERT_REQUIRED

        # 创建httpx客户端，配置更长的超时和更好的SSL处理
        max_retries = 3
        retry_delay = 1.0

        for attempt in range(max_retries):
            try:
                # 添加延迟
                time.sleep(self.delay)

                # 创建客户端，禁用HTTP/2以提高稳定性
                with httpx.Client(
                    timeout=httpx.Timeout(self.timeout, connect=10.0),
                    headers=self.headers,
                    http2=False
                ) as client:
                    logger.info(f"正在请求腾讯财经API: {url} (尝试 {attempt + 1}/{max_retries})")
                    response = client.get(url)
                    response.raise_for_status()

                    # 尝试用GB18030解码
                    try:
                        text = response.content.decode('GB18030')
                    except UnicodeDecodeError:
                        text = response.text

                    logger.info(f"腾讯API请求成功，状态码: {response.status_code}")

                    # 解析价格数据
                    result = self._parse_price_from_response(text, etf_code)

                    if result is not None:
                        price, name = result
                        logger.info(f"成功从腾讯财经获取 {etf_code} 价格: {price}, 名称: {name}")
                        return (price, name)
                    else:
                        logger.error(f"从腾讯财经API解析价格失败")
                        return None

            except httpx.HTTPStatusError as e:
                logger.error(f"腾讯财经API HTTP错误: {e.response.status_code}")
                if attempt < max_retries - 1:
                    logger.info(f"将在 {retry_delay}秒后重试...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # 指数退避
                else:
                    return None
            except httpx.RequestError as e:
                logger.error(f"腾讯财经API请求错误: {e}")
                if attempt < max_retries - 1:
                    logger.info(f"将在 {retry_delay}秒后重试...")
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    return None
            except Exception as e:
                logger.error(f"腾讯财经API请求未知错误: {e}")
                if attempt < max_retries - 1:
                    logger.info(f"将在 {retry_delay}秒后重试...")
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    return None

        return None


def test_tencent_crawler():
    """测试腾讯财经爬虫"""
    import sys
    sys.path.insert(0, '.')

    crawler = TencentCrawler()

    # 测试几个ETF
    test_codes = ['SH560050', 'SZ159967', 'SH513050']

    print("=" * 50)
    print("测试腾讯财经爬虫")
    print("=" * 50)

    for code in test_codes:
        print(f"\n测试 {code}...")
        result = crawler.fetch_price_sync(code)
        if result:
            price, name = result
            print(f"  成功: 价格={price}, 名称={name}")
        else:
            print(f"  失败")


if __name__ == '__main__':
    test_tencent_crawler()
