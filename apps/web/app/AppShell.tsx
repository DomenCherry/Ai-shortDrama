"use client";

import Link from "next/link";
import { ReactNode, useEffect, useState } from "react";
import { Button } from "@/components/ui/button";

const sidebarStorageKey = "ai-short-drama-sidebar-collapsed";

const navItems = [
  { href: "/", label: "项目管理", shortLabel: "项" },
  { href: "/character-cards", label: "角色卡库", shortLabel: "角" },
  { href: "/world-books", label: "世界观库", shortLabel: "世" },
  { href: "/settings", label: "模型配置", shortLabel: "模" }
];

export function AppShell({ children }: { children: ReactNode }) {
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);

  useEffect(() => {
    setIsSidebarCollapsed(window.localStorage.getItem(sidebarStorageKey) === "true");
  }, []);

  const toggleSidebar = () => {
    setIsSidebarCollapsed((currentValue) => {
      const nextValue = !currentValue;

      // 导航折叠是纯前端偏好，保存在浏览器本地即可，避免引入不必要的后端配置。
      window.localStorage.setItem(sidebarStorageKey, String(nextValue));
      return nextValue;
    });
  };

  return (
    <div className={`app-shell ${isSidebarCollapsed ? "app-shell-collapsed" : ""}`}>
      <aside className="sidebar" aria-label="主导航">
        <div className="sidebar-header">
          <div className="brand" title="AI 短剧工作台">
            <span className="brand-full">AI 短剧工作台</span>
            <span className="brand-short">AI</span>
          </div>
          <Button
            aria-expanded={!isSidebarCollapsed}
            aria-label={isSidebarCollapsed ? "展开左侧导航" : "收起左侧导航"}
            className="sidebar-toggle"
            size="icon"
            type="button"
            variant="ghost"
            onClick={toggleSidebar}
          >
            <span aria-hidden="true">{isSidebarCollapsed ? "›" : "‹"}</span>
          </Button>
        </div>
        <nav className="nav" aria-label="工作台模块">
          {navItems.map((item) => (
            <Link href={item.href} key={item.href} title={item.label}>
              <span className="nav-icon" aria-hidden="true">
                {item.shortLabel}
              </span>
              <span className="nav-label">{item.label}</span>
            </Link>
          ))}
        </nav>
      </aside>
      <main className="main">{children}</main>
    </div>
  );
}
