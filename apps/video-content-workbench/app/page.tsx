import Link from "next/link";
import { ArrowRight, CheckCircle2, Clapperboard, Clock3, FileOutput, FileText, Sparkles } from "lucide-react";
import { AppShell } from "./components/AppShell";

const recent = [
  { name: "珍珠项链开箱视频", type: "完整生产线", state: "待审核", time: "今天 10:24", tone: "amber" },
  { name: "DIY 串珠过程图", type: "快速发布文案", state: "已生成", time: "昨天 16:40", tone: "green" },
  { name: "不锈钢耳环展示", type: "完整生产线", state: "平台适配中", time: "昨天 14:12", tone: "blue" },
];

export default function Dashboard() {
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
        <div><Clapperboard size={18} /><span>进行中</span><strong>3</strong><small>个完整项目</small></div>
        <div><Sparkles size={18} /><span>本周快写</span><strong>12</strong><small>条发布文案</small></div>
        <div><Clock3 size={18} /><span>待审核</span><strong>2</strong><small>项需要确认</small></div>
        <div><FileOutput size={18} /><span>本月导出</span><strong>27</strong><small>份内容包</small></div>
      </section>

      <section className="surface recent-section">
        <div className="section-head"><div><h2>最近任务</h2><p>继续处理或查看已经生成的内容。</p></div><Link href="/tasks">查看全部 <ArrowRight size={15} /></Link></div>
        <div className="task-list">
          {recent.map((task) => <div className="task-row" key={task.name}><div className="task-glyph"><FileText size={18} /></div><div className="task-name"><strong>{task.name}</strong><span>{task.type}</span></div><span className={`status ${task.tone}`}>{task.state}</span><time>{task.time}</time><button className="icon-button" aria-label={`打开${task.name}`}><ArrowRight size={17} /></button></div>)}
        </div>
      </section>

      <div className="boundary-note"><CheckCircle2 size={17} /><span>该工作台独立运行，不连接饰品上品与 GEO 工作台的数据。</span></div>
    </AppShell>
  );
}
