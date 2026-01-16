"""
ETF 价格跟踪系统 - 主程序
"""
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box
from typing import Optional

from src.logger import logger
from src.crawler import XueqiuCrawler
from src.storage import price_storage, transaction_storage
from src.calculator import calculate_profit_loss_with_current, check_date_range
from src.alert import check_alert_status
from config.app import ETF_CONFIG

# 初始化
app = typer.Typer(
    help="ETF 价格跟踪与交易提醒系统",
    rich_markup_mode="rich",
    rich_help_panel=True
)
console = Console()


def print_banner():
    """打印欢迎横幅"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║        ETF 价格跟踪与交易提醒系统                            ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"""
    console.print(f"[bold cyan]{banner}[/bold cyan]")


def print_etf_info():
    """打印ETF信息"""
    etf_code = ETF_CONFIG['code']
    etf_name = ETF_CONFIG['name']
    console.print(Panel(
        f"[bold]ETF 代码:[/bold] {etf_code}\n"
        f"[bold]ETF 名称:[/bold] {etf_name}",
        title="[bold]当前跟踪的 ETF[/bold]",
        box=box.ROUNDED
    ))


@app.command("analyze")
def analyze_etf(
    code: str = typer.Option(
        ETF_CONFIG['code'], "--code", "-c",
        help="ETF 代码（如 SZ159915）"
    ),
    price: Optional[float] = typer.Option(
        None, "--price", "-p",
        help="上次交易价格（如果不提供，会提示输入）"
    ),
    quantity: Optional[int] = typer.Option(
        None, "--quantity", "-q",
        help="交易数量（份）（如果不提供，会提示输入）"
    )
):
    """
    分析 ETF 价格和盈亏情况
    """
    print_banner()
    print_etf_info()

    console.print("\n[bold yellow]📊 开始分析 ETF 价格...[/bold yellow]\n")

    # 步骤 1: 获取当前价格
    console.print("[bold]步骤 1: 获取当前价格[/bold]")
    with console.status("正在从雪球网站获取价格...", spinner="dots"):
        crawler = XueqiuCrawler()
        result = crawler.fetch_price_sync(code)

    if not result:
        console.print("[red]✗ 获取价格失败，请检查网络和 ETF 代码[/red]")
        raise typer.Exit(1)

    current_price, etf_name = result

    console.print(f"[green]✓[/green] 成功获取价格: [bold]{current_price} 元[/bold]")
    console.print(f"当前时间: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # 步骤 2: 输入上次交易信息
    console.print("[bold]步骤 2: 输入交易信息[/bold]")

    # 获取上次交易价格
    if price is None:
        price = typer.prompt("请输入上次交易价格（元）", type=float)
    console.print(f"上次交易价格: [bold]{price} 元[/bold]")

    # 获取交易数量
    if quantity is None:
        quantity = typer.prompt("请输入交易数量（份）", type=int)
    console.print(f"交易数量: [bold]{quantity:,} 份[/bold]")

    # 计算上次交易金额
    last_amount = price * quantity
    console.print(f"上次交易金额: [bold]{last_amount:,.2f} 元[/bold]\n")

    # 步骤 3: 判断区间并生成提醒
    console.print("[bold]步骤 3: 区间判断与提醒[/bold]")

    # 进行交易（添加到记录）
    transaction_id = transaction_storage.add_transaction(code, price, quantity)

    # 检查是否需要提醒
    alert_result = check_alert_status(current_price, price, transaction_id)

    # 显示当前价格与上次交易的对比
    change_rate = alert_result['current_change']
    change_arrow = "↑" if change_rate >= 0 else "↓"
    change_color = "green" if change_rate >= 0 else "red"

    console.print(f"\n当前价格相比上次交易: [{change_color}]{change_arrow} {abs(change_rate)}%[/{change_color}]")

    # 显示区间判断结果
    if alert_result['in_range']:
        console.print(Panel(
            f"当前价格 [bold]{current_price} 元[/bold] 落在 [bold red]{alert_result['matched_range']}[/bold red] 区间内！",
            title="⚠️  提醒",
            style="yellow"
        ))

        # 显示距离关键价位的涨跌幅
        levels = alert_result['levels']
        if alert_result['matched_range'] == '[+3% ~ +5%]':
            to_plus5 = ((levels['+5%'] - current_price) / price) * 100
            to_plus3 = ((current_price - levels['+3%']) / price) * 100
            console.print(f"距离 +5% 目标 ({levels['+5%']} 元): {to_plus5:.2f}%")
            console.print(f"距离 +3% 目标 ({levels['+3%']} 元): {to_plus3:.2f}%")
        elif alert_result['matched_range'] == '[-5% ~ -3%]':
            to_minus5 = ((current_price - levels['-5%']) / price) * 100
            to_minus3 = ((levels['-3%'] - current_price) / price) * 100
            console.print(f"距离 -5% 目标 ({levels['-5%']} 元): {to_minus5:.2f}%")
            console.print(f"距离 -3% 目标 ({levels['-3%']} 元): {to_minus3:.2f}%")

        # 显示是否需要提醒
        if alert_result['should_alert']:
            console.print(f"\n[bold yellow]📢 建议操作提醒: {alert_result['alert_reason']}[/bold yellow]")

    else:
        console.print("当前价格未进入关键区间，建议观望")

    # 步骤 4: 盈亏分析
    console.print("\n[bold]步骤 4: 盈亏分析[/bold]\n")

    # 使用表格展示结果
    table = Table(box=box.ROUNDED, show_lines=True)
    table.add_column("涨跌幅", style="bold cyan", justify="center")
    table.add_column("对应价(元)", style="yellow", justify="right")
    table.add_column("交易金额(元)", style="green", justify="right")
    table.add_column("盈亏(元)", style="magenta", justify="right")
    table.add_column("盈亏率", style="blue", justify="right")

    # 计算各价位盈亏
    profit_results = calculate_profit_loss_with_current(current_price, price, quantity)

    # 显示表头
    console.print(f"上次交易: {price} 元 × {quantity:,} 份 = {profit_results['last_transaction']['amount']:,.2f} 元\n")

    # 添加当前价行（高亮）
    current_data = profit_results['current']
    table.add_row(
        "当前价",
        f"[bold]{current_data['price']}[/bold]",
        f"[bold]{current_data['amount']:,.2f}[/bold]",
        f"[bold]{'+' if current_data['profit_amount'] >= 0 else ''}{current_data['profit_amount']:,.2f}[/bold]",
        f"[bold]{'+' if current_data['profit_percentage'] >= 0 else ''}{current_data['profit_percentage']}%[/bold]",
        style="on grey23"
    )

    # 添加各涨跌幅行
    for label in ['+10%', '+5%', '+3%', '-3%', '-5%', '-10%']:
        data = profit_results[label]
        table.add_row(
            label,
            str(data['price']),
            f"{data['amount']:,.2f}",
            f"{'+' if data['profit_amount'] >= 0 else ''}{data['profit_amount']:,.2f}",
            f"{'+' if data['profit_percentage'] >= 0 else ''}{data['profit_percentage']}%"
        )

    console.print(table)

    # 操作建议
    console.print("\n[bold]操作建议:[/bold]")
    if current_price > price:
        profit = current_data['profit_amount']
        profit_rate = current_data['profit_percentage']
        console.print(f"  [green]✓[/green] 目前已盈利 {profit:,.2f} 元 ({profit_rate}%)")

        if 3 <= profit_rate <= 5:
            console.print("  [yellow]⚠️[/yellow] 盈利在 3%-5% 区间，[bold]可考虑部分止盈[/bold]")
        elif profit_rate >= 5:
            console.print("  [yellow]⚠️[/yellow] 盈利超过 5%，[bold]建议考虑止盈[/bold]")
        else:
            console.print("  [blue]ℹ️[/blue] 盈利未达目标区间，[bold]建议继续持有[/bold]")
    else:
        loss = abs(current_data['profit_amount'])
        loss_rate = abs(current_data['profit_percentage'])
        console.print(f"  [red]✗[/red] 目前已亏损 {loss:,.2f} 元 ({loss_rate}%)")

        if loss_rate >= 5:
            console.print("  [red]⚠️[/red] 亏损超过 5%，[bold]建议考虑止损[/bold]")
        elif 3 <= loss_rate <= 5:
            console.print("  [yellow]⚠️[/yellow] 亏损在 3%-5% 区间，[bold]密切关注[/bold]")
        else:
            console.print("  [blue]ℹ️[/blue] 亏损较小，[bold]建议继续持有观望[/bold]")

    # 添加页脚
    console.print("\n" + "─" * 60)
    console.print("[dim]备注：本工具仅供参考，不构成投资建议。投资有风险，入市需谨慎。[/dim]")
    console.print("─" * 60)


@app.command("price")
def get_current_price(
    code: str = typer.Option(
        ETF_CONFIG['code'], "--code", "-c",
        help="ETF 代码"
    )
):
    """
    获取 ETF 当前价格
    """
    print_banner()

    console.print("\n[bold]获取当前 ETF 价格[/bold]\n")

    with console.status("正在连接雪球网站...", spinner="dots"):
        crawler = XueqiuCrawler()
        result = crawler.fetch_price_sync(code)

    if result:
        price, name = result
        console.print(Panel(
            f"ETF 代码: [bold cyan]{code}[/bold cyan]\n"
            f"ETF 名称: [bold]{name}[/bold]\n"
            f"当前价格: [bold green]{price} 元[/bold green]\n"
            f"获取时间: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            title="✓ 价格获取成功",
            box=box.ROUNDED
        ))
    else:
        console.print("[red]✗ 获取价格失败[/red]")
        raise typer.Exit(1)


@app.command("history")
def show_price_history(
    code: str = typer.Option(
        ETF_CONFIG['code'], "--code", "-c",
        help="ETF 代码"
    ),
    days: int = typer.Option(
        7, "--days", "-d",
        help="显示最近几天"
    )
):
    """
    显示价格历史记录
    """
    print_banner()

    console.print(f"\n[bold]价格历史记录（最近 {days} 天）[/bold]\n")

    records = price_storage.get_history(days)

    if not records:
        console.print("暂无历史记录")
        return

    table = Table(box=box.ROUNDED)
    table.add_column("时间", style="cyan")
    table.add_column("ETF", style="yellow")
    table.add_column("价格(元)", style="green", justify="right")

    for record in records:
        table.add_row(
            record['record_time'],
            record['etf_code'],
            record['price']
        )

    console.print(table)
    console.print(f"\n总计 {len(records)} 条记录")


@app.command("fetch")
def fetch_and_save_price(
    code: str = typer.Option(
        ETF_CONFIG['code'], "--code", "-c",
        help="ETF 代码"
    )
):
    """
    获取价格并保存到历史记录
    """
    print_banner()

    console.print("\n[bold]获取价格并保存[/bold]\n")

    with console.status("正在获取价格...", spinner="dots"):
        crawler = XueqiuCrawler()
        result = crawler.fetch_price_sync(code)

    if not result:
        console.print("[red]✗ 获取价格失败[/red]")
        raise typer.Exit(1)

    price, name = result

    # 保存到历史记录
    price_record = price_storage.add_price_record(code, name, price)

    console.print(Panel(
        f"获取成功并保存:\n"
        f"ETF: {code} - {name}\n"
        f"价格: {price} 元\n"
        f"记录时间: {price_record['record_time']}",
        title="✓ 保存成功",
        box=box.ROUNDED,
        style="green"
    ))


@app.command("list")
def list_transactions():
    """
    列出所有交易记录
    """
    print_banner()

    console.print("\n[bold]交易记录列表[/bold]\n")

    records = transaction_storage.read_all()

    if not records:
        console.print("暂无交易记录")
        return

    table = Table(box=box.ROUNDED)
    table.add_column("ID", style="cyan", justify="right")
    table.add_column("日期", style="yellow")
    table.add_column("ETF", style="blue")
    table.add_column("价格", style="green", justify="right")
    table.add_column("数量", style="magenta", justify="right")
    table.add_column("类型", style="red")

    for record in records:
        table.add_row(
            record['id'],
            record['transaction_date'],
            record['etf_code'],
            f"{float(record['transaction_price']):.2f} 元",
            f"{int(record['transaction_quantity']):,}",
            record['transaction_type']
        )

    console.print(table)


@app.callback()
def main():
    """
    ETF 价格跟踪与交易提醒系统

    功能: 自动跟踪 ETF 价格，分析盈亏，提供交易提醒
    """
    pass


if __name__ == '__main__':
    app()
