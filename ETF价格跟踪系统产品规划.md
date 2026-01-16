# ETF 价格跟踪系统产品规划文档

## 一、项目概述

### 项目名称

ETF 价格跟踪与交易提醒系统

### 项目目标

开发一个自动化系统，用于跟踪指定 ETF 的价格变动，基于用户的历史交易价格提供智能交易提醒，并计算不同价格场景下的盈亏情况。

### 适用范围

个人投资者，专注于 ETF（交易型开放式指数基金）的价格监控和交易决策辅助

---

## 二、功能需求分析

### 核心功能模块

#### 模块 1：价格数据采集

- **功能描述**：从雪球网站定时爬取指定 ETF 的实时价格
- **测试标的**：创业板 ETF（SZ159915）
- **数据来源**：https://xueqiu.com/S/SZ159915
- **采集频率**：每个交易日北京时间上午 10:00
- **技术要点**：
  - 需要处理反爬虫机制
  - 需要区分交易日和非交易日
  - 数据需要持久化存储

**技术方案**：

- **数据源**：雪球网站（已确定）
- 使用 Python 的 requests/httpx 库发送 HTTP 请求
- 使用 BeautifulSoup 或 PyQuery 解析 HTML
- 使用 pandas 处理数据
- **存储方案**：CSV 文件（已确定）

---

#### 模块 2：价格计算引擎

- **功能描述**：根据用户的上次交易价格，计算关键涨跌幅对应的价位
- **计算规则**：
  - 上涨 10% 价格 = 上次交易价格 × 1.10
  - 上涨 5% 价格 = 上次交易价格 × 1.05
  - 上涨 3% 价格 = 上次交易价格 × 1.03
  - 下跌 3% 价格 = 上次交易价格 × 0.97
  - 下跌 5% 价格 = 上次交易价格 × 0.95
  - 下跌 10% 价格 = 上次交易价格 × 0.90
- **精度要求**：
  - **计算精度**：内部计算保留小数点后 4 位，确保盈亏计算准确
  - **显示精度**：对外显示保留小数点后两位（0.01 元）

**示例**：

```
上次交易价格：2.08 元

计算值（内部，4位小数）：
+10% = 2.2880 元（2.08 × 1.10）
+5% = 2.1840 元（2.08 × 1.05）
+3% = 2.1424 元（2.08 × 1.03）
-3% = 2.0176 元（2.08 × 0.97）
-5% = 1.9760 元（2.08 × 0.95）
-10% = 1.8720 元（2.08 × 0.90）

显示值（对外，2位小数）：
+10% = 2.29 元
+5% = 2.18 元
+3% = 2.14 元
-3% = 2.02 元
-5% = 1.98 元
-10% = 1.87 元
```

---

#### 模块 3：历史交易价格对比

- **功能描述**：用户输入上次交易价格，系统自动判断当前价格是否接近关键涨跌幅区间
- **标记规则**：
  - 价格区间 1：上次交易价 +3% ~ +5% 区间（即上次交易价的 1.03 倍至 1.05 倍）
  - 价格区间 2：上次交易价 -5% ~ -3% 区间（即上次交易价的 0.95 倍至 0.97 倍）
- **输出形式**：
  - 如果当前价格落在任一区间，高亮标记
  - 显示当前价格、上次交易价格、以及距离各关键价位的涨跌幅
- **提醒策略**：**进入区间才提醒一次**（去重机制）
  - 只在首次进入区间时提醒
  - 如果价格变化导致离开区间后再进入，会再次提醒
  - 需要记录上次的状态（是否在区间内、在哪个区间）

**示例场景**：

**场景 1：首次进入区间（会提醒）**

```
上次交易价格：2.08 元
当前价格：2.14 元

关键价位（基于上次交易价 2.08 元）：
  +5% = 2.18 元
  +3% = 2.14 元
  -3% = 2.02 元
  -5% = 1.98 元

分析结果：
✓ 当前价格 2.14 元落在 [+3% ~ +5%] 区间（2.14 - 2.18 元）
  - 距离 +5% 目标（2.18 元）：-1.87%
  - 距离 +3% 目标（2.14 元）：0.00%（刚好在 +3% 价位）

⚠️ 提醒：首次进入 [+3% ~ +5%] 区间
```

