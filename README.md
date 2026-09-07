# George · 短视频脚本提取与改写工作流

项目级规则见 `AGENTS.md`，适用于本项目下的所有任务和对话。

## 运行

报告生成、文本相似度和合规检查只依赖 Python 标准库，不需要 API Key。

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

## 本地视频文案提取

默认使用本地 `faster-whisper`，再通过本机 Ollama 完成中文翻译、改写和结构分析，不调用 OpenAI API。第一次使用需要安装本地依赖，并可能下载一次开源模型；后续识别使用本机缓存。视频源文件不会复制到仓库，转写输出默认被 Git 忽略。

```powershell
py -3 -m pip install -r requirements-local.txt
py -3 transcribe_local.py "C:\path\to\video.mp4"
```

默认使用 `base` 多语言模型、CPU `int8` 推理、自动语言识别和静音检测，并调用本机 Ollama 的 `qwen2.5-coder:14b`。品牌融合时，工作流会过滤原视频中的价格、优惠和平台归属等未确认商业事实，再加入品牌引导。结果写入 `output/transcribe/YYYY-MM-DD/<视频名>/`，包括：

- `原始文案.txt`：带时间戳的原始语音文案
- `转写结果.json`：语言、置信度、时长和分段数据
- `翻译_改写_分析.md`：中文翻译、原创改写稿和结构分析

工作流默认执行提取、翻译、改写和结构分析。只有明确提出“只提取”时才使用：

```powershell
py -3 transcribe_local.py "C:\path\to\video.mp4" --extract-only
```

完整处理需要本机 Ollama 正在运行并已有对应模型；仅提取模式只需要本地 Whisper 模型。若只允许使用已经下载的本地 Whisper 模型，可增加 `--local-files-only`。

需要融合品牌时，在改写稿中传入品牌与链接；原始转写和忠实翻译不会加入品牌信息：

```powershell
py -3 transcribe_local.py "C:\path\to\video.mp4" --brand "YOHO" --brand-url "www.yohodiy.com"
```
