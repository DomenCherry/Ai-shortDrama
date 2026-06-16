import type { ProjectStoryOutline } from "@/lib/api";
import type { StoryOutlineForm } from "./workbenchTypes";

const STORY_OUTLINE_ASSIST_DRAFT_PREFIX = "story-outline-assist-draft";
const STORY_OUTLINE_ASSIST_DRAFT_TTL_MS = 30 * 60 * 1000;

type StoredStoryOutlineAssistDraft = {
  updatedAt: number;
  form: StoryOutlineForm;
};

const storyOutlineFormKeys: Array<keyof StoryOutlineForm> = [
  "logline",
  "story_background",
  "core_conflict",
  "main_goal",
  "story_start",
  "plot_structure",
  "reversals",
  "emotion_curve",
  "foreshadowing",
  "character_arcs",
  "ending_direction",
  "pacing_advice",
  "capacity_advice",
  "notes",
  "status"
];

export function saveStoryOutlineAssistDraft(projectId: string, form: StoryOutlineForm) {
  if (typeof window === "undefined") return;
  const draft: StoredStoryOutlineAssistDraft = {
    updatedAt: Date.now(),
    form: { ...form }
  };
  window.sessionStorage.setItem(storyOutlineAssistDraftKey(projectId), JSON.stringify(draft));
}

export function readStoryOutlineAssistDraft(projectId: string, savedOutline?: ProjectStoryOutline | null) {
  if (typeof window === "undefined") return null;
  const key = storyOutlineAssistDraftKey(projectId);
  const rawDraft = window.sessionStorage.getItem(key);
  if (!rawDraft) return null;

  try {
    const draft = JSON.parse(rawDraft) as StoredStoryOutlineAssistDraft;
    if (!isStoredStoryOutlineAssistDraft(draft)) {
      window.sessionStorage.removeItem(key);
      return null;
    }
    if (Date.now() - draft.updatedAt > STORY_OUTLINE_ASSIST_DRAFT_TTL_MS) {
      window.sessionStorage.removeItem(key);
      return null;
    }
    if (savedOutline?.updated_at && draft.updatedAt <= new Date(savedOutline.updated_at).getTime()) {
      window.sessionStorage.removeItem(key);
      return null;
    }
    return draft.form;
  } catch {
    window.sessionStorage.removeItem(key);
    return null;
  }
}

export function clearStoryOutlineAssistDraft(projectId: string) {
  if (typeof window === "undefined") return;
  window.sessionStorage.removeItem(storyOutlineAssistDraftKey(projectId));
}

function storyOutlineAssistDraftKey(projectId: string) {
  return `${STORY_OUTLINE_ASSIST_DRAFT_PREFIX}:${projectId}`;
}

function isStoredStoryOutlineAssistDraft(value: unknown): value is StoredStoryOutlineAssistDraft {
  if (!value || typeof value !== "object") return false;
  const draft = value as Partial<StoredStoryOutlineAssistDraft>;
  if (typeof draft.updatedAt !== "number" || !Number.isFinite(draft.updatedAt)) return false;
  if (!draft.form || typeof draft.form !== "object") return false;
  return storyOutlineFormKeys.every((key) => typeof draft.form?.[key] === "string");
}
