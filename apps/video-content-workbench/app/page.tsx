import Link from "next/link";
import { ArrowRight, CheckCircle2, Clapperboard, Clock3, FileOutput, FileText, Sparkles } from "lucide-react";
import { AppShell } from "./components/AppShell";
import { listTasks } from "./lib/task-store";
import { statusLabels, type WorkbenchTask } from "./lib/task-contract";

export const dynamic = "force-dynamic";

function taskTone(task: WorkbenchTask) {
  if (task.status === "review" || task.status === "failed" || task.status === "cancelled") return "amber";
  if (task.status === "processing" || task.status === "queued") return "blue";
  return "green";
}

export default async function Dashboard() {
  const tasks = await listTasks();
  const pipelineActive = tasks.filter((task) => task.type === "pipeline" && !["completed", "cancelled", "failed"].includes(task.status)).length;
  const quickThisWeek = tasks.filter((task) => task.type === "quick-copy" && Date.now() - new Date(task.createdAt).getTime() < 7 * 24 * 60 * 60 * 1000).length;
  const reviewCount = tasks.filter((task) => task.status === "review").length;
  const completedCount = tasks.filter((task) => task.status === "completed").length;
  const recent = tasks.slice(0, 5);
  return (
    <AppShell title="工作台总览">
      <section className="page-heading">
        <div><span className="eyebrow">CONTENT OPERATIONS</span><h1>今天要处理什么内容？</h1><p>从完整视频项目开始，或直接生成单条素材的发布文案。</p></div>
      </section>

      <section className="entry-grid">
        <Link href="/pipeline" className="entry-panel pipeline-entry">
          <div className="entry-icon coral"><Clapperboard size={25} /></div>
          <div className="entry-copy"><span>完整项目</span><h2>视频脚本生产线</h2><p>素材、分析、改写、审核、六平台适配、导出。</p></div>
          <div className="entry-foot"><span>开始新项目</span><ArrowRight size={18} /></div>
        </Link>
        <Link href="/quick-copy" className="entry-panel quick-entry">
          <div className="entry-icon teal"><Sparkles size={25} /></div>
          <div className="entry-copy"><span>快速任务</span><h2>发布文案与标签</h2><p>导入视频、图片或文字，直接获得平台原生文案。</p></div>
          <div className="entry-foot"><span>快速生成</span><ArrowRight size={18} /></div>
        </Link>
      </section>

      <section className="stat-strip">
        <div><Clapperboard size={18} /><span>进行中</span><strong>{pipelineActive}</strong><small>个完整项目</small></div>
        <div><Sparkles size={18} /><span>本周快写</span><strong>{quickThisWeek}</strong><small>条发布文案</small></div>
        <div><Clock3 size={18} /><span>待审核</span><strong>{reviewCount}</strong><small>项需要确认</small></div>
        <div><FileOutput size={18} /><span>已完成</span><strong>{completedCount}</strong><small>个本地任务</small></div>
      </section>

      <section className="surface recent-section">
        <div className="section-head"><div><h2>最近任务</h2><p>继续处理或查看已经生成的内容。</p></div><Link href="/tasks">查看全部 <ArrowRight size={15} /></Link></div>
        <div className="task-list">
          {recent.map((task) => <div className="task-row" key={task.id}><div className="task-glyph"><FileText size={18} /></div><div className="task-name"><strong>{task.name}</strong><span>{task.type === "pipeline" ? "完整生产线" : "快速发布文案"}</span></div><span className={`status ${taskTone(task)}`}>{statusLabels[task.status]}</span><time>{new Date(task.updatedAt).toLocaleString("zh-CN", { month: "numeric", day: "numeric", hour: "2-digit", minute: "2-digit" })}</time><Link className="icon-button" href="/tasks" aria-label={`查看${task.name}`}><ArrowRight size={17} /></Link></div>)}
          {!recent.length && <div className="loading-state">还没有本地任务，可以从上方任一入口开始。</div>}
        </div>
      </section>

      <div className="boundary-note"><CheckCircle2 size={17} /><span>该工作台独立运行，不连接饰品上品与 GEO 工作台的数据。</span></div>
    </AppShell>
  );
}
