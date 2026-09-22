"use client";

import { useEffect, useRef, useState } from "react";
import { AppShell } from "../components/AppShell";
import { Check, ChevronLeft, ChevronRight, Download, FileVideo, Play, ShieldCheck, UploadCloud } from "lucide-react";
import type { TaskStage, WorkbenchTask } from "../lib/task-contract";

const steps = ["素材", "分析", "改写", "审核", "六平台适配", "导出"];
const panels = [
  { title: "导入项目素材", subtitle: "视频保留在本机，当前页面不会上传到外部服务。" },
  { title: "视频结构分析", subtitle: "确认语音、画面信息和内容类型。" },
  { title: "原创脚本改写", subtitle: "保留有效结构，替换表达并融合 YOHO 品牌。" },
  { title: "内容审核", subtitle: "核对事实、相似度和平台合规风险。" },
  { title: "六平台适配", subtitle: "为不同平台生成各自的标题、正文、标签和互动话术。" },
  { title: "导出内容包", subtitle: "选择交付格式并保留版本记录。" },
];

export default function PipelinePage() {
  const [step, setStep] = useState(0);
  const [fileName, setFileName] = useState("");
  const [fileMeta, setFileMeta] = useState<{ mediaType: string; size: number } | null>(null);
  const [projectName, setProjectName] = useState("");
  const [task, setTask] = useState<WorkbenchTask | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  const canContinue = step > 0 || Boolean(fileName && projectName.trim());
  useEffect(() => {
    if (!task || task.status !== "processing") return;
    const timer = window.setInterval(async () => {
      try {
        const response = await fetch(`/api/tasks/${task.id}`, { cache: "no-store" });
        const payload = await response.json();
        if (!response.ok) throw new Error(payload.error || "读取转写状态失败");
        setTask(payload.task);
        if (["review", "failed", "completed"].includes(payload.task.status)) window.clearInterval(timer);
      } catch (caught) {
        setError(caught instanceof Error ? caught.message : "读取本地转写状态失败");
      }
    }, 1500);
    return () => window.clearInterval(timer);
  }, [task?.id, task?.status]);

  async function advance() {
    setError("");
    setBusy(true);
    try {
      if (!task) {
        const video = inputRef.current?.files?.[0];
        if (!video) throw new Error("请选择视频文件");
        const form = new FormData();
        form.set("projectName", projectName);
        form.set("brand", "YOHO");
        form.set("brandUrl", "www.yohodiy.com");
        form.set("market", "美国");
        form.set("language", "双语");
        form.set("video", video);
        const response = await fetch("/api/tasks/transcribe", { method: "POST", body: form });
        const payload = await response.json();
        if (!response.ok) throw new Error(payload.error || "创建任务失败");
        setTask(payload.task);
        setStep(1);
      } else {
        const nextStep = Math.min(5, step + 1);
        const nextStage: TaskStage = ["material", "analysis", "rewrite", "review", "platforms", "export"][nextStep] as TaskStage;
        const nextStatus = nextStep === 3 ? "review" : nextStep === 5 ? "completed" : "processing";
        const response = await fetch(`/api/tasks/${task.id}`, { method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ stage: nextStage, status: nextStatus, progress: Math.round((nextStep / 5) * 100) }) });
        const payload = await response.json();
        if (!response.ok) throw new Error(payload.error || "保存任务进度失败");
        setTask(payload.task);
        setStep(nextStep);
      }
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "本地任务操作失败");
    } finally {
      setBusy(false);
    }
  }
  return (
    <AppShell title="视频脚本生产线">
      <section className="page-heading compact"><div><span className="eyebrow">FULL VIDEO WORKFLOW</span><h1>视频脚本生产线</h1><p>一个项目保留完整的素材、版本、审核和平台适配记录。</p></div><span className="mode-chip"><i />本地流程</span></section>
      {error && <div className="inline-error" role="alert">{error}</div>}
      <div className="pipeline-layout">
        <aside className="stepper surface">
          <div className="stepper-title"><strong>项目进度</strong><span>{step + 1} / {steps.length}</span></div>
          {steps.map((label, index) => <button key={label} className={`step-item ${index === step ? "current" : ""} ${index < step ? "done" : ""}`} onClick={() => index <= step && setStep(index)}><span>{index < step ? <Check size={15} /> : index + 1}</span><div><strong>{label}</strong><small>{index < step ? "已完成" : index === step ? "当前步骤" : "等待处理"}</small></div></button>)}
        </aside>

        <section className="surface work-panel">
          <header className="work-head"><div><span>步骤 {String(step + 1).padStart(2, "0")}</span><h2>{panels[step].title}</h2><p>{panels[step].subtitle}</p></div>{step > 0 && <span className="saved-state"><Check size={14} />已保存</span>}</header>
          <div className="work-body">
            {step === 0 && <MaterialStep fileName={fileName} projectName={projectName} setProjectName={setProjectName} onChoose={() => inputRef.current?.click()} />}
            {step === 1 && <AnalysisStep task={task} />}
            {step === 2 && <RewriteStep />}
            {step === 3 && <ReviewStep />}
            {step === 4 && <PlatformStep />}
            {step === 5 && <ExportStep />}
          </div>
          <footer className="work-footer"><button className="button secondary" disabled={step === 0 || busy} onClick={() => setStep(Math.max(0, step - 1))}><ChevronLeft size={17} />上一步</button>{step < 5 ? <button className="button primary" disabled={!canContinue || busy} onClick={advance}>{busy ? "保存中…" : step === 0 ? "保存并开始分析" : "确认并继续"}<ChevronRight size={17} /></button> : <button className="button primary"><Download size={17} />导出内容包</button>}</footer>
        </section>
      </div>
      <input ref={inputRef} className="sr-only" type="file" accept="video/*" onChange={(event) => { const file = event.target.files?.[0]; setFileName(file?.name ?? ""); setFileMeta(file ? { mediaType: file.type, size: file.size } : null); }} />
    </AppShell>
  );
}

