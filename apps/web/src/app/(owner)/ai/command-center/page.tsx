"use client";

import * as React from "react";
import Link from "next/link";
import { RoleGuard } from "@/components/auth/role-guard";
import { LayoutShell } from "@/components/layout/layout-shell";
import { Button } from "@/components/ui/button";
import { StatusBadge } from "@/components/ui/status-badge";
import {
  Activity,
  AlertTriangle,
  ArrowRight,
  Bot,
  DollarSign,
  RefreshCw,
  Sparkles,
  ThumbsDown,
  Zap,
} from "lucide-react";

export interface RecentRunItem {
  id: string;
  feature: string;
  provider: string;
  model: string;
  cost_usd: string | number;
  status: string;
  at: string;
  tools_called: string[] | null;
}

export interface CommandCenterData {
  ai_calls: number;
  failures: number;
  fallback_rate: number;
  total_cost_usd: string | number;
  thumbs_down_rate: number;
  recent_runs: RecentRunItem[];
}

export function AICommandCenterView() {
  const [data, setData] = React.useState<CommandCenterData | null>(null);
  const [isLoading, setIsLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  const fetchKpis = React.useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/v1/ai/command-center");
      if (!res.ok) {
        if (res.status === 403) {
          throw new Error("Aapko is dashboard ko dekhnay ki ijazat nahi hai (403 Forbidden).");
        }
        throw new Error("Command Center KPIs load karne mein masla pesh aya.");
      }
      const json = await res.json();
      setData(json);
    } catch (err: any) {
      setError(err.message || "Failed to load command center");
    } finally {
      setIsLoading(false);
    }
  }, []);

  React.useEffect(() => {
    fetchKpis();
  }, [fetchKpis]);

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight">AI Command Center</h1>
            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-mono font-medium bg-accent/10 text-accent">
              D-003
            </span>
          </div>
          <p className="text-sm text-fg-muted mt-1">
            Clinic ke AI infrastructure ki live karkardagi (calls, reliability, fallback, cost, aur quality).
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Button variant="secondary" onClick={fetchKpis} disabled={isLoading} className="gap-2">
            <RefreshCw className={`w-4 h-4 ${isLoading ? "animate-spin" : ""}`} />
            Refresh
          </Button>
          <Link href="/ai/activity">
            <Button variant="primary" className="gap-2">
              Full Activity Log
              <ArrowRight className="w-4 h-4" />
            </Button>
          </Link>
        </div>
      </div>

      {/* Error state */}
      {error && (
        <div className="p-4 bg-red-500/10 border border-red-500/30 rounded-lg flex items-center justify-between text-red-500">
          <p className="text-sm font-medium">{error}</p>
          <Button variant="secondary" onClick={fetchKpis} className="text-xs h-8">
            Dobara Koshish
          </Button>
        </div>
      )}

      {/* Loading state */}
      {isLoading ? (
        <div className="p-16 text-center text-fg-muted flex flex-col items-center gap-3 bg-surface-raised border border-border rounded-lg">
          <RefreshCw className="w-6 h-6 animate-spin text-accent" />
          <p className="text-sm">Command Center data load ho raha hai...</p>
        </div>
      ) : data ? (
        <div className="space-y-6">
          {/* 5 KPI Cards Grid */}
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
            {/* AI Calls */}
            <div className="bg-surface-raised border border-border p-4 rounded-lg space-y-2 shadow-sm">
              <div className="flex items-center justify-between text-fg-muted">
                <span className="text-xs font-medium">AI Calls</span>
                <Bot className="w-4 h-4 text-accent" />
              </div>
              <p className="text-2xl font-bold font-mono text-fg">{data.ai_calls}</p>
              <p className="text-[11px] text-fg-muted">Kul inferences</p>
            </div>

            {/* Failures */}
            <div className="bg-surface-raised border border-border p-4 rounded-lg space-y-2 shadow-sm">
              <div className="flex items-center justify-between text-fg-muted">
                <span className="text-xs font-medium">Failures</span>
                <AlertTriangle className="w-4 h-4 text-danger" />
              </div>
              <p className="text-2xl font-bold font-mono text-fg">{data.failures}</p>
              <p className="text-[11px] text-fg-muted">Na-kam requests</p>
            </div>

            {/* Fallback Rate */}
            <div className="bg-surface-raised border border-border p-4 rounded-lg space-y-2 shadow-sm">
              <div className="flex items-center justify-between text-fg-muted">
                <span className="text-xs font-medium">Fallback Rate</span>
                <Zap className="w-4 h-4 text-warning" />
              </div>
              <p className="text-2xl font-bold font-mono text-fg">
                {(data.fallback_rate * 100).toFixed(1)}%
              </p>
              <p className="text-[11px] text-fg-muted">Secondary model use</p>
            </div>

            {/* Total Spend Cost */}
            <div className="bg-surface-raised border border-border p-4 rounded-lg space-y-2 shadow-sm">
              <div className="flex items-center justify-between text-fg-muted">
                <span className="text-xs font-medium">AI Spend (USD)</span>
                <DollarSign className="w-4 h-4 text-success" />
              </div>
              <p className="text-2xl font-bold font-mono text-fg">
                ${Number(data.total_cost_usd).toFixed(4)}
              </p>
              <p className="text-[11px] text-fg-muted">Estimates</p>
            </div>

            {/* Thumbs-down Rate */}
            <div className="bg-surface-raised border border-border p-4 rounded-lg space-y-2 shadow-sm col-span-2 sm:col-span-1">
              <div className="flex items-center justify-between text-fg-muted">
                <span className="text-xs font-medium">Thumbs-down</span>
                <ThumbsDown className="w-4 h-4 text-warning" />
              </div>
              <p className="text-2xl font-bold font-mono text-fg">
                {(data.thumbs_down_rate * 100).toFixed(1)}%
              </p>
              <p className="text-[11px] text-fg-muted">Manfi feedback</p>
            </div>
          </div>

          {/* Recent Runs Section */}
          <div className="bg-surface-raised border border-border rounded-lg overflow-hidden shadow-sm">
            <div className="p-4 border-b border-border flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Activity className="w-4 h-4 text-accent" />
                <h2 className="text-sm font-semibold text-fg">Recent AI Runs (Taza-tareen Runs)</h2>
              </div>
              <Link
                href="/ai/activity"
                className="text-xs text-accent hover:underline flex items-center gap-1"
              >
                Tamam dekhain <ArrowRight className="w-3 h-3" />
              </Link>
            </div>

            {data.recent_runs.length === 0 ? (
              <div className="p-8 text-center text-fg-muted text-xs">
                Abhi tak koi AI run record nahi hua.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-surface text-fg-muted uppercase border-b border-border font-medium">
                    <tr>
                      <th className="px-4 py-2.5">Time</th>
                      <th className="px-4 py-2.5">Feature</th>
                      <th className="px-4 py-2.5">Provider / Model</th>
                      <th className="px-4 py-2.5 text-right">Cost</th>
                      <th className="px-4 py-2.5 text-center">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border font-mono">
                    {data.recent_runs.map((run) => (
                      <tr key={run.id} className="hover:bg-surface/50 transition-colors">
                        <td className="px-4 py-2.5 text-fg whitespace-nowrap font-sans">
                          {new Date(run.at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                        </td>
                        <td className="px-4 py-2.5 whitespace-nowrap">
                          <span className="px-1.5 py-0.5 rounded bg-surface border border-border text-fg font-sans font-medium">
                            {run.feature}
                          </span>
                        </td>
                        <td className="px-4 py-2.5 text-fg whitespace-nowrap">
                          {run.provider} <span className="text-fg-muted">({run.model})</span>
                        </td>
                        <td className="px-4 py-2.5 text-right font-medium text-fg whitespace-nowrap">
                          ${Number(run.cost_usd).toFixed(6)}
                        </td>
                        <td className="px-4 py-2.5 text-center whitespace-nowrap font-sans">
                          <StatusBadge variant={run.status === "success" ? "success" : "danger"}>
                            {run.status === "success" ? "Kamiyab" : "Error"}
                          </StatusBadge>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      ) : null}
    </div>
  );
}

export default function AICommandCenterPage() {
  return (
    <RoleGuard allowedRoles={["owner", "platform_admin"]}>
      <LayoutShell userRole="owner">
        <AICommandCenterView />
      </LayoutShell>
    </RoleGuard>
  );
}
