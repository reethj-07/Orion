"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { apiFetch } from "@/lib/api";

const schema = z.object({
  title: z.string().min(3),
  task_description: z.string().min(10),
});

type FormValues = z.infer<typeof schema>;

/**
 * Create a workflow by describing the objective in natural language.
 */
export default function NewWorkflowPage() {
  const router = useRouter();
  const form = useForm<FormValues>({ resolver: zodResolver(schema) });

  const onSubmit = form.handleSubmit(async (values) => {
    const response = await apiFetch<{ id: string }>("/api/v1/workflows/", {
      method: "POST",
      body: JSON.stringify(values),
    });
    if (response.data?.id) {
      router.push(`/workflow/${response.data.id}`);
    }
  });

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <h1 className="text-3xl font-semibold">Compose a workflow</h1>
        <p className="text-sm text-muted-foreground">
          Describe the outcome; Orion&apos;s orchestrator will plan specialist agents automatically.
        </p>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>Task briefing</CardTitle>
        </CardHeader>
        <CardContent>
          <form className="space-y-4" onSubmit={onSubmit}>
            <div className="space-y-2">
              <Label htmlFor="title">Title</Label>
              <Input id="title" placeholder="Competitive pricing brief" {...form.register("title")} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="task_description">Instructions</Label>
              <textarea
                id="task_description"
                className="min-h-[160px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                placeholder="Analyze our top 3 competitors..."
                {...form.register("task_description")}
              />
            </div>
            <Button type="submit" disabled={form.formState.isSubmitting}>
              {form.formState.isSubmitting ? "Dispatching..." : "Run multi-agent workflow"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