**场景 2：持续在区间内（不提醒）**

```
上次交易价格：2.08 元
当前价格：2.15 元

分析结果：
✓ 当前价格 2.15 元落在 [+3% ~ +5%] 区间（2.14 - 2.18 元）
  - 距离 +5% 目标（2.18 元）：-1.40%
  - 距离 +3% 目标（2.14 元）：+0.47%

（状态未变化，不显示提醒）
```

---

#### 模块 4：盈亏计算引擎

- **功能描述**：根据用户输入的交易数量，计算在不同涨跌幅价位下的盈亏情况
- **输入参数**：
  - 上次交易价格（用户输入）
  - 上次交易数量（用户输入）
- **计算维度**：
  - 在 +10%、+5%、+3%、-3%、-5%、-10% 价位下（基于上次交易价格计算），以同样数量交易
  - 计算与上次交易金额的差额
- **公式**：

```
上次交易金额 = 上次交易价格 × 上次交易数量
当前交易金额 = 当前价格 × 上次交易数量

对于每个涨跌幅（+10%、+5%、+3%、-3%、-5%、-10%）：
目标价（高精度，4位小数）= 上次交易价格 × (1 + 涨跌幅)
目标价（显示值，2位小数）= round(目标价高精度, 2)
目标价交易金额 = 目标价（高精度） × 上次交易数量
盈亏金额 = 目标价交易金额 - 上次交易金额
盈亏率 = (盈亏金额 / 上次交易金额) × 100% = 涨跌幅（精确）

注意：
- 涨跌幅：基于上次交易价格计算（例如：+5% 目标价 = 上次交易价 × 1.05）
- 计算精度：内部使用4位小数计算，确保盈亏率精确等于涨跌幅
- 显示精度：目标价显示时保留2位小数，但盈亏计算使用高精度值
- 盈亏率：使用高精度目标价计算，精确等于涨跌幅（±5.00%、±3.00%）
```

**示例**：

```
上次交易：2.08 元 × 10,000 份 = 20,800 元

关键价位（基于上次交易价 2.08 元）：
  +5% = 2.18 元
  +3% = 2.14 元
  -3% = 2.02 元
  -5% = 1.98 元

盈亏分析（以 +5% 价位为例）：
  目标价交易金额：2.18 × 10,000 = 21,800 元
  盈亏金额：+1,000 元
  盈亏率：+5.00%（等于涨跌幅）
```

---

### 扩展功能（二期）

1. **多 ETF 支持**：支持用户自定义添加多个 ETF 标的

---

## 三、技术架构设计

### 系统架构图

