"use client";

import * as React from "react";
import Link from "next/link";
import { LayoutShell } from "@/components/layout/layout-shell";
import { RoleGuard } from "@/components/auth/role-guard";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { StatusBadge } from "@/components/ui/status-badge";
import {
  AlertCircle,
  Calendar,
  CheckCircle,
  Clock,
  Edit2,
  FileText,
  Filter,
  Phone,
  Search,
  User,
  Users,
  X,
} from "lucide-react";

export interface PatientItem {
  id: string;
  name: string;
  phone: string;
  date_of_birth?: string | null;
  gender?: string | null;
  visit_count: number;
  last_visit_date?: string | null;
  notes?: string | null;
}

interface PatientsPageProps {
  initialPatients?: PatientItem[];
  userRole?: string;
}

export default function PatientSearchPage({
  initialPatients = [],
  userRole = "reception",
}: PatientsPageProps) {
  const [query, setQuery] = React.useState("");
  const [patients, setPatients] = React.useState<PatientItem[]>(initialPatients);
  const [isLoading, setIsLoading] = React.useState(false);
  const [searchError, setSearchError] = React.useState<string | null>(null);

  // Profile modal / drawer state
  const [selectedPatient, setSelectedPatient] = React.useState<PatientItem | null>(null);
  const [isEditing, setIsEditing] = React.useState(false);
  const [editName, setEditName] = React.useState("");
  const [editPhone, setEditPhone] = React.useState("");
  const [editDob, setEditDob] = React.useState("");
  const [editGender, setEditGender] = React.useState("");
  const [editNotes, setEditNotes] = React.useState("");
  const [isSaving, setIsSaving] = React.useState(false);
  const [profileError, setProfileError] = React.useState<string | null>(null);
  const [profileSuccess, setProfileSuccess] = React.useState<string | null>(null);

  const canEdit = userRole === "reception" || userRole === "owner";

  const handleSearch = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    const cleanQuery = query.trim();

    if (cleanQuery.length < 2) {
      setSearchError("Search karne ke liye kam az kam 2 characters likhein.");
      return;
    }

    setSearchError(null);
    setIsLoading(true);

    try {
      const res = await fetch(`/api/v1/patients?query=${encodeURIComponent(cleanQuery)}`);
      if (!res.ok) {
        throw new Error("Mareez daryaft karne mein masla pesh aya.");
      }
      const data = await res.json();
      setPatients(Array.isArray(data) ? data : data.items || []);
    } catch (err: any) {
      setSearchError(err.message || "Failed to search patients.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleOpenProfile = async (p: PatientItem) => {
    setSelectedPatient(p);
    setEditName(p.name);
    setEditPhone(p.phone);
    setEditDob(p.date_of_birth || "");
    setEditGender(p.gender || "");
    setEditNotes(p.notes || "");
    setIsEditing(false);
    setProfileError(null);
    setProfileSuccess(null);

    // Fetch fresh profile with notes
    try {
      const res = await fetch(`/api/v1/patients/${p.id}`);
      if (res.ok) {
        const full = await res.json();
        setSelectedPatient(full);
        setEditName(full.name);
        setEditPhone(full.phone);
        setEditDob(full.date_of_birth || "");
        setEditGender(full.gender || "");
        setEditNotes(full.notes || "");
      }
    } catch {
      // Non-blocking
    }
  };

  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedPatient) return;
    setProfileError(null);
    setProfileSuccess(null);

    if (!editName.trim() || editName.trim().length < 2 || editName.trim().length > 60) {
      setProfileError("Naam 2 se 60 characters ke darmiyan hona chahiye.");
      return;
    }
    if (!editPhone.trim() || editPhone.trim().length < 7) {
      setProfileError("Sahih phone number likhein (kam az kam 7 digits).");
      return;
    }
    if (editDob && new Date(editDob) > new Date()) {
      setProfileError("Pedaish ki tareekh (Date of Birth) maazi (past) ki honi chahiye.");
      return;
    }

    setIsSaving(true);
    try {
      const payload = {
        name: editName.trim(),
        phone: editPhone.trim(),
        date_of_birth: editDob || null,
        gender: editGender || null,
        notes: editNotes.trim() || null,
      };

      const res = await fetch(`/api/v1/patients/${selectedPatient.id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Profile update mein masla pesh aya.");
      }

      const updated: PatientItem = await res.json();
      setSelectedPatient(updated);
      setProfileSuccess("Profile kamyabi se update ho gaya.");
      setIsEditing(false);

      // Update in search list
      setPatients((prev) => prev.map((item) => (item.id === updated.id ? updated : item)));
    } catch (err: any) {
      setProfileError(err.message || "Failed to update profile.");
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <RoleGuard allowedRoles={["reception", "owner", "doctor"]}>
      <LayoutShell
        userRole={userRole}
        navItems={[
          { label: "Aaj ki List", href: "/tokens", icon: <Clock className="w-4 h-4" /> },
          { label: "Walk-in Entry", href: "/tokens/walk-in", icon: <CheckCircle className="w-4 h-4" /> },
          { label: "Patients", href: "/patients", icon: <Filter className="w-4 h-4" />, active: true },
        ]}
      >
        <div className="max-w-6xl mx-auto space-y-6">
          {/* Header */}
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-4 border-b border-border">
            <div>
              <div className="flex items-center gap-2">
                <Users className="w-6 h-6 text-accent" />
                <h1 className="text-2xl font-bold tracking-tight text-fg">Patients Directory</h1>
                <span className="text-xs font-semibold px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20 uppercase">
                  F-006
                </span>
              </div>
              <p className="text-sm text-fg-muted mt-1">
                Mareez daryaft karein (naam ya phone number ke zariye) aur profile dekhein/tabdeel karein
              </p>
            </div>
            <Link href="/tokens/walk-in">
              <Button variant="primary" size="sm">
                + Naya Walk-in Token
              </Button>
            </Link>
          </div>

          {/* Search Box */}
          <div className="bg-surface border border-border rounded-lg p-4">
            <form onSubmit={handleSearch} className="flex flex-col sm:flex-row gap-3">
              <div className="relative flex-1">
                <Search className="w-4 h-4 absolute left-3 top-3 text-fg-muted" />
                <Input
                  type="text"
                  placeholder="Mareez ka naam ya phone number likhein (kam az kam 2 characters)..."
                  value={query}
                  onChange={(e) => {
                    setQuery(e.target.value);
                    if (searchError) setSearchError(null);
                  }}
                  className="pl-9 h-10 w-full"
                  aria-label="Patient search input"
                />
              </div>
              <Button
                type="submit"
                variant="primary"
                disabled={isLoading}
                className="h-10 px-5"
                aria-label="Search button"
              >
                {isLoading ? "Daryaft ho raha hai..." : "Daryaft Karein"}
              </Button>
            </form>

            {searchError && (
              <div className="mt-3 p-3 rounded-md bg-destructive/10 border border-destructive/20 text-destructive text-xs flex items-center gap-2">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{searchError}</span>
              </div>
            )}
          </div>

          {/* Results Table */}
          <div className="bg-surface border border-border rounded-lg overflow-hidden">
            <div className="px-4 py-3 border-b border-border bg-surface-raised flex items-center justify-between">
              <span className="text-xs font-semibold text-fg-muted uppercase tracking-wider">
                Natayej (Results): {patients.length} Mareez
              </span>
            </div>

            {patients.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm" role="table">
                  <thead className="bg-surface-raised/50 text-xs font-semibold text-fg-muted uppercase border-b border-border">
                    <tr>
                      <th className="py-3 px-4">Mareez ka Naam</th>
                      <th className="py-3 px-4">Phone Number</th>
                      <th className="py-3 px-4">Umar / Dob</th>
                      <th className="py-3 px-4">Jins (Gender)</th>
                      <th className="py-3 px-4">Kul Visits</th>
                      <th className="py-3 px-4">Akhri Visit</th>
                      <th className="py-3 px-4 text-right">Amal (Action)</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border">
                    {patients.map((p) => (
                      <tr key={p.id} className="hover:bg-surface-hover/50 transition-colors">
                        <td className="py-3 px-4 font-medium text-fg">
                          <div className="flex items-center gap-2">
                            <User className="w-4 h-4 text-accent/80" />
                            <span>{p.name}</span>
                          </div>
                        </td>
                        <td className="py-3 px-4 font-mono text-xs text-fg-muted">
                          {p.phone}
                        </td>
                        <td className="py-3 px-4 text-xs text-fg-muted">
                          {p.date_of_birth || "—"}
                        </td>
                        <td className="py-3 px-4 text-xs capitalize text-fg-muted">
                          {p.gender || "—"}
                        </td>
                        <td className="py-3 px-4">
                          <StatusBadge variant="info">
                            {p.visit_count} {p.visit_count === 1 ? "visit" : "visits"}
                          </StatusBadge>
                        </td>
                        <td className="py-3 px-4 text-xs text-fg-muted">
                          {p.last_visit_date || "—"}
                        </td>
                        <td className="py-3 px-4 text-right">
                          <Button
                            variant="secondary"
                            size="sm"
                            onClick={() => handleOpenProfile(p)}
                            aria-label={`Open profile for ${p.name}`}
                          >
                            <FileText className="w-3.5 h-3.5 mr-1" />
                            Profile
                          </Button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="py-14 text-center text-fg-muted space-y-2">
                <Users className="w-10 h-10 mx-auto text-fg-muted/40" />
                <p className="text-sm font-medium text-fg">Koi mareez nahi mila</p>
                <p className="text-xs text-fg-muted">
                  Mareez talash karne ke liye upar search box mein naam ya phone number darj karein.
                </p>
              </div>
            )}
          </div>

          {/* Profile Modal / Drawer */}
          {selectedPatient && (
            <div
              className="fixed inset-0 z-50 bg-black/60 backdrop-blur-xs flex items-center justify-center p-4 animate-in fade-in duration-150"
              role="dialog"
              aria-modal="true"
              aria-label="Patient Profile Modal"
            >
              <div className="bg-surface border border-border rounded-lg shadow-xl max-w-xl w-full p-6 space-y-5">
                <div className="flex items-center justify-between border-b border-border pb-3">
                  <div className="flex items-center gap-2">
                    <User className="w-5 h-5 text-accent" />
                    <h2 className="text-lg font-bold text-fg">Mareez ka Profile</h2>
                  </div>
                  <button
                    onClick={() => setSelectedPatient(null)}
                    className="p-1 rounded text-fg-muted hover:text-fg hover:bg-surface-raised"
                    aria-label="Close modal"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>

                {profileError && (
                  <div className="p-3 rounded-md bg-destructive/10 border border-destructive/20 text-destructive text-xs flex items-center gap-2">
                    <AlertCircle className="w-4 h-4 shrink-0" />
                    <span>{profileError}</span>
                  </div>
                )}

                {profileSuccess && (
                  <div className="p-3 rounded-md bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs flex items-center gap-2">
                    <CheckCircle className="w-4 h-4 shrink-0" />
                    <span>{profileSuccess}</span>
                  </div>
                )}

                {!isEditing ? (
                  <div className="space-y-4">
                    {/* Read-only view */}
                    <div className="grid grid-cols-2 gap-4 bg-surface-raised p-4 rounded-md text-xs">
                      <div>
                        <span className="text-fg-muted block">Naam (Name):</span>
                        <span className="text-sm font-semibold text-fg">{selectedPatient.name}</span>
                      </div>
                      <div>
                        <span className="text-fg-muted block">Phone Number:</span>
                        <span className="text-sm font-mono text-fg">{selectedPatient.phone}</span>
                      </div>
                      <div>
                        <span className="text-fg-muted block">Date of Birth:</span>
                        <span className="text-fg font-medium">{selectedPatient.date_of_birth || "Nahi likhi"}</span>
                      </div>
                      <div>
                        <span className="text-fg-muted block">Jins (Gender):</span>
                        <span className="text-fg font-medium capitalize">{selectedPatient.gender || "Nahi likhi"}</span>
                      </div>
                      <div>
                        <span className="text-fg-muted block">Kul Visits (Total Encounters):</span>
                        <span className="text-fg font-bold">{selectedPatient.visit_count}</span>
                      </div>
                      <div>
                        <span className="text-fg-muted block">Akhri Visit (Last Visit):</span>
                        <span className="text-fg font-medium">{selectedPatient.last_visit_date || "—"}</span>
                      </div>
                    </div>

                    {/* Private Clinic Notes */}
                    <div className="space-y-1">
                      <span className="text-xs font-semibold text-fg-muted uppercase tracking-wider">
                        Private Clinic Notes (Staff Only):
                      </span>
                      <div className="p-3 rounded bg-surface-raised border border-border text-xs text-fg min-h-16 whitespace-pre-wrap">
                        {selectedPatient.notes || "Koi private notes darj nahi hain."}
                      </div>
                    </div>

                    <div className="flex justify-between items-center pt-3 border-t border-border">
                      <Button variant="secondary" onClick={() => setSelectedPatient(null)}>
                        Band Karein
                      </Button>
                      {canEdit && (
                        <Button
                          variant="primary"
                          onClick={() => setIsEditing(true)}
                          aria-label="Edit Profile"
                        >
                          <Edit2 className="w-4 h-4 mr-1.5" />
                          Profile Tabdeel Karein
                        </Button>
                      )}
                    </div>
                  </div>
                ) : (
                  <form onSubmit={handleSaveProfile} className="space-y-4">
                    {/* Edit Form */}
                    <div>
                      <label htmlFor="edit-name" className="block text-xs font-medium text-fg-muted mb-1">
                        Mareez ka Naam <span className="text-destructive">*</span>
                      </label>
                      <Input
                        id="edit-name"
                        value={editName}
                        onChange={(e) => setEditName(e.target.value)}
                        required
                        aria-label="Edit patient name"
                      />
                    </div>

                    <div>
                      <label htmlFor="edit-phone" className="block text-xs font-medium text-fg-muted mb-1">
                        Phone Number <span className="text-destructive">*</span>
                      </label>
                      <Input
                        id="edit-phone"
                        type="tel"
                        value={editPhone}
                        onChange={(e) => setEditPhone(e.target.value)}
                        required
                        aria-label="Edit phone"
                      />
                    </div>

                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <label htmlFor="edit-dob" className="block text-xs font-medium text-fg-muted mb-1">
                          Date of Birth
                        </label>
                        <Input
                          id="edit-dob"
                          type="date"
                          value={editDob}
                          onChange={(e) => setEditDob(e.target.value)}
                          aria-label="Edit date of birth"
                        />
                      </div>
                      <div>
                        <label htmlFor="edit-gender" className="block text-xs font-medium text-fg-muted mb-1">
                          Jins (Gender)
                        </label>
                        <select
                          id="edit-gender"
                          value={editGender}
                          onChange={(e) => setEditGender(e.target.value)}
                          className="w-full h-8.5 px-3 py-1 bg-surface-raised border border-border rounded-md text-sm text-fg focus:outline-none focus:ring-1 focus:ring-accent"
                          aria-label="Edit gender"
                        >
                          <option value="">Muntakhib karein</option>
                          <option value="male">Male (Mard)</option>
                          <option value="female">Female (Khatoon)</option>
                          <option value="other">Other</option>
                        </select>
                      </div>
                    </div>

                    <div>
                      <label htmlFor="edit-notes" className="block text-xs font-medium text-fg-muted mb-1">
                        Private Clinic Notes (Staff Only)
                      </label>
                      <textarea
                        id="edit-notes"
                        rows={3}
                        value={editNotes}
                        onChange={(e) => setEditNotes(e.target.value)}
                        placeholder="Clinic staff ke liye private notes (e.g. allergies, previous surgeries)..."
                        className="w-full p-2.5 bg-surface-raised border border-border rounded-md text-xs text-fg focus:outline-none focus:ring-1 focus:ring-accent resize-none"
                        aria-label="Edit notes"
                      />
                    </div>

                    <div className="flex justify-end gap-2 pt-3 border-t border-border">
                      <Button
                        type="button"
                        variant="secondary"
                        onClick={() => setIsEditing(false)}
                        disabled={isSaving}
                      >
                        Cancel
                      </Button>
                      <Button
                        type="submit"
                        variant="primary"
                        disabled={isSaving}
                        aria-label="Save Profile"
                      >
                        {isSaving ? "Mahfooz ho raha hai..." : "Mahfooz Karein (Save)"}
                      </Button>
                    </div>
                  </form>
                )}
              </div>
            </div>
          )}
        </div>
      </LayoutShell>
    </RoleGuard>
  );
}
