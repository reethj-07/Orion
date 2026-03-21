import { useQuery } from "@tanstack/react-query";

import { apiFetch } from "@/lib/api";

export type WorkflowSummary = {
  id: string;
  title: string;
  status: string;
  created_at: string;
};

/**
 * React Query hook listing workflows for the authenticated user.
 */
export function useWorkflows() {
  return useQuery({
    queryKey: ["workflows"],
    queryFn: async () => {
      const response = await apiFetch<WorkflowSummary[]>("/api/v1/workflows/");
      return response.data ?? [];
    },
  });
}
