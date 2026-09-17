# 视频多平台发布方案生成

这是一个独立的 Codex Skill 项目，用于把一条产品短视频整理成 TikTok、Instagram Reels、YouTube Shorts、Facebook、X 和 DIY 垂类账号的定制发布方案。

## 内容

- `video-multiplatform-publishing/SKILL.md`：Skill 入口和适用边界
- `video-multiplatform-publishing/references/platform-playbook.md`：平台差异与时间启发式
- `video-multiplatform-publishing/references/output-template.md`：固定的十段式 Markdown 输出结构
- `video-multiplatform-publishing/agents/openai.yaml`：Codex 界面元数据

## 使用

调用 `$video-multiplatform-publishing`，并提供视频或关键帧，再说明“生成这个视频的多平台发布方案”。未提供的视频事实、品牌、链接、时区和账号数据会被标记为待确认，不会被猜测补全。

## 校验

在项目根目录运行：

```powershell
python "C:\Users\47100\.codex\skills\.system\skill-creator\scripts\quick_validate.py" ".\video-multiplatform-publishing"
```

本项目不保存视频、音频、密钥、`.env.local` 或浏览器缓存。
