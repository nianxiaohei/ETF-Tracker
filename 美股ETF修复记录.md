# 美股ETF修复记录

## 问题描述

美股ETF取数失败，错误码为100，无法获取价格数据。

## 原因分析

东方财富API对不同市场使用不同的市场代码：
- 深圳A股：市场代码 `0`（如：0.159915）
- 上海A股：市场代码 `1`（如：1.510300）
- **美股ETF：市场代码 `107`（如：107.SCHD）**

原代码只处理了A股（SZ/SH前缀），对于美股ETF（如SCHD, GLDM等）默认使用深圳市场代码 `0`，导致API返回错误码100。

## 修复方案

### 1. 修改 `_get_market_code` 方法

```python
def _get_market_code(self, etf_code: str) -> str:
    """
    根据ETF代码前缀获取市场代码

    参数:
        etf_code: ETF代码（如 SZ159915, SH510300, SCHD）

    返回:
        东方财富市场代码（0=深圳，1=上海，107=美股）
    """
    if etf_code.startswith('SZ') or etf_code.startswith('sz'):
        return '0'  # 深圳市场
    elif etf_code.startswith('SH') or etf_code.startswith('sh'):
        return '1'  # 上海市场
    else:
        # 美股ETF（代码不以SZ/SH开头）
        # 从ETF列表中检查是否为美股
        try:
            from src.storage import etf_list_storage
            all_etfs = etf_list_storage.get_all_etfs()
            if etf_code in all_etfs:
                # 从ETF信息中获取市场组别
                etf_info = all_etfs[etf_code]
                group = etf_info.get('group', '')
                # 如果是美股，使用107市场代码
                if group == '美股':
                    return '107'
        except:
            pass

        # 如果不在列表中，检查是否为常见的美股ETF格式（纯字母）
        import re
        if re.match(r'^[A-Z]+$', etf_code.upper()):
            return '107'  # 默认为美股

        return '0'  # 默认为A股深圳市场
```

### 2. 修改代码提取逻辑

**异步方法**（第107-110行）：
```python
# 去掉前缀，获取纯代码（仅A股需要去掉SZ/SH前缀，美股代码保持不变）
if etf_code.startswith(('SZ', 'sz', 'SH', 'sh')):
    pure_code = etf_code[2:]  # 去掉前缀，如SZ159915 -> 159915
else:
    pure_code = etf_code  # 美股ETF保持原样，如SCHD
```

**同步方法**（第221-223行）：
```python
# 获取市场代码和纯代码（仅A股需要去掉SZ/SH前缀，美股代码保持不变）
market_code = self._get_market_code(etf_code)
if etf_code.startswith(('SZ', 'sz', 'SH', 'sh')):
    pure_code = etf_code[2:]  # 去掉前缀，如SZ159915 -> 159915
else:
    pure_code = etf_code  # 美股ETF保持原样，如SCHD
```

## 修复结果

### 美股ETF测试通过✓

- ✅ SCHD (美国红利股ETF) - 价格: 31.47
- ✅ GLDM (黄金MiniShares信托) - 价格: 98.06
- ✅ USMV (美国最小波动率ETF) - 价格: 96.03
- ✅ VNM (越南ETF) - 价格: 18.03

### A股ETF测试正常✓

- ✅ SZ159915 (创业板ETF) - 价格: 3.321
- ✅ SH510300 (沪深300ETF) - 价格: 4.727

## 技术细节

### 美股市场代码验证

通过东方财富搜索接口确认：
```python
search_url = 'https://searchapi.eastmoney.com/api/suggest/get'
params = {'input': 'SCHD', 'type': 14}
```

返回数据：
```json
{
  "QuoteID": "107.SCHD",
  "MarketType": "7",
  "MktNum": "107"
}
```

确认美股ETF的市场代码为 **107**。

## 总结

修复成功，现在同时支持：
- **A股深圳ETF**：SZ开头，市场代码 0
- **A股上海ETF**：SH开头，市场代码 1
- **美股ETF**：纯字母代码，市场代码 107

所有ETF都能正常获取实时价格数据。