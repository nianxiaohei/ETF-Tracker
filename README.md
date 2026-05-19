# ETF-Tracker（已归档 · CLI only）

此仓库 **不再维护**，仅保留 **终端 CLI** 的历史版本（`python main.py`）。

## 请改用主仓库

**当前开发与 Web / API：** [ETF-Pulse-Web](https://github.com/nianxiaohei/ETF-Pulse-Web)

| 能力 | 本仓库（归档） | ETF-Pulse-Web |
|------|----------------|---------------|
| Rich 终端菜单 | ✅ 末版 | ✅ 保留 |
| Web 前端 | ❌ | ✅ `web/` |
| HTTP API / Docker | ❌ | ✅ |

```bash
git clone https://github.com/nianxiaohei/ETF-Pulse-Web.git
cd ETF-Pulse-Web
pip install -r requirements.txt
python main.py
```

## 说明

- 归档时间点约为提交 `83c8e41` 一代的纯 CLI 功能。
- 新功能、爬虫修复、云端部署等 **仅在 ETF-Pulse-Web 更新**。

---

*本文件用于一次性更新 Tracker 仓库首页说明；主项目文档见 Pulse-Web 仓库中的 `README.md` 与 `ETF总控.md`。*