```
┌─────────────────────────────────────────────────────────────┐
│                    ETF 价格跟踪系统                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐       ┌──────────────┐       ┌─────────┐  │
│  │  数据采集层  │──────▶│  数据处理层   │──────▶│ 应用层   │  │
│  │             │       │              │       │         │  │
│  │ • 爬虫模块  │       │ • 价格计算    │       │ • CLI   │  │
│  │ • 定时任务  │       │ • 盈亏计算    │       │ • Web   │  │
│  │ • 数据存储  │       │ • 区间判断    │       │         │  │
│  └─────────────┘       └──────────────┘       └─────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 技术选型

#### 后端技术栈

- **编程语言**：Python 3.9+
- **网络请求**：httpx（异步支持，更现代的 API）
- **HTML 解析**：BeautifulSoup4 / parsel（XPath/CSS 选择器）
- **数据存储**：
  - **CSV 文件**（已确定，初期方案）
    - `data/price_history.csv`：价格历史记录
    - `data/user_transactions.csv`：用户交易记录
    - `data/alert_status.csv`：提醒状态记录
    - `data/alert_history.csv`：提醒历史记录
- **定时任务**：macOS launchd（系统级定时任务，到点自动启动脚本）
  - 备选方案：APScheduler（如需程序常驻运行）
- **数据计算**：pandas（数据处理）、NumPy（数值计算）

#### 前端/交互层技术栈

- **CLI 版本**：Typer / Click（Python 命令行框架）
- **Web 版本**：
  - 后端：FastAPI（高性能异步框架）
  - 前端：HTML + JavaScript + Bootstrap/Ant Design
  - 或者：Streamlit（Python 快速构建数据应用）

#### 其他工具

- **配置管理**：python-dotenv（环境变量管理）
- **日志系统**：loguru（更友好的日志记录）
- **测试框架**：pytest（单元测试、集成测试）

---

## 四、数据模型设计

### 核心数据表

#### 1. 价格数据表（price_history）

| 字段名      | 类型          | 说明                      |
| ----------- | ------------- | ------------------------- |
| id          | INTEGER       | 主键                      |
| etf_code    | VARCHAR       | ETF 代码（如 SZ159915）   |
| etf_name    | VARCHAR       | ETF 名称（如 创业板 ETF） |
| price       | DECIMAL(10,2) | 价格（元）                |
| record_time | DATETIME      | 记录时间                  |
| created_at  | TIMESTAMP     | 创建时间                  |

#### 2. 用户交易记录表（user_transactions）

| 字段名               | 类型          | 说明                 |
| -------------------- | ------------- | -------------------- |
| id                   | INTEGER       | 主键                 |
| etf_code             | VARCHAR       | ETF 代码             |
| transaction_price    | DECIMAL(10,2) | 交易价格             |
| transaction_quantity | INTEGER       | 交易数量（份）       |
| transaction_type     | VARCHAR       | 交易类型（buy/sell） |
| transaction_date     | DATE          | 交易日期             |
| is_alert_enabled     | BOOLEAN       | 是否开启提醒         |
| notes                | TEXT          | 备注信息             |
| created_at           | TIMESTAMP     | 创建时间             |

#### 3. 提醒记录表（alert_history）

| 字段名         | 类型          | 说明                              |
| -------------- | ------------- | --------------------------------- |
| id             | INTEGER       | 主键                              |
| transaction_id | INTEGER       | 关联的交易记录 ID                 |
| alert_type     | VARCHAR       | 提醒类型（+5%, +3%, -3%, -5%）    |
| current_price  | DECIMAL(10,2) | 当前价格                          |
| target_price   | DECIMAL(10,2) | 目标价格                          |
| status         | VARCHAR       | 状态（pending/triggered/ignored） |
| triggered_at   | TIMESTAMP     | 触发时间                          |

#### 4. 提醒状态记录表（alert_status）

| 字段名          | 类型          | 说明                                         |
| --------------- | ------------- | -------------------------------------------- |
| id              | INTEGER       | 主键                                         |
| transaction_id  | INTEGER       | 关联的交易记录 ID                            |
| etf_code        | VARCHAR       | ETF 代码                                     |
| last_price      | DECIMAL(10,2) | 上次分析时的当前价格                         |
| in_range        | BOOLEAN       | 上次是否在区间内                             |
| range_type      | VARCHAR       | 上次所在的区间类型（[+3%~+5%] 或 [-5%~-3%]） |
| last_check_time | TIMESTAMP     | 上次检查时间                                 |
| updated_at      | TIMESTAMP     | 更新时间                                     |

**说明**：用于记录每个交易记录的提醒状态，实现"进入区间才提醒一次"的去重机制

---

## 五、项目里程碑

### 第一阶段：CLI 工具开发（2-3 周）

**目标**：完成核心功能，提供命令行工具

**任务分解**：

1. **Step 1：项目基础搭建**

   - 搭建项目基础框架
   - 实现雪球网站数据爬虫功能（获取 SZ159915 价格）
   - 实现价格计算功能（+10%, +5%, +3%, -3%, -5%, -10%）
   - 数据存储到 CSV 文件

2. **Step 2：核心功能开发**

   - 配置 macOS launchd 定时任务（每天上午 10 点自动执行）
   - 开发 CLI 交互界面
   - 实现历史价格对比功能
   - 实现盈亏计算功能

3. **Step 3：测试与部署**
   - 完善错误处理和日志系统
   - 编写使用文档
   - 测试和 Bug 修复
   - 部署和试运行

**交付物**：

- 可运行的 CLI 工具
- 使用说明文档
- 示例数据

---

### 第二阶段：Web 应用开发（3-4 周）

**目标**：开发 Web 界面，提升易用性

**任务分解**：

1. **Step 4：后端 API 开发**

   - 使用 FastAPI 开发 RESTful API
   - 数据库使用 PostgreSQL
   - 实现用户认证系统

2. **Step 5：前端界面开发**
   - 开发前端界面（React/Vue.js）
   - 响应式布局适配移动端

**交付物**：

- Web 应用程序
- 部署方案

---

## 六、详细实现方案

### 模块 1：数据采集模块详细设计

#### 1.1 爬虫实现步骤

**步骤 1**：发送 HTTP 请求获取雪球页面

关键信息：

- URL: https://xueqiu.com/S/SZ159915
- 请求头：需要 User-Agent 模拟浏览器
- Cookie：可能需要处理（雪球有反爬虫）

**步骤 2**：解析 HTML 获取价格

- 查看页面源代码，找到价格所在的 HTML 标签
- 使用浏览器开发者工具（F12）检查元素
- 雪球价格通常在某个 span 或 div 中，通过 CSS 类名定位

**步骤 3**：数据清洗和验证

- 去除多余字符（如人民币符号 ¥）
- 转换为浮点数
- 验证价格有效性（如范围检查：0 < price < 1000）

**步骤 4**：存储数据

- 保存到 CSV: `data/price_history.csv`
- 字段：日期、时间、ETF 代码、价格

#### 1.2 反爬虫策略处理

可能遇到的问题：

1. **User-Agent 检测**：需要设置合理的 User-Agent
2. **IP 限制**：如果请求频繁可能被封
3. **Cookie 验证**：需要维护会话

解决方案：

- 使用随机的 User-Agent 池
- 控制请求频率（使用时延）
- 如果需要登录，维护会话 Cookie
- 考虑使用代理 IP（二期）

#### 1.3 定时任务实现

**方案选择**：使用 macOS launchd 系统定时任务

**工作原理**：

- macOS 系统在指定时间自动启动 Python 脚本
- 脚本执行完自动退出（不常驻运行）
- 适合简单的定时任务场景

**实现步骤**：

**步骤 1**：创建可执行的 Python 脚本

```python
# scripts/daily_fetch.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.crawler import fetch_price
from src.storage import save_to_csv
from loguru import logger

