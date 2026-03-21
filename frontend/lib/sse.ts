"use client";

import { useEffect, useState } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type WorkflowEvent = {
  raw: string;
};

/**
 * Subscribe to workflow SSE updates for a given workflow identifier.
 *
 * @param workflowId - UUID string for the workflow.
 * @returns Latest event payload and connection flag.
 */
export function useWorkflowStream(workflowId: string | null) {
  const [lastEvent, setLastEvent] = useState<WorkflowEvent | null>(null);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    if (!workflowId) {
      return;
    }
    // Single-arg constructor avoids DOM typings mismatch for EventSourceInit on some TS targets.
    const source = new EventSource(`${API_BASE}/api/v1/workflows/${workflowId}/stream`);
    source.onopen = () => setConnected(true);
    source.onerror = () => setConnected(false);
    source.onmessage = (event) => {
      setLastEvent({ raw: event.data });
    };
    return () => {
      source.close();
      setConnected(false);
    };
  }, [workflowId]);

  return { lastEvent, connected };
}
