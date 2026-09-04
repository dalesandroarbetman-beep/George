# George · 短视频脚本提取与改写工作流

## 运行

本工作流只依赖 Python 标准库，不需要 API Key。

Windows：

```powershell
py -3 generate_vieormexico_report.py
```

Codespaces / Linux：

```bash
python3 generate_vieormexico_report.py
```

报告会生成到 `output/vieormexico-2026-06-22/`，包括 Markdown 和 HTML 两种格式。

规则库位于 `tools/svsw_tools.py`。`.env.local` 仅用于本地私密配置，已被 Git 忽略。
