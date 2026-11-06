"use client";

import * as React from "react";
import Link from "next/link";
import { RoleGuard } from "@/components/auth/role-guard";
import { LayoutShell } from "@/components/layout/layout-shell";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { StatusBadge } from "@/components/ui/status-badge";
import {
  Building2,
  Activity,
  Calendar,
  AlertTriangle,
  Coins,
  Search,
  Plus,
  RefreshCw,
  ExternalLink,
} from "lucide-react";

export interface PlatformKPIs {
  active_clinics: number;
  total_clinics: number;
  tokens_today: number;
  tokens_7_days: number;
  idle_clinics: number;
  ai_spend_this_month: string | number;
}

export interface ClinicOverviewItem {
  id: string;
  name: string;
  slug: string;
  status: string;
  tokens_7d: number;
  tokens_today: number;
  last_activity?: string | null;
}

export interface PlatformOverviewData {
  kpis: PlatformKPIs;
  clinics: ClinicOverviewItem[];
}

interface PlatformOverviewPageProps {
  initialData?: PlatformOverviewData | null;
  userRole?: string;
}

const defaultData: PlatformOverviewData = {
  kpis: {
    active_clinics: 12,
    total_clinics: 15,
    tokens_today: 420,
    tokens_7_days: 2840,
    idle_clinics: 2,
    ai_spend_this_month: "4.20",
  },
  clinics: [
    {
      id: "clinic-1",
      name: "Shifa Family Clinic",
      slug: "shifa-family",
      status: "active",
      tokens_7d: 840,
      tokens_today: 125,
      last_activity: new Date().toISOString(),
    },
    {
      id: "clinic-2",
      name: "Al-Razi Medical Complex",
      slug: "al-razi",
      status: "active",
      tokens_7d: 620,
      tokens_today: 95,
      last_activity: new Date().toISOString(),
    },
    {
      id: "clinic-3",
      name: "Iqra Health Care",
      slug: "iqra-health",
      status: "trial",
      tokens_7d: 0,
      tokens_today: 0,
      last_activity: new Date(Date.now() - 4 * 86400000).toISOString(),
    },
  ],
};

