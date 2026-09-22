import "server-only";

import { randomUUID } from "node:crypto";
import { mkdir, readFile, readdir, rename, writeFile } from "node:fs/promises";
import path from "node:path";
import {
  PIPELINE_STAGES,
  QUICK_COPY_STAGES,
  TASK_STATUSES,
  TASK_TYPES,
  type TaskStage,
  type TaskStatus,
  type TaskType,
  type VideoWorkflowResult,
  type WorkbenchTask,
} from "./task-contract";

const STORAGE_ROOT = path.resolve(process.cwd(), "..", "..", "work", "video-content-workbench", "tasks");
const MAX_NAME_LENGTH = 120;

type CreateTaskInput = {
  name?: unknown;
  type?: unknown;
  source?: { name?: unknown; mediaType?: unknown; size?: unknown } | null;
  settings?: { brand?: unknown; brandUrl?: unknown; market?: unknown; language?: unknown };
};

type UpdateTaskInput = {
  status?: unknown;
  stage?: unknown;
  progress?: unknown;
  error?: { code?: unknown; message?: unknown; recoverable?: unknown } | null;
};

export class TaskValidationError extends Error {}

function requiredText(value: unknown, field: string, maxLength = MAX_NAME_LENGTH): string {
  if (typeof value !== "string" || !value.trim()) throw new TaskValidationError(`${field}不能为空`);
  return value.trim().slice(0, maxLength);
}

function optionalText(value: unknown, fallback: string, maxLength = 240): string {
  return typeof value === "string" && value.trim() ? value.trim().slice(0, maxLength) : fallback;
}

function isTaskType(value: unknown): value is TaskType {
  return typeof value === "string" && TASK_TYPES.includes(value as TaskType);
}

function isTaskStatus(value: unknown): value is TaskStatus {
  return typeof value === "string" && TASK_STATUSES.includes(value as TaskStatus);
}

function allowedStages(type: TaskType): readonly TaskStage[] {
  return type === "pipeline" ? PIPELINE_STAGES : QUICK_COPY_STAGES;
}

async function ensureRoot() {
  await mkdir(STORAGE_ROOT, { recursive: true });
}

export function getTaskDirectory(id: string) {
  taskPath(id);
  return path.join(STORAGE_ROOT, id);
}

function taskPath(id: string) {
  if (!/^[a-z0-9-]{20,64}$/i.test(id)) throw new TaskValidationError("任务 ID 格式无效");
  return path.join(STORAGE_ROOT, `${id}.json`);
}

async function writeTask(task: WorkbenchTask) {
  await ensureRoot();
  const destination = taskPath(task.id);
  const temporary = `${destination}.${process.pid}.${Date.now()}.tmp`;
  await writeFile(temporary, `${JSON.stringify(task, null, 2)}\n`, "utf8");
  await rename(temporary, destination);
}

function isVideoWorkflowResult(value: unknown): value is VideoWorkflowResult {
  if (!value || typeof value !== "object") return false;
  const report = value as Partial<VideoWorkflowResult>;
  return report.contract_version === "video-workflow/1.0"
    && report.inference === "local faster-whisper; OpenAI API not used"
    && Array.isArray(report.segments)
    && Boolean(report.enrichment && typeof report.enrichment === "object");
}

async function reconcileTask(task: WorkbenchTask): Promise<WorkbenchTask> {
  if (task.type !== "pipeline" || task.status !== "processing" || task.result) return task;
  const directory = getTaskDirectory(task.id);
  try {
    const marker = JSON.parse(await readFile(path.join(directory, "worker-status.json"), "utf8")) as { status?: string; message?: string; code?: string };
    if (marker.status === "completed") {
      const report = JSON.parse(await readFile(path.join(directory, "output", "转写结果.json"), "utf8")) as Record<string, unknown>;
      delete report.source_file;
      if (!isVideoWorkflowResult(report)) throw new TaskValidationError("转写结果不符合 video-workflow/1.0 合同");
      const updated: WorkbenchTask = { ...task, status: "review", stage: "analysis", progress: 40, updatedAt: new Date().toISOString(), error: null, result: report };
      await writeTask(updated);
      return updated;
    }
    if (marker.status === "failed") {
      const updated: WorkbenchTask = { ...task, status: "failed", progress: Math.max(task.progress, 20), updatedAt: new Date().toISOString(), error: { code: marker.code || "TRANSCRIPTION_FAILED", message: marker.message || "本地视频处理失败", recoverable: true } };
      await writeTask(updated);
      return updated;
    }
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code !== "ENOENT") throw error;
  }
  return task;
}

