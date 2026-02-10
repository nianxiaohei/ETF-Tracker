# ETF Trace 📈

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![CLI](https://img.shields.io/badge/CLI-Rich%20Terminal-brightgreen.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

> 智能 ETF 价格跟踪与交易信号系统，支持16只ETF实时监控
>✅ 同步测试：Cursor 修改此行
> 智能 ETF 价格跟踪与交易信号系统，支持16只ETF实时监控

## ⚠️ 重要通知：2026.02 更新

**最近遇到爬虫被WAF拦截的问题？** 请按以下步骤操作：

1. **必读修复文档**：`爬虫失效修复总结.md`
2. **配置Cookie**：按照 `API_COOKIE配置指南.md` 操作
3. **问题原因**：雪球网启用了阿里云WAF防护，需要Cookie认证

> **关键步骤**：在 `.env` 文件中添加 `XUEQIU_COOKIE` 配置

一款功能强大的命令行工具，用于自动跟踪 ETF 价格、分析盈亏并提供交易提醒。内置交互式菜单，操作简单直观。

![](https://img.shields.io/badge/支持的ETF-16只-orange.svg)
![](https://img.shields.io/badge/数据源-雪球网-blue.svg)
</div>

## ✨ 核心功能

| 功能 | 描述 | 状态 |
|------|------|------|
| 📊 **实时价格采集** | 自动从雪球网站获取 ETF 实时价格 | ✅ |
| 📈 **智能分析** | 计算关键涨跌幅（±3%、±5%、±10%）对应的目标价格 | ✅ |
| 🔔 **交易信号提醒** | 价格进入关键区间时自动推送提醒 | ✅ |
| 💰 **盈亏计算** | 快速计算不同价格情景下的盈亏情况 | ✅ |
| 💾 **数据持久化** | CSV 格式保存价格历史和交易记录 | ✅ |

| ⏰ **定时任务** | 支持 macOS launchd 每日自动采集（10:00） | ✅ |
| 🎛️ **交互式菜单** | 美观的 CLI 界面，操作便捷 | ✅ |
| 📝 **动态ETF管理** | 支持添加/删除ETF，自定义观察列表 | ✅ |

## 🎯 支持的 ETF

系统预置16只主流 ETF，涵盖宽基指数和行业主题：

| 代码 | 名称 | 类型 |
|------|------|------|
| SH560050 | MSCI中国A50ETF | 宽基 |
| SZ159967 | 创业板成长ETF | 宽基 |
| SZ159952 | 创业板ETF广发 | 宽基 |
| ... | （共16只） | 多种类型 |

**使用方法**：在 `.env` 文件中修改 `ETF_CODE` 配置，或在命令行中通过 `--code` 参数指定。

## 🚀 快速开始

### 前置要求

- Python 3.9+
- macOS / Linux / Windows

```bash
python3 --version
```

### 安装步骤

#### 方法1：一键安装（推荐）

```bash
git clone <repository-url>
cd ETF_trace

# 自动创建虚拟环境并安装依赖
make install  # 或 ./scripts/install.sh
```

#### 方法2：手动安装

```bash
# 1. 克隆项目
git clone <repository-url>
cd ETF_trace

# 2. 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate     # Windows

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置环境
cp .env.example .env
# 按需编辑 .env 文件
```

## 💻 使用指南

### 启动程序

```bash
# 激活虚拟环境
source venv/bin/activate

# 运行主程序
python main.py
```

### 功能菜单

启动后会看到交互式菜单：

```
┌─────────────────────────────────────────────────────────────┐
│  请选择功能：                                               │
│                                                             │
│  1. 更新上次交易价格和数量                                  │
│  2. 交易信号（分析所有 ETF）                                │
│  3. 更新观察列表（新增）                                    │
│  0. 退出程序                                                │
└─────────────────────────────────────────────────────────────┘
```

### 常见场景

#### 场景1：更新交易信息

选择 `1`，输入 ETF 代码、上次交易价格和数量

示例输入：
- ETF代码: `SZ159915`
- 上次交易价格: `2.08`
- 交易数量: `10000`

#### 场景2：查看交易信号

选择 `2`，系统将：
1. 获取所有16只ETF的实时价格
2. 分析涨跌幅
3. 提示进入关键区间的ETF
4. 显示操作建议

#### 场景3：更新观察列表（新增）

选择 `3`，可以动态管理ETF观察列表：

**选项一：删除ETF**
- 选择 `1`，输入要删除的ETF编号
- 确认后，该ETF从列表中移除
- 功能1和功能2将不再显示该ETF

**选项二：添加ETF**
- 选择 `2`，依次输入ETF代码、名称、雪球链接
- 新ETF添加到观察列表
- 可在功能1中设置交易数据，或在功能2中观察价格

**特点：**
- 新添加的ETF没有交易数据时，相关列显示 `--`
- 支持自定义ETF，不限于默认的16只

#### 场景4：命令行模式

```bash
# 分析指定ETF
python main.py analyze --code SZ159915 --price 2.08 --quantity 10000

# 获取当前价格
python main.py price --code SZ159915

# 查看价格历史
python main.py history --days 7
```

## ⚙️ 配置说明

### 环境变量

编辑 `.env` 文件：

```bash
# ETF 配置
ETF_CODE=SZ159915              # 默认ETF代码
ETF_NAME=创业板ETF易方达       # ETF名称

# 路径配置
DATA_DIR=./data                # 数据存储目录
LOG_DIR=./logs                 # 日志输出目录
```

### 数据文件

程序会自动创建 `./data/` 目录并生成以下文件：

| 文件名 | 用途 |
|--------|------|
| `price_history.csv` | 价格历史记录 |
| `user_transactions.csv` | 交易记录 |
| `alert_status.csv` | 提醒状态 |
| `alert_history.csv` | 提醒历史 |
| `etf_list.csv` | ETF观察列表（支持动态管理） |

## 🤖 自动化配置

### macOS Launchd（推荐）

1. **修改配置文件**

编辑 `~/Library/LaunchAgents/com.etf.tracker.plist`，设置正确的路径：

```xml
<key>ProgramArguments</key>
<array>
    <string>/usr/local/bin/python3</string>  <!-- Python路径 -->
    <string>/path/to/ETF_trace/main.py</string>  <!-- 项目主文件路径 -->
    <string>fetch</string>  <!-- 运行模式 -->
</array>
```

2. **加载定时任务**

```bash
# 加载任务
launchctl load ~/Library/LaunchAgents/com.etf.tracker.plist

# 测试运行
launchctl start com.etf.tracker

# 查看状态
launchctl list | grep etf.tracker

# 查看日志
tail -f logs/scheduler.log

# 卸载任务
launchctl unload ~/Library/LaunchAgents/com.etf.tracker.plist
```

### Linux Crontab

```bash
# 每天 10:00 自动执行
0 10 * * 1-5 cd /path/to/ETF_trace && /usr/local/bin/python3 main.py fetch
```

## 🛠️ 技术栈

| 类别 | 技术 |
|------|------|
| **语言** | Python 3.9+ |
| **CLI框架** | Typer + Rich |
| **数据抓取** | httpx + BeautifulSoup4 |
| **数据存储** | Pandas + CSV |
| **日志系统** | Loguru |
| **配置管理** | python-dotenv |

## 📂 项目结构

```
ETF_trace/
├── main.py                 # 主程序（CLI入口）
├── src/                    # 核心模块
│   ├── crawler.py         # 雪球数据爬虫
│   ├── calculator.py      # 价格与盈亏计算器
│   ├── storage.py         # CSV数据存储
│   ├── alert.py           # 提醒管理
│   └── logger.py          # 日志系统
├── config/
│   └── app.py             # 配置管理
├── data/                   # 数据文件（自动生成）
├── logs/                   # 日志文件（自动生成）
├── .env                   # 环境变量配置
├── requirements.txt       # Python依赖
└── README.md             # 本文档
```

## ⚡ 性能特点

- ⚡ **快速启动**：毫秒级数据抓
- 📊 **批量处理**：16只ETF同时监控
- 🔄 **智能缓存**：避免重复计算
- 💾 **轻量级存储**：CSV格式，便于迁移

## ⚠️ 注意事项

### 免责声明

- 本工具仅供个人学习和参考，不构成投资建议
- 投资有风险，入市需谨慎
- 盈亏自负，使用本工具产生的任何损失概不负责

### 合规提示

- 请遵守雪球网站的使用条款
- 不要频繁请求以免触发反爬虫机制
- 建议仅在交易时段（9:30-11:30, 13:00-15:00）使用

## 🔧 故障排除

### 问题1：爬虫失败

```bash
# 查看详细日志
cat logs/app.log | grep ERROR

# 检查网络连接
curl https://xueqiu.com

# 更新依赖
pip install --upgrade httpx beautifulsoup4
```

### 问题2：定时任务未执行

```bash
# 检查launchd状态
launchctl list | grep etf.tracker

# 查看错误日志
cat logs/scheduler.error.log

# 检查Python路径
which python3
```

### 问题3：权限不足

```bash
# 添加执行权限
chmod +x main.py

# 检查数据目录权限
ls -la data/
```

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

### 开发环境搭建

```bash
# 克隆项目
git clone <repository-url>
cd ETF_trace

# 安装开发依赖
pip install -r requirements.txt
pip install pytest pytest-cov

# 运行测试
pytest tests/
```

## 📜 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 👤 作者

- **作者**: nianxiaohei
- **创建日期**: 2025-01-16
- **版本**: v1.0.0

## 📮 联系方式

如有问题或建议：

1. 提交 [GitHub Issue](issues)
2. 加我的VX：Xiaohei713
---

<div align="center">
⭐ 如果这个项目对你有帮助，请给个 Star！
</div>
