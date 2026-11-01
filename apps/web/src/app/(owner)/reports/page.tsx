"use client";

import * as React from "react";
import Link from "next/link";
import { RoleGuard } from "@/components/auth/role-guard";
import { LayoutShell } from "@/components/layout/layout-shell";
import { Button } from "@/components/ui/button";
import {
  Users,
  Clock,
  UserX,
  TrendingUp,
  Calendar,
  Download,
  RefreshCw,
  ArrowRight,
  Filter,
} from "lucide-react";

export interface DailyReportKPIs {
  patients_seen: number;
  avg_wait_minutes: number | string | null;
  no_shows: number;
  online_share_pct: number | string;
  total_tokens: number;
  online_count: number;
  walk_in_count: number;
  cancelled_count: number;
}

export interface DailyTrendItem {
  date: string;
  day_name: string;
  patients_seen: number;
  no_shows: number;
  total_tokens: number;
}

export interface DailyReportData {
  clinic_id: string;
  date: string;
  doctor_id?: string | null;
  doctor_name?: string | null;
  kpis: DailyReportKPIs;
  trend_7_days: DailyTrendItem[];
}

export interface DoctorOption {
  id: string;
  name: string;
}

interface RozKiReportPageProps {
  initialData?: DailyReportData | null;
  initialDoctors?: DoctorOption[];
  userRole?: string;
}

const defaultReportData: DailyReportData = {
  clinic_id: "demo-clinic-id",
  date: new Date().toISOString().split("T")[0],
  kpis: {
    patients_seen: 54,
    avg_wait_minutes: "14.0",
    no_shows: 6,
    online_share_pct: "38.0",
    total_tokens: 60,
    online_count: 23,
    walk_in_count: 37,
    cancelled_count: 2,
  },
  trend_7_days: [
    { date: "2026-10-27", day_name: "Tue", patients_seen: 42, no_shows: 4, total_tokens: 46 },
    { date: "2026-10-28", day_name: "Wed", patients_seen: 48, no_shows: 5, total_tokens: 53 },
    { date: "2026-10-29", day_name: "Thu", patients_seen: 51, no_shows: 3, total_tokens: 54 },
    { date: "2026-10-30", day_name: "Fri", patients_seen: 38, no_shows: 7, total_tokens: 45 },
    { date: "2026-10-31", day_name: "Sat", patients_seen: 55, no_shows: 4, total_tokens: 59 },
    { date: "2026-11-01", day_name: "Sun", patients_seen: 30, no_shows: 2, total_tokens: 32 },
    { date: "2026-11-02", day_name: "Mon", patients_seen: 54, no_shows: 6, total_tokens: 60 },
  ],
};

