import "server-only";

import { spawn } from "node:child_process";
import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";
import { createTask, getTaskDirectory, updateTask } from "./task-store";

const ALLOWED_EXTENSIONS = new Set([".mp4", ".mov", ".webm", ".mkv", ".avi"]);
const MAX_SOURCE_BYTES = 500 * 1024 * 1024;

export class MediaValidationError extends Error {}

export async function startTranscription(input: {
  projectName: string;
  video: File;
  brand?: string;
  brandUrl?: string;
  market?: string;
  language?: string;
}) {
  const extension = path.extname(input.video.name).toLowerCase();
  if (!ALLOWED_EXTENSIONS.has(extension)) throw new MediaValidationError("仅支持 MP4、MOV、WebM、MKV 或 AVI 视频");
  if (!input.video.size) throw new MediaValidationError("视频文件为空");
  if (input.video.size > MAX_SOURCE_BYTES) throw new MediaValidationError("视频不能超过 500 MB");

  const task = await createTask({
    name: input.projectName,
    type: "pipeline",
    source: { name: input.video.name, mediaType: input.video.type || "video/mp4", size: input.video.size },
    settings: { brand: input.brand, brandUrl: input.brandUrl, market: input.market, language: input.language },
  });
  const directory = getTaskDirectory(task.id);
  const sourcePath = path.join(directory, `source${extension}`);
  const outputDir = path.join(directory, "output");
  const configPath = path.join(directory, "worker-config.json");
  try {
    await mkdir(outputDir, { recursive: true });
    await writeFile(sourcePath, new Uint8Array(await input.video.arrayBuffer()));
    await writeFile(configPath, `${JSON.stringify({
      projectRoot: path.resolve(process.cwd(), "..", ".."),
      sourcePath,
      outputDir,
      brand: input.brand || "YOHO",
      brandUrl: input.brandUrl || "www.yohodiy.com",
    }, null, 2)}\n`, "utf8");
    const updated = await updateTask(task.id, { status: "processing", stage: "analysis", progress: 20 });
    const worker = path.join(process.cwd(), "scripts", "transcription-worker.mjs");
    const child = spawn(process.execPath, [worker, configPath], { cwd: process.cwd(), detached: true, stdio: "ignore", windowsHide: true });
    child.unref();
    return updated;
  } catch (error) {
    await updateTask(task.id, { status: "failed", stage: "analysis", progress: 0, error: { code: "TRANSCRIPTION_START_FAILED", message: error instanceof Error ? error.message : "无法启动本地转写", recoverable: true } });
    throw error;
  }
}