export default function PlatformOverviewPage({
  initialData = null,
  userRole = "platform_admin",
}: PlatformOverviewPageProps) {
  const [data, setData] = React.useState<PlatformOverviewData>(
    initialData || defaultData
  );
  const [search, setSearch] = React.useState("");
  const [isLoading, setIsLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  const fetchOverview = React.useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/v1/admin/overview");
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`);
      }
      const fetched: PlatformOverviewData = await res.json();
      setData(fetched);
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      }
    } finally {
      setIsLoading(false);
    }
  }, []);

  React.useEffect(() => {
    if (!initialData) {
      fetchOverview();
    }
  }, [initialData, fetchOverview]);

  const filteredClinics = React.useMemo(() => {
    if (!search.trim()) return data.clinics;
    const q = search.toLowerCase();
    return data.clinics.filter(
      (c) => c.name.toLowerCase().includes(q) || c.slug.toLowerCase().includes(q)
    );
  }, [data.clinics, search]);

  return (
    <RoleGuard allowedRoles={["platform_admin"]}>
      <LayoutShell
        userRole={userRole}
        clinicName="Platform Control"
        userName="Platform Admin"
      >
        <div className="w-full space-y-7 lg:space-y-8">
          {/* Header */}
          <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-5 rounded-2xl border border-border bg-surface px-5 py-6 shadow-sm sm:px-7">
            <div>
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-success" />
                <span className="text-xs font-semibold text-accent uppercase tracking-[0.16em]">
                  Clinic network · live overview
                </span>
              </div>
              <h1 className="font-display text-3xl sm:text-4xl font-medium text-fg tracking-tight mt-1">
                Platform Overview
              </h1>
              <p className="text-sm text-fg-muted mt-1">
                Multi-clinic SaaS operational metrics, throughput, and AI spend (D-002)
              </p>
            </div>

            <div className="flex items-center gap-2">
              <Button
                variant="secondary"
                size="sm"
                onClick={fetchOverview}
                disabled={isLoading}
                aria-label="Refresh Telemetry"
                className="flex items-center gap-1.5"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? "animate-spin" : ""}`} />
                <span className="hidden sm:inline">Refresh</span>
              </Button>
              <Link href="/admin/clinics/new">
                <Button variant="primary" size="sm" className="flex items-center gap-1.5">
                  <Plus className="w-4 h-4" />
                  <span>New Clinic (F-013)</span>
                </Button>
              </Link>
            </div>
          </div>

          {error && (
            <div className="bg-danger-subtle border border-danger-border text-danger px-4 py-3 rounded-lg text-sm">
              {error}
            </div>
          )}

          {/* Top KPI Cards Banner (PRD §29.2 D-002) */}
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-6 lg:gap-4">
            {/* KPI 1: Active Clinics */}
            <div className="relative overflow-hidden bg-accent rounded-2xl border border-accent p-5 text-fg-inverse shadow-md sm:col-span-2 sm:row-span-2">
              <div aria-hidden="true" className="pointer-events-none absolute -right-12 -top-12 h-48 w-48 rounded-full border border-fg-inverse/10" />
              <div className="flex items-center justify-between text-fg-inverse/75">
                <span className="text-xs font-semibold uppercase tracking-wider">
                  Active Clinics
                </span>
                <Building2 className="w-4 h-4" />
              </div>
              <div className="mt-2">
                <div className="font-mono text-5xl font-semibold text-fg-inverse tracking-tight">
                  {data.kpis.active_clinics}
                </div>
                <div className="text-xs text-fg-inverse/75 mt-1">
                  of {data.kpis.total_clinics} registered
                </div>
                <div className="mt-8" role="img" aria-label={`${data.kpis.active_clinics} active out of ${data.kpis.total_clinics} registered clinics`}>
                  <div className="mb-2 flex items-center justify-between text-[10px] font-medium uppercase tracking-wider text-fg-inverse/70">
                    <span>Network activity</span>
                    <span>{data.kpis.total_clinics} clinics</span>
                  </div>
                  <div className="flex gap-1" aria-hidden="true">
                    {Array.from({ length: Math.min(data.kpis.total_clinics, 24) }, (_, index) => (
                      <span
                        key={index}
                        className={`h-1.5 flex-1 rounded-full ${index < data.kpis.active_clinics ? "bg-fg-inverse" : "bg-fg-inverse/25"}`}
                      />
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* KPI 2: Tokens Today */}
            <div className="bg-surface rounded-2xl border border-border p-4 shadow-sm sm:col-span-2">
              <div className="flex items-center justify-between text-fg-muted">
                <span className="text-xs font-semibold uppercase tracking-wider">
                  Tokens Today
                </span>
                <Activity className="w-4 h-4 text-info" />
              </div>
              <div className="mt-2">
                <div className="font-mono text-3xl font-semibold text-fg tracking-tight">
                  {data.kpis.tokens_today}
                </div>
                <div className="text-xs text-fg-muted mt-1">
                  Across all clinics
                </div>
              </div>
            </div>

            {/* KPI 3: Tokens 7d */}
            <div className="bg-surface rounded-2xl border border-border p-4 shadow-sm sm:col-span-2">
              <div className="flex items-center justify-between text-fg-muted">
                <span className="text-xs font-semibold uppercase tracking-wider">
                  Tokens 7d
                </span>
                <Calendar className="w-4 h-4 text-chart-3" />
              </div>
              <div className="mt-2">
                <div className="font-mono text-3xl font-semibold text-fg tracking-tight">
                  {data.kpis.tokens_7_days}
                </div>
                <div className="text-xs text-fg-muted mt-1">
                  Last 7 days throughput
                </div>
              </div>
            </div>

            {/* KPI 4: Idle Clinics */}
            <div className="bg-warning-subtle rounded-2xl border border-warning-border p-4 shadow-sm sm:col-span-2">
              <div className="flex items-center justify-between text-fg-muted">
                <span className="text-xs font-semibold uppercase tracking-wider">
                  Idle Clinics
                </span>
                <AlertTriangle className="w-4 h-4 text-warning" />
              </div>
              <div className="mt-2">
                <div className="font-mono text-3xl font-semibold text-fg tracking-tight">
                  {data.kpis.idle_clinics}
                </div>
                <div className="text-xs text-fg-muted mt-1">
                  Zero activity 3+ days
                </div>
              </div>
            </div>

            {/* KPI 5: AI Spend This Month */}
            <div className="bg-surface rounded-2xl border border-border p-4 shadow-sm col-span-2 sm:col-span-2">
              <div className="flex items-center justify-between text-fg-muted">
                <span className="text-xs font-semibold uppercase tracking-wider">
                  AI Spend
                </span>
                <Coins className="w-4 h-4 text-chart-4" />
              </div>
              <div className="mt-2">
                <div className="font-mono text-3xl font-semibold text-fg tracking-tight">
                  ${data.kpis.ai_spend_this_month}
                </div>
                <div className="text-xs text-fg-muted mt-1">
                  This calendar month
                </div>
              </div>
            </div>
          </div>

          {/* Clinics Activity Table (PRD §29.2 D-002) */}
          <div className="bg-surface rounded-2xl border border-border shadow-sm overflow-hidden">
            <div className="p-4 sm:p-6 border-b border-border flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
              <div>
                <h2 className="font-display text-xl font-medium text-fg">
                  Clinics Activity &amp; Status
                </h2>
                <p className="text-xs text-fg-muted mt-1">
                  Tenant status, weekly volume, and last recorded token activity
                </p>
              </div>

              <div className="relative w-full sm:w-64">
                <Search className="w-4 h-4 text-fg-subtle absolute left-3 top-1/2 -translate-y-1/2" />
                <Input
                  type="text"
                  placeholder="Search clinics..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  className="pl-9 h-8.5 text-xs"
                />
              </div>
            </div>

            {filteredClinics.length === 0 ? (
              <div className="p-12 text-center">
                <Building2 className="w-10 h-10 text-fg-subtle mx-auto mb-3" />
                <h3 className="text-sm font-semibold text-fg">
                  Koi clinic register nahi hua
                </h3>
                <p className="text-xs text-fg-muted mt-1">
                  No clinic records found matching current query.
                </p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead className="bg-surface-sunken text-xs font-semibold text-fg-muted tracking-wide border-b border-border">
                    <tr>
                      <th className="px-5 py-3.5">Clinic Name</th>
                      <th className="px-5 py-3.5">Status</th>
                      <th className="px-5 py-3.5">Tokens 7d</th>
                      <th className="px-5 py-3.5">Tokens Today</th>
                      <th className="px-5 py-3.5">Last Activity</th>
                      <th className="px-5 py-3.5 text-right">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border">
                    {filteredClinics.map((clinic) => (
                      <tr key={clinic.id} className="hover:bg-surface-hover transition-colors">
                        <td className="px-5 py-4">
                          <div className="font-semibold text-fg">{clinic.name}</div>
                          <div className="text-xs text-fg-subtle font-mono">/c/{clinic.slug}</div>
                        </td>
                        <td className="px-5 py-4">
                          <StatusBadge
                            variant={
                              clinic.status === "active"
                                ? "success"
                                : clinic.status === "trial"
                                  ? "info"
                                  : "warning"
                            }
                          >
                            {clinic.status}
                          </StatusBadge>
                        </td>
                        <td className="px-5 py-4 font-mono font-semibold text-fg">
                          {clinic.tokens_7d}
                        </td>
                        <td className="px-5 py-4 font-mono font-semibold text-fg">
                          {clinic.tokens_today}
                        </td>
                        <td className="px-5 py-4 text-xs text-fg-muted">
                          {clinic.last_activity
                            ? new Date(clinic.last_activity).toLocaleDateString()
                            : "—"}
                        </td>
                        <td className="px-5 py-4 text-right">
                          <Link
                            href="/admin/clinics"
                            className="inline-flex items-center text-xs font-semibold text-accent hover:text-accent-hover gap-1"
                          >
                            Manage <ExternalLink className="w-3 h-3" />
                          </Link>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      </LayoutShell>
    </RoleGuard>
  );
}
