"use client";

import { useMemo, useRef, useState } from "react";
import { AppShell } from "../components/AppShell";
import { Check, Copy, FileImage, FileText, FileVideo, RefreshCw, Sparkles, UploadCloud } from "lucide-react";
import type { WorkbenchTask } from "../lib/task-contract";

const platforms = ["TikTok", "Instagram", "YouTube", "Facebook", "X", "DIY 账号"];
const copy: Record<string, { text: string; tags: string[] }> = {
  TikTok: { text: "Your next jewelry obsession might be one stack away. Mix it, layer it, make it yours with YOHO. Link in bio.", tags: ["#YOHOJewelry", "#JewelryTok", "#LayeredJewelry", "#StyleIdeas", "#EverydayJewelry"] },
  Instagram: { text: "A little shine, styled your way. Build a jewelry stack that changes with every look. Discover YOHO through the link in bio.", tags: ["#YOHOJewelry", "#JewelryStyle", "#StackingJewelry", "#DailyDetails", "#OutfitInspiration"] },
  YouTube: { text: "Three easy ways to build a jewelry stack that feels personal. Explore more YOHO pieces through the link in our profile.", tags: ["#JewelryIdeas", "#YOHOJewelry", "#Shorts", "#StyleTips", "#JewelryStacking"] },
  Facebook: { text: "Which combination would you wear first? Explore different ways to mix and layer your favorite jewelry with YOHO.", tags: ["#YOHOJewelry", "#JewelryInspiration", "#PersonalStyle", "#EverydayAccessories", "#StyleCommunity"] },
  X: { text: "One stack, countless moods. Which YOHO combination fits your style today?", tags: ["#YOHOJewelry", "#JewelryStyle", "#StyleYourWay"] },
  "DIY 账号": { text: "Start with one focal piece, then add texture and contrast. A simple stacking formula for a look that feels entirely yours.", tags: ["#DIYJewelry", "#JewelryMaking", "#StackingGuide", "#CreativeProcess", "#YOHOJewelry"] },
};

