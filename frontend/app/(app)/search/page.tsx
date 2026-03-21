"use client";

import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { apiFetch } from "@/lib/api";

type SearchHit = {
  source_name?: string | null;
  text_preview?: string | null;
  score: number;
};

/**
 * Semantic and hybrid search experiment surface for operators.
 */
export default function SearchPage() {
  const [query, setQuery] = useState("pricing strategy");
  const [hits, setHits] = useState<SearchHit[]>([]);
  const [mode, setMode] = useState<"semantic" | "hybrid">("semantic");

  const runSearch = async () => {
    const path = mode === "semantic" ? "/api/v1/search/semantic" : "/api/v1/search/hybrid";
    const response = await apiFetch<SearchHit[]>(path, {
      method: "POST",
      body: JSON.stringify({ query, limit: 8 }),
    });
    setHits(response.data ?? []);
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-semibold">Semantic search</h1>
        <p className="text-sm text-muted-foreground">Query your org vector collections with hybrid rescoring.</p>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>Query</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="query">Prompt</Label>
            <Input id="query" value={query} onChange={(event) => setQuery(event.target.value)} />
          </div>
          <div className="flex flex-wrap gap-2">
            <Button variant={mode === "semantic" ? "default" : "outline"} onClick={() => setMode("semantic")}>
              Semantic
            </Button>
            <Button variant={mode === "hybrid" ? "default" : "outline"} onClick={() => setMode("hybrid")}>
              Hybrid
            </Button>
            <Button onClick={runSearch}>Search</Button>
          </div>
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>Results</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          {hits.length === 0 && <p className="text-muted-foreground">No results yet.</p>}
          {hits.map((hit, index) => (
            <div key={`${hit.source_name}-${index}`} className="rounded-md border p-3">
              <p className="text-xs text-muted-foreground">
                {hit.source_name} · {hit.score.toFixed(3)}
              </p>
              <p>{hit.text_preview}</p>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
