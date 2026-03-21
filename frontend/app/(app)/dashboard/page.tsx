"use client";

import Link from "next/link";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useWorkflows } from "@/lib/hooks/use-workflows";

/**
 * Dashboard summarizing recent workflows and quick navigation.
 */
export default function DashboardPage() {
  const { data, isLoading, isError } = useWorkflows();

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight">Mission control</h1>
          <p className="text-sm text-muted-foreground">Monitor autonomous workflows and ingestion health.</p>
        </div>
        <Button asChild>
          <Link href="/workflow/new">Launch workflow</Link>
        </Button>
      </div>
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium text-muted-foreground">Active workflows</CardTitle>
          </CardHeader>
          <CardContent className="text-3xl font-semibold">
            {isLoading ? <Skeleton className="h-8 w-24" /> : data?.filter((w) => w.status === "running").length ?? 0}
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium text-muted-foreground">Completed</CardTitle>
          </CardHeader>
          <CardContent className="text-3xl font-semibold">
            {isLoading ? <Skeleton className="h-8 w-24" /> : data?.filter((w) => w.status === "completed").length ?? 0}
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium text-muted-foreground">Failed</CardTitle>
          </CardHeader>
          <CardContent className="text-3xl font-semibold">
            {isLoading ? <Skeleton className="h-8 w-24" /> : data?.filter((w) => w.status === "failed").length ?? 0}
          </CardContent>
        </Card>
      </div>
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>Recent workflows</CardTitle>
          <Button variant="ghost" size="sm" asChild>
            <Link href="/workflow/new">New</Link>
          </Button>
        </CardHeader>
        <CardContent className="space-y-3">
          {isError && <p className="text-sm text-destructive">Unable to load workflows.</p>}
          {isLoading && <Skeleton className="h-24 w-full" />}
          {!isLoading &&
            data?.map((workflow) => (
              <div key={workflow.id} className="flex items-center justify-between rounded-md border p-3">
                <div>
                  <p className="font-medium">{workflow.title}</p>
                  <p className="text-xs text-muted-foreground">{new Date(workflow.created_at).toLocaleString()}</p>
                </div>
                <div className="flex items-center gap-3">
                  <Badge variant="outline">{workflow.status}</Badge>
                  <Button size="sm" variant="secondary" asChild>
                    <Link href={`/workflow/${workflow.id}`}>Open</Link>
                  </Button>
                </div>
              </div>
            ))}
          {!isLoading && data?.length === 0 && (
            <p className="text-sm text-muted-foreground">No workflows yet. Start with a natural language task.</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
