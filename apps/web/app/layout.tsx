import Link from "next/link";
import "./globals.css";

export const metadata = {
  title: "AI 短剧创作工作台",
  description: "AI short drama creation workspace"
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN">
      <body>
        <div className="app-shell">
          <aside className="sidebar">
            <div className="brand">AI 短剧工作台</div>
            <nav className="nav">
              <Link href="/">项目管理</Link>
              <Link href="/character-cards">角色卡库</Link>
              <Link href="/world-books">世界观库</Link>
              <Link href="/settings">模型配置</Link>
            </nav>
          </aside>
          <main className="main">{children}</main>
        </div>
      </body>
    </html>
  );
}
