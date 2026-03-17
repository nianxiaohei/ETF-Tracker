# ETF Trace

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![CLI](https://img.shields.io/badge/CLI-Rich%20Terminal-brightgreen.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

智能 ETF 价格跟踪与交易信号系统，支持 A股+美股 ETF 实时监控。

## 功能特点

| 功能 | 描述 |
|------|------|
| 多数据源 | 腾讯财经 + 东方财富 + Yahoo Finance，自动切换 |
| A股支持 | 实时获取上海/深圳ETF价格 |
| 美股支持 | 获取 USMV、VIG、SCHD、QQQM 等美股ETF |
| 交易信号 | 智能分析涨跌幅（±3%、±5%、±10%） |
| 交互界面 | 美观的CLI菜单，操作简单 |
| 动态管理 | 支持自定义添加/删除ETF观察列表 |

## 支持的ETF

### A股ETF

| 代码 | 名称 |
|------|------|
| SH560050 | 中国A50ETF |
| SZ159967 | 创业板成长ETF |
| SH513050 | 中概互联网ETF |
| SZ159915 | 创业板50ETF |
| SH510300 | 沪深300ETF |
| SH588300 | 科创创业50ETF |

### 美股ETF

| 代码 | 名称 |
|------|------|
| SCHD | 红利低波ETF |
| QQQM | 纳指100ETF |
| USMV | 低波动ETF |
| VIG | 成长ETF |
| VGIT | 中期国债ETF |
| TLT | 长期国债ETF |

## 快速开始

### 环境要求

- Python 3.9+
- macOS / Linux / Windows

### 安装

```bash
# 克隆项目
git clone https://github.com/nianxiaohei/ETF-Tracker.git
cd ETF-Tracker

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 使用

```bash
# 启动程序
python main.py
```

### 功能菜单

```
┌─────────────────────────────────────────────────────────────┐
│  请选择功能：                                               │
│                                                             │
│  1. 更新上次交易价格和数量                                  │
│  2. 交易信号（分析所有ETF）                                 │
│  3. 更新观察列表                                            │
│  0. 退出程序                                                │
└─────────────────────────────────────────────────────────────┘
```

## 项目结构

```
ETF-Tracker/
├── main.py                      # 主程序入口
├── src/
│   ├── crawler_tencent.py      # 腾讯财经爬虫
│   ├── crawler_eastmoney.py     # 东方财富爬虫
│   ├── data_source_manager.py   # 多数据源管理器
│   ├── storage.py               # CSV数据存储
│   ├── calculator.py            # 价格计算
│   ├── alert.py                 # 提醒功能
│   └── logger.py                # 日志系统
├── config/
│   └── app.py                   # 配置
├── data/                        # 数据文件
├── logs/                        # 日志文件
└── requirements.txt             # Python依赖
```

## 数据源说明

系统采用多数据源设计，确保稳定性：

1. **A股ETF** → 腾讯财经（主） → 东方财富（备用）
2. **美股ETF** → Yahoo Finance

当前数据源失败时自动切换到备用源。

## 技术栈

- Python 3.9+
- Rich - CLI界面
- httpx - HTTP请求
- CSV - 数据存储

## 注意事项

- 本工具仅供个人学习参考，不构成投资建议
- 投资有风险，入市需谨慎

## 许可证

MIT License

---

⭐ 如果对你有帮助，请给个 Star！
