#!/usr/bin/env python3
"""
快速Cookie配置脚本
使用方法：先获取Cookie，然后运行此脚本粘贴
"""

import sys
from pathlib import Path

print("="*70)
print("ETF Trace - 快速Cookie配置")
print("="*70)
print()

# 说明
print("📋 请先完成以下步骤：")
print()
print("1. 打开浏览器访问 https://xueqiu.com")
print("2. 登录你的雪球账号")
print("3. 按 F12 打开开发者工具")
print("4. 切换到 Network 标签")
print("5. 刷新页面")
print("6. 点击任意请求，找到 Cookie 字段")
print("7. 复制完整的 Cookie 内容")
print()
print("="*70)
print()

# 获取Cookie输入
print("📋 现在请粘贴你的Cookie（直接粘贴后按回车）：")
cookie = input().strip()

if not cookie:
    print("❌ 错误：Cookie不能为空")
    sys.exit(1)

if len(cookie) < 50:
    print("⚠️  警告：Cookie似乎过短，可能不完整")
    print("是否继续？(y/n)")
    choice = input().strip().lower()
    if choice != 'y':
        print("已取消")
        sys.exit(0)

# 保存到.env文件
env_file = Path(".env")
env_content = ""

if env_file.exists():
    with open(env_file, 'r') as f:
        lines = f.readlines()
        # 移除旧的Cookie行
        for line in lines:
            if not line.startswith('XUEQIU_COOKIE='):
                env_content += line

# 添加新的Cookie
env_content += f'XUEQIU_COOKIE={cookie}\n'

with open(env_file, 'w') as f:
    f.write(env_content)

print()
print("="*70)
print("✅ Cookie 配置成功！")
print("="*70)
print()
print(f"📄 已保存到: {env_file.absolute()}")
print(f"🔑 Cookie 长度: {len(cookie)} 字符")
print()
print("下一步：测试API爬虫")
print("="*70)
print()

# 建议测试
print("是否要测试新的API爬虫？(y/n)")
choice = input().strip().lower()

if choice == 'y':
    print()
    print("运行测试...")
    import subprocess
    result = subprocess.run(
        ["venv/bin/python", "src/crawler_eastmoney.py"],
        capture_output=False,
        text=True
    )
    print()
    print("="*70)
    print("测试完成！")
    print("="*70)

print()
print("现在可以运行主程序了：")
print("  python main.py")
print()