def main():
    """每日定时任务主函数"""
    try:
        logger.info("开始执行每日价格采集任务")
        price_data = fetch_price('SZ159915')
        save_to_csv(price_data)
        logger.info("任务执行成功")
    except Exception as e:
        logger.error(f"任务执行失败: {e}")
        raise

if __name__ == '__main__':
    main()
```

**步骤 2**：创建 launchd 配置文件

创建文件：`~/Library/LaunchAgents/com.etf.tracker.plist`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.etf.tracker</string>

    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/python3</string>
        <string>/Users/你的用户名/ETF_trace/scripts/daily_fetch.py</string>
    </array>

    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>10</integer>
        <key>Minute</key>
        <integer>0</integer>
        <key>Weekday</key>
        <integer>1</integer>  <!-- 1=周一, 2=周二, 3=周三, 4=周四, 5=周五 -->
    </dict>
    <!-- 注意：launchd 的 StartCalendarInterval 只能设置单个 Weekday 值 -->
    <!-- 如需周一到周五都执行，需要创建 5 个 plist 文件，或使用其他定时方案 -->

    <key>StandardOutPath</key>
    <string>/Users/你的用户名/ETF_trace/logs/scheduler.log</string>

    <key>StandardErrorPath</key>
    <string>/Users/你的用户名/ETF_trace/logs/scheduler.error.log</string>

    <key>RunAtLoad</key>
    <false/>
</dict>
</plist>
```

**步骤 3**：加载定时任务

```bash
# 加载任务（开机自动启动）
launchctl load ~/Library/LaunchAgents/com.etf.tracker.plist

# 立即测试运行一次（不等待定时）
launchctl start com.etf.tracker

# 查看任务状态
launchctl list | grep etf.tracker

# 卸载任务（如需停止）
launchctl unload ~/Library/LaunchAgents/com.etf.tracker.plist
```

**配置说明**：

- **触发时间**：每天 10:00（北京时间，需确保系统时区正确）
- **执行日期**：周一至周五（Weekday 1-5）
  - **注意**：launchd 的 `StartCalendarInterval` 只能设置单个 Weekday 值
  - **解决方案**：创建 5 个 plist 文件（分别设置 Weekday 1-5），或使用脚本在运行时判断是否为交易日
