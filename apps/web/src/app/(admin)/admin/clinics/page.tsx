"use client";

import * as React from "react";
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
  const [newClinicName, setNewClinicName] = React.useState("");
  const [newClinicSlug, setNewClinicSlug] = React.useState("");
  const [isCreating, setIsCreating] = React.useState(false);
  const [formError, setFormError] = React.useState<string | null>(null);

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

  const handleCreateClinic = (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);

    if (newClinicName.length < 2) {
      setFormError("Clinic name must be at least 2 characters.");
      return;
    }
    if (!/^[a-z0-9-]+$/.test(newClinicSlug)) {
      setFormError("Slug must contain only lowercase letters, numbers, and hyphens.");
      return;
    }

    const created: ClinicItem = {
      id: typeof crypto !== "undefined" && crypto.randomUUID ? crypto.randomUUID() : String(Date.now()),
      name: newClinicName,
      slug: newClinicSlug,
      status: "trial",
      created_at: new Date().toISOString(),
    };

    setClinics((prev) => [created, ...prev]);
    setNewClinicName("");
    setNewClinicSlug("");
    setIsCreating(false);
  };

  const handleToggleStatus = (id: string, currentStatus: "trial" | "active" | "suspended") => {
    const nextStatus = currentStatus === "active" ? "suspended" : "active";
    setClinics((prev) =>
      prev.map((c) => (c.id === id ? { ...c, status: nextStatus } : c))
    );
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
          onClick={() => handleToggleStatus(row.id, row.status)}
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
      <Button
        variant="primary"
        onClick={() => setIsCreating((prev) => !prev)}
      >
        {isCreating ? "Cancel" : "+ New Clinic"}
      </Button>
    </div>
  );

  const creationFormContent = isCreating ? (
    <form
      onSubmit={handleCreateClinic}
      className="mb-4 rounded-lg border border-border bg-surface p-4 shadow-xs"
    >
      <h2 className="text-sm font-semibold text-fg mb-3">
        Onboard New Clinic
      </h2>
      <div className="grid gap-3 sm:grid-cols-2">
        <Input
          label="Clinic Name"
          placeholder="e.g. Al-Shifa Family Clinic"
          required
          value={newClinicName}
          onChange={(e) => setNewClinicName(e.target.value)}
        />
        <Input
          label="Booking Slug"
          placeholder="e.g. al-shifa-clinic"
          required
          value={newClinicSlug}
          onChange={(e) => setNewClinicSlug(e.target.value.toLowerCase())}
        />
      </div>
      {formError && (
        <p className="mt-2 text-xs text-danger font-medium">{formError}</p>
      )}
      <div className="mt-4 flex justify-end gap-2">
        <Button
          type="button"
          variant="secondary"
          onClick={() => setIsCreating(false)}
        >
          Cancel
        </Button>
        <Button type="submit" variant="primary">
          Save Clinic
        </Button>
      </div>
    </form>
  ) : null;

  return (
    <LayoutShell
      clinicName="Platform Console"
      userName="Admin User"
      userRole="Platform Admin"
    >
      <FormShell
        title="Platform Administration"
        description="F-013 New Clinic & F-014 Clinics Management"
        badge={
          <span className="inline-block px-2 py-0.5 rounded text-2xs bg-emerald-500/10 text-emerald-600 font-medium">
            Live Sync
          </span>
        }
        masterFields={filtersContent}
        detailGrid={
          <div>
            {creationFormContent}
            <DataGrid
              columns={columns}
              data={filteredClinics}
              isLoading={isLoading}
              isUnauthorized={!isAuthorized}
              isError={Boolean(fetchError)}
              errorMessage={fetchError ?? undefined}
              onRetry={() => {
                setFetchError(null);
                setIsLoading(true);
                setTimeout(() => setIsLoading(false), 200);
              }}
              emptyTitle="No clinics registered"
              emptyAction={
                <Button
                  size="sm"
                  variant="primary"
                  onClick={() => setIsCreating(true)}
                >
                  Create First Clinic
                </Button>
              }
            />
          </div>
        }
        auditPanel={
          <div className="flex items-center justify-between text-xs text-fg-muted">
            <span>Audit: Monitored platform master register</span>
            <span>Total Clinics: {filteredClinics.length}</span>
          </div>
        }
      />
    </LayoutShell>
  );
}
