# ETF 价格跟踪系统

一个用于自动跟踪 ETF 价格、分析盈亏并提供交易提醒的 CLI 工具。

## 功能特性

✅ **自动价格采集** - 从雪球网站定时获取 ETF 价格
✅ **价格计算分析** - 计算关键涨跌幅（±10%、±5%、±3%）对应的价格
✅ **区间提醒** - 当价格进入关键区间时自动提醒
✅ **盈亏计算** - 计算不同价格下的盈亏情况
✅ **数据持久化** - 使用 CSV 文件存储价格历史和交易记录
✅ **定时任务** - 支持 macOS launchd 定时采集（每天上午 10 点）

## 快速开始

### 1. 环境准备

确保 Python 3.9+ 已安装：

```bash
python3 --version
```

### 2. 克隆项目

```bash
git clone <repository-url>
cd ETF_trace
```

### 3. 创建虚拟环境并安装依赖

```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate  # macOS/Linux
# 或
venv\Scripts\activate      # Windows

# 安装依赖
pip install -r requirements.txt
```

### 4. 配置文件

复制示例配置文件：

```bash
cp .env.example .env
```

（可选）编辑 `.env` 文件修改配置：

```bash
# ETF 代码（默认: SZ159915）
ETF_CODE=SZ159915
ETF_NAME=创业板ETF易方达

# 数据存储路径
DATA_DIR=./data
LOG_DIR=./logs
```

### 5. 运行程序

激活虚拟环境：

```bash
source venv/bin/activate
```

#### 方式一：手动分析

```bash
# 分析 ETF（交互式输入）
python main.py analyze

# 或直接指定参数
python main.py analyze --price 2.08 --quantity 10000
```

#### 方式二：仅获取当前价格

```bash
python main.py price
```

#### 方式三：获取并保存价格

```bash
python main.py fetch
```

## 使用示例

### 场景 1：首次使用分析

```bash
$ python main.py analyze
```

程序会自动：
1. 获取当前 ETF 价格
2. 提示输入上次交易价格和数量
3. 分析当前价格是否进入关键区间
4. 显示各价位下的盈亏情况
5. 提供操作建议

### 场景 2：每日自动采集

使用 macOS 定时任务（见下文配置），每天上午 10 点自动采集价格

## 命令参考

### `analyze` 分析 ETF

分析当前价格与交易的对比：

```bash
python main.py analyze [选项]

选项:
  -c, --code TEXT      ETF 代码 [默认: SZ159915]
  -p, --price FLOAT    上次交易价格
  -q, --quantity INT   交易数量（份）
```

**示例**:

```bash
# 交互式输入
python main.py analyze

# 指定参数
python main.py analyze --price 2.08 --quantity 10000

# 指定 ETF 代码
python main.py analyze --code SH510300 --price 3.5 --quantity 5000
```

### `price` 获取价格

仅获取当前价格：

```bash
python main.py price [选项]

选项:
  -c, --code TEXT  ETF 代码 [默认: SZ159915]
```

### `fetch` 获取并保存

获取价格并保存到历史记录：

```bash
python main.py fetch [选项]

选项:
  -c, --code TEXT  ETF 代码 [默认: SZ159915]
```

### `history` 查看历史

查看价格历史记录：

```bash
python main.py history [选项]

选项:
  -c, --code TEXT   ETF 代码 [默认: SZ159915]
  -d, --days INT    显示最近几天 [默认: 7]
```

### `list` 查看交易记录

列出所有交易记录：

```bash
python main.py list
```

## 定时任务配置（macOS）

### 方式 1：使用 launchd（推荐）

1. **修改定时任务配置**

编辑 `~/Library/LaunchAgents/com.etf.tracker.plist`，修改以下路径：

```xml
<array>
    <string>/usr/local/bin/python3</string>  <!-- 你的 Python 路径 -->
    <string>/Users/你的用户名/ETF_trace/scripts/daily_fetch.py</string>  <!-- 项目完整路径 -->
</array>

<key>StandardOutPath</key>
<string>/Users/你的用户名/ETF_trace/logs/scheduler.log</string>  <!-- 日志路径 -->

<key>StandardErrorPath</key>
<string>/Users/你的用户名/ETF_trace/logs/scheduler.error.log</string>  <!-- 错误日志路径 -->
```

查看 Python 路径：

```bash
which python3
```

2. **加载定时任务**

```bash
# 加载任务（开机自动启动）
launchctl load ~/Library/LaunchAgents/com.etf.tracker.plist

# 立即测试运行（不等待定时）
launchctl start com.etf.tracker

# 查看任务状态
launchctl list | grep etf.tracker

# 查看日志
tail -f logs/scheduler.log

# 卸载任务（如需停止）
launchctl unload ~/Library/LaunchAgents/com.etf.tracker.plist
```

