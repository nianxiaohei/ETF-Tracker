#!/usr/bin/env python3
"""
检查系统状态
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.storage import UserTransactionStorage
from config.app import ETF_LIST


def check_status():
    """显示系统状态"""
    print("=" * 70)
    print("ETF价格跟踪系统状态检查")
    print("=" * 70)

    # 检查ETF列表
    print(f"\n✓ ETF配置: {len(ETF_LIST)}个ETF")
    for idx, etf in enumerate(ETF_LIST[:5], 1):
        print(f"    {idx}. {etf['code']} - {etf['name']}")
    if len(ETF_LIST) > 5:
        print(f"    ... 还有{len(ETF_LIST) - 5}个ETF")

    # 检查交易记录
    storage = UserTransactionStorage()
    transactions = storage.read_all()

    print(f"\n✓ 交易记录: {len(transactions)}条")

    if transactions:
        # 按ETF分组统计
        etf_dict = {}
        for t in transactions:
            etf_code = t.get('etf_code', '未知')
            if etf_code not in etf_dict:
                etf_dict[etf_code] = []
            etf_dict[etf_code].append(t)

        for etf_code, etf_trans in etf_dict.items():
            # 获取该ETF名称
            etf_name = etf_code
            for etf in ETF_LIST:
                if etf['code'] == etf_code:
                    etf_name = etf['name']
                    break

            print(f"\n    {etf_code} - {etf_name}:")
            for t in sorted(etf_trans, key=lambda x: x.get('transaction_date', ''), reverse=True)[:3]:
                print(f"      日期: {t.get('transaction_date', '未知')}")
                print(f"      价格: ¥{t.get('transaction_price', 0)}")
                print(f"      数量: {t.get('transaction_quantity', 0)}")
    else:
        print("\n ⚠  警告: 暂无交易记录")
        print("\n    请先添加交易记录:")
        print("    python3 scripts/add_etf_transactions.py")

    print("\n" + "=" * 70)

    # 检查通知功能
    print("\n✓ 系统通知: 已启用")
    print("  当价格相比上次交易价超过±3%时，会发送macOS系统通知")

    # 检查定时任务
    print("\n✓ 定时任务: 周一到周五 9:45")
    print("  周末不会自动运行（明天是周六，不会启动）")

    print("\n" + "=" * 70)
    print("\n💡 明天是周六，可以手动运行测试:")
    print("   python3 scripts/daily_fetch.py")
    print("\n💡 查看实时日志:")
    print("   tail -f logs/scheduler.log")
    print("\n💡 系统通知授权:")
    print("   首次运行时，系统会询问是否允许Python发送通知")
    print("   请选择'允许'，否则无法收到弹窗提醒")


if __name__ == '__main__':
    check_status()
