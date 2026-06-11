"use client";

import { useParams, useSearchParams } from "next/navigation";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import { LandingModule } from "./_components/LandingModule";
import { ProductionModule } from "./_components/ProductionModule";
import { ProjectAssetsModule } from "./_components/ProjectAssetsModule";
import { StoryTextModule } from "./_components/StoryTextModule";
import { LoadingWorkbench, MissingProject, WorkbenchHeader, WorkbenchStatusStrip } from "./_components/WorkbenchLayout";
import { useProjectWorkbench } from "./_hooks/useProjectWorkbench";
import type { WorkspaceMode } from "./_utils/workbenchTypes";

export default function ProjectWorkbenchClient({ mode = "landing" }: { mode?: WorkspaceMode }) {
  const params = useParams<{ id: string }>();
  const searchParams = useSearchParams();
  const projectId = params.id;
  const requestedStage = searchParams.get("stage");
  const workbench = useProjectWorkbench({ projectId, mode, requestedStage });

  if (workbench.isLoading) {
    return <LoadingWorkbench />;
  }

  if (!workbench.project) {
    return <MissingProject error={workbench.error} />;
  }

  return (
    <div className={`stack ${!workbench.isLandingMode ? "module-workbench" : ""}`}>
      <ConfirmDialog
        destructive={workbench.pendingConfirmation?.destructive}
        open={Boolean(workbench.pendingConfirmation)}
        title={workbench.pendingConfirmation?.title ?? ""}
        description={workbench.pendingConfirmation?.description ?? ""}
        confirmLabel={workbench.pendingConfirmation?.confirmLabel}
        onOpenChange={(open) => {
          if (!open) workbench.setPendingConfirmation(null);
        }}
        onConfirm={() => void workbench.confirmPendingAction()}
      />
      <WorkbenchHeader workbench={workbench} />
      <LandingModule workbench={workbench} />
      <WorkbenchStatusStrip workbench={workbench} />
      <ProjectAssetsModule workbench={workbench} />
      <StoryTextModule workbench={workbench} />
      <ProductionModule workbench={workbench} />
    </div>
  );
}
