import { create } from "zustand";

export type WorkflowSummary = {
  id: string;
  title: string;
  status: string;
  created_at: string;
};

type WorkflowState = {
  drafts: WorkflowSummary[];
  setDrafts: (rows: WorkflowSummary[]) => void;
};

/**
 * Optimistic workflow list cache for dashboard views.
 */
export const useWorkflowStore = create<WorkflowState>((set) => ({
  drafts: [],
  setDrafts: (rows) => set({ drafts: rows }),
}));
