"""
计算模块
价格计算和盈亏计算
"""
from typing import Dict, List, Optional
from src.logger import logger
from config.app import PRICE_CALCULATION


def calculate_price_levels(transaction_price: float, precision: int = None) -> Dict[str, float]:
    """
    计算关键价格水平（基于上次交易价格）

    参数:
        transaction_price: 上次交易价格
        precision: 计算精度（默认为内部配置4位小数）

    返回:
        dict: 各涨跌幅对应的目标价（使用高精度，用于计算）
    """
    if precision is None:
        precision = PRICE_CALCULATION['calculation_precision']

    return {
        '+10%': round(transaction_price * 1.10, precision),
        '+5%': round(transaction_price * 1.05, precision),
        '+3%': round(transaction_price * 1.03, precision),
        '-3%': round(transaction_price * 0.97, precision),
        '-5%': round(transaction_price * 0.95, precision),
        '-10%': round(transaction_price * 0.90, precision)
    }


def format_price_for_display(price: float, precision: int = None) -> float:
    """
    格式化价格用于显示（保留2位小数）

    参数:
        price: 价格值
        precision: 显示精度（默认为2位小数）

    返回:
        float: 格式化后的价格
    """
    if precision is None:
        precision = PRICE_CALCULATION['display_precision']

    return round(price, precision)


def check_date_range(current_price: float, transaction_price: float) -> Dict[str, any]:
    """
    判断当前价格是否落在关键区间（基于上次交易价格计算的区间）

    参数:
        current_price: 当前价格
        transaction_price: 上次交易价格

    返回:
        dict: 包含区间判断结果
    """
    levels = calculate_price_levels(transaction_price)

    results = {
        'levels': levels,
        'in_range': False,
        'matched_range': None,
        'current_change': round(((current_price - transaction_price) / transaction_price * 100), 2)
    }

    # 判断当前价格是否在 +3% 到 +5% 区间（基于上次交易价格计算）
    if levels['+3%'] <= current_price <= levels['+5%']:
        results['in_range'] = True
        results['matched_range'] = '[+3% ~ +5%]'

    # 判断当前价格是否在 -5% 到 -3% 区间（基于上次交易价格计算）
    elif levels['-5%'] <= current_price <= levels['-3%']:
        results['in_range'] = True
        results['matched_range'] = '[-5% ~ -3%]'

    return results


def calculate_profit_loss(transaction_price: float, quantity: int) -> Dict[str, any]:
    """
    计算在不同涨跌幅价位下的盈亏（基于上次交易价格）

    参数:
        transaction_price: 上次交易价格
        quantity: 交易数量（份）

    返回:
        dict: 各涨跌幅价位下的盈亏情况
    """
    # 计算上次交易金额
    last_amount = transaction_price * quantity

    # 计算各涨跌幅对应的目标价（使用高精度，4位小数）
    levels = calculate_price_levels(transaction_price)

    results = {
        'last_transaction': {
            'price': transaction_price,
            'quantity': quantity,
            'amount': round(last_amount, 2)
        }
    }

    # 计算各价位下的盈亏（使用高精度的目标价）
    for label, target_price_precise in levels.items():
        # 使用高精度价格计算盈亏
        target_amount = target_price_precise * quantity
        profit_amount = target_amount - last_amount
        profit_percentage = (profit_amount / last_amount) * 100

        results[label] = {
            'price_precise': target_price_precise,  # 高精度值（用于计算）
            'price': format_price_for_display(target_price_precise, 2),  # 显示值（2位小数）
            'amount': round(target_amount, 2),
            'profit_amount': round(profit_amount, 2),
            'profit_percentage': round(profit_percentage, 2)
        }

    return results


def calculate_profit_loss_with_current(current_price: float, transaction_price: float, quantity: int) -> Dict[str, any]:
    """
    计算盈亏，包括当前价格的情况

    参数:
        current_price: 当前价格
        transaction_price: 上次交易价格
        quantity: 交易数量

    返回:
        dict: 包含当前价格和各涨跌幅价位的盈亏情况
    """
    # 先计算各涨跌幅的盈亏
    results = calculate_profit_loss(transaction_price, quantity)

    # 添加当前价格的盈亏计算
    last_amount = transaction_price * quantity
    current_amount = current_price * quantity
    profit_amount = current_amount - last_amount
    profit_percentage = (profit_amount / last_amount) * 100

    results['current'] = {
        'price': format_price_for_display(current_price, 2),
        'amount': round(current_amount, 2),
        'profit_amount': round(profit_amount, 2),
        'profit_percentage': round(profit_percentage, 2)
    }

    return results


def test_calculator():
    """测试计算器"""
    print("\n测试价格计算器...")

    transaction_price = 2.08
    quantity = 10000

    # 测试价格计算
    print("\n1. 关键价位计算（基于上次交易价格 2.08 元）：")
    levels = calculate_price_levels(transaction_price)
    for label, price in levels.items():
        print(f"  {label}: {price}元 (显示值: {format_price_for_display(price)})")

    # 测试盈亏计算
    print("\n2. 盈亏计算（上次交易 2.08 元 × 10,000 份 = 20,800 元）：")
    results = calculate_profit_loss(transaction_price, quantity)
    print(f"  上次交易金额: {results['last_transaction']['amount']} 元")
    for label in ['+10%', '+5%', '+3%', '-3%', '-5%', '-10%']:
        data = results[label]
        print(f"  {label} ({data['price']}元): 交易金额={data['amount']}元, 盈亏={data['profit_amount']}元, 盈亏率={data['profit_percentage']}%")

    # 测试区间判断
    print("\n3. 区间判断测试（当前价 2.15 元）：")
    current_price = 2.15
    range_result = check_date_range(current_price, transaction_price)
    print(f"  当前比上次交易涨跌: {range_result['current_change']}%")
    print(f"  是否在区间内: {range_result['in_range']}")
    if range_result['in_range']:
        print(f"  所在区间: {range_result['matched_range']}")

    print("\n✓ 计算器测试完成")


if __name__ == '__main__':
    test_calculator()
