"use client";

import * as React from "react";
import { Column, DataGrid } from "@/components/grid/data-grid";
import { LayoutShell } from "@/components/layout/layout-shell";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { StatusBadge } from "@/components/ui/status-badge";

export type StaffRole = "owner" | "doctor" | "reception";

export interface StaffMemberItem {
  id: string;
  clinic_id: string;
  user_id: string;
  name: string;
  email: string;
  phone?: string | null;
  role: StaffRole;
  doctor_id?: string | null;
  doctor_name?: string | null;
  active: boolean;
  created_at: string;
  updated_at?: string;
}

export interface DoctorOption {
  id: string;
  name: string;
  specialty?: string | null;
}

interface StaffManagementPageProps {
  initialMembers?: StaffMemberItem[];
  initialDoctors?: DoctorOption[];
  userRole?: string;
}

export default function StaffManagementPage({
  initialMembers = [],
  initialDoctors = [],
  userRole = "owner",
}: StaffManagementPageProps) {
  const [members, setMembers] = React.useState<StaffMemberItem[]>(initialMembers);
  const [doctors, setDoctors] = React.useState<DoctorOption[]>(initialDoctors);
  const [search, setSearch] = React.useState("");

  // Invite Modal State
  const [isInviteOpen, setIsInviteOpen] = React.useState(false);
  const [inviteName, setInviteName] = React.useState("");
  const [inviteEmail, setInviteEmail] = React.useState("");
  const [invitePhone, setInvitePhone] = React.useState("");
  const [inviteRole, setInviteRole] = React.useState<StaffRole>("reception");
  const [inviteDoctorId, setInviteDoctorId] = React.useState("");
  const [inviteError, setInviteError] = React.useState<string | null>(null);
  const [isSubmittingInvite, setIsSubmittingInvite] = React.useState(false);

  // Status/Role Change Modal State
  const [roleModalTarget, setRoleModalTarget] = React.useState<StaffMemberItem | null>(null);
  const [editRole, setEditRole] = React.useState<StaffRole>("reception");
  const [editDoctorId, setEditDoctorId] = React.useState("");
  const [roleChangeError, setRoleChangeError] = React.useState<string | null>(null);
  const [isUpdatingMember, setIsUpdatingMember] = React.useState(false);

  const [isLoading, setIsLoading] = React.useState(false);
  const [fetchError, setFetchError] = React.useState<string | null>(null);

  const isAuthorized = userRole === "owner";

  const fetchMembers = React.useCallback(async () => {
    if (!isAuthorized) return;
    setIsLoading(true);
    setFetchError(null);
    try {
      const res = await fetch("/api/v1/members");
      if (!res.ok) {
        throw new Error(`Failed to fetch staff members (${res.status})`);
      }
      const data = await res.json();
      setMembers(data.items || []);
    } catch (err: unknown) {
      if (err instanceof Error) {
        setFetchError(err.message);
      } else {
        setFetchError("An error occurred while loading staff members.");
      }
    } finally {
      setIsLoading(false);
    }
  }, [isAuthorized]);

  React.useEffect(() => {
    if (initialMembers.length === 0 && isAuthorized) {
      void fetchMembers();
    }
  }, [initialMembers.length, isAuthorized, fetchMembers]);

  const filteredMembers = React.useMemo(() => {
    if (!search.trim()) return members;
    const q = search.toLowerCase();
    return members.filter(
      (m) =>
        m.name.toLowerCase().includes(q) ||
        m.email.toLowerCase().includes(q) ||
        m.role.toLowerCase().includes(q)
    );
  }, [members, search]);

  const handleOpenInvite = () => {
    setInviteName("");
    setInviteEmail("");
    setInvitePhone("");
    setInviteRole("reception");
    setInviteDoctorId("");
    setInviteError(null);
    setIsInviteOpen(true);
  };

  const handleInviteSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inviteName.trim() || !inviteEmail.trim()) {
      setInviteError("Name and email are required.");
      return;
    }

    if (inviteRole === "doctor" && !inviteDoctorId) {
      setInviteError("Please select a practicing doctor for this doctor account.");
      return;
    }

    setIsSubmittingInvite(true);
    setInviteError(null);

    try {
      const payload = {
        name: inviteName.trim(),
        email: inviteEmail.trim(),
        phone: invitePhone.trim() || null,
        role: inviteRole,
        doctor_id: inviteRole === "doctor" ? inviteDoctorId : null,
      };

      const res = await fetch("/api/v1/members", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        throw new Error(errorData.detail || `Failed to invite staff member (${res.status})`);
      }

      const createdMember: StaffMemberItem = await res.json();
      setMembers((prev) => [...prev, createdMember]);
      setIsInviteOpen(false);
    } catch (err: unknown) {
      if (err instanceof Error) {
        setInviteError(err.message);
      } else {
        setInviteError("Unable to invite staff member.");
      }
    } finally {
      setIsSubmittingInvite(false);
    }
  };

  const handleOpenRoleModal = (member: StaffMemberItem) => {
    setRoleModalTarget(member);
    setEditRole(member.role);
    setEditDoctorId(member.doctor_id || "");
    setRoleChangeError(null);
  };

  const handleUpdateRoleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!roleModalTarget) return;

    if (editRole === "doctor" && !editDoctorId) {
      setRoleChangeError("Please select a practicing doctor for this doctor account.");
      return;
    }

    setIsUpdatingMember(true);
    setRoleChangeError(null);

    try {
      const res = await fetch(`/api/v1/members/${roleModalTarget.id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          role: editRole,
          doctor_id: editRole === "doctor" ? editDoctorId : null,
        }),
      });

      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        throw new Error(errorData.detail || `Failed to update member role (${res.status})`);
      }

      const updated = await res.json();
      setMembers((prev) => prev.map((m) => (m.id === updated.id ? updated : m)));
      setRoleModalTarget(null);
    } catch (err: unknown) {
      if (err instanceof Error) {
        setRoleChangeError(err.message);
      } else {
        setRoleChangeError("Unable to update member role.");
      }
    } finally {
      setIsUpdatingMember(false);
    }
  };

  const handleToggleActive = async (member: StaffMemberItem) => {
    const nextActive = !member.active;
    const confirmMessage = nextActive
      ? `Re-activate login access for ${member.name}?`
      : `Deactivate ${member.name}? Their current sessions and login access will be revoked.`;

    if (!window.confirm(confirmMessage)) return;

    try {
      const res = await fetch(`/api/v1/members/${member.id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ active: nextActive }),
      });

      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        throw new Error(errorData.detail || "Failed to update member status");
      }

      const updated = await res.json();
      setMembers((prev) => prev.map((m) => (m.id === updated.id ? updated : m)));
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Error updating member status";
      alert(msg);
    }
  };

  if (!isAuthorized) {
    return (
      <LayoutShell userRole={userRole}>
        <div className="p-8 max-w-2xl mx-auto">
          <div className="bg-danger-subtle border border-danger-border rounded-lg p-6 text-center">
            <h1 className="text-xl font-semibold text-danger">403 — Unauthorized Access</h1>
            <p className="text-fg-muted mt-2">
              Staff management is restricted to clinic owners (PRD §14.2).
            </p>
          </div>
        </div>
      </LayoutShell>
    );
  }

  const columns: Column<StaffMemberItem>[] = [
    {
      key: "name",
      header: "Staff Member",
      render: (m) => (
        <div>
          <div className="font-medium text-fg">{m.name}</div>
          <div className="text-xs text-fg-muted">{m.email}</div>
        </div>
      ),
    },
    {
      key: "role",
      header: "Role",
      render: (m) => {
        const variant =
          m.role === "owner" ? "warning" : m.role === "doctor" ? "info" : "neutral";
        return (
          <StatusBadge variant={variant} className="capitalize font-mono text-xs">
            {m.role}
          </StatusBadge>
        );
      },
    },
    {
      key: "doctor_name",
      header: "Linked Doctor",
      render: (m) => (
        <span className="text-sm text-fg">
          {m.role === "doctor" ? m.doctor_name || "Doctor linked" : "—"}
        </span>
      ),
    },
    {
      key: "phone",
      header: "Contact Phone",
      render: (m) => <span className="text-sm text-fg-muted font-mono">{m.phone || "—"}</span>,
    },
    {
      key: "active",
      header: "Status",
      render: (m) => (
        <StatusBadge variant={m.active ? "success" : "danger"}>
          {m.active ? "Active" : "Deactivated"}
        </StatusBadge>
      ),
    },
    {
      key: "actions",
      header: "Actions",
      align: "right",
      render: (m) => (
        <div className="flex items-center justify-end gap-2">
          <Button
            size="sm"
            variant="ghost"
            onClick={() => handleOpenRoleModal(m)}
            aria-label={`Change role for ${m.name}`}
          >
            Role
          </Button>
          <Button
            size="sm"
            variant={m.active ? "danger" : "secondary"}
            onClick={() => void handleToggleActive(m)}
            aria-label={`${m.active ? "Deactivate" : "Activate"} ${m.name}`}
          >
            {m.active ? "Deactivate" : "Activate"}
          </Button>
        </div>
      ),
    },
  ];

  return (
    <LayoutShell userRole={userRole}>
      <div className="p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto space-y-6">
        {/* Page Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-fg">Staff Management</h1>
            <p className="text-sm text-fg-muted mt-1">
              Manage clinic members, role permissions, and practicing doctor assignments (PRD §5.3 F-015).
            </p>
          </div>
          <div>
            <Button onClick={handleOpenInvite} className="w-full sm:w-auto">
              + Add Staff
            </Button>
          </div>
        </div>

        {/* Search and Filters */}
        <div className="flex items-center gap-4">
          <div className="relative flex-1 max-w-sm">
            <label htmlFor="staff-search" className="sr-only">
              Search staff
            </label>
            <Input
              id="staff-search"
              placeholder="Search by name, email, or role..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full"
            />
          </div>
        </div>

        {/* Error banner */}
        {fetchError && (
          <div className="p-4 rounded-md bg-danger-subtle border border-danger-border text-sm text-danger flex items-center justify-between">
            <span>{fetchError}</span>
            <Button size="sm" variant="ghost" onClick={() => void fetchMembers()}>
              Retry
            </Button>
          </div>
        )}

        {/* Data Grid */}
        <DataGrid
          data={filteredMembers}
          columns={columns}
          isLoading={isLoading}
          emptyTitle="No staff members registered"
        />

        {/* Invite Staff Modal */}
        {isInviteOpen && (
          <div
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
            role="dialog"
            aria-modal="true"
            aria-labelledby="invite-modal-title"
          >
            <div className="bg-surface border border-border rounded-xl shadow-xl max-w-md w-full p-6 space-y-4">
              <div className="flex items-center justify-between">
                <h2 id="invite-modal-title" className="text-lg font-bold text-fg">
                  Invite Staff Member
                </h2>
                <button
                  type="button"
                  onClick={() => setIsInviteOpen(false)}
                  className="text-fg-muted hover:text-fg text-sm"
                  aria-label="Close dialog"
                >
                  ✕
                </button>
              </div>

              {inviteError && (
                <div className="p-3 text-sm bg-danger-subtle border border-danger-border text-danger rounded-md">
                  {inviteError}
                </div>
              )}

              <form onSubmit={handleInviteSubmit} className="space-y-4">
                <Input
                  id="staff-name"
                  label="Staff Name"
                  required
                  placeholder="e.g. Tariq Mehmood"
                  value={inviteName}
                  onChange={(e) => setInviteName(e.target.value)}
                />

                <div>
                  <Input
                    id="staff-email"
                    label="Email Address"
                    type="email"
                    required
                    placeholder="staff@clinic.com"
                    value={inviteEmail}
                    onChange={(e) => setInviteEmail(e.target.value)}
                  />
                  <p className="text-xs text-fg-muted mt-1">Used for email magic link sign-in.</p>
                </div>

                <Input
                  id="staff-phone"
                  label="Contact Phone"
                  type="tel"
                  placeholder="+92 300 1234567"
                  value={invitePhone}
                  onChange={(e) => setInvitePhone(e.target.value)}
                />

                <div>
                  <label htmlFor="staff-role" className="text-xs text-fg-muted font-medium block mb-1">
                    Staff Role <span className="text-danger ml-0.5">*</span>
                  </label>
                  <select
                    id="staff-role"
                    required
                    value={inviteRole}
                    onChange={(e) => setInviteRole(e.target.value as StaffRole)}
                    className="w-full h-8.5 px-3 rounded-md border border-border bg-surface text-fg text-sm focus:outline-hidden focus:border-border-focus focus:ring-1 focus:ring-border-focus"
                  >
                    <option value="reception">Reception</option>
                    <option value="doctor">Doctor</option>
                    <option value="owner">Owner</option>
                  </select>
                </div>

                {inviteRole === "doctor" && (
                  <div>
                    <label htmlFor="staff-doctor" className="text-xs text-fg-muted font-medium block mb-1">
                      Linked Doctor <span className="text-danger ml-0.5">*</span>
                    </label>
                    <select
                      id="staff-doctor"
                      required
                      value={inviteDoctorId}
                      onChange={(e) => setInviteDoctorId(e.target.value)}
                      className="w-full h-8.5 px-3 rounded-md border border-border bg-surface text-fg text-sm focus:outline-hidden focus:border-border-focus focus:ring-1 focus:ring-border-focus"
                    >
                      <option value="">Select a practicing doctor...</option>
                      {doctors.map((d) => (
                        <option key={d.id} value={d.id}>
                          {d.name} {d.specialty ? `(${d.specialty})` : ""}
                        </option>
                      ))}
                    </select>
                    {doctors.length === 0 && (
                      <p className="text-xs text-warning mt-1">
                        No doctors registered yet. You can create doctors in Doctor Management (F-016).
                      </p>
                    )}
                  </div>
                )}

                <div className="flex justify-end gap-3 pt-3 border-t border-border">
                  <Button
                    type="button"
                    variant="secondary"
                    onClick={() => setIsInviteOpen(false)}
                    disabled={isSubmittingInvite}
                  >
                    Cancel
                  </Button>
                  <Button type="submit" disabled={isSubmittingInvite}>
                    {isSubmittingInvite ? "Sending Invite..." : "Send Invite"}
                  </Button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Change Role Modal */}
        {roleModalTarget && (
          <div
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
            role="dialog"
            aria-modal="true"
            aria-labelledby="role-modal-title"
          >
            <div className="bg-surface border border-border rounded-xl shadow-xl max-w-md w-full p-6 space-y-4">
              <div className="flex items-center justify-between">
                <h2 id="role-modal-title" className="text-lg font-bold text-fg">
                  Change Role — {roleModalTarget.name}
                </h2>
                <button
                  type="button"
                  onClick={() => setRoleModalTarget(null)}
                  className="text-fg-muted hover:text-fg text-sm"
                  aria-label="Close dialog"
                >
                  ✕
                </button>
              </div>

              {roleChangeError && (
                <div className="p-3 text-sm bg-danger-subtle border border-danger-border text-danger rounded-md">
                  {roleChangeError}
                </div>
              )}

              <form onSubmit={handleUpdateRoleSubmit} className="space-y-4">
                <div>
                  <label htmlFor="edit-staff-role" className="block text-sm font-medium text-fg mb-1">
                    Staff Role *
                  </label>
                  <select
                    id="edit-staff-role"
                    required
                    value={editRole}
                    onChange={(e) => setEditRole(e.target.value as StaffRole)}
                    className="w-full h-9 px-3 rounded-md border border-border bg-surface text-fg text-sm focus:outline-hidden focus:ring-2 focus:ring-accent"
                  >
                    <option value="reception">Reception</option>
                    <option value="doctor">Doctor</option>
                    <option value="owner">Owner</option>
                  </select>
                </div>

                {editRole === "doctor" && (
                  <div>
                    <label htmlFor="edit-staff-doctor" className="block text-sm font-medium text-fg mb-1">
                      Linked Doctor *
                    </label>
                    <select
                      id="edit-staff-doctor"
                      required
                      value={editDoctorId}
                      onChange={(e) => setEditDoctorId(e.target.value)}
                      className="w-full h-9 px-3 rounded-md border border-border bg-surface text-fg text-sm focus:outline-hidden focus:ring-2 focus:ring-accent"
                    >
                      <option value="">Select a practicing doctor...</option>
                      {doctors.map((d) => (
                        <option key={d.id} value={d.id}>
                          {d.name} {d.specialty ? `(${d.specialty})` : ""}
                        </option>
                      ))}
                    </select>
                  </div>
                )}

                <div className="flex justify-end gap-3 pt-3 border-t border-border">
                  <Button
                    type="button"
                    variant="secondary"
                    onClick={() => setRoleModalTarget(null)}
                    disabled={isUpdatingMember}
                  >
                    Cancel
                  </Button>
                  <Button type="submit" disabled={isUpdatingMember}>
                    {isUpdatingMember ? "Saving..." : "Save Role"}
                  </Button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    </LayoutShell>
  );
}
