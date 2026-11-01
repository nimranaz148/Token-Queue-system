"use client";

import * as React from "react";
import { RoleGuard } from "@/components/auth/role-guard";
import { LayoutShell } from "@/components/layout/layout-shell";
import { Button } from "@/components/ui/button";
import { StatusBadge } from "@/components/ui/status-badge";
import { Activity, RefreshCw, Filter, Search, Terminal, AlertCircle } from "lucide-react";

export interface AIRunItem {
  id: string;
  clinic_id: string | null;
  feature: string;
  requested_by: string | null;
  provider: string;
  model: string;
  tools_called: string[] | null;
  input_tokens: number;
  output_tokens: number;
  cost_usd: string | number;
  status: string;
  error: string | null;
  at: string;
}

export function AIActivityView() {
  const [runs, setRuns] = React.useState<AIRunItem[]>([]);
  const [total, setTotal] = React.useState(0);
  const [isLoading, setIsLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  // Filters
  const [startDate, setStartDate] = React.useState("");
  const [endDate, setEndDate] = React.useState("");
  const [featureFilter, setFeatureFilter] = React.useState("all");

  const fetchActivity = React.useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      if (startDate) params.set("start_date", startDate);
      if (endDate) params.set("end_date", endDate);
      if (featureFilter && featureFilter !== "all") params.set("feature", featureFilter);

      const res = await fetch(`/api/v1/ai/activity?${params.toString()}`);
      if (!res.ok) {
        if (res.status === 403) {
          throw new Error("Aapko is page ko dekhnay ki ijazat nahi hai (403 Forbidden).");
        }
        throw new Error("AI activity record load karne mein masla pesh aya.");
      }
      const data = await res.json();
      setRuns(data.items || []);
      setTotal(data.total || 0);
    } catch (err: any) {
      setError(err.message || "Something went wrong");
    } finally {
      setIsLoading(false);
    }
  }, [startDate, endDate, featureFilter]);

  React.useEffect(() => {
    fetchActivity();
  }, [fetchActivity]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight">AI Activity Log</h1>
            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-mono font-medium bg-accent/10 text-accent">
              F-017
            </span>
          </div>
          <p className="text-sm text-fg-muted mt-1">
            Clinic ke tamam AI features, tool calls, token usage aur cost ka audit record.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="secondary" onClick={fetchActivity} disabled={isLoading} className="gap-2">
            <RefreshCw className={`w-4 h-4 ${isLoading ? "animate-spin" : ""}`} />
            Refresh
          </Button>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-surface-raised border border-border p-4 rounded-lg flex flex-wrap gap-4 items-center">
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-fg-muted" />
          <span className="text-sm font-medium">Filters:</span>
        </div>

        <div className="flex items-center gap-2">
          <label htmlFor="start-date" className="text-xs text-fg-muted">From:</label>
          <input
            id="start-date"
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            className="h-8.5 px-3 py-1 bg-surface border border-border rounded-md text-sm text-fg focus:outline-none focus:ring-1 focus:ring-accent"
          />
        </div>

        <div className="flex items-center gap-2">
          <label htmlFor="end-date" className="text-xs text-fg-muted">To:</label>
          <input
            id="end-date"
            type="date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
            className="h-8.5 px-3 py-1 bg-surface border border-border rounded-md text-sm text-fg focus:outline-none focus:ring-1 focus:ring-accent"
          />
        </div>

        <div className="flex items-center gap-2">
          <label htmlFor="feature-select" className="text-xs text-fg-muted">Feature:</label>
          <select
            id="feature-select"
            value={featureFilter}
            onChange={(e) => setFeatureFilter(e.target.value)}
            className="h-8.5 px-3 py-1 bg-surface border border-border rounded-md text-sm text-fg focus:outline-none focus:ring-1 focus:ring-accent"
          >
            <option value="all">Tamam Features (All)</option>
            <option value="chat">Patient Chat (F-019)</option>
            <option value="brief">Daily Brief (F-018)</option>
            <option value="summary">Visit Summary (F-008)</option>
            <option value="prediction">Wait Prediction</option>
          </select>
        </div>

        {(startDate || endDate || featureFilter !== "all") && (
          <Button
            variant="ghost"
            onClick={() => {
              setStartDate("");
              setEndDate("");
              setFeatureFilter("all");
            }}
            className="text-xs h-8.5 px-2"
          >
            Reset Filters
          </Button>
        )}
      </div>

      {/* Error state */}
      {error && (
        <div className="p-4 bg-red-500/10 border border-red-500/30 rounded-lg flex items-center justify-between">
          <div className="flex items-center gap-2 text-red-500">
            <AlertCircle className="w-5 h-5 flex-shrink-0" />
            <p className="text-sm font-medium">{error}</p>
          </div>
          <Button variant="secondary" onClick={fetchActivity} className="text-xs h-8">
            Dobara Koshish (Retry)
          </Button>
        </div>
      )}

      {/* Table / List */}
      <div className="bg-surface-raised border border-border rounded-lg overflow-hidden">
        {isLoading ? (
          <div className="p-12 text-center text-fg-muted flex flex-col items-center gap-3">
            <RefreshCw className="w-6 h-6 animate-spin text-accent" />
            <p className="text-sm">AI activity load ho rahi hai...</p>
          </div>
        ) : runs.length === 0 ? (
          <div className="p-12 text-center text-fg-muted flex flex-col items-center gap-3">
            <Activity className="w-10 h-10 text-fg-muted/40" />
            <p className="text-base font-medium">Koi AI activity record nahi mila</p>
            <p className="text-xs text-fg-muted max-w-sm">
              Muntakhib kardah filters ke mutabiq koi AI execution record mojood nahi hai.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-surface text-fg-muted text-xs uppercase border-b border-border">
                <tr>
                  <th className="px-4 py-3 font-semibold">Time</th>
                  <th className="px-4 py-3 font-semibold">Feature</th>
                  <th className="px-4 py-3 font-semibold">Provider / Model</th>
                  <th className="px-4 py-3 font-semibold">Tools Called</th>
                  <th className="px-4 py-3 font-semibold text-right">Tokens</th>
                  <th className="px-4 py-3 font-semibold text-right">Cost (USD)</th>
                  <th className="px-4 py-3 font-semibold text-center">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border font-mono text-xs">
                {runs.map((run) => (
                  <tr key={run.id} className="hover:bg-surface/50 transition-colors">
                    <td className="px-4 py-3 text-fg whitespace-nowrap font-sans">
                      {new Date(run.at).toLocaleString()}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap">
                      <span className="px-2 py-0.5 rounded bg-surface border border-border text-fg font-sans font-medium">
                        {run.feature}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-fg whitespace-nowrap">
                      <span className="text-fg font-medium">{run.provider}</span>
                      <span className="text-fg-muted ml-1">({run.model})</span>
                    </td>
                    <td className="px-4 py-3 text-fg-muted max-w-xs truncate">
                      {run.tools_called && run.tools_called.length > 0 ? (
                        <div className="flex flex-wrap gap-1">
                          {run.tools_called.map((tool, idx) => (
                            <span key={idx} className="px-1.5 py-0.5 rounded bg-accent/10 text-accent text-[10px]">
                              {tool}
                            </span>
                          ))}
                        </div>
                      ) : (
                        <span className="text-fg-muted/60">—</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-right text-fg whitespace-nowrap">
                      {run.input_tokens + run.output_tokens}
                      <span className="text-fg-muted text-[10px] ml-1">
                        ({run.input_tokens}in / {run.output_tokens}out)
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right font-medium text-fg whitespace-nowrap">
                      ${Number(run.cost_usd).toFixed(6)}
                    </td>
                    <td className="px-4 py-3 text-center whitespace-nowrap font-sans">
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

        {/* Footer pagination info */}
        <div className="px-4 py-3 bg-surface border-t border-border flex items-center justify-between text-xs text-fg-muted">
          <span>Kul record: {total}</span>
          <span>Safah 1</span>
        </div>
      </div>
    </div>
  );
}

export default function AIActivityPage() {
  return (
    <RoleGuard allowedRoles={["owner", "platform_admin"]}>
      <LayoutShell userRole="owner">
        <AIActivityView />
      </LayoutShell>
    </RoleGuard>
  );
}