- **时区处理**：脚本内部使用 `Asia/Shanghai` 时区判断
- **任务执行**：调用爬虫函数，保存价格到 CSV

**交易日判断**：

- **交易日规则**：只排除周末（已确定）
  - 周一至周五（Weekday 1-5）：执行任务
  - 周六、周日：不执行任务
- 初始版本不处理法定节假日（节假日也会执行，但数据可能无效）
- 进阶版本可配置交易日历（二期功能）

**注意事项**：

1. **Python 路径**：需要修改 plist 中的 Python 路径（使用 `which python3` 查看）
2. **脚本路径**：需要修改为实际的项目路径
3. **日志目录**：确保 `logs/` 目录存在
4. **权限问题**：首次加载可能需要授权（系统设置 → 隐私与安全性 → 完全磁盘访问权限）
5. **电脑睡眠**：如果电脑在 10:00 处于睡眠状态，任务不会执行（需要保持电脑唤醒或使用 `Wake` 配置）

**备选方案**：如果需要在程序运行时查询任务状态或手动触发，可使用 APScheduler（程序常驻运行）

---

### 模块 2：价格计算模块详细设计

#### 2.1 计算逻辑

```python
def calculate_price_levels(transaction_price, precision=4):
    """
    计算关键价格水平（基于上次交易价格）

    参数:
        transaction_price: 上次交易价格
        precision: 计算精度（默认4位小数，用于内部计算）

    返回:
        dict: 包含各涨跌幅对应的目标价（高精度值，用于计算）
    """
    return {
        '+10%': round(transaction_price * 1.10, precision),
        '+5%': round(transaction_price * 1.05, precision),
        '+3%': round(transaction_price * 1.03, precision),
        '-3%': round(transaction_price * 0.97, precision),
        '-5%': round(transaction_price * 0.95, precision),
        '-10%': round(transaction_price * 0.90, precision)
    }

def format_price_for_display(price, precision=2):
    """
    格式化价格用于显示（保留2位小数）

    参数:
        price: 价格值
        precision: 显示精度（默认2位小数）

    返回:
        float: 格式化后的价格
    """
    return round(price, precision)
```

**边界情况处理**：

- 价格精度：ETF 价格通常精确到分（0.01 元）
- 四舍五入：使用 Python 的 round() 函数，保留 2 位小数
- 输入验证：确保价格在合理范围内

#### 2.2 区间判断逻辑

```python
def check_price_in_range(current_price, transaction_price):
    """
    判断当前价格是否落在关键区间（基于上次交易价格计算的区间）

    参数:
        current_price: 当前价格
        transaction_price: 上次交易价格

    返回:
        dict: 包含区间判断结果
    """
    levels = calculate_price_levels(transaction_price)

    results = {
        '+5%': levels['+5%'],
        '+3%': levels['+3%'],
        '-3%': levels['-3%'],
        '-5%': levels['-5%'],
        'in_range': False,
        'matched_range': None
    }

    # 判断当前价格是否在 +3% 到 +5% 区间
    if levels['+3%'] <= current_price <= levels['+5%']:
        results['in_range'] = True
        results['matched_range'] = '[+3% ~ +5%]'

    # 判断当前价格是否在 -5% 到 -3% 区间
    elif levels['-5%'] <= current_price <= levels['-3%']:
        results['in_range'] = True
        results['matched_range'] = '[-5% ~ -3%]'

    return results
```

---

### 模块 3：历史交易价格对比模块详细设计

#### 3.1 区间判断与提醒去重逻辑