export async function createTask(input: CreateTaskInput): Promise<WorkbenchTask> {
  if (!isTaskType(input.type)) throw new TaskValidationError("任务类型无效");
  const now = new Date().toISOString();
  const source = input.source ? {
    name: requiredText(input.source.name, "素材名称", 255),
    mediaType: optionalText(input.source.mediaType, "application/octet-stream", 120),
    size: Number.isFinite(Number(input.source.size)) ? Math.max(0, Number(input.source.size)) : 0,
  } : null;
  const task: WorkbenchTask = {
    contractVersion: "video-content-task/1.0",
    id: `task-${randomUUID()}`,
    name: requiredText(input.name, "任务名称"),
    type: input.type,
    status: "queued",
    stage: "material",
    progress: 0,
    createdAt: now,
    updatedAt: now,
    source,
    settings: {
      brand: optionalText(input.settings?.brand, "YOHO", 80),
      brandUrl: optionalText(input.settings?.brandUrl, "www.yohodiy.com", 240),
      market: optionalText(input.settings?.market, "美国", 80),
      language: optionalText(input.settings?.language, "双语", 80),
    },
    error: null,
    result: null,
  };
  await writeTask(task);
  return task;
}

export async function getTask(id: string): Promise<WorkbenchTask | null> {
  try {
    return reconcileTask(JSON.parse(await readFile(taskPath(id), "utf8")) as WorkbenchTask);
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code === "ENOENT") return null;
    throw error;
  }
}

export async function listTasks(): Promise<WorkbenchTask[]> {
  await ensureRoot();
  const files = (await readdir(STORAGE_ROOT)).filter((name) => /^task-[a-z0-9-]+\.json$/i.test(name));
  const tasks = await Promise.all(files.map(async (name) => reconcileTask(JSON.parse(await readFile(path.join(STORAGE_ROOT, name), "utf8")) as WorkbenchTask)));
  return tasks.sort((left, right) => right.updatedAt.localeCompare(left.updatedAt));
}

export async function updateTask(id: string, input: UpdateTaskInput): Promise<WorkbenchTask | null> {
  const current = await getTask(id);
  if (!current) return null;
  const status = input.status === undefined ? current.status : input.status;
  if (!isTaskStatus(status)) throw new TaskValidationError("任务状态无效");
  const stage = input.stage === undefined ? current.stage : input.stage;
  if (typeof stage !== "string" || !allowedStages(current.type).includes(stage as TaskStage)) throw new TaskValidationError("任务阶段无效");
  const progress = input.progress === undefined ? current.progress : Number(input.progress);
  if (!Number.isFinite(progress) || progress < 0 || progress > 100) throw new TaskValidationError("任务进度必须为 0 到 100");
  const nextError = input.error === undefined ? current.error : input.error === null ? null : {
    code: optionalText(input.error.code, "TASK_ERROR", 80),
    message: requiredText(input.error.message, "错误信息", 500),
    recoverable: Boolean(input.error.recoverable),
  };
  if (status === "failed" && !nextError) throw new TaskValidationError("失败任务必须包含错误信息");
  const task: WorkbenchTask = {
    ...current,
    status,
    stage: stage as TaskStage,
    progress,
    updatedAt: new Date().toISOString(),
    error: nextError,
  };
  if (status !== "failed") task.error = null;
  await writeTask(task);
  return task;
}
