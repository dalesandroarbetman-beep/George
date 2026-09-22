# YOHO 内容生产工作台

独立的视频脚本与平台发布文案工作台。该应用与 `apps/yohodiy-listing-console` 完全分离，不共享页面、路由、状态或数据。

## V1 范围

- 双入口：首页分别进入“视频脚本生产线”和“快速发布文案”。
- 完整流程：素材、分析、改写、审核、六平台适配、导出。
- 快速流程：单素材输入、平台选择、发布文案与标签生成。
- 任务记录：查看两种任务的来源、进度和状态。
- 本地任务引擎：任务状态写入项目根目录的 `work/video-content-workbench/tasks/`，该目录已被 Git 忽略。
- P0-2 已接入真实视频处理：上传后由本地 `faster-whisper` 转写，再由本机 Ollama 生成中文翻译、原创改写和结构分析；页面会轮询任务状态并展示真实结果。
- 当前完整链路的“素材 → 分析”已真实运行；“改写 → 审核 → 六平台适配 → 导出”仍保留为后续迭代入口，不能视为已完成的发布链路。

## 本地视频处理

- 上传接口：`POST /api/tasks/transcribe`，使用 `multipart/form-data`。
- 必填字段：`projectName`、`video`。
- 可选字段：`brand`、`brandUrl`、`market`、`language`；默认品牌为 `YOHO`，网址为 `www.yohodiy.com`。
- 支持格式：MP4、MOV、WebM、MKV、AVI；单个视频不超过 500 MB。
- 任务目录：`work/video-content-workbench/tasks/<task-id>/`。源视频、配置、worker 状态和结果均保存在本地；该目录被 Git 忽略。
- 结果文件：`output/转写结果.json`；任务完成后状态变为“待审核”。失败任务会保存错误码、中文错误信息和 `recoverable` 字段，便于重试或人工处理。

### 本地依赖

- Python 3.11+
- `faster-whisper`
- Ollama 服务及可用模型（当前验收使用 `qwen2.5-coder:14b`）
- 不调用 OpenAI API。

## 本地任务 API

- `POST /api/tasks`：创建完整生产线或快速发布文案任务。
- `GET /api/tasks`：按更新时间倒序读取本地任务。
- `GET /api/tasks/{id}`：读取单个任务。
- `PATCH /api/tasks/{id}`：更新阶段、状态、进度和错误详情。

任务合同版本为 `video-content-task/1.0`。任务进入失败状态时必须保存错误码、中文错误信息和是否可恢复。

## 启动

```powershell
npm install
npm run dev
```

访问 `http://127.0.0.1:3086`。
