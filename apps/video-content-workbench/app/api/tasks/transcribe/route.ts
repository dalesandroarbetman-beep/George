import { NextResponse } from "next/server";
import { MediaValidationError, startTranscription } from "../../../lib/transcription-runner";
import { TaskValidationError } from "../../../lib/task-store";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

function text(form: FormData, name: string, fallback = "") {
  const value = form.get(name);
  return typeof value === "string" ? value : fallback;
}

export async function POST(request: Request) {
  try {
    const form = await request.formData();
    const video = form.get("video");
    if (!(video instanceof File)) return NextResponse.json({ error: "请选择视频文件" }, { status: 400 });
    const task = await startTranscription({ projectName: text(form, "projectName"), video, brand: text(form, "brand", "YOHO"), brandUrl: text(form, "brandUrl", "www.yohodiy.com"), market: text(form, "market", "美国"), language: text(form, "language", "双语") });
    return NextResponse.json({ task }, { status: 202 });
  } catch (error) {
    if (error instanceof MediaValidationError || error instanceof TaskValidationError) return NextResponse.json({ error: error.message }, { status: 400 });
    console.error("启动本地转写失败", error);
    return NextResponse.json({ error: "无法启动本地视频处理" }, { status: 500 });
  }
}