function MaterialStep({ fileName, projectName, setProjectName, onChoose }: { fileName: string; projectName: string; setProjectName: (value: string) => void; onChoose: () => void }) {
  return <div className="material-grid"><button className={`upload-zone ${fileName ? "has-file" : ""}`} onClick={onChoose}>{fileName ? <><FileVideo size={36} /><strong>{fileName}</strong><span>点击更换视频</span></> : <><UploadCloud size={38} /><strong>选择视频文件</strong><span>MP4、MOV 或 WebM</span></>}</button><div className="form-stack"><label>项目名称<input value={projectName} onChange={(event) => setProjectName(event.target.value)} placeholder="例如：珍珠项链开箱视频" /></label><label>品牌<input value="YOHO" readOnly /></label><label>官网<input value="www.yohodiy.com" readOnly /></label><div className="field-grid"><label>主要市场<select defaultValue="美国"><option>美国</option><option>英国</option><option>加拿大</option><option>澳大利亚</option></select></label><label>输出语言<select defaultValue="双语"><option>双语</option><option>英文</option><option>中文</option></select></label></div></div></div>;
}

function AnalysisStep({ task }: { task: WorkbenchTask | null }) {
  const result = task?.result;
  const sourceText = result?.segments.map((segment) => segment.text).filter(Boolean).join("\n") || (task?.status === "failed" ? task.error?.message || "本地视频处理失败" : "本地识别中，请稍候…");
  const translation = result?.enrichment.translation || (task?.status === "failed" ? "处理失败，修复环境后可重试。" : "等待本地 Ollama 返回中文翻译…");
  const duration = result?.duration_seconds ? `${Math.round(result.duration_seconds)} 秒` : "处理中";
  return <div className="editor-layout"><div className="video-preview"><span><Play size={24} /></span><small>{duration} · 本地任务</small></div><div className="analysis-fields"><label>处理状态<input value={task ? `${task.status === "review" ? "转写完成，待审核" : task.status === "failed" ? "处理失败" : "本地识别中"} · ${task.progress}%` : "等待任务"} readOnly /></label><label>识别原文<textarea value={sourceText} readOnly /></label><label>中文翻译<textarea value={translation} readOnly /></label>{result?.transcription_quality?.needs_visual_review && <div className="inline-error">转写质量提示：{result.transcription_quality.review_reasons?.join("；") || "建议结合画面复核"}</div>}<div className="tag-line"><span>{result?.language ? `识别语言：${result.language}` : "自动识别语言"}</span><span>{result?.inference ? "本地 faster-whisper" : "等待识别"}</span></div></div></div>;
}

function RewriteStep() { return <div className="rewrite-grid"><section><div className="editor-label"><b>参考结构</b><span>只保留叙事逻辑</span></div><textarea className="large-editor" defaultValue={"开头：快速展示成品\n中段：切换不同搭配\n结尾：邀请观众选择喜欢的款式"} /></section><section><div className="editor-label"><b>YOHO 原创改写</b><span className="quality-score">相似度 18%</span></div><textarea className="large-editor active" defaultValue={"One look, your rules. Mix the pieces you love and build a stack that feels completely yours. Discover more at YOHO. Link in bio."} /></section></div>; }

function ReviewStep() { return <div className="review-grid"><section className="review-score"><ShieldCheck size={32} /><strong>可以进入平台适配</strong><span>4 项检查已通过，1 项建议确认</span></section><div className="check-list"><label><input type="checkbox" defaultChecked />原视频价格与优惠信息已移除</label><label><input type="checkbox" defaultChecked />未添加未经确认的材质或性能主张</label><label><input type="checkbox" defaultChecked />品牌与官网信息正确</label><label><input type="checkbox" defaultChecked />与参考文案保持低相似度</label><label className="warning"><input type="checkbox" />确认视频画面没有第三方水印</label></div></div>; }

function PlatformStep() { const platforms = ["TikTok", "Instagram", "YouTube Shorts", "Facebook", "X", "DIY 账号"]; return <div className="platform-editor"><div className="platform-tabs">{platforms.map((name, index) => <button key={name} className={index === 0 ? "active" : ""}>{name}<span>{index < 3 ? <Check size={12} /> : "待"}</span></button>)}</div><label>发布正文<textarea className="large-editor active" defaultValue={"Your jewelry stack should feel like you. Mix, layer, and make it personal with YOHO. Find your next favorite piece through the link in bio."} /></label><label>标签<div className="hashtag-box"><span>#YOHOJewelry</span><span>#JewelryStacking</span><span>#EverydayJewelry</span><span>#StyleYourWay</span><span>#JewelryTok</span></div></label><div className="field-grid"><label>CTA<input defaultValue="Link in bio" /></label><label>建议时段<input defaultValue="19:00–21:00（当地时间）" /></label></div></div>; }

function ExportStep() { return <div className="export-options"><label><input type="radio" name="format" defaultChecked /><FileVideo size={21} /><span><b>HTML 完整报告</b><small>适合浏览、审核和归档</small></span></label><label><input type="radio" name="format" /><FileVideo size={21} /><span><b>Markdown 文案包</b><small>适合继续编辑和版本管理</small></span></label><label><input type="radio" name="format" /><FileVideo size={21} /><span><b>JSON 数据包</b><small>适合后续系统接入</small></span></label><div className="export-summary"><span>项目内容</span><strong>原文、翻译、改写、审核记录、六平台文案</strong><span>保存位置</span><strong>output/video-workbench/</strong></div></div>; }
