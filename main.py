"""
ETF 价格跟踪系统 - 主程序
交互式菜单版本，支持16只ETF同时监控
"""
import time
import sys
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box
from rich.live import Live
from typing import Dict, Optional, List

from src.logger import logger
from src.crawler import XueqiuCrawler
from src.storage import etf_transaction_storage
from config.app import ETF_CONFIG
from src.calculator import calculate_profit_loss_with_current
# 初始化
console = Console()


def print_banner():
    """打印欢迎横幅"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║        ETF 价格跟踪与交易提醒系统                            ║
║              支持16只ETF同时监控                             ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"""
    console.print(f"[bold cyan]{banner}[/bold cyan]")


def print_menu():
    """打印主菜单"""
    menu = """
┌─────────────────────────────────────────────────────────────┐
│  请选择功能：                                                │
│                                                             │
│  [bold cyan]1.[/bold cyan] ETF最新价                                      │
│     每隔1秒抓取16只ETF的最新价格                            │
│                                                             │
│  [bold cyan]2.[/bold cyan] 更新上次交易价格和数量                            │
│     更新任意ETF的上次交易价格和数量                         │
│                                                             │
│  [bold cyan]3.[/bold cyan] 交易信号                                      │
│     分析所有ETF的价格涨跌幅并提示交易信号                   │
│                                                             │
│  [bold cyan]0.[/bold cyan] 退出程序                                      │
└─────────────────────────────────────────────────────────────┘
"""
    console.print(menu)


def fetch_latest_prices():
    """
    选项1：连续抓取16只ETF的最新价格
    每隔1秒刷新一次
    """
    console.print("\n[bold yellow]开始实时监控ETF价格（按Ctrl+C停止）[/bold yellow]\n")

    crawler = XueqiuCrawler()

    try:
        with Live(console=console, refresh_per_second=1) as live:
            while True:
                # 创建表格
                table = Table(box=box.ROUNDED, show_lines=False)
                table.add_column("#", style="cyan", justify="right", width=3)
                table.add_column("ETF代码", style="yellow", width=10)
                table.add_column("ETF名称", style="blue", width=20)
                table.add_column("最新价格", style="green", justify="right", width=10)
                table.add_column("更新时间", style="dim", width=20)

                # 依次抓取16只ETF价格
                for idx, (etf_code, etf_info) in enumerate(ETF_CONFIG.items(), 1):
                    try:
                        result = crawler.fetch_price_sync(etf_code)
                        if result:
                            price, name = result
                            table.add_row(
                                str(idx),
                                etf_code,
                                name,
                                f"[bold]{price:.3f}[/bold] 元",
                                time.strftime('%H:%M:%S')
                            )
                        else:
                            table.add_row(
                                str(idx),
                                etf_code,
                                etf_info['name'],
                                "[red]获取失败[/red]",
                                time.strftime('%H:%M:%S')
                            )
                    except Exception as e:
                        table.add_row(
                            str(idx),
                            etf_code,
                            etf_info['name'],
                            "[red]错误[/red]",
                            time.strftime('%H:%M:%S')
                        )
                        logger.error(f"获取{etf_code}价格失败: {e}")

                    # 短暂延迟，避免请求过快
                    time.sleep(0.1)

                live.update(Panel(
                    table,
                    title=f"[bold]ETF价格实时监控[/bold] | 更新时间: {time.strftime('%Y-%m-%d %H:%M:%S')}",
                    box=box.ROUNDED
                ))

                # 等待1秒后刷新
                time.sleep(1)

    except KeyboardInterrupt:
        console.print("\n[yellow]已停止实时监控[/yellow]\n")


