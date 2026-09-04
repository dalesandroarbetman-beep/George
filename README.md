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

## TikTok 饰品公开候选

使用 TikTok Creative Center 的公开接口采集近 30 天广告素材候选，不需要 API Key，也不下载视频文件：

```powershell
py -3 collect_tiktok_jewelry.py
```

结果写入 `output/tiktok-jewelry-YYYY-MM-DD/`，包括 `候选视频.json` 和 `候选视频.md`。默认查询 US、GB、CA、AU，并按公开标题、品牌和行业字段归档为 DIY 配件、成品饰品、人设口播。报告中的点赞和 CTR 只代表接口返回值；视频预览地址是 TikTok CDN 的时效链接，可能过期。

当前工作流只保存公开链接、素材 ID、可验证元数据和结构分类，不复制他人完整文案，不提交视频文件，也不绕过地区、登录或反爬限制。
