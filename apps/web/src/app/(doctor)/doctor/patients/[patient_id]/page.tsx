"use client";

import * as React from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { LayoutShell } from "@/components/layout/layout-shell";
import { RoleGuard } from "@/components/auth/role-guard";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { StatusBadge } from "@/components/ui/status-badge";
import {
  AlertCircle,
  ArrowLeft,
  Calendar,
  CheckCircle,
  Clock,
  Eye,
  EyeOff,
  FileText,
  History,
  Lock,
  Pill,
  PlusCircle,
  Save,
  Share2,
  Stethoscope,
  User,
} from "lucide-react";

export interface VisitHistoryItem {
  id: string;
  doctor_id: string;
  doctor_name: string;
  complaint?: string | null;
  notes?: string | null;
  medicines_advice?: string | null;
  share_with_patient: boolean;
  token_id?: string | null;
  token_number?: number | null;
  created_at: string;
}

export interface PatientHistoryData {
  patient_id: string;
  patient_name: string;
  phone: string;
  date_of_birth?: string | null;
  gender?: string | null;
  notes?: string | null;
  share_advice_clinic_setting: boolean;
  visits: VisitHistoryItem[];
}

interface PatientHistoryPageProps {
  initialData?: PatientHistoryData;
  userRole?: string;
}