export default function RozKiReportPage({
  initialData = null,
  initialDoctors = [],
  userRole = "owner",
}: RozKiReportPageProps) {
  const [selectedDate, setSelectedDate] = React.useState<string>(
    initialData?.date || new Date().toISOString().split("T")[0]
  );
  const [selectedDoctorId, setSelectedDoctorId] = React.useState<string>("");
  const [reportData, setReportData] = React.useState<DailyReportData>(
    initialData || defaultReportData
  );
  const [doctors, setDoctors] = React.useState<DoctorOption[]>(initialDoctors);
  const [isLoading, setIsLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  const fetchReport = React.useCallback(async (dateStr: string, docId: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      if (dateStr) params.append("date", dateStr);
      if (docId) params.append("doctor_id", docId);

      const res = await fetch(`/api/v1/reports/daily?${params.toString()}`);
      if (!res.ok) {
        throw new Error(`Report load failed: ${res.status}`);
      }
      const data: DailyReportData = await res.json();
      setReportData(data);
    } catch (err: unknown) {
      // In test or local dev when API is mocked, keep current data or fallback
      if (err instanceof Error) {
        setError(err.message);
      }
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Fetch doctors for filter if not provided
  React.useEffect(() => {
    if (doctors.length === 0) {
      fetch("/api/v1/doctors")
        .then((res) => (res.ok ? res.json() : []))
        .then((data: DoctorOption[]) => {
          if (Array.isArray(data)) setDoctors(data);
        })
        .catch(() => {});
    }
  }, [doctors.length]);

  const handleDateChange = (newDate: string) => {
    setSelectedDate(newDate);
    fetchReport(newDate, selectedDoctorId);
  };

  const handleDoctorChange = (docId: string) => {
    setSelectedDoctorId(docId);
    fetchReport(selectedDate, docId);
  };

  const setToday = () => {
    const today = new Date().toISOString().split("T")[0];
    setSelectedDate(today);
    fetchReport(today, selectedDoctorId);
  };

  const handleExportCSV = () => {
    const csvContent =
      "data:text/csv;charset=utf-8," +
      "Date,Doctor,Patients Seen,Avg Wait (min),No Shows,Online Share (%)\n" +
      `${reportData.date},${reportData.doctor_name || "All"},${reportData.kpis.patients_seen},${reportData.kpis.avg_wait_minutes || 0},${reportData.kpis.no_shows},${reportData.kpis.online_share_pct}%\n`;

    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `roz_ki_report_${reportData.date}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const maxSeen = Math.max(
    1,
    ...reportData.trend_7_days.map((d) => d.patients_seen)
  );

  return (
    <RoleGuard allowedRoles={["owner", "doctor"]}>
      <LayoutShell
        userRole={userRole}
        clinicName="Shifa Clinic"
        userName="Clinic Owner"
      >
        <div className="space-y-6">
          {/* Header */}
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-4 border-b border-gray-200">
            <div>
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse" />
                <span className="text-xs font-semibold text-emerald-700 uppercase tracking-wider">
                  Live Analytics
                </span>
              </div>
              <h1 className="text-2xl sm:text-3xl font-extrabold text-gray-900 tracking-tight mt-1">
                Roz ki Report
              </h1>
              <p className="text-sm text-gray-500 mt-0.5">
                Daily OPD performance, wait times, and queue throughput (D-001 / F-010)
              </p>
            </div>

            {/* Filter controls: [Aaj ▾] [Doctor ▾] */}
            <div className="flex flex-wrap items-center gap-2">
              <div className="flex items-center bg-white border border-gray-300 rounded-lg shadow-sm px-2.5 py-1.5">
                <Calendar className="w-4 h-4 text-gray-500 mr-2" />
                <input
                  type="date"
                  aria-label="Report Date"
                  value={selectedDate}
                  onChange={(e) => handleDateChange(e.target.value)}
                  className="text-sm font-medium text-gray-700 bg-transparent border-none outline-none focus:ring-0"
                />
                <button
                  type="button"
                  onClick={setToday}
                  className="ml-2 text-xs font-bold text-teal-700 bg-teal-50 px-2 py-0.5 rounded hover:bg-teal-100"
                >
                  Aaj
                </button>
              </div>

              <div className="flex items-center bg-white border border-gray-300 rounded-lg shadow-sm px-2.5 py-1.5">
                <Filter className="w-4 h-4 text-gray-500 mr-2" />
                <select
                  aria-label="Doctor Filter"
                  value={selectedDoctorId}
                  onChange={(e) => handleDoctorChange(e.target.value)}
                  className="text-sm font-medium text-gray-700 bg-transparent border-none outline-none focus:ring-0"
                >
                  <option value="">All Doctors (Tamam)</option>
                  {doctors.map((doc) => (
                    <option key={doc.id} value={doc.id}>
                      {doc.name}
                    </option>
                  ))}
                </select>
              </div>

              <Button
                variant="secondary"
                size="sm"
                onClick={() => fetchReport(selectedDate, selectedDoctorId)}
                disabled={isLoading}
                aria-label="Refresh Report"
                className="flex items-center gap-1.5"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? "animate-spin" : ""}`} />
                <span className="hidden sm:inline">Refresh</span>
              </Button>
            </div>
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
              {error}
            </div>
          )}

          {/* KPI Cards Grid (PRD §29.1 D-001) */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Card 1: Patients seen */}
            <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm hover:shadow-md transition-shadow">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
                  Patients Seen
                </span>
                <div className="w-8 h-8 rounded-lg bg-teal-50 flex items-center justify-center text-teal-600">
                  <Users className="w-4 h-4" />
                </div>
              </div>
              <div className="mt-3">
                <div className="text-3xl font-black text-gray-900 tracking-tight">
                  {reportData.kpis.patients_seen}
                </div>
                <div className="flex items-center justify-between mt-2">
                  <span className="text-xs text-gray-500">Mareez dekhe gaye</span>
                  <Link
                    href="/tokens?status=done"
                    className="inline-flex items-center text-xs font-bold text-teal-600 hover:text-teal-700 gap-0.5"
                  >
                    View <ArrowRight className="w-3 h-3" />
                  </Link>
                </div>
              </div>
            </div>

            {/* Card 2: Avg wait */}
            <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm hover:shadow-md transition-shadow">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
                  Avg Wait
                </span>
                <div className="w-8 h-8 rounded-lg bg-blue-50 flex items-center justify-center text-blue-600">
                  <Clock className="w-4 h-4" />
                </div>
              </div>
              <div className="mt-3">
                <div className="text-3xl font-black text-gray-900 tracking-tight">
                  {reportData.kpis.avg_wait_minutes ? `${reportData.kpis.avg_wait_minutes}m` : "—"}
                </div>
                <div className="text-xs text-gray-500 mt-2">
                  Average intezar duration
                </div>
              </div>
            </div>

            {/* Card 3: No-shows */}
            <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm hover:shadow-md transition-shadow">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
                  No-shows
                </span>
                <div className="w-8 h-8 rounded-lg bg-amber-50 flex items-center justify-center text-amber-600">
                  <UserX className="w-4 h-4" />
                </div>
              </div>
              <div className="mt-3">
                <div className="text-3xl font-black text-gray-900 tracking-tight">
                  {reportData.kpis.no_shows}
                </div>
                <div className="flex items-center justify-between mt-2">
                  <span className="text-xs text-gray-500">Ghair hazir tokens</span>
                  <Link
                    href="/tokens?status=no_show"
                    className="inline-flex items-center text-xs font-bold text-amber-600 hover:text-amber-700 gap-0.5"
                  >
                    View <ArrowRight className="w-3 h-3" />
                  </Link>
                </div>
              </div>
            </div>

            {/* Card 4: Online share */}
            <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm hover:shadow-md transition-shadow">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
                  Online Share
                </span>
                <div className="w-8 h-8 rounded-lg bg-purple-50 flex items-center justify-center text-purple-600">
                  <TrendingUp className="w-4 h-4" />
                </div>
              </div>
              <div className="mt-3">
                <div className="text-3xl font-black text-gray-900 tracking-tight">
                  {reportData.kpis.online_share_pct} %
                </div>
                <div className="text-xs text-gray-500 mt-2">
                  {reportData.kpis.online_count} online · {reportData.kpis.walk_in_count} walk-in
                </div>
              </div>
            </div>
          </div>

          {/* 7-Day Trend Chart Card (PRD §29.1 D-001) */}
          <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 pb-4 border-b border-gray-100">
              <div>
                <h2 className="text-base font-bold text-gray-900">
                  7 din ka chart
                </h2>
                <p className="text-xs text-gray-500">
                  Daily patients treated over the last 7 days
                </p>
              </div>
              <span className="text-xs text-gray-500 font-medium">
                Peak: {maxSeen} patients
              </span>
            </div>

            {/* Visual Bar Chart */}
            <div className="mt-6 flex items-end justify-between gap-2 sm:gap-4 h-48 px-2">
              {reportData.trend_7_days.map((item, idx) => {
                const heightPct = Math.max(12, Math.round((item.patients_seen / maxSeen) * 100));
                const isSelected = item.date === selectedDate;

                return (
                  <div
                    key={item.date}
                    className="flex-1 flex flex-col items-center gap-2 h-full justify-end group"
                  >
                    <span className="text-xs font-bold text-gray-700 opacity-90 group-hover:text-teal-700 transition-colors">
                      {item.patients_seen}
                    </span>
                    <div
                      style={{ height: `${heightPct}%` }}
                      className={`w-full max-w-[48px] rounded-t-md transition-all duration-300 ${
                        isSelected
                          ? "bg-teal-600 shadow-md ring-2 ring-teal-400"
                          : "bg-teal-500/80 hover:bg-teal-600"
                      }`}
                    />
                    <div className="text-center pt-1 border-t border-gray-100 w-full">
                      <div className="text-xs font-semibold text-gray-800">
                        {item.day_name}
                      </div>
                      <div className="text-[10px] text-gray-500">
                        {item.date.slice(5)}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Export & Actions footer */}
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4 bg-gray-50 rounded-xl p-4 border border-gray-200">
            <div className="text-xs text-gray-600">
              <span className="font-semibold text-gray-800">Akhri update:</span> Auto-aggregated from daily OPD stats.
            </div>
            <Button
              variant="secondary"
              size="sm"
              onClick={handleExportCSV}
              className="flex items-center gap-1.5"
            >
              <Download className="w-4 h-4" />
              Mahine ki report download (CSV)
            </Button>
          </div>
        </div>
      </LayoutShell>
    </RoleGuard>
  );
}
