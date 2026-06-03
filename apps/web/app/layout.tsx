import { AppShell } from "./AppShell";
import "./globals.css";

export const metadata = {
  title: "AI 短剧创作工作台",
  description: "AI short drama creation workspace"
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN">
      <body>
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}