```python
def check_price_in_range_with_alert(current_price, transaction_price, transaction_id):
    """
    判断当前价格是否落在关键区间（基于上次交易价格），并实现提醒去重

    参数:
        current_price: 当前价格
        transaction_price: 上次交易价格
        transaction_id: 交易记录 ID

    返回:
        dict: 包含区间判断结果和是否需要提醒
    """
    # 1. 判断当前价格是否在区间内（区间基于上次交易价格计算）
    levels = calculate_price_levels(transaction_price)
    in_range = False
    matched_range = None

    if levels['+3%'] <= current_price <= levels['+5%']:
        in_range = True
        matched_range = '[+3% ~ +5%]'
    elif levels['-5%'] <= current_price <= levels['-3%']:
        in_range = True
        matched_range = '[-5% ~ -3%]'

    # 2. 读取上次的状态
    last_status = get_alert_status(transaction_id)

    # 3. 判断是否需要提醒（去重逻辑）
    should_alert = False
    alert_reason = None

    if in_range:
        if last_status is None:
            # 首次检查，在区间内，需要提醒
            should_alert = True
            alert_reason = '首次进入区间'
        elif not last_status['in_range']:
            # 上次不在区间，现在在区间，状态变化，需要提醒
            should_alert = True
            alert_reason = '从区间外进入区间'
        elif last_status['range_type'] != matched_range:
            # 上次在不同区间，现在换到新区间，需要提醒
            should_alert = True
            alert_reason = '切换到新区间'
        # else: 上次就在同一区间，不提醒

    # 4. 更新状态记录
    update_alert_status(
        transaction_id=transaction_id,
        last_price=current_price,
        in_range=in_range,
        range_type=matched_range
    )

    # 5. 如果需要提醒，记录提醒历史
    if should_alert:
        create_alert_history(
            transaction_id=transaction_id,
            alert_type=matched_range,
            current_price=current_price,
            target_price=transaction_price
        )

    return {
        'in_range': in_range,
        'matched_range': matched_range,
        'should_alert': should_alert,
        'alert_reason': alert_reason,
        'levels': levels
    }
```

#### 3.2 状态记录函数

```python
def get_alert_status(transaction_id):
    """
    获取上次的提醒状态

    返回:
        dict 或 None: {
            'last_price': float,
            'in_range': bool,
            'range_type': str
        }
    """
    # 从 CSV 或数据库读取
    # 简化版：从 CSV 文件读取
    status_file = 'data/alert_status.csv'
    # ... 读取逻辑
    return status_data

def update_alert_status(transaction_id, last_price, in_range, range_type):
    """
    更新提醒状态记录
    """
    # 保存到 CSV 或数据库
    status_file = 'data/alert_status.csv'
    # ... 保存逻辑
    pass

def create_alert_history(transaction_id, alert_type, current_price, target_price):
    """
    创建提醒历史记录
    """
    # 保存到 alert_history.csv
    alert_file = 'data/alert_history.csv'
    # ... 保存逻辑
    pass
```

#### 3.3 提醒去重示例场景

**场景 1：首次进入区间**

```
上次交易价格：2.08 元
关键价位：+5%=2.18, +3%=2.14, -3%=2.02, -5%=1.98

第1天：
- 当前价格：2.15 元
- 判断：在 [+3% ~ +5%] 区间（2.14 - 2.18 元）
- 上次状态：None（首次）
- 结果：⚠️ 提醒（首次进入区间）
- 更新状态：in_range=True, range_type='[+3% ~ +5%]'
```

**场景 2：持续在区间内**

```
上次交易价格：2.08 元
关键价位：+5%=2.18, +3%=2.14, -3%=2.02, -5%=1.98

第2天：
- 当前价格：2.16 元
- 判断：在 [+3% ~ +5%] 区间（2.14 - 2.18 元）
- 上次状态：in_range=True, range_type='[+3% ~ +5%]'
- 结果：不提醒（状态未变化）
- 更新状态：保持不变
```

**场景 3：离开区间后再进入**

```
上次交易价格：2.08 元
关键价位：+5%=2.18, +3%=2.14, -3%=2.02, -5%=1.98

第3天：
- 当前价格：2.00 元
- 判断：不在区间内（2.00 < 2.02，不在 [-5% ~ -3%] 区间）
- 上次状态：in_range=True
- 结果：不提醒（不在区间）
- 更新状态：in_range=False, range_type=None

第4天：
- 当前价格：2.15 元
- 判断：在 [+3% ~ +5%] 区间（2.14 - 2.18 元）
- 上次状态：in_range=False
- 结果：⚠️ 提醒（再次进入区间）
- 更新状态：in_range=True, range_type='[+3% ~ +5%]'
```

---

### 模块 4：盈亏计算模块详细设计

#### 4.1 盈亏计算逻辑

