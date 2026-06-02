import { Suspense } from "react";
import EditForm from "./EditForm";

export default function EditPage() {
  return (
    <Suspense
      fallback={
        <div className="main">
          <div className="panel stack">
            <p className="hint">加载中...</p>
          </div>
        </div>
      }
    >
      <EditForm />
    </Suspense>
  );
}
