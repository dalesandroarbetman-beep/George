# 视频脚本工作流

本项目用于本地完成视频原文提取、中文翻译、原创改写和结构分析，并生成六个平台的双语发布方案。默认优先使用本机 `faster-whisper` 与 Ollama，不调用 OpenAI API，也不把视频、音频或私密配置提交到仓库。

## 主要能力

- `transcribe_local.py`：执行完整四阶段视频处理；明确要求“只提取”时可使用 `--extract-only`。
- `skills/video-multiplatform-publishing/`：基于已确认的视频内容生成平台适配的中英文发布包。
- `contracts/video-workflow-v1.schema.json`：约束视频处理结果的数据结构。

## 本地运行

```powershell
py -3 -m pip install -r requirements-local.txt
py -3 transcribe_local.py "C:\path\to\video.mp4"
```

完整处理需要本机 Ollama 可用，并已有配置的本地模型。视频源文件和生成目录默认不进入 Git。
