import { Badge } from "@/components/ui/badge";

type AgentStatusProps = {
  label: string;
  status: "pending" | "running" | "done" | "failed";
};

const variants: Record<AgentStatusProps["status"], "default" | "secondary" | "outline"> = {
  pending: "outline",
  running: "secondary",
  done: "default",
  failed: "outline",
};

/**
 * Visual badge describing an agent lifecycle state.
 */
export function AgentStatus({ label, status }: AgentStatusProps) {
  return (
    <div className="flex items-center gap-2">
      <span className="text-sm font-medium">{label}</span>
      <Badge variant={variants[status]}>{status}</Badge>
    </div>
  );
}
