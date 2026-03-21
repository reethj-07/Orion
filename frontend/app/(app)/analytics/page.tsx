"use client";

import { useQuery } from "@tanstack/react-query";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { apiFetch } from "@/lib/api";

type UsageStats = {
  workflow_counts: Record<string, number>;
  token_usage: Record<string, number>;
  workflow_results: number;
};

/**
 * Analytics dashboard visualizing workflow throughput and usage signals.
 */
export default function AnalyticsPage() {
  const usageQuery = useQuery({
    queryKey: ["usage"],
    queryFn: async () => {
      const response = await apiFetch<UsageStats>("/api/v1/analytics/usage");
      return response.data;
    },
  });

  const chartData = usageQuery.data
    ? Object.entries(usageQuery.data.workflow_counts).map(([status, total]) => ({
        status,
        total,
      }))
    : [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-semibold">Analytics</h1>
        <p className="text-sm text-muted-foreground">Operational metrics sourced from PostgreSQL and MongoDB.</p>
      </div>
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle className="text-sm text-muted-foreground">Workflow results</CardTitle>
          </CardHeader>
          <CardContent className="text-3xl font-semibold">
            {usageQuery.isLoading ? <Skeleton className="h-8 w-16" /> : usageQuery.data?.workflow_results}
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-sm text-muted-foreground">Prompt tokens (stub)</CardTitle>
          </CardHeader>
          <CardContent className="text-3xl font-semibold">
            {usageQuery.isLoading ? <Skeleton className="h-8 w-16" /> : usageQuery.data?.token_usage.prompt}
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-sm text-muted-foreground">Completion tokens (stub)</CardTitle>
          </CardHeader>
          <CardContent className="text-3xl font-semibold">
            {usageQuery.isLoading ? <Skeleton className="h-8 w-16" /> : usageQuery.data?.token_usage.completion}
          </CardContent>
        </Card>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>Workflow status distribution</CardTitle>
        </CardHeader>
        <CardContent className="h-72">
          {usageQuery.isLoading ? (
            <Skeleton className="h-full w-full" />
          ) : (
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="status" />
                <YAxis allowDecimals={false} />
                <Tooltip />
                <Line type="monotone" dataKey="total" stroke="#6366f1" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
