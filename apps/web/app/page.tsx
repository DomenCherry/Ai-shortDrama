import Link from "next/link";

export default function HomePage() {
  return (
    <div>
      <header className="page-header">
        <div>
          <h1 className="page-title">我的短剧项目</h1>
          <p className="page-description">
            先配置模型 API，再创建第一个短剧项目。第一期会从项目创建和文本生成链路开始搭建。
          </p>
        </div>
        <Link className="button" href="/projects/new">
          创建项目
        </Link>
      </header>

      <section className="panel stack">
        <h2>当前框架能力</h2>
        <p className="hint">项目列表接口已经预留，下一步会接入真实项目列表展示。</p>
        <div className="actions" style={{ justifyContent: "flex-start" }}>
          <Link className="button secondary" href="/settings">
            配置模型 API
          </Link>
          <Link className="button" href="/projects/new">
            创建第一个项目
          </Link>
        </div>
      </section>
    </div>
  );
}

