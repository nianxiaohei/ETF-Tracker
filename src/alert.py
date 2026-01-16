"""
提醒管理模块
实现提醒去重记录和历史管理
"""
from typing import Dict, Optional
from src.logger import logger
from src.storage import alert_status_storage, alert_history_storage
from src.calculator import check_date_range


def check_alert_status(current_price: float, transaction_price: float, transaction_id: int) -> Dict[str, any]:
    """
    判断当前价格是否落在关键区间（基于上次交易价格），并实现提醒去重

    参数:
        current_price: 当前价格
        transaction_price: 上次交易价格
        transaction_id: 交易记录 ID

    返回:
        dict: 包含区间判断结果和是否需要提醒
    """
    # 1. 判断当前价格是否在区间内（区间基于上次交易价格计算）
    range_result = check_date_range(current_price, transaction_price)
    in_range = range_result['in_range']
    matched_range = range_result['matched_range']

    # 2. 读取上次的状态
    last_status = get_alert_status(transaction_id)

    # 3. 判断是否需要提醒（去重逻辑）
    should_alert = False
    alert_reason = None

    if in_range:
        if last_status is None:
            # 首次检查，在区间内，需要提醒
            should_alert = True
            alert_reason = '首次进入区间'
        elif not last_status['in_range']:
            # 上次不在区间，现在在区间，状态变化，需要提醒
            should_alert = True
            alert_reason = '从区间外进入区间'
        elif last_status['range_type'] != matched_range:
            # 上次在不同区间，现在换到新区间，需要提醒
            should_alert = True
            alert_reason = '切换到新区间'
        # else: 上次就在同一区间，不提醒

    # 4. 更新状态记录
    update_alert_status(
        transaction_id=transaction_id,
        last_price=current_price,
        in_range=in_range,
        range_type=matched_range
    )

    # 5. 如果需要提醒，记录提醒历史
    if should_alert:
        create_alert_history(
            transaction_id=transaction_id,
            alert_type=matched_range,
            current_price=current_price,
            target_price=transaction_price
        )

    return {
        'in_range': in_range,
        'matched_range': matched_range,
        'should_alert': should_alert,
        'alert_reason': alert_reason,
        'levels': range_result['levels'],
        'current_change': range_result['current_change']
    }


def get_alert_status(transaction_id: int) -> Optional[Dict[str, any]]:
    """
    获取上次的提醒状态

    参数:
        transaction_id: 交易记录 ID

    返回:
        dict 或 None: 状态数据
    """
    try:
        status_data = alert_status_storage.get_status(transaction_id)
        return status_data
    except Exception as e:
        logger.error(f"获取提醒状态失败: {e}")
        return None


def update_alert_status(transaction_id: int, last_price: float, in_range: bool, range_type: str = None):
    """
    更新提醒状态记录

    参数:
        transaction_id: 交易记录 ID
        last_price: 上次分析时的价格
        in_range: 是否在区间内
        range_type: 区间类型
    """
    try:
        alert_status_storage.update_status(
            transaction_id=transaction_id,
            last_price=last_price,
            in_range=in_range,
            range_type=range_type
        )
        logger.debug(f"更新提醒状态: transaction_id={transaction_id}, in_range={in_range}")
    except Exception as e:
        logger.error(f"更新提醒状态失败: {e}")
        raise


def create_alert_history(transaction_id: int, alert_type: str, current_price: float, target_price: float):
    """
    创建提醒历史记录

    参数:
        transaction_id: 交易记录 ID
        alert_type: 提醒类型
        current_price: 当前价格
        target_price: 目标价格
    """
    try:
        alert_history_storage.add_alert(
            transaction_id=transaction_id,
            alert_type=alert_type,
            current_price=current_price,
            target_price=target_price
        )
    except Exception as e:
        logger.error(f"创建提醒历史记录失败: {e}")
        raise


def test_alert_system():
    """测试提醒系统"""
    print("\n测试提醒系统...")

    transaction_price = 2.08
    transaction_id = 1
    quantity = 10000

    print("\n测试场景 1：首次进入 [+3% ~ +5%] 区间")
    current_price = 2.15
    result = check_alert_status(current_price, transaction_price, transaction_id)
    print(f"  当前价格: {current_price} 元")
    print(f"  上次交易价格: {transaction_price} 元")
    print(f"  是否在区间: {result['in_range']}")
    print(f"  所在区间: {result['matched_range']}")
    print(f"  是否需要提醒: {result['should_alert']}")
    if result['should_alert']:
        print(f"  提醒原因: {result['alert_reason']}")

    print("\n测试场景 2：继续在同区间内（不应提醒）")
    current_price = 2.16
    result = check_alert_status(current_price, transaction_price, transaction_id)
    print(f"  当前价格: {current_price} 元")
    print(f"  是否需要提醒: {result['should_alert']}")

    print("\n测试场景 3：离开区间（不应提醒）")
    current_price = 2.20
    result = check_alert_status(current_price, transaction_price, transaction_id)
    print(f"  当前价格: {current_price} 元")
    print(f"  是否在区间: {result['in_range']}")
    print(f"  是否需要提醒: {result['should_alert']}")

    print("\n测试场景 4：重新进入区间（应再次提醒）")
    current_price = 2.15
    result = check_alert_status(current_price, transaction_price, transaction_id)
    print(f"  当前价格: {current_price} 元")
    print(f"  是否在区间: {result['in_range']}")
    print(f"  是否需要提醒: {result['should_alert']}")
    if result['should_alert']:
        print(f"  提醒原因: {result['alert_reason']}")

    print("\n✓ 提醒系统测试完成")


if __name__ == '__main__':
    test_alert_system()
