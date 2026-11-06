"use client";

import * as React from "react";
import { Column, DataGrid } from "@/components/grid/data-grid";
import { LayoutShell } from "@/components/layout/layout-shell";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { StatusBadge } from "@/components/ui/status-badge";
import { Settings, Stethoscope, Tv, Users } from "lucide-react";

const WEEKDAYS = [
  "Monday",
  "Tuesday",
  "Wednesday",
  "Thursday",
  "Friday",
  "Saturday",
  "Sunday",
];

export interface DoctorScheduleItem {
  id?: string;
  weekday: number;
  start_time: string;
  end_time: string;
}

export interface DoctorItem {
  id: string;
  clinic_id: string;
  name: string;
  specialty?: string | null;
  daily_online_limit?: number | null;
  consult_minutes?: number | null;
  active: boolean;
  schedules: DoctorScheduleItem[];
  created_at: string;
  updated_at?: string;
}

interface DoctorManagementPageProps {
  initialDoctors?: DoctorItem[];
  userRole?: string;
}

export default function DoctorManagementPage({
  initialDoctors = [],
  userRole = "owner",
}: DoctorManagementPageProps) {
  const [doctors, setDoctors] = React.useState<DoctorItem[]>(initialDoctors);
  const [search, setSearch] = React.useState("");

  // Loading and error states
  const [isLoading, setIsLoading] = React.useState(false);
  const [fetchError, setFetchError] = React.useState<string | null>(null);

  // Add Doctor Modal
  const [isAddOpen, setIsAddOpen] = React.useState(false);
  const [name, setName] = React.useState("");
  const [specialty, setSpecialty] = React.useState("");
  const [dailyLimit, setDailyLimit] = React.useState<string>("");
  const [consultMinutes, setConsultMinutes] = React.useState<string>("10");
  const [isActive, setIsActive] = React.useState(true);
  const [formError, setFormError] = React.useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = React.useState(false);

  // Edit Doctor Modal
  const [editingDoctor, setEditingDoctor] = React.useState<DoctorItem | null>(null);
  const [editName, setEditName] = React.useState("");
  const [editSpecialty, setEditSpecialty] = React.useState("");
  const [editDailyLimit, setEditDailyLimit] = React.useState<string>("");
  const [editConsultMinutes, setEditConsultMinutes] = React.useState<string>("10");
  const [editIsActive, setEditIsActive] = React.useState(true);
  const [editError, setEditError] = React.useState<string | null>(null);
  const [isUpdating, setIsUpdating] = React.useState(false);

  // Schedule Modal
  const [scheduleDoctor, setScheduleDoctor] = React.useState<DoctorItem | null>(null);
  const [scheduleList, setScheduleList] = React.useState<DoctorScheduleItem[]>([]);
  const [scheduleError, setScheduleError] = React.useState<string | null>(null);
  const [isSavingSchedule, setIsSavingSchedule] = React.useState(false);

  // Delete Confirm Dialog
  const [deletingDoctor, setDeletingDoctor] = React.useState<DoctorItem | null>(null);
  const [isDeleting, setIsDeleting] = React.useState(false);

  const isAuthorized = userRole === "owner";

  const fetchDoctors = React.useCallback(async () => {
    if (!isAuthorized) return;
    setIsLoading(true);
    setFetchError(null);
    try {
      const res = await fetch("/api/v1/doctors");
      if (!res.ok) {
        throw new Error(`Failed to fetch doctors (${res.status})`);
      }
      const data = await res.json();
      setDoctors(data.items || []);
    } catch (err: unknown) {
      if (err instanceof Error) {
        setFetchError(err.message);
      } else {
        setFetchError("An error occurred while loading doctors.");
      }
    } finally {
      setIsLoading(false);
    }
  }, [isAuthorized]);

  React.useEffect(() => {
    if (initialDoctors.length === 0 && isAuthorized) {
      void fetchDoctors();
    }
  }, [initialDoctors.length, isAuthorized, fetchDoctors]);

  const filteredDoctors = React.useMemo(() => {
    if (!search.trim()) return doctors;
    const q = search.toLowerCase();
    return doctors.filter(
      (d) =>
        d.name.toLowerCase().includes(q) ||
        (d.specialty && d.specialty.toLowerCase().includes(q))
    );
  }, [doctors, search]);

  const handleOpenAdd = () => {
    setName("");
    setSpecialty("");
    setDailyLimit("");
    setConsultMinutes("10");
    setIsActive(true);
    setFormError(null);
    setIsAddOpen(true);
  };

  const handleCreateDoctor = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) {
      setFormError("Doctor name is required");
      return;
    }
    setFormError(null);
    setIsSubmitting(true);
    try {
      const payload = {
        name: name.trim(),
        specialty: specialty.trim() || null,
        daily_online_limit: dailyLimit ? parseInt(dailyLimit, 10) : null,
        consult_minutes: consultMinutes ? parseInt(consultMinutes, 10) : 10,
        active: isActive,
        schedules: [],
      };

      const res = await fetch("/api/v1/doctors", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || `Failed to create doctor (${res.status})`);
      }

      const created: DoctorItem = await res.json();
      setDoctors((prev) => [created, ...prev]);
      setIsAddOpen(false);
    } catch (err: unknown) {
      setFormError(err instanceof Error ? err.message : "Failed to create doctor");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleOpenEdit = (doc: DoctorItem) => {
    setEditingDoctor(doc);
    setEditName(doc.name);
    setEditSpecialty(doc.specialty || "");
    setEditDailyLimit(doc.daily_online_limit ? String(doc.daily_online_limit) : "");
    setEditConsultMinutes(doc.consult_minutes ? String(doc.consult_minutes) : "10");
    setEditIsActive(doc.active);
    setEditError(null);
  };

  const handleUpdateDoctor = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingDoctor) return;
    if (!editName.trim()) {
      setEditError("Doctor name cannot be empty");
      return;
    }
    setEditError(null);
    setIsUpdating(true);
    try {
      const payload = {
        name: editName.trim(),
        specialty: editSpecialty.trim() || null,
        daily_online_limit: editDailyLimit ? parseInt(editDailyLimit, 10) : null,
        consult_minutes: editConsultMinutes ? parseInt(editConsultMinutes, 10) : 10,
        active: editIsActive,
      };

      const res = await fetch(`/api/v1/doctors/${editingDoctor.id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || "Failed to update doctor");
      }

      const updated: DoctorItem = await res.json();
      setDoctors((prev) => prev.map((d) => (d.id === updated.id ? updated : d)));
      setEditingDoctor(null);
    } catch (err: unknown) {
      setEditError(err instanceof Error ? err.message : "Failed to update doctor");
    } finally {
      setIsUpdating(false);
    }
  };

  const handleOpenSchedule = (doc: DoctorItem) => {
    setScheduleDoctor(doc);
    setScheduleList(doc.schedules || []);
    setScheduleError(null);
  };

  const handleAddScheduleSlot = () => {
    setScheduleList((prev) => [
      ...prev,
      { weekday: 0, start_time: "09:00", end_time: "13:00" },
    ]);
  };

  const handleRemoveScheduleSlot = (index: number) => {
    setScheduleList((prev) => prev.filter((_, i) => i !== index));
  };

  const handleSaveSchedule = async () => {
    if (!scheduleDoctor) return;
    setScheduleError(null);

    // Validate times
    for (const s of scheduleList) {
      if (s.end_time <= s.start_time) {
        setScheduleError("End time must be after start time for all OPD slots");
        return;
      }
    }

    setIsSavingSchedule(true);
    try {
      const res = await fetch(`/api/v1/doctors/${scheduleDoctor.id}/schedule`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(scheduleList),
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || "Failed to save schedule");
      }

      const updatedSchedules: DoctorScheduleItem[] = await res.json();
      setDoctors((prev) =>
        prev.map((d) =>
          d.id === scheduleDoctor.id ? { ...d, schedules: updatedSchedules } : d
        )
      );
      setScheduleDoctor(null);
    } catch (err: unknown) {
      setScheduleError(err instanceof Error ? err.message : "Failed to save schedule");
    } finally {
      setIsSavingSchedule(false);
    }
  };

  const handleDeleteDoctor = async () => {
    if (!deletingDoctor) return;
    setIsDeleting(true);
    try {
      const res = await fetch(`/api/v1/doctors/${deletingDoctor.id}`, {
        method: "DELETE",
      });

      if (!res.ok && res.status !== 204) {
        throw new Error("Failed to delete doctor");
      }

      setDoctors((prev) => prev.filter((d) => d.id !== deletingDoctor.id));
      setDeletingDoctor(null);
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Failed to delete doctor");
    } finally {
      setIsDeleting(false);
    }
  };

  const columns: Column<DoctorItem>[] = [
    {
      key: "name",
      header: "Doctor Name",
      render: (row) => (
        <div>
          <div className="font-medium text-fg-default">{row.name}</div>
          <div className="text-xs text-fg-muted">{row.specialty || "General Physician"}</div>
        </div>
      ),
    },
    {
      key: "status",
      header: "Status",
      render: (row) => (
        <StatusBadge variant={row.active ? "success" : "neutral"}>
          {row.active ? "Active" : "Inactive"}
        </StatusBadge>
      ),
    },
    {
      key: "limits",
      header: "Consult / Online Limit",
      render: (row) => (
        <div className="text-xs text-fg-default">
          <span>{row.consult_minutes ?? 10} min/consult</span>
          <span className="mx-1 text-fg-muted">•</span>
          <span>{row.daily_online_limit ? `${row.daily_online_limit} tokens/day` : "Unlimited"}</span>
        </div>
      ),
    },
    {
      key: "schedule",
      header: "Weekly OPD Schedule",
      render: (row) => {
        if (!row.schedules || row.schedules.length === 0) {
          return <span className="text-xs text-fg-muted">No schedule set</span>;
        }
        return (
          <div className="text-xs text-fg-default flex flex-wrap gap-1">
            {row.schedules.slice(0, 3).map((s, idx) => (
              <span
                key={idx}
                className="bg-surface-sunken px-1.5 py-0.5 rounded text-[11px] font-mono"
              >
                {WEEKDAYS[s.weekday]?.slice(0, 3)}: {s.start_time}-{s.end_time}
              </span>
            ))}
            {row.schedules.length > 3 && (
              <span className="text-[11px] text-fg-muted">
                +{row.schedules.length - 3} more
              </span>
            )}
          </div>
        );
      },
    },
    {
      key: "actions",
      header: "Actions",
      align: "right",
      render: (row) => (
        <div className="flex justify-end gap-2">
          <Button
            size="sm"
            variant="secondary"
            onClick={() => handleOpenSchedule(row)}
            aria-label={`Manage schedule for ${row.name}`}
          >
            OPD Timings
          </Button>
          <Button
            size="sm"
            variant="secondary"
            onClick={() => handleOpenEdit(row)}
            aria-label={`Edit ${row.name}`}
          >
            Edit
          </Button>
          <Button
            size="sm"
            variant="ghost"
            className="text-red-600 hover:text-red-700 hover:bg-red-50"
            onClick={() => setDeletingDoctor(row)}
            aria-label={`Delete ${row.name}`}
          >
            Delete
          </Button>
        </div>
      ),
    },
  ];

  return (
    <LayoutShell
      userRole={userRole}
      navItems={[
        { label: "Clinic Settings", href: "/settings", icon: <Settings className="w-4 h-4" /> },
        {
          label: "Doctors",
          href: "/settings/doctors",
          icon: <Stethoscope className="w-4 h-4" />,
          active: true,
        },
        { label: "Staff", href: "/settings/staff", icon: <Users className="w-4 h-4" /> },
        { label: "TV Screens", href: "/settings/tv", icon: <Tv className="w-4 h-4" /> },
      ]}
    >
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-fg-default">
              Doctor Management
            </h1>
            <p className="text-sm text-fg-muted">
              Configure doctor profiles, OPD schedules, consult times, and online booking limits (F-016).
            </p>
          </div>
          {isAuthorized && (
            <Button onClick={handleOpenAdd} className="w-full sm:w-auto">
              Add Doctor
            </Button>
          )}
        </div>

        {/* Search */}
        <div className="flex items-center gap-4">
          <div className="w-full max-w-sm">
            <Input
              placeholder="Search by name or specialty..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              aria-label="Search doctors"
            />
          </div>
        </div>

        {/* DataGrid */}
        <DataGrid
          columns={columns}
          data={filteredDoctors}
          isLoading={isLoading}
          isError={Boolean(fetchError)}
          isUnauthorized={!isAuthorized}
          errorMessage={fetchError || undefined}
          onRetry={fetchDoctors}
          emptyTitle="No doctors found"
          emptyAction={
            isAuthorized ? (
              <Button onClick={handleOpenAdd} size="sm">
                Add Doctor
              </Button>
            ) : undefined
          }
        />

        {/* Add Doctor Modal */}
        {isAddOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
            <div className="w-full max-w-md bg-white rounded-lg shadow-lg border border-border p-6 space-y-4">
              <h2 className="text-lg font-semibold text-fg-default">Add New Doctor</h2>

              {formError && (
                <div className="p-3 bg-red-50 border border-red-200 rounded text-sm text-red-600">
                  {formError}
                </div>
              )}

              <form onSubmit={handleCreateDoctor} className="space-y-4">
                <div>
                  <label className="block text-xs font-medium text-fg-muted mb-1">
                    Doctor Name *
                  </label>
                  <Input
                    required
                    placeholder="e.g. Dr. Ayesha Ahmed"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-fg-muted mb-1">
                    Specialty
                  </label>
                  <Input
                    placeholder="e.g. Pediatrician, General Physician"
                    value={specialty}
                    onChange={(e) => setSpecialty(e.target.value)}
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-medium text-fg-muted mb-1">
                      Avg Consult (mins)
                    </label>
                    <Input
                      type="number"
                      min={1}
                      max={120}
                      value={consultMinutes}
                      onChange={(e) => setConsultMinutes(e.target.value)}
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-fg-muted mb-1">
                      Daily Online Limit
                    </label>
                    <Input
                      type="number"
                      min={1}
                      max={500}
                      placeholder="Optional"
                      value={dailyLimit}
                      onChange={(e) => setDailyLimit(e.target.value)}
                    />
                  </div>
                </div>

                <div className="flex items-center gap-2 pt-1">
                  <input
                    type="checkbox"
                    id="doctor-active"
                    checked={isActive}
                    onChange={(e) => setIsActive(e.target.checked)}
                    className="h-4 w-4 rounded border-border text-primary focus:ring-primary"
                  />
                  <label htmlFor="doctor-active" className="text-sm text-fg-default">
                    Active for OPD queue bookings
                  </label>
                </div>

                <div className="flex justify-end gap-2 pt-2">
                  <Button
                    type="button"
                    variant="secondary"
                    onClick={() => setIsAddOpen(false)}
                    disabled={isSubmitting}
                  >
                    Cancel
                  </Button>
                  <Button type="submit" disabled={isSubmitting}>
                    {isSubmitting ? "Creating..." : "Save Doctor"}
                  </Button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Edit Doctor Modal */}
        {editingDoctor && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
            <div className="w-full max-w-md bg-white rounded-lg shadow-lg border border-border p-6 space-y-4">
              <h2 className="text-lg font-semibold text-fg-default">Edit Doctor Profile</h2>

              {editError && (
                <div className="p-3 bg-red-50 border border-red-200 rounded text-sm text-red-600">
                  {editError}
                </div>
              )}

              <form onSubmit={handleUpdateDoctor} className="space-y-4">
                <div>
                  <label className="block text-xs font-medium text-fg-muted mb-1">
                    Doctor Name *
                  </label>
                  <Input
                    required
                    value={editName}
                    onChange={(e) => setEditName(e.target.value)}
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-fg-muted mb-1">
                    Specialty
                  </label>
                  <Input
                    value={editSpecialty}
                    onChange={(e) => setEditSpecialty(e.target.value)}
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-medium text-fg-muted mb-1">
                      Avg Consult (mins)
                    </label>
                    <Input
                      type="number"
                      min={1}
                      max={120}
                      value={editConsultMinutes}
                      onChange={(e) => setEditConsultMinutes(e.target.value)}
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-fg-muted mb-1">
                      Daily Online Limit
                    </label>
                    <Input
                      type="number"
                      min={1}
                      max={500}
                      placeholder="Optional"
                      value={editDailyLimit}
                      onChange={(e) => setEditDailyLimit(e.target.value)}
                    />
                  </div>
                </div>

                <div className="flex items-center gap-2 pt-1">
                  <input
                    type="checkbox"
                    id="edit-doctor-active"
                    checked={editIsActive}
                    onChange={(e) => setEditIsActive(e.target.checked)}
                    className="h-4 w-4 rounded border-border text-primary focus:ring-primary"
                  />
                  <label htmlFor="edit-doctor-active" className="text-sm text-fg-default">
                    Active for OPD queue bookings
                  </label>
                </div>

                <div className="flex justify-end gap-2 pt-2">
                  <Button
                    type="button"
                    variant="secondary"
                    onClick={() => setEditingDoctor(null)}
                    disabled={isUpdating}
                  >
                    Cancel
                  </Button>
                  <Button type="submit" disabled={isUpdating}>
                    {isUpdating ? "Saving..." : "Save Changes"}
                  </Button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Schedule Modal */}
        {scheduleDoctor && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
            <div className="w-full max-w-lg bg-white rounded-lg shadow-lg border border-border p-6 space-y-4">
              <div className="flex justify-between items-center">
                <h2 className="text-lg font-semibold text-fg-default">
                  OPD Schedule — {scheduleDoctor.name}
                </h2>
                <Button size="sm" variant="secondary" onClick={handleAddScheduleSlot}>
                  + Add Slot
                </Button>
              </div>

              {scheduleError && (
                <div className="p-3 bg-red-50 border border-red-200 rounded text-sm text-red-600">
                  {scheduleError}
                </div>
              )}

              <div className="space-y-3 max-h-80 overflow-y-auto">
                {scheduleList.length === 0 ? (
                  <p className="text-sm text-fg-muted text-center py-4">
                    No OPD timings configured. Click "+ Add Slot" above to set regular weekly hours.
                  </p>
                ) : (
                  scheduleList.map((slot, idx) => (
                    <div
                      key={idx}
                      className="flex items-center gap-2 p-2.5 bg-surface-sunken rounded border border-border"
                    >
                      <select
                        value={slot.weekday}
                        onChange={(e) => {
                          const val = parseInt(e.target.value, 10);
                          setScheduleList((prev) =>
                            prev.map((s, i) => (i === idx ? { ...s, weekday: val } : s))
                          );
                        }}
                        className="text-xs border border-border rounded px-2 py-1.5 bg-white text-fg-default"
                        aria-label={`Weekday for slot ${idx + 1}`}
                      >
                        {WEEKDAYS.map((day, dIdx) => (
                          <option key={dIdx} value={dIdx}>
                            {day}
                          </option>
                        ))}
                      </select>

                      <input
                        type="time"
                        value={slot.start_time}
                        onChange={(e) => {
                          const val = e.target.value;
                          setScheduleList((prev) =>
                            prev.map((s, i) => (i === idx ? { ...s, start_time: val } : s))
                          );
                        }}
                        className="text-xs border border-border rounded px-2 py-1 bg-white text-fg-default"
                        aria-label={`Start time for slot ${idx + 1}`}
                      />
                      <span className="text-xs text-fg-muted">to</span>
                      <input
                        type="time"
                        value={slot.end_time}
                        onChange={(e) => {
                          const val = e.target.value;
                          setScheduleList((prev) =>
                            prev.map((s, i) => (i === idx ? { ...s, end_time: val } : s))
                          );
                        }}
                        className="text-xs border border-border rounded px-2 py-1 bg-white text-fg-default"
                        aria-label={`End time for slot ${idx + 1}`}
                      />

                      <Button
                        type="button"
                        size="sm"
                        variant="ghost"
                        className="text-red-600 hover:text-red-700 px-2 ml-auto"
                        onClick={() => handleRemoveScheduleSlot(idx)}
                        aria-label={`Remove slot ${idx + 1}`}
                      >
                        ✕
                      </Button>
                    </div>
                  ))
                )}
              </div>

              <div className="flex justify-end gap-2 pt-2 border-t border-border">
                <Button
                  type="button"
                  variant="secondary"
                  onClick={() => setScheduleDoctor(null)}
                  disabled={isSavingSchedule}
                >
                  Cancel
                </Button>
                <Button
                  type="button"
                  onClick={handleSaveSchedule}
                  disabled={isSavingSchedule}
                >
                  {isSavingSchedule ? "Saving..." : "Save Schedule"}
                </Button>
              </div>
            </div>
          </div>
        )}

        {/* Delete Confirmation Dialog */}
        {deletingDoctor && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
            <div className="w-full max-w-sm bg-white rounded-lg shadow-lg border border-border p-6 space-y-4">
              <h2 className="text-lg font-semibold text-fg-default">Deactivate Doctor?</h2>
              <p className="text-sm text-fg-muted">
                Are you sure you want to deactivate{" "}
                <span className="font-semibold text-fg-default">
                  {deletingDoctor.name}
                </span>
                ? They will no longer accept queue bookings or appear in public doctor lists.
              </p>
              <div className="flex justify-end gap-2 pt-2">
                <Button
                  variant="secondary"
                  onClick={() => setDeletingDoctor(null)}
                  disabled={isDeleting}
                >
                  Cancel
                </Button>
                <Button
                  variant="danger"
                  className="bg-red-600 hover:bg-red-700 text-white"
                  onClick={handleDeleteDoctor}
                  disabled={isDeleting}
                >
                  {isDeleting ? "Deactivating..." : "Deactivate"}
                </Button>
              </div>
            </div>
          </div>
        )}
      </div>
    </LayoutShell>
  );
}
