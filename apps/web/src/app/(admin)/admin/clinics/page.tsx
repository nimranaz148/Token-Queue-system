"use client";

import * as React from "react";
import Link from "next/link";
import { FormShell } from "@/components/form/form-shell";
import { Column, DataGrid } from "@/components/grid/data-grid";
import { LayoutShell } from "@/components/layout/layout-shell";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { StatusBadge } from "@/components/ui/status-badge";

export interface ClinicItem {
  id: string;
  name: string;
  slug: string;
  status: "trial" | "active" | "suspended";
  doctors_count?: number;
  tokens_last_7d?: number;
  created_at: string;
}

interface ClinicListPageProps {
  initialClinics?: ClinicItem[];
  userRole?: string;
}

export default function ClinicsPage({
  initialClinics = [],
  userRole = "platform_admin",
}: ClinicListPageProps) {
  const [clinics, setClinics] = React.useState<ClinicItem[]>(initialClinics);
  const [search, setSearch] = React.useState("");

  // Status transition modal state (PRD §5.3: Reason required; audited)
  const [statusTarget, setStatusTarget] = React.useState<{
    id: string;
    name: string;
    currentStatus: "trial" | "active" | "suspended";
    nextStatus: "active" | "suspended";
  } | null>(null);
  const [statusReason, setStatusReason] = React.useState("");
  const [statusError, setStatusError] = React.useState<string | null>(null);
  const [isUpdatingStatus, setIsUpdatingStatus] = React.useState(false);

  const [isLoading, setIsLoading] = React.useState(false);
  const [fetchError, setFetchError] = React.useState<string | null>(null);

  const isAuthorized = userRole === "platform_admin";

  const filteredClinics = React.useMemo(() => {
    if (!search.trim()) return clinics;
    const q = search.toLowerCase();
    return clinics.filter(
      (c) => c.name.toLowerCase().includes(q) || c.slug.toLowerCase().includes(q)
    );
  }, [clinics, search]);

  const handleOpenStatusModal = (
    id: string,
    name: string,
    currentStatus: "trial" | "active" | "suspended"
  ) => {
    const nextStatus = currentStatus === "active" ? "suspended" : "active";
    setStatusTarget({ id, name, currentStatus, nextStatus });
    setStatusReason("");
    setStatusError(null);
  };

  const handleConfirmStatusChange = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!statusTarget) return;

    if (!statusReason.trim() || statusReason.trim().length < 3) {
      setStatusError("Wajah (reason) darj karna zaroori hai (min 3 characters).");
      return;
    }

    setIsUpdatingStatus(true);
    setStatusError(null);

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const token = typeof window !== "undefined" ? localStorage.getItem("token") || "" : "";

      const res = await fetch(`${apiUrl}/api/v1/admin/clinics/${statusTarget.id}/status`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          status: statusTarget.nextStatus,
          reason: statusReason.trim(),
        }),
      });

      if (!res.ok) {
        const data = await res.json();
        setStatusError(data.detail || "Status tabdeel karne mein masla pesh aya");
        return;
      }

      setClinics((prev) =>
        prev.map((c) =>
          c.id === statusTarget.id ? { ...c, status: statusTarget.nextStatus } : c
        )
      );
      setStatusTarget(null);
    } catch {
      setStatusError("Network error. Baraye meherbani dobara koshish karein.");
    } finally {
      setIsUpdatingStatus(false);
    }
  };

  const columns: Column<ClinicItem>[] = [
    {
      key: "name",
      header: "Clinic Name",
      render: (row) => (
        <div>
          <span className="font-medium text-fg">{row.name}</span>
          <span className="block text-2xs text-fg-muted">/c/{row.slug}</span>
        </div>
      ),
    },
    {
      key: "status",
      header: "Status",
      render: (row) => {
        const variant =
          row.status === "active"
            ? "success"
            : row.status === "suspended"
            ? "danger"
            : "warning";
        return (
          <StatusBadge variant={variant}>
            {row.status.toUpperCase()}
          </StatusBadge>
        );
      },
    },
    {
      key: "doctors_count",
      header: "Doctors",
      numeric: true,
      align: "right",
      render: (row) => (
        <span className="font-mono text-sm text-fg">
          {row.doctors_count ?? 0}
        </span>
      ),
    },
    {
      key: "tokens_last_7d",
      header: "Tokens 7d",
      numeric: true,
      align: "right",
      render: (row) => (
        <span className="font-mono text-sm text-fg">
          {row.tokens_last_7d ?? 0}
        </span>
      ),
    },
    {
      key: "created_at",
      header: "Onboarded",
      render: (row) => (
        <span className="text-xs text-fg-muted">
          {new Date(row.created_at).toLocaleDateString()}
        </span>
      ),
    },
    {
      key: "actions",
      header: "Action",
      align: "right",
      render: (row) => (
        <Button
          size="sm"
          variant={row.status === "active" ? "danger" : "secondary"}
          onClick={() => handleOpenStatusModal(row.id, row.name, row.status)}
        >
          {row.status === "active" ? "Suspend" : "Activate"}
        </Button>
      ),
    },
  ];

  const filtersContent = (
    <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
      <div className="w-full sm:w-72">
        <Input
          placeholder="Search by clinic name or slug..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>
      <Link href="/admin/clinics/new">
        <Button variant="primary">
          + New Clinic
        </Button>
      </Link>
    </div>
  );

  return (
    <LayoutShell
      clinicName="Platform Console"
      userName="Admin User"
      userRole="Platform Admin"
    >
      <div className="w-full max-w-7xl mx-auto py-6">
        {/* Status Change Dialog (PRD §5.3 F-014: Reason required; audited) */}
        {statusTarget && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
            <div className="w-full max-w-md rounded-xl border border-border bg-surface p-6 shadow-lg">
              <h3 className="text-base font-semibold text-fg">
                Clinic Status Change: {statusTarget.name}
              </h3>
              <p className="mt-1 text-xs text-fg-muted">
                Status ko <span className="font-medium text-fg uppercase">{statusTarget.nextStatus}</span> karne ki wajah darj karein. Yeh action immutable audit log mein mehfooz hoga.
              </p>

              <form onSubmit={handleConfirmStatusChange} className="mt-4 flex flex-col gap-3">
                <Input
                  label="Audited Reason (Wajah)"
                  placeholder="e.g. Subscription activated / Billing delinquency"
                  value={statusReason}
                  disabled={isUpdatingStatus}
                  error={statusError || undefined}
                  onChange={(e) => setStatusReason(e.target.value)}
                  required
                />

                <div className="flex justify-end gap-2 pt-2">
                  <Button
                    type="button"
                    variant="secondary"
                    disabled={isUpdatingStatus}
                    onClick={() => setStatusTarget(null)}
                  >
                    Cancel
                  </Button>
                  <Button
                    type="submit"
                    variant={statusTarget.nextStatus === "suspended" ? "danger" : "primary"}
                    disabled={isUpdatingStatus}
                  >
                    {isUpdatingStatus ? "Updating..." : `Confirm ${statusTarget.nextStatus}`}
                  </Button>
                </div>
              </form>
            </div>
          </div>
        )}

        <FormShell
          title="Clinics Directory"
          badge={<StatusBadge variant="info">F-014</StatusBadge>}
          description="View telemetry, doctors, 7-day token load, and manage clinic operational status."
          masterFields={filtersContent}
          detailGrid={
            <DataGrid<ClinicItem>
              data={filteredClinics}
              columns={columns}
              isLoading={isLoading}
              isError={!!fetchError}
              errorMessage={fetchError || undefined}
              isUnauthorized={!isAuthorized}
              emptyTitle="No clinics registered"
              emptyAction={
                <Link href="/admin/clinics/new">
                  <Button size="sm" variant="primary">
                    + Onboard First Clinic
                  </Button>
                </Link>
              }
              onRetry={() => {
                setFetchError(null);
                setIsLoading(true);
                setTimeout(() => setIsLoading(false), 500);
              }}
            />
          }
          summary={
            <div className="text-xs text-fg-muted flex gap-4">
              <span>
                Total Clinics: <strong className="text-fg">{clinics.length}</strong>
              </span>
              <span>
                Active:{" "}
                <strong className="text-success">
                  {clinics.filter((c) => c.status === "active").length}
                </strong>
              </span>
              <span>
                Trial:{" "}
                <strong className="text-warning">
                  {clinics.filter((c) => c.status === "trial").length}
                </strong>
              </span>
              <span>
                Suspended:{" "}
                <strong className="text-danger">
                  {clinics.filter((c) => c.status === "suspended").length}
                </strong>
              </span>
            </div>
          }
          auditPanel={
            <span>
              All clinic status transitions are permanently logged and verified per PRD §14.1.
            </span>
          }
        />
      </div>
    </LayoutShell>
  );
}
