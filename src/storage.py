"""
数据存储模块
支持 CSV 文件的读写操作
"""
import csv
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
from src.logger import logger
from config.app import CSV_FILES


class CSVStorage:
    """CSV 数据存储类"""

    def __init__(self, file_path: str):
        """
        初始化存储

        参数:
            file_path: CSV 文件路径
        """
        self.file_path = Path(file_path)
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

    def _get_file_size(self) -> int:
        """获取文件大小"""
        if self.file_path.exists():
            return self.file_path.stat().st_size
        return 0

    def exists(self) -> bool:
        """检查文件是否存在"""
        return self.file_path.exists()

    def append(self, row: Dict[str, Any], fieldnames: List[str] = None):
        """
        追加一行数据

        参数:
            row: 行数据字典
            fieldnames: 字段名列表（如果不存在则自动创建文件）
        """
        try:
            file_exists = self.exists()
            mode = 'a' if file_exists else 'w'

            # 如果文件不存在，从 row 的 keys 获取 fieldnames
            if not fieldnames:
                fieldnames = list(row.keys())

            with open(self.file_path, mode, newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)

                # 如果文件不存在，写入表头
                if not file_exists:
                    writer.writeheader()
                    logger.debug(f"创建 CSV 文件: {self.file_path}")

                writer.writerow(row)

        except Exception as e:
            logger.error(f"写入 CSV 失败: {e}")
            raise

    def read_all(self) -> List[Dict[str, Any]]:
        """读取所有数据"""
        try:
            if not self.exists():
                return []

            with open(self.file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                return list(reader)

        except Exception as e:
            logger.error(f"读取 CSV 失败: {e}")
            raise

    def read_last(self) -> Optional[Dict[str, Any]]:
        """读取最后一行数据"""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                return rows[-1] if rows else None

        except Exception as e:
            logger.error(f"读取 CSV 最后一行失败: {e}")
            raise

    def count(self) -> int:
        """统计记录数"""
        try:
            if not self.exists():
                return 0

            with open(self.file_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                # 去掉表头
                next(reader, None)
                return sum(1 for _ in reader)

        except Exception as e:
            logger.error(f"统计 CSV 记录数失败: {e}")
            raise

    def delete(self):
        """删除文件"""
        if self.exists():
            self.file_path.unlink()
            logger.info(f"已删除文件: {self.file_path}")


class PriceHistoryStorage(CSVStorage):
    """价格历史数据存储"""

    def __init__(self):
        super().__init__(CSV_FILES['price_history'])

    def add_price_record(self, etf_code: str, etf_name: str, price: float) -> Dict[str, Any]:
        """
        添加价格记录

        参数:
            etf_code: ETF 代码
            etf_name: ETF 名称
            price: 价格

        返回:
            添加的记录
        """
        record = {
            'id': self.count() + 1,
            'etf_code': etf_code,
            'etf_name': etf_name,
            'price': round(price, 2),
            'record_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        fieldnames = ['id', 'etf_code', 'etf_name', 'price', 'record_time', 'created_at']
        self.append(record, fieldnames)

        logger.info(f"添加价格记录: {etf_code} - {price}元")
        return record

    def get_latest_price(self) -> Optional[float]:
        """获取最新价格"""
        last_record = self.read_last()
        if last_record and 'price' in last_record:
            return float(last_record['price'])
        return None

    def get_history(self, days: int = 7) -> List[Dict[str, Any]]:
        """
        获取最近几天的历史数据

        参数:
            days: 天数

        返回:
            历史记录列表
        """
        all_records = self.read_all()
        if not all_records:
            return []

        # 按时间倒序排列
        all_records.sort(key=lambda x: x['record_time'], reverse=True)

        # 截取指定天数的数据
        return all_records[:days * 24]  # 假设每小时一条数据


class UserTransactionStorage(CSVStorage):
    """用户交易记录存储"""

    def __init__(self):
        super().__init__(CSV_FILES['user_transactions'])

    def add_transaction(self, etf_code: str, price: float, quantity: int,
                       transaction_type: str = 'buy', notes: str = '') -> int:
        """
        添加交易记录

        参数:
            etf_code: ETF 代码
            price: 交易价格
            quantity: 交易数量
            transaction_type: 交易类型（buy/sell）
            notes: 备注

        返回:
            交易记录 ID
        """
        transaction_id = self.count() + 1

        record = {
            'id': transaction_id,
            'etf_code': etf_code,
            'transaction_price': round(price, 2),
            'transaction_quantity': quantity,
            'transaction_type': transaction_type,
            'transaction_date': datetime.now().strftime('%Y-%m-%d'),
            'is_alert_enabled': 'true',
            'notes': notes,
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        fieldnames = [
            'id', 'etf_code', 'transaction_price', 'transaction_quantity',
            'transaction_type', 'transaction_date', 'is_alert_enabled', 'notes', 'created_at'
        ]

        self.append(record, fieldnames)
        logger.info(f"添加交易记录: {transaction_id} - {transaction_type} {price}元 × {quantity}份")

        return transaction_id

    def get_latest_transaction(self) -> Optional[Dict[str, Any]]:
        """获取最近一笔交易记录"""
        return self.read_last()


class AlertStatusStorage(CSVStorage):
    """提醒状态存储"""

    def __init__(self):
        super().__init__(CSV_FILES['alert_status'])

    def get_status(self, transaction_id: int) -> Optional[Dict[str, Any]]:
        """
        获取交易记录的状态

        参数:
            transaction_id: 交易记录 ID

        返回:
            状态数据或 None
        """
        records = self.read_all()

        # 查找该交易 ID 的最新状态
        transaction_records = [r for r in records if int(r['transaction_id']) == transaction_id]
        if not transaction_records:
            return None

        # 按更新时间倒序，取最新的一条
        transaction_records.sort(key=lambda x: x['updated_at'], reverse=True)
        latest = transaction_records[0]

        return {
            'last_price': float(latest['last_price']),
            'in_range': latest['in_range'].lower() == 'true',
            'range_type': latest['range_type'] if latest['range_type'] else None,
            'last_check_time': latest['last_check_time']
        }

    def update_status(self, transaction_id: int, last_price: float, in_range: bool, range_type: str = None):
        """
        更新状态记录

        参数:
            transaction_id: 交易记录 ID
            last_price: 上次分析时的价格
            in_range: 是否在区间内
            range_type: 区间类型
        """
        record = {
            'id': self.count() + 1,
            'transaction_id': transaction_id,
            'etf_code': ETF_CODE,  # 假设使用全局配置
            'last_price': round(last_price, 2),
            'in_range': str(in_range).lower(),
            'range_type': range_type if range_type else '',
            'last_check_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        fieldnames = [
            'id', 'transaction_id', 'etf_code', 'last_price', 'in_range',
            'range_type', 'last_check_time', 'updated_at'
        ]

        self.append(record, fieldnames)


class AlertHistoryStorage(CSVStorage):
    """提醒历史记录存储"""

    def __init__(self):
        super().__init__(CSV_FILES['alert_history'])

    def add_alert(self, transaction_id: int, alert_type: str, current_price: float, target_price: float):
        """
        添加提醒记录

        参数:
            transaction_id: 交易记录 ID
            alert_type: 提醒类型（[±3%~±5%]）
            current_price: 当前价格
            target_price: 目标价格（交易价格）
        """
        record = {
            'id': self.count() + 1,
            'transaction_id': transaction_id,
            'alert_type': alert_type,
            'current_price': round(current_price, 2),
            'target_price': round(target_price, 2),
            'status': 'triggered',
            'triggered_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        fieldnames = ['id', 'transaction_id', 'alert_type', 'current_price', 'target_price', 'status', 'triggered_at']
        self.append(record, fieldnames)

        logger.info(f"添加提醒记录: {alert_type} - 当前价: {current_price}元")


# 初始化全局存储实例
from config.app import ETF_CONFIG
ETF_CODE = ETF_CONFIG['code']
ETF_NAME = ETF_CONFIG['name']

price_storage = PriceHistoryStorage()
transaction_storage = UserTransactionStorage()
alert_status_storage = AlertStatusStorage()
alert_history_storage = AlertHistoryStorage()

__all__ = [
    'price_storage',
    'transaction_storage',
    'alert_status_storage',
    'alert_history_storage',
    'CSVStorage'
]
