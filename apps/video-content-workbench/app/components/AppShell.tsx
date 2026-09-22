"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Archive,
  Bell,
  Clapperboard,
  FileText,
  HelpCircle,
  LayoutDashboard,
  Library,
  Menu,
  Settings,
  Sparkles,
  X,
} from "lucide-react";
import { useState } from "react";

const nav = [
  { href: "/", label: "工作台总览", icon: LayoutDashboard },
  { href: "/pipeline", label: "视频脚本生产线", icon: Clapperboard },
  { href: "/quick-copy", label: "快速发布文案", icon: Sparkles },
  { href: "/tasks", label: "任务记录", icon: Archive },
  { href: "/library", label: "素材库", icon: Library, disabled: true },
];

export function AppShell({ children, title }: { children: React.ReactNode; title: string }) {
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <div className="app-shell">
      <aside className={`sidebar ${mobileOpen ? "mobile-open" : ""}`}>
        <div className="brand-row">
          <div className="brand-mark">Y</div>
          <div><strong>YOHO</strong><span>内容生产工作台</span></div>
          <button className="mobile-close icon-button" onClick={() => setMobileOpen(false)} aria-label="关闭导航"><X size={19} /></button>
        </div>
        <div className="workspace-label"><span>独立工作区</span><strong>视频与社媒内容</strong></div>
        <nav className="nav-list" aria-label="主导航">
          {nav.map((item) => {
            const Icon = item.icon;
            const active = pathname === item.href;
            return item.disabled ? (
              <button key={item.href} className="nav-item" disabled title="后续版本开放"><Icon size={18} /><span>{item.label}</span><em>稍后</em></button>
            ) : (
              <Link key={item.href} href={item.href} className={`nav-item ${active ? "active" : ""}`} onClick={() => setMobileOpen(false)}>
                <Icon size={18} /><span>{item.label}</span>
              </Link>
            );
          })}
        </nav>
        <div className="sidebar-foot">
          <button className="nav-item"><Settings size={18} /><span>品牌与平台设置</span></button>
          <button className="nav-item"><HelpCircle size={18} /><span>帮助</span></button>
          <div className="local-status"><i />本地处理模式</div>
        </div>
      </aside>
      {mobileOpen && <button className="mobile-backdrop" onClick={() => setMobileOpen(false)} aria-label="关闭导航遮罩" />}
      <main className="main-area">
        <header className="topbar">
          <div className="topbar-left">
            <button className="mobile-menu icon-button" onClick={() => setMobileOpen(true)} aria-label="打开导航"><Menu size={20} /></button>
            <span>内容生产</span><b>/</b><strong>{title}</strong>
          </div>
          <div className="topbar-actions">
            <button className="icon-button" aria-label="通知"><Bell size={19} /><i className="notice-dot" /></button>
            <div className="operator"><span>林主管</span><small>内容运营</small></div>
            <div className="avatar">林</div>
          </div>
        </header>
        <div className="page-content">{children}</div>
      </main>
    </div>
  );
}
