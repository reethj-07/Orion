"use client";

import { useRouter } from "next/navigation";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { apiFetch } from "@/lib/api";
import { useAuthStore } from "@/store/auth-store";

/**
 * Organization settings hub with session termination controls.
 */
export default function SettingsPage() {
  const router = useRouter();
  const setUser = useAuthStore((state) => state.setUser);

  const logout = async () => {
    await apiFetch("/api/v1/auth/logout", { method: "POST", body: JSON.stringify({}) });
    setUser(null);
    router.push("/login");
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-semibold">Settings</h1>
        <p className="text-sm text-muted-foreground">Manage organization preferences and API access.</p>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>Session</CardTitle>
        </CardHeader>
        <CardContent>
          <Button variant="outline" onClick={logout}>
            Sign out everywhere on this browser
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