export default function QuickCopyPage() {
  const [inputType, setInputType] = useState("文字");
  const [selected, setSelected] = useState(["TikTok", "Instagram"]);
  const [source, setSource] = useState("");
  const [fileName, setFileName] = useState("");
  const [generated, setGenerated] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [active, setActive] = useState("TikTok");
  const [copied, setCopied] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);
  const current = copy[active] ?? copy.TikTok;
  const canGenerate = source.trim().length > 0 || fileName.length > 0;
  const selectedLabels = useMemo(() => selected.join("、"), [selected]);

  function togglePlatform(platform: string) {
    setSelected((items) => items.includes(platform) ? items.filter((item) => item !== platform) : [...items, platform]);
  }

  async function generateCopy() {
    setError("");
    setBusy(true);
    try {
      const sourceName = fileName || `${inputType}素材-${new Date().toISOString().slice(0, 10)}`;
      const response = await fetch("/api/tasks", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ name: sourceName, type: "quick-copy", source: { name: sourceName, mediaType: inputType, size: 0 }, settings: { brand: "YOHO", brandUrl: "www.yohodiy.com" } }) });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.error || "创建快速任务失败");
      const created = payload.task as WorkbenchTask;
      const resultResponse = await fetch(`/api/tasks/${created.id}`, { method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ status: "completed", stage: "result", progress: 100 }) });
      const resultPayload = await resultResponse.json();
      if (!resultResponse.ok) throw new Error(resultPayload.error || "保存快速任务失败");
      setGenerated(true);
      setActive(selected[0]);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "快速任务操作失败");
    } finally {
      setBusy(false);
    }
  }

  return (
    <AppShell title="快速发布文案">
      <section className="page-heading compact"><div><span className="eyebrow">QUICK SOCIAL COPY</span><h1>快速发布文案</h1><p>单条素材直接生成平台文案、标签和互动话术。</p></div><span className="mode-chip teal"><Sparkles size={14} />快速任务</span></section>
      {error && <div className="inline-error" role="alert">{error}</div>}
      <div className="quick-layout">
        <section className="surface quick-input-panel">
          <div className="section-head"><div><h2>输入素材</h2><p>选择一种素材类型。</p></div></div>
          <div className="segmented">{[["视频", FileVideo], ["图片", FileImage], ["文字", FileText]].map(([label, Icon]) => { const IconComponent = Icon as typeof FileVideo; return <button key={label as string} className={inputType === label ? "active" : ""} onClick={() => { setInputType(label as string); setFileName(""); setSource(""); }}><IconComponent size={16} />{label as string}</button>; })}</div>
          {inputType === "文字" ? <label className="copy-source">素材内容<textarea value={source} onChange={(event) => setSource(event.target.value)} placeholder="粘贴脚本、商品卖点或内容摘要…" /><small>{source.length} / 1200</small></label> : <button className={`compact-upload ${fileName ? "has-file" : ""}`} onClick={() => fileRef.current?.click()}><UploadCloud size={25} /><strong>{fileName || `选择${inputType}文件`}</strong><span>{fileName ? "点击更换" : "文件只在本机处理"}</span></button>}
          <input ref={fileRef} className="sr-only" type="file" accept={inputType === "视频" ? "video/*" : "image/*"} onChange={(event) => setFileName(event.target.files?.[0]?.name ?? "")} />
          <div className="control-group"><span className="control-label">目标平台</span><div className="platform-picker">{platforms.map((platform) => <button key={platform} className={selected.includes(platform) ? "selected" : ""} onClick={() => togglePlatform(platform)}>{selected.includes(platform) && <Check size={13} />}{platform}</button>)}</div></div>
          <div className="field-grid"><label>输出语言<select defaultValue="英文 + 中文翻译"><option>英文 + 中文翻译</option><option>仅英文</option><option>仅中文</option></select></label><label>内容语气<select defaultValue="自然种草"><option>自然种草</option><option>专业批发</option><option>DIY 教程</option><option>人设口播</option></select></label></div>
          <button className="button primary wide" disabled={!canGenerate || !selected.length || busy} onClick={generateCopy}><Sparkles size={17} />{busy ? "保存中…" : `生成 ${selected.length || 0} 个平台方案`}</button>
        </section>

        <section className="surface result-panel">
          {!generated ? <div className="result-empty"><Sparkles size={34} /><strong>等待生成</strong><span>{canGenerate ? `将为${selectedLabels}生成定制文案` : "输入素材后即可开始"}</span></div> : <><header className="result-head"><div><span className="result-kicker">已生成 {selected.length} 个平台方案</span><h2>发布文案与标签</h2></div><button className="icon-button" title="重新生成"><RefreshCw size={17} /></button></header><div className="result-tabs">{selected.map((platform) => <button key={platform} className={active === platform ? "active" : ""} onClick={() => { setActive(platform); setCopied(false); }}>{platform}</button>)}</div><div className="result-body"><div className="result-block"><div><b>发布正文</b><button onClick={() => { navigator.clipboard?.writeText(current.text); setCopied(true); }}>{copied ? <Check size={15} /> : <Copy size={15} />}{copied ? "已复制" : "复制"}</button></div><p>{current.text}</p><small>中文：用你自己的方式叠搭饰品，让每一种组合都更像你。通过主页链接探索 YOHO。</small></div><div className="result-block"><div><b>推荐标签</b><span>{current.tags.length} 个</span></div><div className="hashtag-box">{current.tags.map((tag) => <span key={tag}>{tag}</span>)}</div></div><div className="result-block inline-result"><div><b>首评建议</b></div><p>Which piece would you add to your stack first?</p></div><div className="result-meta"><span>CTA</span><b>Link in bio</b><span>建议时段</span><b>19:00–21:00</b></div></div></>}
        </section>
      </div>
    </AppShell>
  );
}