```python
def calculate_profit_loss(transaction_price, quantity):
    """
    计算在不同涨跌幅价位下的盈亏（基于上次交易价格）

    参数:
        transaction_price: 上次交易价格
        quantity: 交易数量（份）

    返回:
        dict: 包含各涨跌幅价位下的盈亏情况
    """
    # 计算上次交易金额
    last_amount = transaction_price * quantity

    # 计算各涨跌幅对应的目标价（使用高精度，4位小数）
    levels = calculate_price_levels(transaction_price, precision=4)

    results = {
        'last_transaction': {
            'price': transaction_price,
            'quantity': quantity,
            'amount': round(last_amount, 2)
        }
    }

    # 计算各价位下的盈亏（使用高精度的目标价）
    for label, target_price_precise in levels.items():
        # 使用高精度价格计算盈亏
        target_amount = target_price_precise * quantity
        profit_amount = target_amount - last_amount
        profit_percentage = (profit_amount / last_amount) * 100

        results[label] = {
            'price_precise': target_price_precise,  # 高精度值（用于计算）
            'price': format_price_for_display(target_price_precise, 2),  # 显示值（2位小数）
            'amount': round(target_amount, 2),
            'profit_amount': round(profit_amount, 2),
            'profit_percentage': round(profit_percentage, 2)
        }

    return results
```

#### 4.2 数据展示格式

**CLI 输出示例**：

````
╔════════════════════════════════════════════╗
║         ETF 交易提醒                        ║
╚════════════════════════════════════════════╝

ETF：创业板ETF易方达(SZ159915)


当前价格: 2.15 元 (2025-01-16 10:00)
上次交易价格: 2.08 元

当前价比上次交易价格: +3.36%

⚠️  提醒：当前价格 2.15 元落在 [+3% ~ +5%] 区间内！

上次交易数量: 10,000 份
上次交易金额: 20,800 元

【关键价位分析】
（涨跌幅基于上次交易价格 2.08 元计算）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
涨跌幅      对应价   上次交易数量计算   交易金额      盈亏         盈亏率
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
+10%        2.29          10,000    22,880      +2,080.00   +10.00%
+5%         2.18          10,000    21,840      +1,040.00   +5.00%
+3%         2.14          10,000    21,424      +624.00     +3.00%
当前价       2.15          10,000    21,500      +700.00     +3.37%
-3%         2.02          10,000    20,176      -624.00     -3.00%
-5%         1.98          10,000    19,760      -1,040.00   -5.00%
-10%        1.87          10,000    18,720      -2,080.00   -10.00%
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

---

### 模块 5：CLI 交互界面设计

#### 5.1 主要命令

```bash
# 初始化配置
etf-tracker config init

# 手动获取当前价格
etf-tracker price get --code SZ159915

# 查看价格历史
etf-tracker price history --code SZ159915 --days 7

# 分析交易
etf-tracker analyze --code SZ159915 --price 2.08 --quantity 10000

# 启动定时任务（后台运行）
etf-tracker schedule start

# 停止定时任务
etf-tracker schedule stop

# 查看定时任务状态
etf-tracker schedule status
````

#### 5.2 交互流程

**场景 1：首次使用**

```
$ etf-tracker config init
欢迎使用 ETF 价格跟踪系统！

请配置以下信息：
1. ETF 代码（默认为 SZ159915）: SZ159915
2. 数据存储路径（默认为 ./data）: ./data
3. 是否启用定时任务（Y/n）: Y
4. 定时任务时间（默认为 10:00）: 10:00

✓ 配置已保存到 config.ini
```

**场景 2：分析交易**

```
$ etf-tracker analyze --code SZ159915
请输入上次交易价格: 2.08
请输入交易数量（份）: 10000

[显示分析结果]
```

---

## 七、部署方案

### 环境要求

- **操作系统**：Linux / macOS / Windows
- **Python 版本**：3.9 或更高
- **依赖库**：requirements.txt

### 部署步骤

#### 开发环境

```bash
# 克隆代码
git clone <repository-url>
cd etf-tracker

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate    # Windows

# 安装依赖
pip install -r requirements.txt

# 初始化配置
python main.py config init

# 测试运行
python main.py price get --code SZ159915
```

#### macOS 本地环境（定时任务配置）

```bash
# 1. 确保脚本有执行权限
chmod +x scripts/daily_fetch.py

# 2. 修改 launchd 配置文件中的路径（Python 路径和项目路径）
# 编辑 ~/Library/LaunchAgents/com.etf.tracker.plist

