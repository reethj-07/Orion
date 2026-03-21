"use client";

import { useQuery } from "@tanstack/react-query";
import { useParams } from "next/navigation";

import { AgentStatus } from "@/components/workflow/agent-status";
import { ReportViewer } from "@/components/workflow/report-viewer";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { apiFetch } from "@/lib/api";
import { useWorkflowStream } from "@/lib/sse";

type WorkflowDetail = {
  id: string;
  title: string;
  status: string;
  task_description: string;
  report?: { markdown_report?: string } | null;
  trace: { agent_type?: string; status?: string }[];
};

/**
 * Live workflow console combining polling, SSE, and rendered markdown output.
 */
export default function WorkflowDetailPage() {
  const params = useParams();
  const rawId = params?.id;
  const workflowId =
    typeof rawId === "string" ? rawId : Array.isArray(rawId) ? (rawId[0] ?? null) : null;

  const { lastEvent, connected } = useWorkflowStream(workflowId);

  const { data, isLoading } = useQuery({
    queryKey: ["workflow", workflowId],
    queryFn: async () => {
      if (!workflowId) {
        throw new Error("Missing workflow id");
      }
      const response = await apiFetch<WorkflowDetail>(`/api/v1/workflows/${workflowId}`);
      return response.data;
    },
    enabled: Boolean(workflowId),
    refetchInterval: 4000,
  });

  const markdown = data?.report && "markdown_report" in data.report ? String(data.report.markdown_report ?? "") : "";

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="text-sm text-muted-foreground">Workflow</p>
          <h1 className="text-3xl font-semibold">
            {isLoading ? <Skeleton className="h-8 w-64" /> : data?.title}
          </h1>
        </div>
        <div className="flex items-center gap-3">
          <Badge variant="outline">{connected ? "Live stream" : "Stream paused"}</Badge>
          <Badge>{data?.status ?? "unknown"}</Badge>
        </div>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>Agent mesh</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {isLoading && <Skeleton className="h-16 w-full" />}
          {data?.trace?.map((event, index) => (
            <AgentStatus
              key={`${event.agent_type}-${index}`}
              label={String(event.agent_type ?? "agent")}
              status={mapAgentStatus(String(event.status ?? ""))}
            />
          ))}
          {lastEvent && (
            <p className="text-xs text-muted-foreground">Latest event: {lastEvent.raw}</p>
          )}
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>Final report</CardTitle>
        </CardHeader>
        <CardContent>{markdown ? <ReportViewer markdown={markdown} /> : <p className="text-sm text-muted-foreground">Report will appear when agents finish.</p>}</CardContent>
      </Card>
    </div>
  );
}
