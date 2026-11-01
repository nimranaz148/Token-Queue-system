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
        <div className="space-y-6">
          {/* Header */}
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-4 border-b border-gray-200">
            <div>
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-blue-500 animate-pulse" />
                <span className="text-xs font-semibold text-blue-700 uppercase tracking-wider">
                  Platform Telemetry
                </span>
              </div>
              <h1 className="text-2xl sm:text-3xl font-extrabold text-gray-900 tracking-tight mt-1">
                Platform Overview
              </h1>
              <p className="text-sm text-gray-500 mt-0.5">
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
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
              {error}
            </div>
          )}

          {/* Top KPI Cards Banner (PRD §29.2 D-002) */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">
            {/* KPI 1: Active Clinics */}
            <div className="bg-white rounded-xl border border-gray-200 p-4 shadow-sm">
              <div className="flex items-center justify-between text-gray-500">
                <span className="text-xs font-semibold uppercase tracking-wider">
                  Active Clinics
                </span>
                <Building2 className="w-4 h-4 text-emerald-600" />
              </div>
              <div className="mt-2">
                <div className="text-2xl font-black text-gray-900 tracking-tight">
                  {data.kpis.active_clinics}
                </div>
                <div className="text-[11px] text-gray-500 mt-0.5">
                  of {data.kpis.total_clinics} registered
                </div>
              </div>
            </div>

            {/* KPI 2: Tokens Today */}
            <div className="bg-white rounded-xl border border-gray-200 p-4 shadow-sm">
              <div className="flex items-center justify-between text-gray-500">
                <span className="text-xs font-semibold uppercase tracking-wider">
                  Tokens Today
                </span>
                <Activity className="w-4 h-4 text-blue-600" />
              </div>
              <div className="mt-2">
                <div className="text-2xl font-black text-gray-900 tracking-tight">
                  {data.kpis.tokens_today}
                </div>
                <div className="text-[11px] text-gray-500 mt-0.5">
                  Across all clinics
                </div>
              </div>
            </div>

            {/* KPI 3: Tokens 7d */}
            <div className="bg-white rounded-xl border border-gray-200 p-4 shadow-sm">
              <div className="flex items-center justify-between text-gray-500">
                <span className="text-xs font-semibold uppercase tracking-wider">
                  Tokens 7d
                </span>
                <Calendar className="w-4 h-4 text-purple-600" />
              </div>
              <div className="mt-2">
                <div className="text-2xl font-black text-gray-900 tracking-tight">
                  {data.kpis.tokens_7_days}
                </div>
                <div className="text-[11px] text-gray-500 mt-0.5">
                  Last 7 days throughput
                </div>
              </div>
            </div>

            {/* KPI 4: Idle Clinics */}
            <div className="bg-white rounded-xl border border-gray-200 p-4 shadow-sm">
              <div className="flex items-center justify-between text-gray-500">
                <span className="text-xs font-semibold uppercase tracking-wider">
                  Idle Clinics
                </span>
                <AlertTriangle className="w-4 h-4 text-amber-600" />
              </div>
              <div className="mt-2">
                <div className="text-2xl font-black text-gray-900 tracking-tight">
                  {data.kpis.idle_clinics}
                </div>
                <div className="text-[11px] text-gray-500 mt-0.5">
                  Zero activity 3+ days
                </div>
              </div>
            </div>

            {/* KPI 5: AI Spend This Month */}
            <div className="bg-white rounded-xl border border-gray-200 p-4 shadow-sm col-span-2 sm:col-span-1">
              <div className="flex items-center justify-between text-gray-500">
                <span className="text-xs font-semibold uppercase tracking-wider">
                  AI Spend
                </span>
                <Coins className="w-4 h-4 text-teal-600" />
              </div>
              <div className="mt-2">
                <div className="text-2xl font-black text-gray-900 tracking-tight">
                  ${data.kpis.ai_spend_this_month}
                </div>
                <div className="text-[11px] text-gray-500 mt-0.5">
                  This calendar month
                </div>
              </div>
            </div>
          </div>

          {/* Clinics Activity Table (PRD §29.2 D-002) */}
          <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
            <div className="p-4 sm:p-5 border-b border-gray-200 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
              <div>
                <h2 className="text-base font-bold text-gray-900">
                  Clinics Activity &amp; Status
                </h2>
                <p className="text-xs text-gray-500">
                  Tenant status, weekly volume, and last recorded token activity
                </p>
              </div>

              <div className="relative w-full sm:w-64">
                <Search className="w-4 h-4 text-gray-400 absolute left-3 top-1/2 -translate-y-1/2" />
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
                <Building2 className="w-10 h-10 text-gray-300 mx-auto mb-3" />
                <h3 className="text-sm font-semibold text-gray-800">
                  Koi clinic register nahi hua
                </h3>
                <p className="text-xs text-gray-500 mt-1">
                  No clinic records found matching current query.
                </p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead className="bg-gray-50 text-xs font-semibold text-gray-500 uppercase tracking-wider border-b border-gray-200">
                    <tr>
                      <th className="px-5 py-3.5">Clinic Name</th>
                      <th className="px-5 py-3.5">Status</th>
                      <th className="px-5 py-3.5">Tokens 7d</th>
                      <th className="px-5 py-3.5">Tokens Today</th>
                      <th className="px-5 py-3.5">Last Activity</th>
                      <th className="px-5 py-3.5 text-right">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {filteredClinics.map((clinic) => (
                      <tr key={clinic.id} className="hover:bg-gray-50/70 transition-colors">
                        <td className="px-5 py-4">
                          <div className="font-bold text-gray-900">{clinic.name}</div>
                          <div className="text-xs text-gray-400 font-mono">/c/{clinic.slug}</div>
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
                        <td className="px-5 py-4 font-semibold text-gray-700">
                          {clinic.tokens_7d}
                        </td>
                        <td className="px-5 py-4 font-semibold text-gray-700">
                          {clinic.tokens_today}
                        </td>
                        <td className="px-5 py-4 text-xs text-gray-500">
                          {clinic.last_activity
                            ? new Date(clinic.last_activity).toLocaleDateString()
                            : "—"}
                        </td>
                        <td className="px-5 py-4 text-right">
                          <Link
                            href="/admin/clinics"
                            className="inline-flex items-center text-xs font-semibold text-teal-600 hover:text-teal-700 gap-1"
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
