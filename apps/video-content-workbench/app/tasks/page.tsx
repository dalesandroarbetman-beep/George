"use client";

import { useEffect, useMemo, useState } from "react";
import { ArrowRight, Filter, Search } from "lucide-react";
import { AppShell } from "../components/AppShell";
import { stageLabels, statusLabels, type WorkbenchTask } from "../lib/task-contract";

export default function TasksPage() {
  const [tasks, setTasks] = useState<WorkbenchTask[]>([]);
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    fetch("/api/tasks")
      .then(async (response) => {
        const payload = await response.json();
        if (!response.ok) throw new Error(payload.error || "读取任务失败");
        setTasks(payload.tasks);
      })
      .catch((caught) => setError(caught instanceof Error ? caught.message : "读取任务失败"))
      .finally(() => setLoading(false));
  }, []);

  const filtered = useMemo(() => tasks.filter((task) => task.name.toLowerCase().includes(query.toLowerCase())), [tasks, query]);
  const taskTypeLabel = (task: WorkbenchTask) => task.type === "pipeline" ? "完整生产线" : "快速发布文案";
  const tone = (task: WorkbenchTask) => task.status === "failed" || task.status === "cancelled" || task.status === "review" ? "amber" : task.status === "processing" || task.status === "queued" ? "blue" : "green";
  const updatedAt = (task: WorkbenchTask) => new Date(task.updatedAt).toLocaleString("zh-CN", { month: "numeric", day: "numeric", hour: "2-digit", minute: "2-digit" });

  return (
    <AppShell title="任务记录">
      <section className="page-heading compact"><div><span className="eyebrow">TASK HISTORY</span><h1>任务记录</h1><p>完整项目和快速任务在这里统一检索，但各自保持独立流程。</p></div></section>
      <section className="surface tasks-surface">
        <div className="task-toolbar"><label><Search size={16} /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="搜索任务名称" /></label><button className="button secondary"><Filter size={16} />筛选</button></div>
        {error && <div className="inline-error" role="alert">{error}</div>}
        {loading ? <div className="loading-state">正在读取本地任务…</div> : <div className="task-table">
          <div className="task-table-head"><span>任务名称</span><span>任务类型</span><span>当前阶段</span><span>状态</span><span>更新时间</span><span /></div>
          {filtered.map((task) => <div className="task-table-row" key={task.id}><div className="task-table-name"><strong>{task.name}</strong>{task.error && <small title={task.error.code}>{task.error.message}</small>}</div><span>{taskTypeLabel(task)}</span><span>{stageLabels[task.stage]} · {task.progress}%</span><span className={`status ${tone(task)}`}>{statusLabels[task.status]}</span><time>{updatedAt(task)}</time><button className="icon-button" aria-label={`打开${task.name}`}><ArrowRight size={16} /></button></div>)}
          {!filtered.length && !error && <div className="loading-state">还没有本地任务</div>}
        </div>}
      </section>
    </AppShell>
  );
}
