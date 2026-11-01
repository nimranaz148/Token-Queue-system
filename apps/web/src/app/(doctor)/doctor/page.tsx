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
  ArrowRight,
  CheckCircle,
  Clock,
  FastForward,
  FileText,
  History,
  Pause,
  Play,
  RotateCcw,
  Stethoscope,
  User,
  Users,
  X,
} from "lucide-react";

export interface DoctorQueueTokenItem {
  id: string;
  number: number;
  public_code: string;
  status: string;
  source: string;
  patient_id: string;
  patient_name: string;
  patient_age?: number | null;
  patient_gender?: string | null;
  position: number;
  arrived_at?: string | null;
  called_at?: string | null;
  cancelled_reason?: string | null;
  created_at: string;
}

export interface DoctorQueueData {
  doctor_id: string;
  doctor_name: string;
  visit_date: string;
  current_token?: DoctorQueueTokenItem | null;
  next_tokens: DoctorQueueTokenItem[];
  waiting_tokens: DoctorQueueTokenItem[];
  skipped_tokens: DoctorQueueTokenItem[];
  counts: Record<string, number>;
}

interface DoctorPanelPageProps {
  initialQueue?: DoctorQueueData;
  userRole?: string;
}

export default function DoctorPanelPage({
  initialQueue,
  userRole = "doctor",
}: DoctorPanelPageProps) {
  const [queue, setQueue] = React.useState<DoctorQueueData | null>(initialQueue || null);
  const [isLoading, setIsLoading] = React.useState(!initialQueue);
  const [actionError, setActionError] = React.useState<string | null>(null);
  const [actionSuccess, setActionSuccess] = React.useState<string | null>(null);

  // Quick consult note
  const [quickNote, setQuickNote] = React.useState("");
  const [isSubmittingNext, setIsSubmittingNext] = React.useState(false);

  // Hold dialog state
  const [showHoldModal, setShowHoldModal] = React.useState(false);
  const [holdReason, setHoldReason] = React.useState("");
  const [isHolding, setIsHolding] = React.useState(false);

  const fetchQueue = React.useCallback(async () => {
    try {
      const res = await fetch("/api/v1/tokens/doctor/queue");
      if (res.ok) {
        const data: DoctorQueueData = await res.json();
        setQueue(data);
      }
    } catch {
      // Non-blocking fetch
    } finally {
      setIsLoading(false);
    }
  }, []);

  React.useEffect(() => {
    if (!initialQueue) {
      fetchQueue();
    }
  }, [initialQueue, fetchQueue]);

  // NEXT patient action (completes current serving and calls next)
  const handleCallNext = async () => {
    setActionError(null);
    setActionSuccess(null);
    setIsSubmittingNext(true);

    try {
      const res = await fetch("/api/v1/tokens/doctor/next", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          quick_note: quickNote.trim() || null,
        }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Agla mareez bulane mein masla pesh aya.");
      }

      const result = await res.json();
      setActionSuccess(result.message || "Agla mareez bula liya gaya.");
      setQuickNote("");
      await fetchQueue();
    } catch (err: any) {
      setActionError(err.message || "Failed to call next patient.");
    } finally {
      setIsSubmittingNext(false);
    }
  };

  // Skip current patient
  const handleSkip = async () => {
    if (!queue?.current_token) return;
    setActionError(null);
    setActionSuccess(null);

    try {
      const res = await fetch("/api/v1/tokens/doctor/skip", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({}),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Mareez ko skip karne mein masla pesh aya.");
      }

      const result = await res.json();
      setActionSuccess(result.message || "Mareez ko skip kar diya gaya.");
      await fetchQueue();
    } catch (err: any) {
      setActionError(err.message || "Failed to skip patient.");
    }
  };

  // Hold current patient
  const handleConfirmHold = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!queue?.current_token) return;
    setActionError(null);
    setActionSuccess(null);
    setIsHolding(true);

    try {
      const res = await fetch("/api/v1/tokens/doctor/hold", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ reason: holdReason.trim() || null }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Mareez ko hold par rakhne mein masla pesh aya.");
      }

      const result = await res.json();
      setActionSuccess(result.message || "Mareez ko hold par rakh diya gaya.");
      setShowHoldModal(false);
      setHoldReason("");
      await fetchQueue();
    } catch (err: any) {
      setActionError(err.message || "Failed to hold patient.");
    } finally {
      setIsHolding(false);
    }
  };

  // Recall skipped or hold patient
  const handleRecall = async (tokenId: string) => {
    setActionError(null);
    setActionSuccess(null);

    try {
      const res = await fetch("/api/v1/tokens/doctor/recall", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token_id: tokenId }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Mareez ko recall karne mein masla pesh aya.");
      }

      const result = await res.json();
      setActionSuccess(result.message || "Mareez ko queue ke shuru mein recall kar liya gaya.");
      await fetchQueue();
    } catch (err: any) {
      setActionError(err.message || "Failed to recall patient.");
    }
  };

  const currentToken = queue?.current_token;
  const nextTokens = queue?.next_tokens || [];
  const skippedTokens = queue?.skipped_tokens || [];

  return (
    <RoleGuard allowedRoles={["doctor", "owner"]}>
      <LayoutShell
        userRole={userRole}
        navItems={[
          { label: "Doctor Panel", href: "/doctor", icon: <Stethoscope className="w-4 h-4" />, active: true },
          { label: "Patient History", href: "/doctor/history", icon: <History className="w-4 h-4" /> },
          { label: "Aaj ki List", href: "/tokens", icon: <Clock className="w-4 h-4" /> },
        ]}
      >
        <div className="max-w-6xl mx-auto space-y-6">
          {/* Header */}
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-4 border-b border-border">
            <div>
              <div className="flex items-center gap-2">
                <Stethoscope className="w-6 h-6 text-accent" />
                <h1 className="text-2xl font-bold tracking-tight text-fg">
                  Doctor Consultation Panel
                </h1>
                <span className="text-xs font-semibold px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 uppercase">
                  F-007
                </span>
              </div>
              <p className="text-sm text-fg-muted mt-1">
                {queue?.doctor_name ? `${queue.doctor_name} — ` : ""}
                Mareez ko call karein (NEXT), skip ya hold karein aur quick consult notes likhein
              </p>
            </div>

            {/* Queue Counter Badges */}
            <div className="flex items-center gap-2 text-xs">
              <span className="px-2.5 py-1 rounded-md bg-surface-raised border border-border text-fg">
                Kul: <strong className="text-accent">{queue?.counts.total || 0}</strong>
              </span>
              <span className="px-2.5 py-1 rounded-md bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
                Arrived: <strong>{queue?.counts.arrived || 0}</strong>
              </span>
              <span className="px-2.5 py-1 rounded-md bg-amber-500/10 border border-amber-500/20 text-amber-400">
                Hold/Skip: <strong>{(queue?.counts.hold || 0) + (queue?.counts.skipped || 0)}</strong>
              </span>
            </div>
          </div>

          {/* Alert Banners */}
          {actionError && (
            <div className="p-3.5 rounded-md bg-destructive/10 border border-destructive/20 text-destructive text-sm flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{actionError}</span>
            </div>
          )}

            {actionSuccess && (
            <div className="p-3.5 rounded-md bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-sm flex items-center gap-2">
              <CheckCircle className="w-4 h-4 shrink-0" />
              <span>{actionSuccess}</span>
            </div>
          )}

          {/* Main Grid: Left = Active Patient & Actions, Right = Next in line & Recalls */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
            {/* Left 7 Columns: Active Patient & Big NEXT Button */}
            <div className="lg:col-span-7 space-y-6">
              {/* Active Serving Card */}
              <div className="bg-surface border border-accent/40 rounded-xl p-6 shadow-xs space-y-5">
                <div className="flex items-center justify-between pb-3 border-b border-border">
                  <div className="flex items-center gap-2">
                    <span className="w-3 h-3 rounded-full bg-accent animate-pulse" />
                    <span className="text-xs font-semibold uppercase tracking-wider text-accent">
                      Currently Serving (Zair-e-Muaina)
                    </span>
                  </div>
                  {currentToken && (
                    <StatusBadge variant="info">SERVING #{currentToken.number}</StatusBadge>
                  )}
                </div>

                {currentToken ? (
                  <div className="space-y-4">
                    <div className="flex flex-col sm:flex-row sm:items-baseline justify-between gap-2">
                      <div className="space-y-1">
                        <div className="text-4xl font-black text-accent font-mono">
                          #{currentToken.number}
                        </div>
                        <h2 className="text-2xl font-bold text-fg flex items-center gap-2">
                          <User className="w-5 h-5 text-accent" />
                          {currentToken.patient_name}
                        </h2>
                        <div className="flex items-center gap-3 text-xs text-fg-muted">
                          {currentToken.patient_age !== null && (
                            <span>Umar: <strong className="text-fg">{currentToken.patient_age} saal</strong></span>
                          )}
                          {currentToken.patient_gender && (
                            <span className="capitalize">Jins: <strong className="text-fg">{currentToken.patient_gender}</strong></span>
                          )}
                          <span>Source: <strong className="font-mono text-fg uppercase">{currentToken.source}</strong></span>
                        </div>
                      </div>

                      <Link href={`/doctor/patients/${currentToken.patient_id}`}>
                        <Button variant="secondary" size="sm" aria-label="View full patient history">
                          <FileText className="w-3.5 h-3.5 mr-1" />
                          Full History (F-008)
                        </Button>
                      </Link>
                    </div>

                    {/* Quick Consult Note */}
                    <div className="space-y-1.5 pt-2 border-t border-border">
                      <label htmlFor="quick-consult-note" className="block text-xs font-medium text-fg-muted">
                        Quick Consult Note (≤ 2000 chars — Visit record mein mahfooz ho ga)
                      </label>
                      <textarea
                        id="quick-consult-note"
                        rows={3}
                        value={quickNote}
                        onChange={(e) => setQuickNote(e.target.value)}
                        placeholder="Mareez ki shikayat, tashkhees ya quick hidayat darj karein..."
                        className="w-full p-2.5 bg-surface-raised border border-border rounded-md text-xs text-fg focus:outline-none focus:ring-1 focus:ring-accent resize-none"
                        aria-label="Quick consult note"
                      />
                    </div>

                    {/* Secondary Actions for Serving Token: Skip & Hold */}
                    <div className="flex items-center gap-3 pt-2">
                      <Button
                        variant="secondary"
                        onClick={handleSkip}
                        className="flex-1"
                        aria-label="Skip patient button"
                      >
                        <FastForward className="w-4 h-4 mr-1.5 text-amber-400" />
                        Skip (Chhorein)
                      </Button>
                      <Button
                        variant="secondary"
                        onClick={() => setShowHoldModal(true)}
                        className="flex-1"
                        aria-label="Hold patient button"
                      >
                        <Pause className="w-4 h-4 mr-1.5 text-blue-400" />
                        Hold (Rokein)
                      </Button>
                    </div>
                  </div>
                ) : (
                  <div className="py-12 text-center text-fg-muted space-y-3">
                    <div className="w-16 h-16 rounded-full bg-surface-raised border border-border mx-auto flex items-center justify-center text-fg-muted/40 font-mono text-2xl font-bold">
                      #--
                    </div>
                    <p className="text-base font-semibold text-fg">Koi mareez active nahi hai</p>
                    <p className="text-xs text-fg-muted max-w-sm mx-auto">
                      Agla mareez bulane ke liye neeche diya gaya bara "NEXT PATIENT" button dabayein.
                    </p>
                  </div>
                )}

                {/* Big NEXT Button (PRD §5.3 F-007: Big button, completes current & calls next) */}
                <div className="pt-4 border-t border-border">
                  <Button
                    variant="primary"
                    onClick={handleCallNext}
                    disabled={isSubmittingNext}
                    className="w-full h-14 text-lg font-black tracking-wider uppercase shadow-md flex items-center justify-center gap-2"
                    aria-label="Call next patient button"
                  >
                    <Play className="w-5 h-5 fill-current" />
                    {isSubmittingNext ? "BULAYA JA RAHA HAI..." : "NEXT PATIENT (AGLA MAREEZ)"}
                    <ArrowRight className="w-5 h-5 ml-1" />
                  </Button>
                </div>
              </div>
            </div>

            {/* Right 5 Columns: Next 3 in line & Skipped/Hold Recalls */}
            <div className="lg:col-span-5 space-y-6">
              {/* Next in Line (Next 3 Patients) */}
              <div className="bg-surface border border-border rounded-xl p-5 space-y-4">
                <div className="flex items-center justify-between pb-2 border-b border-border">
                  <h3 className="text-sm font-semibold text-fg flex items-center gap-1.5">
                    <Users className="w-4 h-4 text-accent" />
                    Agly 3 Mareez (Next in Line)
                  </h3>
                  <span className="text-xs text-fg-muted font-mono">
                    {nextTokens.length} waiting
                  </span>
                </div>

                {nextTokens.length > 0 ? (
                  <div className="space-y-2.5">
                    {nextTokens.map((tok, idx) => (
                      <div
                        key={tok.id}
                        className="p-3 rounded-lg bg-surface-raised border border-border/80 flex items-center justify-between gap-3"
                      >
                        <div className="flex items-center gap-3">
                          <div className="w-8 h-8 rounded-full bg-accent/10 border border-accent/20 flex items-center justify-center font-mono font-bold text-sm text-accent">
                            {tok.number}
                          </div>
                          <div>
                            <div className="font-semibold text-sm text-fg">
                              {tok.patient_name}
                            </div>
                            <div className="text-xs text-fg-muted flex items-center gap-2">
                              <span>Position: {idx + 1}</span>
                              <span>•</span>
                              <span className="uppercase font-mono">{tok.source}</span>
                            </div>
                          </div>
                        </div>
                        <StatusBadge variant={tok.status === "arrived" ? "success" : "neutral"}>
                          {tok.status.toUpperCase()}
                        </StatusBadge>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="py-6 text-center text-xs text-fg-muted">
                    Waiting queue mein koi mareez nahi hai.
                  </div>
                )}
              </div>

              {/* Skipped / On-Hold Patients (Recallable) */}
              <div className="bg-surface border border-border rounded-xl p-5 space-y-4">
                <div className="flex items-center justify-between pb-2 border-b border-border">
                  <h3 className="text-sm font-semibold text-fg flex items-center gap-1.5">
                    <RotateCcw className="w-4 h-4 text-amber-400" />
                    Skipped & Hold (Recallable)
                  </h3>
                  <span className="text-xs text-fg-muted font-mono">
                    {skippedTokens.length}
                  </span>
                </div>

                {skippedTokens.length > 0 ? (
                  <div className="space-y-2.5">
                    {skippedTokens.map((tok) => (
                      <div
                        key={tok.id}
                        className="p-3 rounded-lg bg-surface-raised border border-border flex items-center justify-between gap-2"
                      >
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="font-mono font-bold text-sm text-fg">
                              #{tok.number}
                            </span>
                            <span className="font-medium text-xs text-fg">
                              {tok.patient_name}
                            </span>
                            <StatusBadge variant={tok.status === "hold" ? "warning" : "danger"}>
                              {tok.status.toUpperCase()}
                            </StatusBadge>
                          </div>
                          {tok.cancelled_reason && (
                            <p className="text-xs text-fg-muted mt-1 italic">
                              Wajah: {tok.cancelled_reason}
                            </p>
                          )}
                        </div>
                        <Button
                          variant="secondary"
                          size="sm"
                          onClick={() => handleRecall(tok.id)}
                          aria-label={`Recall token ${tok.number}`}
                        >
                          <RotateCcw className="w-3 h-3 mr-1 text-emerald-400" />
                          Recall
                        </Button>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="py-6 text-center text-xs text-fg-muted">
                    Koi skipped ya hold mareez nahi hai.
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Hold Dialog Modal */}
          {showHoldModal && (
            <div
              className="fixed inset-0 z-50 bg-black/60 backdrop-blur-xs flex items-center justify-center p-4 animate-in fade-in duration-150"
              role="dialog"
              aria-modal="true"
              aria-label="Hold Patient Dialog"
            >
              <div className="bg-surface border border-border rounded-lg shadow-xl max-w-md w-full p-6 space-y-4">
                <div className="flex items-center justify-between border-b border-border pb-3">
                  <h3 className="text-base font-bold text-fg flex items-center gap-2">
                    <Pause className="w-5 h-5 text-blue-400" />
                    Mareez ko Hold Par Rakhein
                  </h3>
                  <button
                    onClick={() => setShowHoldModal(false)}
                    className="p-1 rounded text-fg-muted hover:text-fg"
                    aria-label="Close modal"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>

                <p className="text-xs text-fg-muted">
                  Mareez #{currentToken?.number} ({currentToken?.patient_name}) ko temporary hold par rakh diya jaye ga (maslan reports ka intezar).
                </p>

                <form onSubmit={handleConfirmHold} className="space-y-4">
                  <div>
                    <label htmlFor="hold-reason" className="block text-xs font-medium text-fg-muted mb-1">
                      Hold ki Wajah (Optional Reason, ≤ 200 chars)
                    </label>
                    <Input
                      id="hold-reason"
                      value={holdReason}
                      onChange={(e) => setHoldReason(e.target.value)}
                      placeholder="e.g. Waiting for blood test reports / ECG"
                      maxLength={200}
                      aria-label="Hold reason"
                    />
                  </div>

                  <div className="flex justify-end gap-2 pt-2 border-t border-border">
                    <Button
                      type="button"
                      variant="secondary"
                      onClick={() => setShowHoldModal(false)}
                      disabled={isHolding}
                    >
                      Cancel
                    </Button>
                    <Button
                      type="submit"
                      variant="primary"
                      disabled={isHolding}
                      aria-label="Confirm Hold"
                    >
                      {isHolding ? "Hold ho raha hai..." : "Hold Par Rakhein"}
                    </Button>
                  </div>
                </form>
              </div>
            </div>
          )}
        </div>
      </LayoutShell>
    </RoleGuard>
  );
}
