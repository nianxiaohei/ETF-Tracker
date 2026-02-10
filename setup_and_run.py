#!/usr/bin/env python3
"""
自动配置和运行脚本
自动完成环境检查、Cookie配置和程序启动

使用方法：
python setup_and_run.py
"""

import os
import sys
import subprocess
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich import box

console = Console()


class SetupManager:
    def __init__(self):
        self.project_dir = Path(__file__).parent
        self.env_file = self.project_dir / ".env"
        self.venv_dir = self.project_dir / "venv"
        self.console = Console()

    def check_venv(self):
        """检查并激活虚拟环境"""
        self.console.print("\n[bold cyan]1. 检查虚拟环境[/bold cyan]\n")

        if not self.venv_dir.exists():
            self.console.print("[yellow]未找到虚拟环境，正在创建...[/yellow]")
            result = subprocess.run(
                [sys.executable, "-m", "venv", "venv"],
                cwd=self.project_dir,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                self.console.print("[green]✓[/green] 虚拟环境创建成功")
            else:
                self.console.print(f"[red]✗[/red] 虚拟环境创建失败: {result.stderr}")
                return False
        else:
            self.console.print("[green]✓[/green] 虚拟环境已存在")

        # 检查依赖
        pip_path = self.venv_dir / "bin" / "pip"
        if not pip_path.exists():
            pip_path = self.venv_dir / "Scripts" / "pip.exe"

        result = subprocess.run(
            [str(pip_path), "list"],
            capture_output=True,
            text=True
        )

        if "httpx" not in result.stdout:
            self.console.print("[yellow]正在安装依赖...[/yellow]")
            result = subprocess.run(
                [str(pip_path), "install", "-r", "requirements.txt"],
                cwd=self.project_dir,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                self.console.print("[green]✓[/green] 依赖安装成功")
            else:
                self.console.print(f"[red]✗[/red] 依赖安装失败")
                return False
        else:
            self.console.print("[green]✓[/green] 依赖已安装")

        return True

    def check_cookie(self):
        """检查并配置Cookie"""
        self.console.print("\n[bold cyan]2. 检查Cookie配置[/bold cyan]\n")

        # 加载现有的.env文件
        dotenv_path = self.project_dir / ".env"
        cookies = ""

        if dotenv_path.exists():
            with open(dotenv_path, 'r') as f:
                content = f.read()
                for line in content.split('\n'):
                    if line.startswith('XUEQIU_COOKIE='):
                        cookies = line.split('=', 1)[1].strip().strip('"\'')
                        break

        if cookies and cookies != "YOUR_COOKIE_HERE":
            self.console.print(f"[green]✓[/green] 已配置Cookie (长度: {len(cookies)})")
            self.console.print(f"[dim]Cookie: {cookies[:50]}...[/dim]")

            # 验证Cookie
            choice = Prompt.ask(
                "\n是否使用现有Cookie？",
                choices=["y", "n"],
                default="y"
            )
            if choice == "y":
                return cookies

        # 需要配置新的Cookie
        self.console.print(Panel(
            "[bold]需要配置雪球Cookie[/bold]\n\n"
            "由于雪球网启用了WAF防护，必须使用浏览器Cookie才能访问。\n\n"
            "[yellow]获取Cookie步骤：[/yellow]\n"
            "1. 在浏览器中访问 https://xueqiu.com\n"
            "2. [bold]登录你的雪球账号[/bold](必需)\n"
            "3. 按F12打开开发者工具\n"
            "4. 切换到Network标签\n"
            "5. 刷新页面，找到任意请求\n"
            "6. 复制Request Headers中的[bold]Cookie[/bold]字段[bold](完整内容)[/bold]",
            title="配置说明",
            box=box.ROUNDED,
            border_style="cyan"
        ))

        self.console.print("\n[bold yellow]请现在打开浏览器获取Cookie，完成后回到这里[/bold yellow]\n")

        while True:
            cookies = Prompt.ask("请输入Cookie (或直接粘贴)")

            if not cookies:
                self.console.print("[red]Cookie不能为空[/red]")
                continue

            if len(cookies) < 50:
                self.console.print("[yellow]⚠ Cookie似乎过短，可能不完整[/yellow]")
                confirm = Prompt.ask("是否继续？", choices=["y", "n"], default="n")
                if confirm == "n":
                    continue

            # 保存到.env文件
            self._save_cookie_to_env(cookies)
            self.console.print("[green]✓[/green] Cookie已保存到 .env 文件")
            break

        return cookies

    def _save_cookie_to_env(self, cookies):
        """保存Cookie到.env文件"""
        env_content = ""

        if self.env_file.exists():
            with open(self.env_file, 'r') as f:
                lines = f.readlines()
                # 移除旧的Cookie行
                for line in lines:
                    if not line.startswith('XUEQIU_COOKIE='):
                        env_content += line

        # 添加新的Cookie
        env_content += f'XUEQIU_COOKIE={cookies}\n'

        with open(self.env_file, 'w') as f:
            f.write(env_content)

    def test_crawler(self):
        """测试爬虫"""
        self.console.print("\n[bold cyan]3. 测试东方财富API爬虫[/bold cyan]\n")

        # 使用虚拟环境中的Python
        python_path = self.venv_dir / "bin" / "python"
        if not python_path.exists():
            python_path = self.venv_dir / "Scripts" / "python.exe"

        self.console.print("[yellow]正在测试几只ETF...[/yellow]\n")

        result = subprocess.run(
            [str(python_path), "src/crawler_eastmoney.py"],
            cwd=self.project_dir,
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            self.console.print(result.stdout)
            return True
        else:
            self.console.print(result.stdout)
            self.console.print(f"[red]✗[/red] 测试失败")
            self.console.print(f"\n错误信息:\n{result.stderr}")
            return False

    def run_main_program(self):
        """运行主程序"""
        self.console.print("\n[bold cyan]4. 启动主程序[/bold cyan]\n")

        python_path = self.venv_dir / "bin" / "python"
        if not python_path.exists():
            python_path = self.venv_dir / "Scripts" / "python.exe"

        self.console.print("[yellow]正在启动 ETF Trace 程序...[/yellow]\n")
        self.console.print("="*60)

        # 运行主程序
        subprocess.run(
            [str(python_path), "main.py"],
            cwd=self.project_dir
        )

    def print_summary(self):
        """打印配置总结"""
        self.console.print(Panel(
            "[bold green]✓ 配置完成！[/bold green]\n\n"
            "接下来你可以：\n"
            "• 直接运行: [cyan]python main.py[/cyan]\n"
            "• 或使用本脚本: [cyan]python setup_and_run.py[/cyan]\n\n"
            "其他命令:\n"
            "• 测试爬虫: [cyan]python src/crawler_api.py[/cyan]\n"
            "• 查看日志: [cyan]tail -f logs/app.log[/cyan]\n\n"
            "需要帮助？查看:\n"
            "• API_COOKIE配置指南.md\n"
            "• 爬虫失效修复总结.md",
            title="配置完成",
            box=box.ROUNDED,
            border_style="green"
        ))


def main():
    """主流程"""
    console.print("\n")
    console.print(Panel(
        "[bold]ETF Trace - 自动配置脚本[/bold]\n\n"
        "本脚本将自动完成:\n"
        "1. 检查并配置虚拟环境\n"
        "2. 配置雪球Cookie（绕过WAF拦截）\n"
        "3. 测试API爬虫\n"
        "4. 启动主程序",
        title="欢迎使用",
        box=box.ROUNDED,
        border_style="blue"
    ))

    setup = SetupManager()

    # 步骤1: 检查虚拟环境
    if not setup.check_venv():
        console.print("\n[red]虚拟环境配置失败，请检查错误信息后重试[/red]")
        sys.exit(1)

    # 步骤2: 配置Cookie
    cookie = setup.check_cookie()
    if not cookie:
        console.print("\n[red]Cookie配置失败，无法继续[/red]")
        sys.exit(1)

    # 步骤3: 测试爬虫
    console.print("\n[bold]按回车键开始测试...[/bold]")
    input()

    if not setup.test_crawler():
        choice = Prompt.ask(
            "\n测试未完全通过，是否继续启动主程序？",
            choices=["y", "n"],
            default="n"
        )
        if choice == "n":
            console.print("\n[yellow]已取消，请查看错误信息并修复后重试[/yellow]")
            sys.exit(1)

    # 步骤4: 启动主程序
    console.print("\n[bold]按回车键启动主程序...[/bold]")
    input()

    setup.run_main_program()

    # 打印总结
    setup.print_summary()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n\n[yellow]用户取消操作[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[red]错误: {e}[/red]")
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/dim]")
        sys.exit(1)