export default function PatientHistoryPage({
  initialData,
  userRole = "doctor",
}: PatientHistoryPageProps) {
  const params = useParams();
  const patientId = (params?.patient_id as string) || initialData?.patient_id;

  const [data, setData] = React.useState<PatientHistoryData | null>(initialData || null);
  const [isLoading, setIsLoading] = React.useState(!initialData);
  const [errorMessage, setErrorMessage] = React.useState<string | null>(null);
  const [successMessage, setSuccessMessage] = React.useState<string | null>(null);

  // New Visit Note Form state
  const [complaint, setComplaint] = React.useState("");
  const [notes, setNotes] = React.useState("");
  const [medicinesAdvice, setMedicinesAdvice] = React.useState("");
  const [shareWithPatient, setShareWithPatient] = React.useState(true);
  const [isSaving, setIsSaving] = React.useState(false);

  const fetchHistory = React.useCallback(async () => {
    if (!patientId) return;
    try {
      const res = await fetch(`/api/v1/visits/patient/${patientId}`);
      if (res.ok) {
        const result: PatientHistoryData = await res.json();
        setData(result);
      } else {
        throw new Error("Mareez ki history load karne mein masla pesh aya.");
      }
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to load patient history.");
    } finally {
      setIsLoading(false);
    }
  }, [patientId]);

  React.useEffect(() => {
    if (!initialData && patientId) {
      fetchHistory();
    }
  }, [initialData, patientId, fetchHistory]);

  const handleSaveVisitNote = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);
    setSuccessMessage(null);

    if (complaint.length > 500) {
      setErrorMessage("Complaint 500 characters se ziyada nahi ho sakti.");
      return;
    }
    if (notes.length > 4000) {
      setErrorMessage("Private notes 4000 characters se ziyada nahi ho sakty.");
      return;
    }
    if (medicinesAdvice.length > 2000) {
      setErrorMessage("Dawa / advice 2000 characters se ziyada nahi ho sakti.");
      return;
    }

    setIsSaving(true);
    try {
      const payload = {
        patient_id: patientId,
        complaint: complaint.trim() || null,
        notes: notes.trim() || null,
        medicines_advice: medicinesAdvice.trim() || null,
        share_with_patient: shareWithPatient,
      };

      const res = await fetch("/api/v1/visits", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Visit note save karne mein masla pesh aya.");
      }

      setSuccessMessage("Visit note kamyabi se mahfooz ho gaya.");
      setComplaint("");
      setNotes("");
      setMedicinesAdvice("");
      await fetchHistory();
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to save visit note.");
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <RoleGuard allowedRoles={["doctor", "owner"]}>
      <LayoutShell
        userRole={userRole}
        navItems={[
          { label: "Doctor Panel", href: "/doctor", icon: <Stethoscope className="w-4 h-4" /> },
          { label: "Patient History", href: "/doctor/history", icon: <History className="w-4 h-4" />, active: true },
          { label: "Aaj ki List", href: "/tokens", icon: <Clock className="w-4 h-4" /> },
        ]}
      >
        <div className="max-w-5xl mx-auto space-y-6">
          {/* Header */}
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-4 border-b border-border">
            <div className="flex items-center gap-3">
              <Link
                href="/doctor"
                className="text-fg-muted hover:text-fg p-1 rounded-md transition-colors"
                aria-label="Back to Doctor Panel"
              >
                <ArrowLeft className="w-5 h-5" />
              </Link>
              <div>
                <div className="flex items-center gap-2">
                  <h1 className="text-2xl font-bold tracking-tight text-fg">
                    Patient History & Visit Note
                  </h1>
                  <span className="text-xs font-semibold px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 uppercase">
                    F-008
                  </span>
                </div>
                <p className="text-sm text-fg-muted mt-0.5">
                  Mareez ka pichla record dekhein aur naya visit note / nuskha darj karein
                </p>
              </div>
            </div>

            <Link href="/doctor">
              <Button variant="secondary" size="sm">
                Doctor Panel
              </Button>
            </Link>
          </div>

          {/* Feedback alerts */}
          {errorMessage && (
            <div className="p-3.5 rounded-md bg-destructive/10 border border-destructive/20 text-destructive text-sm flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{errorMessage}</span>
            </div>
          )}

          {successMessage && (
            <div className="p-3.5 rounded-md bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-sm flex items-center gap-2">
              <CheckCircle className="w-4 h-4 shrink-0" />
              <span>{successMessage}</span>
            </div>
          )}

          {/* Patient Profile Card */}
          {data && (
            <div className="bg-surface border border-border rounded-lg p-5">
              <div className="flex flex-wrap items-center justify-between gap-4">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 rounded-full bg-accent/10 border border-accent/20 flex items-center justify-center text-accent">
                    <User className="w-6 h-6" />
                  </div>
                  <div>
                    <h2 className="text-lg font-bold text-fg">{data.patient_name}</h2>
                    <div className="flex flex-wrap items-center gap-3 text-xs text-fg-muted mt-0.5">
                      <span className="font-mono text-fg">{data.phone}</span>
                      {data.date_of_birth && <span>DOB: {data.date_of_birth}</span>}
                      {data.gender && <span className="capitalize">Jins: {data.gender}</span>}
                      <span>Kul Visits: <strong className="text-fg font-semibold">{data.visits.length}</strong></span>
                    </div>
                  </div>
                </div>

                {data.notes && (
                  <div className="bg-surface-raised border border-border p-2.5 rounded-md text-xs max-w-sm">
                    <span className="text-fg-muted font-medium flex items-center gap-1 mb-0.5">
                      <Lock className="w-3 h-3 text-amber-400" />
                      Clinic Notes:
                    </span>
                    <p className="text-fg">{data.notes}</p>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Form & Timeline Split */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
            {/* New Visit Form (Left 6 Columns) */}
            <div className="lg:col-span-6 bg-surface border border-border rounded-lg p-6 space-y-5">
              <h2 className="text-base font-semibold text-fg flex items-center gap-2">
                <FileText className="w-4 h-4 text-accent" />
                Naya Visit Note (Current Encounter)
              </h2>

              <form onSubmit={handleSaveVisitNote} className="space-y-4">
                {/* Complaint */}
                <div>
                  <label htmlFor="visit-complaint" className="block text-xs font-medium text-fg-muted mb-1">
                    Mareez ki Shikayat (Complaint, ≤ 500 chars)
                  </label>
                  <Input
                    id="visit-complaint"
                    value={complaint}
                    onChange={(e) => setComplaint(e.target.value)}
                    placeholder="e.g. Bukhar 3 din se, khansi aur gala kharab"
                    maxLength={500}
                    aria-label="Complaint input"
                  />
                </div>

                {/* Private Notes (Staff only) */}
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <label htmlFor="visit-private-notes" className="text-xs font-medium text-fg-muted flex items-center gap-1.5">
                      <Lock className="w-3.5 h-3.5 text-amber-400" />
                      Private Notes (Clinic Staff Only — Mareez ko nahi dikhaya jata)
                    </label>
                    <span className="text-xs text-amber-400/80 font-mono">≤ 4000 chars</span>
                  </div>
                  <textarea
                    id="visit-private-notes"
                    rows={3}
                    value={notes}
                    onChange={(e) => setNotes(e.target.value)}
                    placeholder="Clinical findings, differential diagnosis, internal observations..."
                    className="w-full p-2.5 bg-surface-raised border border-border rounded-md text-xs text-fg focus:outline-none focus:ring-1 focus:ring-accent resize-none"
                    maxLength={4000}
                    aria-label="Private notes input"
                  />
                </div>

                {/* Medicines & Advice (Shareable) */}
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <label htmlFor="visit-medicines" className="text-xs font-medium text-fg-muted flex items-center gap-1.5">
                      <Pill className="w-3.5 h-3.5 text-accent" />
                      Dawa / Advice (Medicines & Instructions)
                    </label>
                    <span className="text-xs text-fg-muted font-mono">≤ 2000 chars</span>
                  </div>
                  <textarea
                    id="visit-medicines"
                    rows={4}
                    value={medicinesAdvice}
                    onChange={(e) => setMedicinesAdvice(e.target.value)}
                    placeholder="1. Tab Panadol 500mg (1 subha, 1 sham 5 din)&#10;2. Syrup Acefyl (2 chamach din mein 3 bar)&#10;Hidayat: Thanda pani na piyein."
                    className="w-full p-2.5 bg-surface-raised border border-border rounded-md text-xs text-fg focus:outline-none focus:ring-1 focus:ring-accent resize-none font-mono"
                    maxLength={2000}
                    aria-label="Medicines advice input"
                  />
                  <p className="text-xs text-fg-muted mt-1">
                    Ye nuskha token link par mareez ke sath share kiya ja sakta hai (Doctor ki Hidayat F-021).
                  </p>
                </div>

                {/* Share With Patient Checkbox (Shown only when clinic setting is ON) */}
                {data?.share_advice_clinic_setting && (
                  <div className="p-3 rounded-md bg-accent-subtle border border-accent-border">
                    <label className="flex items-start gap-2.5 cursor-pointer text-xs text-fg select-none">
                      <input
                        type="checkbox"
                        checked={shareWithPatient}
                        onChange={(e) => setShareWithPatient(e.target.checked)}
                        className="mt-0.5 rounded border-border text-accent focus:ring-accent"
                        aria-label="Share with patient checkbox"
                      />
                      <div>
                        <span className="font-semibold text-accent flex items-center gap-1">
                          <Share2 className="w-3.5 h-3.5" />
                          Mareez ko dikhayein (Share advice with patient — A-014)
                        </span>
                        <p className="text-fg-muted text-xs mt-0.5">
                          Ticked hone par mareez apne public token link par ye dawa aur hidayat dekh saky ga.
                        </p>
                      </div>
                    </label>
                  </div>
                )}

                <div className="pt-3 border-t border-border">
                  <Button
                    type="submit"
                    variant="primary"
                    disabled={isSaving}
                    className="w-full h-10 font-semibold"
                    aria-label="Save visit note button"
                  >
                    <Save className="w-4 h-4 mr-1.5" />
                    {isSaving ? "Mahfooz ho raha hai..." : "Visit Note Mahfooz Karein"}
                  </Button>
                </div>
              </form>
            </div>

            {/* Timeline (Right 6 Columns) */}
            <div className="lg:col-span-6 bg-surface border border-border rounded-lg p-6 space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-border">
                <h2 className="text-base font-semibold text-fg flex items-center gap-2">
                  <History className="w-4 h-4 text-accent" />
                  Timeline (Pichly Visits — Newest First)
                </h2>
                <span className="text-xs font-mono text-fg-muted">
                  {data?.visits.length || 0} visits
                </span>
              </div>

              {data && data.visits.length > 0 ? (
                <div className="space-y-4 max-h-[600px] overflow-y-auto pr-1">
                  {data.visits.map((v) => (
                    <div
                      key={v.id}
                      className="p-4 rounded-lg bg-surface-raised border border-border/80 space-y-3"
                    >
                      {/* Visit Header */}
                      <div className="flex items-center justify-between text-xs pb-2 border-b border-border">
                        <div className="flex items-center gap-2 font-medium text-fg">
                          <Calendar className="w-3.5 h-3.5 text-accent" />
                          <span>{new Date(v.created_at).toLocaleDateString()}</span>
                          <span className="text-fg-muted">•</span>
                          <span>{v.doctor_name}</span>
                        </div>
                        {v.token_number && (
                          <span className="font-mono text-accent font-bold">
                            Token #{v.token_number}
                          </span>
                        )}
                      </div>

                      {/* Complaint */}
                      {v.complaint && (
                        <div>
                          <span className="text-xs font-semibold text-fg-muted block">
                            Shikayat (Complaint):
                          </span>
                          <p className="text-xs text-fg mt-0.5">{v.complaint}</p>
                        </div>
                      )}

                      {/* Staff Notes */}
                      {v.notes && (
                        <div className="p-2.5 rounded bg-surface border border-border/80">
                          <span className="text-xs font-medium text-amber-400 flex items-center gap-1">
                            <Lock className="w-3 h-3" />
                            Staff Private Note:
                          </span>
                          <p className="text-xs text-fg mt-1 whitespace-pre-wrap">{v.notes}</p>
                        </div>
                      )}

                      {/* Medicines / Advice */}
                      {v.medicines_advice && (
                        <div className="p-2.5 rounded bg-surface border border-accent/30">
                          <div className="flex items-center justify-between text-xs mb-1">
                            <span className="font-semibold text-accent flex items-center gap-1">
                              <Pill className="w-3 h-3" />
                              Dawa / Advice:
                            </span>
                            {v.share_with_patient ? (
                              <span className="text-xs text-emerald-400 flex items-center gap-0.5">
                                <Eye className="w-3 h-3" /> Shared
                              </span>
                            ) : (
                              <span className="text-xs text-fg-muted flex items-center gap-0.5">
                                <EyeOff className="w-3 h-3" /> Hidden from patient
                              </span>
                            )}
                          </div>
                          <p className="text-xs font-mono text-fg whitespace-pre-wrap">
                            {v.medicines_advice}
                          </p>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <div className="py-14 text-center text-fg-muted space-y-2">
                  <History className="w-10 h-10 mx-auto text-fg-muted/40" />
                  <p className="text-sm font-medium text-fg">Koi purana visit record nahi hai</p>
                  <p className="text-xs text-fg-muted">
                    Is mareez ka pehla visit note darj karein to yahan timeline mein numayan ho jaye ga.
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      </LayoutShell>
    </RoleGuard>
  );
}