# 3. 加载定时任务
launchctl load ~/Library/LaunchAgents/com.etf.tracker.plist

# 4. 立即测试运行（不等待定时）
launchctl start com.etf.tracker

# 5. 查看任务状态
launchctl list | grep etf.tracker

# 6. 查看日志
tail -f logs/scheduler.log

# 7. 卸载任务（如需停止）
launchctl unload ~/Library/LaunchAgents/com.etf.tracker.plist
```

**注意事项**：

- 确保电脑在 10:00 处于唤醒状态（或配置系统唤醒）
- 首次加载可能需要授权（系统设置 → 隐私与安全性）
- Python 路径需要使用完整路径（`which python3` 查看）

#### 生产环境（Linux 服务器，二期）

```bash
# 使用 systemd 服务（推荐）
sudo cp etf-tracker.service /etc/systemd/system/
sudo systemctl enable etf-tracker
sudo systemctl start etf-tracker
sudo systemctl status etf-tracker
```

---

## 八、测试计划

### 单元测试

- **测试覆盖率目标**：> 80%
- **测试内容**：
  1. 价格计算函数测试
  2. 盈亏计算函数测试
  3. 区间判断函数测试
  4. 数据存储函数测试

### 集成测试

- **爬虫测试**：测试雪球网站数据获取
- **定时任务测试**：验证 10 点执行任务
- **全流程测试**：从数据采集到分析展示

### 测试命令

```bash
# 运行所有测试
pytest tests/

# 运行覆盖率检查
pytest --cov=. --cov-report=html

# 运行特定测试
pytest tests/test_calculator.py
```

---

## 九、维护与监控

### 日志系统

- **日志文件**：logs/app.log
- **日志级别**：INFO（正常）、WARNING（警告）、ERROR（错误）
- **日志内容**：
  - 爬虫执行情况
  - 价格记录
  - 系统错误
  - 定时任务状态

### 监控指标

- **数据采集成功率**：目标 > 95%
- **定时任务执行率**：目标 100%
- **系统响应时间**：目标 < 1 秒

### 常见问题处理

1. **爬虫失败**：

   - 检查网络连接
   - 检查雪球网站是否改版
   - 查看日志获取详细错误

2. **定时任务未执行**：
   - 检查系统时间是否正确
   - 确认是否交易日（周一至周五）
   - 检查电脑是否在 10:00 处于唤醒状态
   - 查看任务状态：`launchctl list | grep etf.tracker`
   - 查看日志：`tail -f logs/scheduler.log`
   - 检查 launchd 配置是否正确加载：`launchctl list com.etf.tracker`

---

## 十、风险评估

### 技术风险

| 风险           | 可能性 | 影响 | 应对措施                               |
| -------------- | ------ | ---- | -------------------------------------- |
| 雪球网站反爬虫 | 中     | 高   | 使用延迟、随机 User-Agent、维护 Cookie |
| 网站结构变化   | 低     | 高   | 定期监控、建立监控告警                 |
| 定时任务失败   | 低     | 中   | 增加重试机制、日志监控                 |
| 数据准确性     | 中     | 高   | 多数据源对比、数据校验                 |

### 业务风险

- **市场风险**：本工具仅作为参考，不构成投资建议
- **合规风险**：确保数据采集符合雪球网站的使用条款
- **使用风险**：用户需自行判断交易时机，盈亏自负

---

## 十一、附录

### 术语表

| 术语   | 说明                              |
| ------ | --------------------------------- |
| ETF    | 交易型开放式指数基金              |
| 涨跌幅 | (当前价 - 参考价) / 参考价 × 100% |
| 止盈   | 达到盈利目标后卖出获利            |
| 止损   | 亏损达到一定程度后卖出以控制损失  |

### 参考资料

- [雪球网站](https://xueqiu.com/)
- [macOS launchd 官方文档](https://developer.apple.com/library/archive/documentation/MacOSX/Conceptual/BPSystemStartup/Chapters/CreatingLaunchdJobs.html)
- [launchd.plist 配置指南](https://www.launchd.info/)
- [APScheduler 文档](https://apscheduler.readthedocs.io/)（备选方案）
- [FastAPI 文档](https://fastapi.tiangolo.com/)

### 联系方式

- 项目负责人：nianxiaohei
- 创建日期：2025-01-16
