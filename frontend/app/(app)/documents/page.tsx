"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { apiFetch } from "@/lib/api";

type DocumentRow = {
  id: string;
  name: string;
  source_type: string;
  ingestion_status: string;
  created_at: string;
};

/**
 * Document source management with URL ingestion and listing.
 */
export default function DocumentsPage() {
  const client = useQueryClient();
  const [name, setName] = useState("Research article");
  const [url, setUrl] = useState("https://example.com");

  const documentsQuery = useQuery({
    queryKey: ["documents"],
    queryFn: async () => {
      const response = await apiFetch<DocumentRow[]>("/api/v1/documents/");
      return response.data ?? [];
    },
  });

  const ingestMutation = useMutation({
    mutationFn: async () => {
      await apiFetch("/api/v1/documents/ingest/url", {
        method: "POST",
        body: JSON.stringify({ name, url }),
      });
    },
    onSuccess: async () => {
      await client.invalidateQueries({ queryKey: ["documents"] });
    },
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-semibold">Documents</h1>
        <p className="text-sm text-muted-foreground">Track ingestion jobs and vector readiness.</p>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>Ingest from URL</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="name">Name</Label>
              <Input id="name" value={name} onChange={(event) => setName(event.target.value)} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="url">URL</Label>
              <Input id="url" value={url} onChange={(event) => setUrl(event.target.value)} />
            </div>
          </div>
          <Button onClick={() => ingestMutation.mutate()} disabled={ingestMutation.isPending}>
            {ingestMutation.isPending ? "Queueing..." : "Enqueue ingestion"}
          </Button>
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>Library</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {documentsQuery.isLoading && <Skeleton className="h-24 w-full" />}
          {documentsQuery.data?.map((doc) => (
            <div key={doc.id} className="flex items-center justify-between rounded-md border p-3 text-sm">
              <div>
                <p className="font-medium">{doc.name}</p>
                <p className="text-xs text-muted-foreground">
                  {doc.source_type} · {new Date(doc.created_at).toLocaleString()}
                </p>
              </div>
              <span className="text-xs uppercase text-muted-foreground">{doc.ingestion_status}</span>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
