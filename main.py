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
from src.data_source_manager import fetch_etf_price
from src.storage import etf_transaction_storage, etf_list_storage
from config.app import ETF_CONFIG
# 初始化
console = Console()


def print_banner():
    """打印欢迎横幅"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║              ETF 价格跟踪与交易提醒系统                      ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"""
    console.print(f"[bold cyan]{banner}[/bold cyan]")


def process_group_trading_analysis(etf_list, transaction_data, current_prices):
    """
    处理单个组的ETF交易分析

    参数:
        etf_list: 该组的ETF列表
        transaction_data: 所有ETF的交易数据
        current_prices: 当前价格数据

    返回:
        包含items和alerts的字典
    """
    items = []
    alerts = []

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
            items.append({
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
                alerts.append({
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
            items.append({
                'etf_code': etf_code,
                'etf_info': etf_info,
                'has_transaction': False,
                'current_data': current_data
            })

    # 按涨跌幅排序（升序）
    items.sort(key=lambda x: x.get('change_rate', float('inf')))

    return {'items': items, 'alerts': alerts}


def render_trading_table(items, alerts, group_name: str):
    """
    渲染交易信号表格

    参数:
        items: ETF数据列表
        alerts: 提醒列表（仅用于判断是否高亮，不用于展示）
        group_name: 组别名称（"A股"或"美股"）
    """
    table = Table(box=box.ROUNDED)
    table.add_column(f"{group_name}ETF", style="cyan")
    table.add_column("ETF名称")
    table.add_column("上次交易价", style="yellow")
    table.add_column("最新价")
    table.add_column("涨跌幅", style="magenta")
    table.add_column("接近目标", style="red")

    for item in items:
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

            # 根据涨跌设置最新价颜色（只显示数字）
            if change_rate >= 0:
                current_price_str = f"[green]{current_data['price']:.3f}[/green]"
            else:
                current_price_str = f"[red]{current_data['price']:.3f}[/red]"

            # 高亮超过±3%的ETF
            if abs(change_rate) >= 3:
                etf_code_str = f"[bold red]{etf_code}[/bold red]"
                name_str = etf_info['name']
                target_text = f"{closest_target:+.0f}% ({data['price'] * (1 + closest_target / 100):.3f})"
            else:
                etf_code_str = etf_code
                name_str = etf_info['name']
                target_text = "--"

            table.add_row(
                etf_code_str,
                name_str,
                f"{data['price']:.3f}",
                current_price_str,
                change_str,
                target_text
            )

        else:
            # 没有交易数据
            etf_code_str = etf_code
            name_str = etf_info['name']
            last_price_str = "[dim]--[/dim]"
            current_price_str = f"{item['current_data']['price']:.3f}"
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
                result = fetch_etf_price(etf_code)
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
    增加组别选择步骤
    """
    console.print("\n[bold yellow]更新ETF上次交易数据[/bold yellow]\n")

    # --- 新增：选择市场组别 ---
    group_menu = """
┌─────────────────────────────────────────────────────────────┐
│  请选择市场组别：                                           │
│                                                             │
│  [bold cyan]1.[/bold cyan] A股ETF                                          │
│     更新A股基金的资料                                      │
│                                                             │
│  [bold cyan]2.[/bold cyan] 美股ETF                                         │
│     更新美股基金的资料                                     │
│                                                             │
│  [bold cyan]0.[/bold cyan] 返回上级菜单                                     │
└─────────────────────────────────────────────────────────────┘
"""
    console.print(group_menu)
    group_choice = input("请输入选项编号：").strip()

    if group_choice == '1':
        group = "A股"
    elif group_choice == '2':
        group = "美股"
    elif group_choice == '0':
        return
    else:
        console.print("[red]无效选项[/red]\n")
        return

    # 获取该组的ETF列表
    etf_list = etf_list_storage.get_all_etfs(group=group)
    if not etf_list:
        console.print(f"[yellow]{group}ETF列表为空[/yellow]\n")
        return

    # --- 原有逻辑：显示该组ETF并更新 ---
    console.print(f"\n[bold]{group}ETF列表[/bold]\n")
    table = Table(box=box.ROUNDED)
    table.add_column("编号", style="cyan")
    table.add_column("ETF代码", style="yellow")
    table.add_column("ETF名称", style="white")
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
                f"{data['price']:.3f}",
                f"{data['quantity']:,}"
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
            price = float(input("请输入上次交易价格: ").strip())

            # 输入数量
            quantity = int(input("请输入交易数量: ").strip())

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
    先连续展示两个表格，再统一展示交易信号
    """
    console.print("\n[bold yellow]分析交易信号[/bold yellow]\n")

    # --- 获取两个组的数据 ---
    a_share_etfs = etf_list_storage.get_all_etfs(group="A股")
    us_stock_etfs = etf_list_storage.get_all_etfs(group="美股")

    transaction_data = etf_transaction_storage.get_all_etf_transactions()

    # 抓取所有ETF价格（一次抓取，分组展示）
    current_prices = {}
    all_etf_codes = list(a_share_etfs.keys()) + list(us_stock_etfs.keys())

    if all_etf_codes:
        console.print("[cyan]正在抓取ETF最新价格...[/cyan]")
        progress = console.status("抓取中...")
        progress.start()

        for etf_code in all_etf_codes:
            try:
                result = fetch_etf_price(etf_code)
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

    # 收集所有交易信号
    all_alerts = {'A股': [], '美股': []}

    # --- 处理并展示A股表格 ---
    if a_share_etfs:
        a_share_results = process_group_trading_analysis(
            a_share_etfs,
            transaction_data,
            current_prices
        )
        if a_share_results:
            render_trading_table(a_share_results['items'], a_share_results['alerts'], "A股")
            all_alerts['A股'] = a_share_results['alerts']

    # --- 处理并展示美股表格 ---
    if us_stock_etfs:
        us_stock_results = process_group_trading_analysis(
            us_stock_etfs,
            transaction_data,
            current_prices
        )
        if us_stock_results:
            render_trading_table(us_stock_results['items'], us_stock_results['alerts'], "美股")
            all_alerts['美股'] = us_stock_results['alerts']

    # --- 统一展示交易信号（分成A股和美股两部分） ---
    # A股信号
    if all_alerts['A股']:
        console.print("\n" + "=" * 80)
        console.print("⏰ A股交易信号")
        console.print("=" * 80 + "\n")
        for alert in all_alerts['A股']:
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

    # 美股信号
    if all_alerts['美股']:
        console.print("\n" + "=" * 80)
        console.print("⏰ 美股交易信号")
        console.print("=" * 80 + "\n")
        for alert in all_alerts['美股']:
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

    # 如果没有信号，显示提示
    if not all_alerts['A股'] and not all_alerts['美股']:
        console.print("\n[blue]ℹ️  暂无任何ETF涨跌幅超过±3%[/blue]\n")

    # 显示通用提示信息
    console.print("\n" + "─" * 80)
    console.print("[dim]备注：本工具仅供参考，不构成投资建议。投资有风险，入市需谨慎。[/dim]")
    console.print("─" * 80 + "\n")


def add_etf_to_watchlist(group: str = "A股"):
    """
    选项3-2：添加新的ETF到观察列表
    用户依次输入ETF代码、ETF名称、雪球链接
    """
    console.print(f"\n[bold yellow]添加{group}ETF到观察列表[/bold yellow]\n")

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

    # 输入ETF链接（提供默认值）
    default_url = f"https://quote.eastmoney.com/sz{etf_code[2:]}.html" if etf_code.startswith('SZ') else f"https://quote.eastmoney.com/sh{etf_code[2:]}.html"
    url = input(f"请输入ETF链接: ").strip()

    if not url:
        url = default_url

    # 确认添加
    console.print(f"\n[bold]请确认ETF信息：[/bold]")
    console.print(f"  ETF代码: {etf_code}")
    console.print(f"  ETF名称: {etf_name}")
    console.print(f"  市场组别: {group}")
    console.print(f"  ETF链接: {url}\n")

    confirm = input("确认添加？（y/n）: ").strip().lower()

    if confirm == 'y':
        success = etf_list_storage.add_etf(etf_code, etf_name, url, group=group)
        if success:
            console.print(f"\n[green]✓[/green] ETF {etf_code} 已成功添加到观察列表\n")
        else:
            console.print(f"\n[red]✗[/red] 添加失败\n")
    else:
        console.print("[yellow]已取消添加[/yellow]\n")


def remove_etf_from_watchlist(group: str = "A股"):
    """
    选项3-1：从观察列表删除ETF
    用户输入ETF编号，确认后删除
    """
    console.print(f"\n[bold yellow]从{group}观察列表删除ETF[/bold yellow]\n")

    # 显示指定组的ETF列表
    etf_list = etf_list_storage.get_all_etfs(group=group)

    if not etf_list:
        console.print(f"[red]{group}ETF列表为空，无法删除[/red]\n")
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
    增加组别选择步骤
    """
    console.print("\n[bold yellow]更新ETF观察列表[/bold yellow]\n")

    # 显示当前ETF数量
    etf_count = etf_list_storage.get_etf_count()
    console.print(f"当前观察列表共有 [bold]{etf_count}[/bold] 只ETF\n")

    # --- 新增：选择市场组别 ---
    group_menu = """
┌─────────────────────────────────────────────────────────────┐
│  请选择市场组别：                                           │
│                                                             │
│  [bold cyan]1.[/bold cyan] A股ETF                                          │
│     查看/管理A股基金                                        │
│                                                             │
│  [bold cyan]2.[/bold cyan] 美股ETF                                         │
│     查看/管理美股基金                                      │
│                                                             │
│  [bold cyan]0.[/bold cyan] 返回上级菜单                                     │
└─────────────────────────────────────────────────────────────┘
"""
    console.print(group_menu)
    group_choice = input("请输入选项编号：").strip()

    if group_choice == '1':
        group = "A股"
    elif group_choice == '2':
        group = "美股"
    elif group_choice == '0':
        return
    else:
        console.print("[red]无效选项[/red]\n")
        return

    # 显示该组的ETF数量
    group_etfs = etf_list_storage.get_all_etfs(group=group)
    console.print(f"{group}ETF数量: {len(group_etfs)}\n")

    # --- 原有逻辑：显示操作菜单 ---
    sub_menu = """
┌─────────────────────────────────────────────────────────────┐
│  请选择操作：                                               │
│                                                             │
│  [bold cyan]1.[/bold cyan] 删除列表中的ETF                                  │
│     从观察列表删除指定的ETF                               │
│                                                             │
│  [bold cyan]2.[/bold cyan] 添加ETF                                          │
│     添加新的ETF到观察列表                                   │
│                                                             │
│  [bold cyan]0.[/bold cyan] 返回上级菜单                                     │
└─────────────────────────────────────────────────────────────┘
"""
    console.print(sub_menu)
    choice = input("请输入选项编号（0-2）：").strip()

    if choice == '1':
        remove_etf_from_watchlist(group=group)
    elif choice == '2':
        add_etf_to_watchlist(group=group)
    elif choice == '0':
        return
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
