import { NextResponse } from "next/server";
import { getTask, TaskValidationError, updateTask } from "../../../lib/task-store";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

type Context = { params: Promise<{ id: string }> };

export async function GET(_request: Request, context: Context) {
  try {
    const task = await getTask((await context.params).id);
    return task ? NextResponse.json({ task }) : NextResponse.json({ error: "任务不存在" }, { status: 404 });
  } catch (error) {
    if (error instanceof TaskValidationError) return NextResponse.json({ error: error.message }, { status: 400 });
    console.error("读取任务失败", error);
    return NextResponse.json({ error: "读取本地任务失败" }, { status: 500 });
  }
}

export async function PATCH(request: Request, context: Context) {
  try {
    const task = await updateTask((await context.params).id, await request.json());
    return task ? NextResponse.json({ task }) : NextResponse.json({ error: "任务不存在" }, { status: 404 });
  } catch (error) {
    if (error instanceof TaskValidationError) return NextResponse.json({ error: error.message }, { status: 400 });
    console.error("更新任务失败", error);
    return NextResponse.json({ error: "更新本地任务失败" }, { status: 500 });
  }
}