**注意事项**：

- 确保电脑在 10:00 处于唤醒状态（可在系统设置中配置电源管理）
- 首次加载可能需要授权（系统设置 → 隐私与安全性 → 完全磁盘访问权限）
- Python 路径需要使用完整路径（使用 `which python3` 查看）

### 方式 2：使用 crontab（Linux/macOS）

```bash
# 编辑 crontab
crontab -e

# 添加定时任务（每天 10:00 执行）
0 10 * * 1-5 cd /Users/你的用户名/ETF_trace && /usr/local/bin/python3 scripts/daily_fetch.py >> logs/cron.log 2>&1
```

## 数据文件说明

### 数据文件位置

所有数据文件存储在 `./data/` 目录下：

- `price_history.csv` - 价格历史记录
- `user_transactions.csv` - 用户交易记录
- `alert_status.csv` - 提醒状态记录
- `alert_history.csv` - 提醒历史记录

### CSV 文件格式

#### price_history.csv

| id | etf_code | etf_name | price | record_time | created_at |
|----|----------|----------|-------|-------------|------------|
| 1 | SZ159915 | 创业板ETF易方达 | 2.15 | 2025-01-16 10:00:00 | 2025-01-16 10:00:00 |

#### user_transactions.csv

| id | etf_code | transaction_price | transaction_quantity | transaction_type | transaction_date | is_alert_enabled | notes | created_at |
|----|----------|-------------------|----------------------|------------------|------------------|------------------|-------|------------|
| 1 | SZ159915 | 2.08 | 10000 | buy | 2025-01-15 | true | 首次买入 | 2025-01-16 10:00:00 |

## 技术架构

### 模块结构

```
ETF_trace/
├── src/
│   ├── logger.py          # 日志系统
│   ├── crawler.py         # 爬虫模块（雪球网站）
│   ├── calculator.py      # 计算模块（价格、盈亏）
│   ├── storage.py         # 数据存储模块（CSV）
│   └── alert.py           # 提醒管理模块
├── scripts/
│   └── daily_fetch.py     # 每日采集脚本
├── config/
│   └── app.py             # 配置管理
├── data/                  # 数据文件
├── logs/                  # 日志文件
├── main.py                # CLI 主程序
└── requirements.txt       # 依赖库
```

### 核心流程

1. **数据采集** → 从雪球网站获取 ETF 价格
2. **价格计算** → 计算关键涨跌幅对应的价格
3. **区间判断** → 判断当前价格是否进入关键区间
4. **盈亏计算** → 计算各价位下的盈亏情况
5. **提醒管理** → 生成提醒并避免重复提醒

## 常见问题

### Q1: 爬虫失败？

**原因**：
- 雪球网站反爬虫机制
- 网络连接问题
- 页面结构变化

**解决方案**：
- 检查网络连接
- 查看日志获取详细错误
- 更新爬虫代码适配新页面结构

### Q2: 定时任务未执行？

**原因**：
- 电脑在 10:00 处于睡眠状态
- launchd 配置错误
- 脚本没有执行权限

**解决方案**：
- 检查电脑在 10:00 是否唤醒
- 检查 launchd 配置语法
- 添加执行权限：`chmod +x scripts/daily_fetch.py`
- 查看系统日志：`tail -f logs/scheduler.error.log`

### Q3: 如何更换 ETF 标的？

**方法**：

编辑 `.env` 文件：

```bash
ETF_CODE=SH510300   # 改为其他 ETF 代码
ETF_NAME=沪深300ETF # 对应名称
```

或在命令中指定：

```bash
python main.py analyze --code SH510300
```

### Q4: 如何备份数据？

**方法**：

```bash
# 备份 data 目录
cp -r data backup_data_$(date +%Y%m%d)

# 或压缩备份
tar -czf etf_data_$(date +%Y%m%d).tar.gz data/
```

## 注意事项

⚠️ **免责声明**：

- 本工具仅供个人学习和参考使用
- 不构成任何投资建议
- 投资有风险，入市需谨慎
- 盈亏自负，使用本工具产生的任何损失概不负责

⚠️ **合规提示**：

- 请遵守雪球网站的使用条款
- 不要频繁请求以免触发反爬虫
- 建议仅在交易时段使用

## 版本信息

- **当前版本**: v1.0.0
- **开发日期**: 2025-01-16
- **作者**: nianxiaohei

## 许可证

MIT License

## 问题反馈

如有问题或建议，欢迎提交 Issue 或 Pull Request。
