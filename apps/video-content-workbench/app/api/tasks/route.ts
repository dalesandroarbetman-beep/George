import { NextResponse } from "next/server";
import { createTask, listTasks, TaskValidationError } from "../../lib/task-store";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET() {
  try {
    return NextResponse.json({ tasks: await listTasks() });
  } catch (error) {
    console.error("读取任务列表失败", error);
    return NextResponse.json({ error: "读取本地任务失败" }, { status: 500 });
  }
}

export async function POST(request: Request) {
  try {
    const task = await createTask(await request.json());
    return NextResponse.json({ task }, { status: 201 });
  } catch (error) {
    if (error instanceof TaskValidationError) return NextResponse.json({ error: error.message }, { status: 400 });
    console.error("创建任务失败", error);
    return NextResponse.json({ error: "创建本地任务失败" }, { status: 500 });
  }
}
