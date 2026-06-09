import { AppShell } from "./AppShell";
import "./globals.css";
import { TooltipProvider } from "@/components/ui/tooltip";

export const metadata = {
  title: "AI 短剧创作工作台",
  description: "AI short drama creation workspace"
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN">
      <body>
        <TooltipProvider>
          <AppShell>{children}</AppShell>
        </TooltipProvider>
      </body>
    </html>
  );
}
