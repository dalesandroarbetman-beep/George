import { AppShell } from "../components/AppShell";
import { ArrowRight, Filter, Search } from "lucide-react";

const tasks = [
  ["珍珠项链开箱视频", "完整生产线", "审核", "待审核", "今天 10:24"],
  ["DIY 串珠过程图", "快速发布文案", "已完成", "已生成", "昨天 16:40"],
  ["不锈钢耳环展示", "完整生产线", "六平台适配", "处理中", "昨天 14:12"],
  ["秋季叠戴卖点", "快速发布文案", "已完成", "已生成", "9 月 20 日"],
  ["戒指组合选择视频", "完整生产线", "导出", "已完成", "9 月 19 日"],
];

export default function TasksPage() {
  return <AppShell title="任务记录"><section className="page-heading compact"><div><span className="eyebrow">TASK HISTORY</span><h1>任务记录</h1><p>完整项目和快速任务在这里统一检索，但各自保持独立流程。</p></div></section><section className="surface tasks-surface"><div className="task-toolbar"><label><Search size={16} /><input placeholder="搜索任务名称" /></label><button className="button secondary"><Filter size={16} />筛选</button></div><div className="task-table"><div className="task-table-head"><span>任务名称</span><span>任务类型</span><span>当前阶段</span><span>状态</span><span>更新时间</span><span /></div>{tasks.map((task) => <div className="task-table-row" key={task[0]}><strong>{task[0]}</strong><span>{task[1]}</span><span>{task[2]}</span><span className={`status ${task[3] === "待审核" ? "amber" : task[3] === "处理中" ? "blue" : "green"}`}>{task[3]}</span><time>{task[4]}</time><button className="icon-button"><ArrowRight size={16} /></button></div>)}</div></section></AppShell>;
}
