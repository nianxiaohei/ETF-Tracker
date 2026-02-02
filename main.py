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
from typing import Dict, List

from src.logger import logger
from src.crawler import XueqiuCrawler
from src.storage import etf_transaction_storage, etf_list_storage
from config.app import ETF_CONFIG
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
│  请选择功能：                                               │
│                                                             │
│  [bold cyan]1.[/bold cyan] 更新上次交易价格和数量                            │
│     更新任意ETF的上次交易价格和数量                         │
│                                                             │
│  [bold cyan]2.[/bold cyan] 交易信号                                          │
│     分析所有ETF的价格涨跌幅并提示交易信号                   │
│                                                             │
│  [bold cyan]3.[/bold cyan] 更新观察列表                                      │
│     添加新的ETF或删除列表中的ETF                            │
│                                                             │
│  [bold cyan]0.[/bold cyan] 退出程序                                          │
└─────────────────────────────────────────────────────────────┘
"""
    console.print(menu)


def fetch_latest_prices():
    """
    选项1：抓取16只ETF的最新价格（一次性）
    """
    console.print("\n[bold yellow]正在抓取16只ETF最新价格...[/bold yellow]\n")

    crawler = XueqiuCrawler()

    # 创建表格
    table = Table(box=box.ROUNDED, show_lines=False)
    table.add_column("#", style="cyan", justify="right", width=3)
    table.add_column("ETF代码", style="yellow", width=12)
    table.add_column("ETF名称", style="blue", width=22)
    table.add_column("最新价格", style="green", justify="right", width=12)

    # 依次抓取16只ETF价格
    with console.status("正在抓取价格数据...", spinner="dots"):
        for idx, (etf_code, etf_info) in enumerate(ETF_CONFIG.items(), 1):
            try:
                result = crawler.fetch_price_sync(etf_code)
                if result:
                    price, name = result
                    table.add_row(
                        str(idx),
                        etf_code,
                        name,
                        f"[bold]{price:.3f}[/bold] 元"
                    )
                else:
                    table.add_row(
                        str(idx),
                        etf_code,
                        etf_info['name'],
                        "[red]获取失败[/red]"
                    )
            except Exception as e:
                table.add_row(
                    str(idx),
                    etf_code,
                    etf_info['name'],
                    "[red]错误[/red]"
                )
                logger.error(f"获取{etf_code}价格失败: {e}")

            # 短暂延迟，避免请求过快
            time.sleep(0.1)

    # 显示结果
    console.print(Panel(
        table,
        title=f"[bold]ETF最新价格[/bold] | 更新时间: {time.strftime('%Y-%m-%d %H:%M:%S')}",
        box=box.ROUNDED
    ))

    console.print("\n[green]✓[/green] 价格抓取完成\n")


def update_transaction_data():
    """
    选项1：更新上次交易价格和数量
    显示所有ETF，询问哪只需要更新（包括没有交易数据的ETF，显示为"--"）
    """
    console.print("\n[bold yellow]更新ETF上次交易数据[/bold yellow]\n")

    # 获取动态的ETF列表
    etf_list = etf_list_storage.get_all_etfs()

    # 显示所有ETF列表
    table = Table(box=box.ROUNDED)
    table.add_column("编号", style="cyan")
    table.add_column("ETF代码", style="yellow")
    table.add_column("ETF名称", style="blue")
    table.add_column("上次交易价", style="green")
    table.add_column("交易数量", style="magenta")

    current_data = etf_transaction_storage.get_all_etf_transactions()

    for idx, (etf_code, etf_info) in enumerate(etf_list.items(), 1):
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
                "[dim]--[/dim]",
                "[dim]--[/dim]"
            )

    console.print(table)

    # 询问哪只ETF需要更新
    etf_count = len(etf_list)
    choice = input(f"\n请选择要更新的ETF编号（1-{etf_count}），或按回车返回菜单: ").strip()

    if not choice:
        console.print("[yellow]返回主菜单[/yellow]\n")
        return

    try:
        idx = int(choice) - 1
        if 0 <= idx < etf_count:
            etf_code = list(etf_list.keys())[idx]
            etf_name = etf_list[etf_code]['name']

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
    选项2：交易信号分析
    分析每只ETF的价格涨跌幅，与±3%、±5%、±10%比较
    重点提示超过±3%的ETF
    支持显示没有交易数据的ETF（显示为"--"）
    """
    console.print("\n[bold yellow]分析交易信号[/bold yellow]\n")

    # 获取动态的ETF列表
    etf_list = etf_list_storage.get_all_etfs()

    # 获取所有ETF的交易数据
    transaction_data = etf_transaction_storage.get_all_etf_transactions()

    # 抓取所有ETF的当前价格
    crawler = XueqiuCrawler()
    current_prices = {}

    console.print("[cyan]正在抓取ETF最新价格...[/cyan]")
    progress = console.status("抓取中...")
    progress.start()

    for etf_code, etf_info in etf_list.items():
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
    table.add_column("ETF名称")  # 白色文字（默认样式）
    table.add_column("上次交易价", style="yellow")
    table.add_column("最新价")  # 动态颜色（绿色/红色）
    table.add_column("涨跌幅", style="magenta")
    table.add_column("接近目标", style="red")

    # 重点提示的ETF
    alert_list = []

    # 收集所有需要显示的ETF数据，并计算涨跌幅
    etf_display_list = []

    for etf_code, etf_info in etf_list.items():
        if etf_code not in current_prices:
            continue

        current_data = current_prices[etf_code]

        # 检查是否有交易数据
        if etf_code in transaction_data:
            # 有交易数据，计算涨跌幅
            data = transaction_data[etf_code]
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

            # 添加到显示列表
            etf_display_list.append({
                'etf_code': etf_code,
                'etf_info': etf_info,
                'has_transaction': True,
                'data': data,
                'current_data': current_data,
                'change_rate': change_rate,
                'closest_target': closest_target
            })

            # 如果涨跌幅超过±3%，添加到提醒列表
            if abs(change_rate) >= 3:
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
            # 没有交易数据
            etf_display_list.append({
                'etf_code': etf_code,
                'etf_info': etf_info,
                'has_transaction': False,
                'current_data': current_data
            })

    # 按照涨跌幅排序（优先有交易数据的，按change_rate升序排列）
    # 有交易数据的排在前面，没有交易数据的排在后面
    etf_display_list.sort(key=lambda x: x.get('change_rate', float('inf')))

    # 按排序后的顺序添加到表格
    for item in etf_display_list:
        etf_code = item['etf_code']
        etf_info = item['etf_info']

        if item['has_transaction']:
            # 有交易数据
            data = item['data']
            current_data = item['current_data']
            change_rate = item['change_rate']
            closest_target = item['closest_target']

            # 格式化涨跌幅
            if change_rate >= 0:
                change_str = f"[green]↑ {change_rate:.2f}%[/green]"
            else:
                change_str = f"[red]↓ {abs(change_rate):.2f}%[/red]"

            # 根据涨跌设置最新价颜色
            if change_rate >= 0:
                current_price_str = f"[green]{current_data['price']:.3f} 元[/green]"
            else:
                current_price_str = f"[red]{current_data['price']:.3f} 元[/red]"

            # 高亮超过±3%的ETF
            if abs(change_rate) >= 3:
                etf_code_str = f"[bold red]{etf_code}[/bold red]"
                name_str = etf_info['name']
                target_text = f"{closest_target:+.0f}% ({data['price'] * (1 + closest_target / 100):.3f})"
            else:
                etf_code_str = etf_code
                name_str = etf_info['name']
                target_text = "--"  # 涨跌幅小于±3%的显示--

            table.add_row(
                etf_code_str,
                name_str,
                f"{data['price']:.3f} 元",
                current_price_str,
                change_str,
                target_text
            )

        else:
            # 没有交易数据
            etf_code_str = etf_code
            name_str = etf_info['name']
            last_price_str = "[dim]--[/dim]"
            current_price_str = f"{item['current_data']['price']:.3f} 元"  # 白色文字
            change_str = "[dim]--[/dim]"
            target_text = "[dim]--[/dim]"

            table.add_row(
                etf_code_str,
                name_str,
                last_price_str,
                current_price_str,
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


def add_etf_to_watchlist():
    """
    选项3-2：添加新的ETF到观察列表
    用户依次输入ETF代码、ETF名称、雪球链接
    """
    console.print("\n[bold yellow]添加新的ETF到观察列表[/bold yellow]\n")

    # 输入ETF代码
    etf_code = input("请输入ETF代码（如：SZ159915）: ").strip().upper()

    if not etf_code:
        console.print("[yellow]取消操作，返回上级菜单[/yellow]\n")
        return

    # 检查是否已存在
    if etf_list_storage.etf_exists(etf_code):
        console.print(f"[red]ETF {etf_code} 已存在于观察列表中[/red]\n")
        return

    # 输入ETF名称
    etf_name = input("请输入ETF名称: ").strip()

    if not etf_name:
        console.print("[red]ETF名称不能为空[/red]\n")
        return

    # 输入雪球链接（提供默认值）
    default_url = f"https://xueqiu.com/S/{etf_code}"
    url = input(f"请输入雪球个股页链接（直接回车使用默认值: {default_url}）: ").strip()

    if not url:
        url = default_url

    # 确认添加
    console.print(f"\n[bold]请确认ETF信息：[/bold]")
    console.print(f"  ETF代码: {etf_code}")
    console.print(f"  ETF名称: {etf_name}")
    console.print(f"  雪球链接: {url}\n")

    confirm = input("确认添加？（y/n）: ").strip().lower()

    if confirm == 'y':
        success = etf_list_storage.add_etf(etf_code, etf_name, url)
        if success:
            console.print(f"\n[green]✓[/green] ETF {etf_code} 已成功添加到观察列表\n")
        else:
            console.print(f"\n[red]✗[/red] 添加失败\n")
    else:
        console.print("[yellow]已取消添加[/yellow]\n")


def remove_etf_from_watchlist():
    """
    选项3-1：从观察列表删除ETF
    用户输入ETF编号，确认后删除
    """
    console.print("\n[bold yellow]从观察列表删除ETF[/bold yellow]\n")

    # 显示所有ETF列表
    etf_list = etf_list_storage.get_all_etfs()

    if not etf_list:
        console.print("[red]观察列表为空，无法删除[/red]\n")
        return

    table = Table(box=box.ROUNDED)
    table.add_column("编号", style="cyan")
    table.add_column("ETF代码", style="yellow")
    table.add_column("ETF名称", style="blue")

    for idx, (etf_code, etf_info) in enumerate(etf_list.items(), 1):
        table.add_row(str(idx), etf_code, etf_info['name'])

    console.print(table)

    # 询问要删除的ETF
    etf_count = len(etf_list)
    choice = input(f"\n请选择要删除的ETF编号（1-{etf_count}），或按回车取消: ").strip()

    if not choice:
        console.print("[yellow]取消操作，返回上级菜单[/yellow]\n")
        return

    try:
        idx = int(choice) - 1
        if 0 <= idx < etf_count:
            etf_code = list(etf_list.keys())[idx]
            etf_name = etf_list[etf_code]['name']

            # 确认删除
            console.print(f"\n[bold red]⚠️  警告：[/bold red] 即将删除 {etf_code} - {etf_name}")
            confirm = input("确认删除？（y/n）: ").strip().lower()

            if confirm == 'y':
                success = etf_list_storage.remove_etf(etf_code)
                if success:
                    console.print(f"\n[green]✓[/green] ETF {etf_code} 已从观察列表删除\n")
                else:
                    console.print(f"\n[red]✗[/red] 删除失败\n")
            else:
                console.print("[yellow]已取消删除[/yellow]\n")
        else:
            console.print("[red]编号超出范围[/red]\n")
    except ValueError:
        console.print("[red]请输入有效的数字[/red]\n")


def update_etf_watchlist():
    """
    选项3：更新观察列表
    提供两个子选项：删除ETF 或 添加ETF
    """
    console.print("\n[bold yellow]更新ETF观察列表[/bold yellow]\n")

    # 显示当前ETF数量
    etf_count = etf_list_storage.get_etf_count()
    console.print(f"当前观察列表共有 [bold]{etf_count}[/bold] 只ETF\n")

    # 显示子菜单
    sub_menu = """
┌─────────────────────────────────────────────────────────────┐
│  请选择操作：                                               │
│                                                             │
│  [bold cyan]1.[/bold cyan] 删除列表中的ETF                                  │
│     从观察列表中删除指定的ETF                               │
│                                                             │
│  [bold cyan]2.[/bold cyan] 添加ETF                                          │
│     添加新的ETF到观察列表                                   │
│                                                             │
│  [bold cyan]0.[/bold cyan] 返回上级菜单                                      │
└─────────────────────────────────────────────────────────────┘
"""
    console.print(sub_menu)

    choice = input("请输入选项编号（0-2）: ").strip()

    if choice == '1':
        remove_etf_from_watchlist()
    elif choice == '2':
        add_etf_to_watchlist()
    elif choice == '0':
        console.print("[yellow]返回主菜单[/yellow]\n")
    else:
        console.print("[red]无效选项[/red]\n")


def main():
    """
    主程序入口
    交互式菜单系统
    """
    print_banner()

    # 程序启动时初始化ETF列表（首次运行时从默认配置导入）
    etf_list_storage.init_default_etfs()

    while True:
        print_menu()

        choice = input("请输入选项编号（0-3）: ").strip()

        if choice == '1':
            update_transaction_data()
        elif choice == '2':
            analyze_trading_signals()
        elif choice == '3':
            update_etf_watchlist()
        elif choice == '0':
            console.print("\n[yellow]感谢使用，再见！[/yellow]\n")
            sys.exit(0)
        else:
            console.print("[red]无效选项，请重新输入[/red]\n")

        input("\n按回车键继续...")


if __name__ == '__main__':
    main()