def update_transaction_data():
    """
    选项2：更新上次交易价格和数量
    显示所有ETF，询问哪只需要更新
    """
    console.print("\n[bold yellow]更新ETF上次交易数据[/bold yellow]\n")

    # 显示所有ETF列表
    table = Table(box=box.ROUNDED)
    table.add_column("编号", style="cyan")
    table.add_column("ETF代码", style="yellow")
    table.add_column("ETF名称", style="blue")
    table.add_column("上次交易价", style="green")
    table.add_column("交易数量", style="magenta")

    current_data = etf_transaction_storage.get_all_etf_transactions()

    for idx, (etf_code, etf_info) in enumerate(ETF_CONFIG.items(), 1):
        if etf_code in current_data:
            data = current_data[etf_code]
            table.add_row(
                str(idx),
                etf_code,
                etf_info['name'],
                f"{data['price']:.3f} 元",
                f"{data['quantity']:,} 份"
            )
        else:
            table.add_row(
                str(idx),
                etf_code,
                etf_info['name'],
                "[dim]未设置[/dim]",
                "[dim]未设置[/dim]"
            )

    console.print(table)

    # 询问哪只ETF需要更新
    choice = input("\n请选择要更新的ETF编号（1-16），或按回车返回菜单: ").strip()

    if not choice:
        console.print("[yellow]返回主菜单[/yellow]\n")
        return

    try:
        idx = int(choice) - 1
        if 0 <= idx < len(ETF_CONFIG):
            etf_code = list(ETF_CONFIG.keys())[idx]
            etf_name = ETF_CONFIG[etf_code]['name']

            console.print(f"\n[bold]正在更新: {etf_code} - {etf_name}[/bold]\n")

            # 输入价格
            price = float(input("请输入上次交易价格（元）: ").strip())

            # 输入数量
            quantity = int(input("请输入交易数量（份）: ").strip())

            # 保存数据
            etf_transaction_storage.save_etf_transaction(etf_code, price, quantity)

            console.print(f"\n[green]✓[/green] 已更新 {etf_name} 的数据:")
            console.print(f"  上次交易价格: {price:.3f} 元")
            console.print(f"  交易数量: {quantity:,} 份\n")

        else:
            console.print("[red]编号超出范围[/red]\n")
    except ValueError:
        console.print("[red]请输入有效的数字[/red]\n")


