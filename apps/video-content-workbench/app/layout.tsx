import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "YOHO 内容生产工作台",
  description: "独立的视频脚本生产与平台发布文案工作台",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>
    </html>
  );
}
