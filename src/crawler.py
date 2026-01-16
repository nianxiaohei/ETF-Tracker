"""
数据采集模块
从雪球网站爬取 ETF 价格
"""
import asyncio
import time
import httpx
from bs4 import BeautifulSoup
from datetime import datetime
from typing import Dict, Optional, Tuple
from src.logger import logger
from config.app import HTTP_CONFIG, ETF_CONFIG


class XueqiuCrawler:
    """雪球爬虫类"""

    def __init__(self):
        self.base_url = "https://xueqiu.com"
        self.timeout = HTTP_CONFIG['timeout']
        self.delay = HTTP_CONFIG['delay']
        self.headers = {
            'User-Agent': HTTP_CONFIG['user_agent'],
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }

    async def fetch_page(self, etf_code: str) -> Optional[str]:
        """
        异步获取雪球页面内容

        参数:
            etf_code: ETF 代码（如 SZ159915）

        返回:
            HTML 内容或 None
        """
        url = f"{self.base_url}/S/{etf_code}"

        try:
            # 添加延迟，避免触发反爬虫
            await asyncio.sleep(self.delay)

            async with httpx.AsyncClient(timeout=self.timeout, headers=self.headers) as client:
                logger.info(f"正在请求: {url}")
                response = await client.get(url)
                response.raise_for_status()

                logger.info(f"请求成功，状态码: {response.status_code}")
                return response.text

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP 错误: {e.response.status_code} - {e.response.text}")
            return None
        except httpx.RequestError as e:
            logger.error(f"请求错误: {e}")
            return None
        except Exception as e:
            logger.error(f"未知错误: {e}")
            return None

    def parse_price(self, html_content: str, etf_code: str) -> Optional[float]:
        """
        从 HTML 中解析价格

        参数:
            html_content: HTML 内容
            etf_code: ETF 代码（用于调试输出）

        返回:
            价格（浮点数）或 None
        """
        if not html_content:
            logger.error("HTML 内容为空")
            return None

        try:
            soup = BeautifulSoup(html_content, 'lxml')

            # 方法 1：查找股票代码和价格相关的元素
            # 雪球网站的价格通常在具有 stock-info 或类似 class 的元素中

            # 查找 meta 标签中的 stockCurrentPrice
            meta_tags = soup.find_all('meta', {'name': True, 'content': True})
            for meta in meta_tags:
                if meta.get('name') == 'current-price' or 'price' in meta.get('name', '').lower():
                    price_str = meta.get('content')
                    if price_str and self._is_price(price_str):
                        price = float(price_str)
                        logger.info(f"从 meta 标签解析到价格: {price}")
                        return price

            # 方法 2：查找具有 stock-current 类或包含价格的 span
            price_spans = soup.find_all(['span', 'div'], text=True)
            for element in price_spans:
                text = element.get_text().strip()
                # 查找类似 "2.15" 的格式
                if self._is_price(text):
                    # 验证这个元素附近是否有股票代码信息
                    parent = element.find_parent()
                    if parent and (etf_code in parent.get_text() or 'SZ' in parent.get_text() or 'SH' in parent.get_text()):
                        price = float(text)
                        logger.info(f"从 HTML 元素解析到价格: {price}")
                        return price

            # 方法 3：查找 JavaScript 数据
            scripts = soup.find_all('script')
            for script in scripts:
                if script.string:
                    import re
                    # 查找 "current": "3.346" 格式的价格
                    match = re.search(r'"current"\s*:\s*"([0-9]+\.?[0-9]*)"', script.string)
                    if match:
                        price = float(match.group(1))
                        logger.info(f"从 JavaScript 数据解析到价格: {price}")
                        return price

                    # 备选：查找 'current': '3.346' 格式（单引号）
                    match = re.search(r"'current'\s*:\s*'([0-9]+\.?[0-9]*)'", script.string)
                    if match:
                        price = float(match.group(1))
                        logger.info(f"从 JavaScript 数据解析到价格: {price}")
                        return price

                    # 备选：查找 current: "3.346" 格式（无引号）
                    match = re.search(r"\scurrent\s*:\s*\"([0-9]+\.?[0-9]*)\"", script.string)
                    if match:
                        price = float(match.group(1))
                        logger.info(f"从 JavaScript 数据解析到价格: {price}")
                        return price

            # 方法 4：尝试输出页面标题和部分内容，便于调试
            title = soup.title.string if soup.title else '无标题'
            logger.warning(f"无法解析价格，页面标题: {title}")

            # 保存页面源码到文件，便于人工查看
            debug_file = f'debug_{etf_code}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.html'
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            logger.info(f"已保存调试文件: {debug_file}")

            return None

        except Exception as e:
            logger.error(f"解析 HTML 时出错: {e}")
            return None

    def _is_price(self, text: str) -> bool:
        """
        判断字符串是否为价格格式

        参数:
            text: 待检测的文本

        返回:
            是否为价格格式
        """
        try:
            # 去除可能的货币符号和空格
            text = text.replace('¥', '').replace('￥', '').replace('$', '').replace(',', '').strip()

            # 检查是否为数字格式（允许小数）
            import re
            pattern = r'^\d+\.?\d*$'
            if not re.match(pattern, text):
                return False

            # 转换为浮点数
            value = float(text)

            # ETF 价格通常在 0.1 到 1000 之间
            if 0.1 <= value <= 1000:
                return True

            return False

        except (ValueError, TypeError):
            return False

    async def fetch_price(self, etf_code: str) -> Optional[Tuple[float, str]]:
        """
        获取 ETF 当前价格（主方法）

        参数:
            etf_code: ETF 代码

        返回:
            (价格, ETF 名称) 元组，失败返回 None
        """
        logger.info(f"开始获取 {etf_code} 的价格")

        html = await self.fetch_page(etf_code)
        if not html:
            logger.error(f"获取 {etf_code} 页面失败")
            return None

        price = self.parse_price(html, etf_code)
        if price is None:
            logger.error(f"解析 {etf_code} 价格失败")
            return None

        logger.info(f"成功获取 {etf_code} 价格: {price}")
        return (price, ETF_CONFIG['name'])

    def fetch_price_sync(self, etf_code: str) -> Optional[Tuple[float, str]]:
        """
        同步方法获取价格

        参数:
            etf_code: ETF 代码

        返回:
            (价格, ETF 名称) 元组，失败返回 None
        """
        try:
            # 简单的延迟
            time.sleep(self.delay)

            with httpx.Client(timeout=self.timeout, headers=self.headers) as client:
                url = f"{self.base_url}/S/{etf_code}"
                logger.info(f"正在请求: {url}")
                response = client.get(url)
                response.raise_for_status()

                html = response.text
                price = self.parse_price(html, etf_code)

                if price is not None:
                    logger.info(f"成功获取 {etf_code} 价格: {price}")
                    return (price, ETF_CONFIG['name'])

                return None

        except Exception as e:
            logger.error(f"同步获取价格失败: {e}")
            return None


def test_crawler():
    """测试爬虫"""
    print("测试雪球爬虫...")

    crawler = XueqiuCrawler()
    result = crawler.fetch_price_sync('SZ159915')

    if result:
        price, name = result
        print(f"✓ 成功获取价格: {name} - {price}元")
    else:
        print("✗ 获取价格失败")

    return result


__all__ = ['XueqiuCrawler']