def analyze_trading_signals():
    """
    选项3：交易信号分析
    分析每只ETF的价格涨跌幅，与±3%、±5%、±10%比较
    重点提示超过±3%的ETF
    """
    console.print("\n[bold yellow]分析交易信号[/bold yellow]\n")

    # 获取所有ETF的交易数据
    transaction_data = etf_transaction_storage.get_all_etf_transactions()

    if not transaction_data:
        console.print("[red]暂无ETF交易数据，请先更新交易数据[/red]\n")
        return

    # 抓取所有ETF的当前价格
    crawler = XueqiuCrawler()
    current_prices = {}

    console.print("[cyan]正在抓取ETF最新价格...[/cyan]")
    progress = console.status("抓取中...")
    progress.start()

    for etf_code, etf_info in ETF_CONFIG.items():
        try:
            result = crawler.fetch_price_sync(etf_code)
            if result:
                price, name = result
                current_prices[etf_code] = {
                    'price': price,
                    'name': name
                }
        except Exception as e:
            logger.error(f"获取{etf_code}价格失败: {e}")

        time.sleep(0.1)  # 避免请求过快

    progress.stop()

    # 分析结果表格
    table = Table(box=box.ROUNDED)
    table.add_column("ETF代码", style="cyan")
    table.add_column("ETF名称", style="blue")
    table.add_column("上次交易价", style="yellow")
    table.add_column("最新价", style="green")
    table.add_column("涨跌幅", style="magenta")
    table.add_column("接近目标", style="red")

    # 重点提示的ETF
    alert_list = []

    # 检查每组ETF
    for etf_code, data in transaction_data.items():
        if etf_code not in current_prices:
            continue

        etf_info = ETF_CONFIG[etf_code]
        current_data = current_prices[etf_code]

        # 计算涨跌幅
        change_rate = ((current_data['price'] - data['price']) / data['price']) * 100

        # 检查接近哪些目标价位
        targets = [-10, -5, -3, 3, 5, 10]
        closest_target = None
        distance = 999

        for target in targets:
            target_price = data['price'] * (1 + target / 100)
            current_distance = abs(current_data['price'] - target_price)
            if current_distance < distance:
                distance = current_distance
                closest_target = target

        # 格式化涨跌幅
        if change_rate >= 0:
            change_str = f"[green]↑ {change_rate:.2f}%[/green]"
        else:
            change_str = f"[red]↓ {abs(change_rate):.2f}%[/red]"

        # 高亮超过±3%的ETF
        if abs(change_rate) >= 3:
            etf_code_str = f"[bold red]{etf_code}[/bold red]"
            name_str = f"[bold]{etf_info['name']}[/bold]"
            alert_list.append({
                'code': etf_code,
                'name': etf_info['name'],
                'last_price': data['price'],
                'current_price': current_data['price'],
                'change_rate': change_rate,
                'quantity': data['quantity'],
                'last_amount': data['price'] * data['quantity'],
                'current_amount': current_data['price'] * data['quantity']
            })
        else:
            etf_code_str = etf_code
            name_str = etf_info['name']

        target_text = f"{closest_target:+.0f}% ({data['price'] * (1 + closest_target / 100):.3f})"

        table.add_row(
            etf_code_str,
            name_str,
            f"{data['price']:.3f} 元",
            f"{current_data['price']:.3f} 元",
            change_str,
            target_text
        )

    console.print(table)

    # 显示重点提示
    if alert_list:
        console.print("\n" + "=" * 80)
        console.print("[bold red]⏰ 重点交易信号（涨跌幅超过±3%）[/bold red]")
        console.print("=" * 80 + "\n")

        for alert in alert_list:
            change_color = "green" if alert['change_rate'] >= 0 else "red"
            change_symbol = "↑" if alert['change_rate'] >= 0 else "↓"

            console.print(Panel(
                f"[bold]{alert['name']} ({alert['code']})[/bold]\n\n"
                f"上次交易: {alert['last_price']:.3f} 元 × {alert['quantity']:,} 份 = {alert['last_amount']:,.2f} 元\n"
                f"最新价格: {alert['current_price']:.3f} 元 × {alert['quantity']:,} 份 = {alert['current_amount']:,.2f} 元\n\n"
                f"总盈亏: {'+' if alert['change_rate'] >= 0 else ''}{alert['current_amount'] - alert['last_amount']:,.2f} 元\n"
                f"涨跌幅: [{change_color}]{change_symbol} {abs(alert['change_rate']):.2f}%[/{change_color}]",
                title=f"{change_symbol} {abs(alert['change_rate']):.2f}%",
                style=change_color,
                box=box.ROUNDED
            ))

            # 操作建议
            if alert['change_rate'] >= 3:
                console.print(f"[bold yellow]📈 操作建议: 涨幅较大，可考虑止盈[/bold yellow]\n")
            elif alert['change_rate'] <= -3:
                console.print(f"[bold yellow]📉 操作建议: 跌幅较大，建议密切关注[/bold yellow]\n")

    else:
        console.print("\n[blue]ℹ️  暂无任何ETF涨跌幅超过±3%[/blue]\n")

    console.print("\n" + "─" * 80)
    console.print("[dim]备注：本工具仅供参考，不构成投资建议。投资有风险，入市需谨慎。[/dim]")
    console.print("─" * 80 + "\n")


def main():
    """
    主程序入口
    交互式菜单系统
    """
    print_banner()

    while True:
        print_menu()

        choice = input("请输入选项编号（0-3）: ").strip()

        if choice == '1':
            fetch_latest_prices()
        elif choice == '2':
            update_transaction_data()
        elif choice == '3':
            analyze_trading_signals()
        elif choice == '0':
            console.print("\n[yellow]感谢使用，再见！[/yellow]\n")
            sys.exit(0)
        else:
            console.print("[red]无效选项，请重新输入[/red]\n")

        input("\n按回车键继续...")


if __name__ == '__main__':
    main()
