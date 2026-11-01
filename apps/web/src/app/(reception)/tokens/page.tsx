"use client";

import * as React from "react";
import { LayoutShell } from "@/components/layout/layout-shell";
import { RoleGuard } from "@/components/auth/role-guard";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { StatusBadge, type StatusBadgeVariant } from "@/components/ui/status-badge";
import { AlertCircle, CheckCircle, Clock, Filter, RefreshCw, XCircle } from "lucide-react";

export interface ReceptionTokenItem {
  id: string;
  number: number;
  patient_id: string;
  patient_name: string;
  phone: string;
  source: string;
  status: string;
  doctor_id: string;
  doctor_name: string;
  visit_date: string;
  position: number;
  arrived_at?: string | null;
  called_at?: string | null;
  completed_at?: string | null;
  cancelled_reason?: string | null;
  created_at: string;
}

export interface DoctorOption {
  id: string;
  name: string;
}

interface ReceptionTokensPageProps {
  initialTokens?: ReceptionTokenItem[];
  userRole?: string;
}

export default function ReceptionTokensPage({
  initialTokens = [],
  userRole = "reception",
}: ReceptionTokensPageProps) {
  const [tokens, setTokens] = React.useState<ReceptionTokenItem[]>(initialTokens);
  const [total, setTotal] = React.useState<number>(initialTokens.length);
  const [doctors, setDoctors] = React.useState<DoctorOption[]>([]);

  // Filter state
  const todayStr = React.useMemo(() => new Date().toISOString().split("T")[0], []);
  const [selectedDate, setSelectedDate] = React.useState<string>(todayStr);
  const [doctorFilter, setDoctorFilter] = React.useState<string>("");
  const [statusFilter, setStatusFilter] = React.useState<string>("all");
  const [search, setSearch] = React.useState<string>("");

  // Loading and error states
  const [isLoading, setIsLoading] = React.useState(false);
  const [fetchError, setFetchError] = React.useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = React.useState<string>("");

  // Action states
  const [markingId, setMarkingId] = React.useState<string | null>(null);
  const [actionSuccess, setActionSuccess] = React.useState<string | null>(null);
  const [actionError, setActionError] = React.useState<string | null>(null);

  // Cancel modal
  const [cancellingToken, setCancellingToken] = React.useState<ReceptionTokenItem | null>(null);
  const [cancelReason, setCancelReason] = React.useState("");
  const [cancelModalError, setCancelModalError] = React.useState<string | null>(null);
  const [isCancelling, setIsCancelling] = React.useState(false);

  // Fetch doctors list for filter
  React.useEffect(() => {
    async function loadDoctors() {
      try {
        const res = await fetch("/api/v1/doctors");
        if (res.ok) {
          const data = await res.json();
          const items = Array.isArray(data) ? data : data.items || [];
          setDoctors(items);
        }
      } catch {
        // Non-blocking doctor filter load
      }
    }
    loadDoctors();
  }, []);

  // Fetch tokens callback
  const fetchTokens = React.useCallback(async () => {
    setIsLoading(true);
    setFetchError(null);
    try {
      const params = new URLSearchParams();
      if (selectedDate) params.append("date", selectedDate);
      if (doctorFilter) params.append("doctor_id", doctorFilter);
      if (statusFilter && statusFilter !== "all") params.append("status", statusFilter);
      if (search.trim().length >= 2) params.append("search", search.trim());

      const res = await fetch(`/api/v1/tokens?${params.toString()}`);
      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || "Tokens load karne mein masla pesh aya.");
      }

      const data = await res.json();
      setTokens(data.items || []);
      setTotal(data.total ?? (data.items || []).length);
      setLastUpdated(new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" }));
    } catch (err: any) {
      setFetchError(err.message || "Network error. Tokens refresh karein.");
    } finally {
      setIsLoading(false);
    }
  }, [selectedDate, doctorFilter, statusFilter, search]);

  React.useEffect(() => {
    fetchTokens();
  }, [fetchTokens]);

  // Mark arrived
  const handleMarkArrived = async (token: ReceptionTokenItem) => {
    setMarkingId(token.id);
    setActionSuccess(null);
    setActionError(null);
    try {
      const res = await fetch(`/api/v1/tokens/${token.id}/arrive`, {
        method: "POST",
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Mark arrived failed.");
      }
      const updated = await res.json();
      setTokens((prev) => prev.map((t) => (t.id === token.id ? updated : t)));
      setActionSuccess(`Token #${token.number} (${token.patient_name}) arrived mark ho gaya.`);
    } catch (err: any) {
      setActionError(err.message);
    } finally {
      setMarkingId(null);
    }
  };

  // Submit cancellation
  const handleCancelSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!cancellingToken) return;
    if (cancelReason.trim().length < 2) {
      setCancelModalError("Mansookhi ki wajah likhna zaroori hai (kam az kam 2 characters).");
      return;
    }

    setIsCancelling(true);
    setCancelModalError(null);
    try {
      const res = await fetch(`/api/v1/tokens/${cancellingToken.id}/cancel`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ reason: cancelReason.trim() }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Cancel operation failed.");
      }
      const updated = await res.json();
      setTokens((prev) => prev.map((t) => (t.id === cancellingToken.id ? updated : t)));
      setActionSuccess(`Token #${cancellingToken.number} mansookh (cancelled) ho gaya.`);
      setCancellingToken(null);
      setCancelReason("");
    } catch (err: any) {
      setCancelModalError(err.message);
    } finally {
      setIsCancelling(false);
    }
  };

  const getStatusVariant = (status: string): StatusBadgeVariant => {
    switch (status.toLowerCase()) {
      case "serving":
        return "success";
      case "arrived":
        return "info";
      case "booked":
        return "neutral";
      case "skipped":
      case "hold":
        return "warning";
      case "cancelled":
      case "no_show":
        return "danger";
      default:
        return "neutral";
    }
  };

  return (
    <RoleGuard allowedRoles={["reception", "owner", "doctor"]}>
      <LayoutShell
        userRole={userRole}
        navItems={[
          { label: "Aaj ki List", href: "/tokens", icon: <Clock className="w-4 h-4" />, active: true },
          { label: "Walk-in Entry", href: "/tokens/walk-in", icon: <CheckCircle className="w-4 h-4" /> },
          { label: "Patients", href: "/patients", icon: <Filter className="w-4 h-4" /> },
        ]}
      >
        <div className="space-y-6">
          {/* Header Banner */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-border">
            <div>
              <div className="flex items-center gap-3">
                <h1 className="text-2xl font-bold tracking-tight text-fg">Aaj ki List</h1>
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-accent-subtle text-accent border border-accent/20">
                  {total} Tokens
                </span>
              </div>
              <p className="text-sm text-fg-muted mt-1">
                Reception Token Management · Live OPD Queue Tracking
              </p>
            </div>
            <div className="flex items-center gap-3">
              {lastUpdated && (
                <span className="text-xs text-fg-muted">
                  Last updated: <span className="font-mono text-fg">{lastUpdated}</span>
                </span>
              )}
              <Button
                variant="secondary"
                size="sm"
                onClick={() => fetchTokens()}
                disabled={isLoading}
                aria-label="Refresh Tokens"
              >
                <RefreshCw className={`w-3.5 h-3.5 mr-1.5 ${isLoading ? "animate-spin" : ""}`} />
                Refresh
              </Button>
            </div>
          </div>

          {/* Action Alerts */}
          {actionSuccess && (
            <div className="p-3.5 rounded-md bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-sm flex items-center gap-2">
              <CheckCircle className="w-4 h-4 shrink-0" />
              <span>{actionSuccess}</span>
            </div>
          )}
          {actionError && (
            <div className="p-3.5 rounded-md bg-destructive/10 border border-destructive/20 text-destructive text-sm flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{actionError}</span>
            </div>
          )}
          {fetchError && (
            <div className="p-4 rounded-md bg-destructive/10 border border-destructive/20 text-destructive text-sm flex items-center justify-between gap-2">
              <div className="flex items-center gap-2">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{fetchError}</span>
              </div>
              <Button variant="secondary" size="sm" onClick={() => fetchTokens()}>
                Retry
              </Button>
            </div>
          )}

          {/* Filters Bar */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 bg-surface border border-border p-4 rounded-lg">
            {/* Date Filter */}
            <div>
              <label htmlFor="token-date" className="block text-xs font-medium text-fg-muted mb-1">
                Date (Tareekh)
              </label>
              <input
                id="token-date"
                type="date"
                value={selectedDate}
                onChange={(e) => setSelectedDate(e.target.value)}
                className="w-full h-8.5 px-3 py-1 bg-surface-raised border border-border rounded-md text-sm text-fg focus:outline-none focus:ring-1 focus:ring-accent"
                aria-label="Visit Date"
              />
            </div>

            {/* Doctor Filter */}
            <div>
              <label htmlFor="token-doctor" className="block text-xs font-medium text-fg-muted mb-1">
                Doctor (Doctor ka intekhab)
              </label>
              <select
                id="token-doctor"
                value={doctorFilter}
                onChange={(e) => setDoctorFilter(e.target.value)}
                className="w-full h-8.5 px-3 py-1 bg-surface-raised border border-border rounded-md text-sm text-fg focus:outline-none focus:ring-1 focus:ring-accent"
                aria-label="Doctor Filter"
              >
                <option value="">All Doctors (Tamam Doctors)</option>
                {doctors.map((doc) => (
                  <option key={doc.id} value={doc.id}>
                    {doc.name}
                  </option>
                ))}
              </select>
            </div>

            {/* Status Filter */}
            <div>
              <label htmlFor="token-status" className="block text-xs font-medium text-fg-muted mb-1">
                Status (Token Halat)
              </label>
              <select
                id="token-status"
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="w-full h-8.5 px-3 py-1 bg-surface-raised border border-border rounded-md text-sm text-fg focus:outline-none focus:ring-1 focus:ring-accent"
                aria-label="Status Filter"
              >
                <option value="all">All Statuses (Tamam)</option>
                <option value="booked">Booked (Online)</option>
                <option value="arrived">Arrived (Clinic mein)</option>
                <option value="serving">Serving (Doctor ke paas)</option>
                <option value="done">Done (Mukammal)</option>
                <option value="skipped">Skipped (Chhor diya)</option>
                <option value="hold">Hold (Roka hua)</option>
                <option value="cancelled">Cancelled (Mansookh)</option>
                <option value="no_show">No Show (Ghair hazir)</option>
              </select>
            </div>

            {/* Search Filter */}
            <div>
              <label htmlFor="token-search" className="block text-xs font-medium text-fg-muted mb-1">
                Search (Naam ya Phone)
              </label>
              <Input
                id="token-search"
                placeholder="≥ 2 chars (e.g. Usman)..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                aria-label="Search tokens"
              />
            </div>
          </div>

          {/* Tokens List / Table */}
          <div className="bg-surface border border-border rounded-lg overflow-hidden shadow-sm">
            {isLoading && tokens.length === 0 ? (
              <div className="p-12 text-center text-fg-muted">
                <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-accent" />
                <p className="text-sm">Tokens load ho rahe hain...</p>
              </div>
            ) : tokens.length === 0 ? (
              <div className="p-12 text-center text-fg-muted">
                <Clock className="w-8 h-8 mx-auto mb-2 opacity-40" />
                <p className="text-base font-semibold text-fg">Koi token mojud nahi hai</p>
                <p className="text-sm text-fg-muted mt-1">
                  Selected filters ya date ke mutabiq koi tokens nahi mile.
                </p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse text-sm">
                  <thead>
                    <tr className="border-b border-border bg-surface-raised/50 text-xs font-semibold text-fg-muted uppercase tracking-wider">
                      <th className="py-3 px-4 w-20">Token #</th>
                      <th className="py-3 px-4">Mareez (Patient)</th>
                      <th className="py-3 px-4">Phone</th>
                      <th className="py-3 px-4">Source</th>
                      <th className="py-3 px-4">Doctor</th>
                      <th className="py-3 px-4">Status</th>
                      <th className="py-3 px-4 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border">
                    {tokens.map((token) => (
                      <tr
                        key={token.id}
                        className="hover:bg-surface-raised/30 transition-colors"
                        data-testid={`token-row-${token.number}`}
                      >
                        {/* Token Number */}
                        <td className="py-3.5 px-4 font-mono font-bold text-base text-accent">
                          #{token.number}
                        </td>

                        {/* Patient Name */}
                        <td className="py-3.5 px-4 font-medium text-fg">
                          {token.patient_name}
                        </td>

                        {/* Masked Phone */}
                        <td className="py-3.5 px-4 font-mono text-fg-muted">
                          {token.phone}
                        </td>

                        {/* Source */}
                        <td className="py-3.5 px-4">
                          <span
                            className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium uppercase ${
                              token.source === "walk_in"
                                ? "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                                : "bg-cyan-500/10 text-cyan-400 border border-cyan-500/20"
                            }`}
                          >
                            {token.source === "walk_in" ? "Walk-in" : "Online"}
                          </span>
                        </td>

                        {/* Doctor */}
                        <td className="py-3.5 px-4 text-fg-muted">
                          {token.doctor_name}
                        </td>

                        {/* Status Badge */}
                        <td className="py-3.5 px-4">
                          <StatusBadge variant={getStatusVariant(token.status)}>
                            {token.status.toUpperCase()}
                          </StatusBadge>
                        </td>

                        {/* Actions */}
                        <td className="py-3.5 px-4 text-right">
                          <div className="flex items-center justify-end gap-2">
                            {/* Mark Arrived Action */}
                            {token.status === "booked" && (
                              <Button
                                size="sm"
                                variant="secondary"
                                onClick={() => handleMarkArrived(token)}
                                disabled={markingId === token.id}
                                aria-label={`Mark arrived for token ${token.number}`}
                                className="h-7 px-2.5 text-xs text-emerald-400 border-emerald-500/30 hover:bg-emerald-500/10"
                              >
                                {markingId === token.id ? (
                                  <RefreshCw className="w-3 h-3 animate-spin mr-1" />
                                ) : (
                                  <CheckCircle className="w-3 h-3 mr-1" />
                                )}
                                Mark Arrived
                              </Button>
                            )}

                            {/* Cancel Action */}
                            {(token.status === "booked" || token.status === "arrived") && (
                              <Button
                                size="sm"
                                variant="secondary"
                                onClick={() => {
                                  setCancellingToken(token);
                                  setCancelReason("");
                                  setCancelModalError(null);
                                }}
                                aria-label={`Cancel token ${token.number}`}
                                className="h-7 px-2.5 text-xs text-destructive border-destructive/30 hover:bg-destructive/10"
                              >
                                <XCircle className="w-3 h-3 mr-1" />
                                Cancel
                              </Button>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>

        {/* Cancel Confirmation Modal */}
        {cancellingToken && (
          <div
            className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4"
            role="dialog"
            aria-modal="true"
            aria-labelledby="cancel-modal-title"
          >
            <div className="bg-surface border border-border rounded-lg max-w-md w-full p-6 shadow-xl space-y-4">
              <div className="flex items-start justify-between">
                <div>
                  <h3 id="cancel-modal-title" className="text-lg font-semibold text-fg">
                    Token Mansookh Karein (Cancel Token)
                  </h3>
                  <p className="text-sm text-fg-muted mt-0.5">
                    Token #{cancellingToken.number} — {cancellingToken.patient_name}
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => setCancellingToken(null)}
                  className="text-fg-muted hover:text-fg p-1 rounded-md"
                  aria-label="Close dialog"
                >
                  <XCircle className="w-5 h-5" />
                </button>
              </div>

              {cancelModalError && (
                <div className="p-3 rounded-md bg-destructive/10 border border-destructive/20 text-destructive text-sm flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 shrink-0" />
                  <span>{cancelModalError}</span>
                </div>
              )}

              <form onSubmit={handleCancelSubmit} className="space-y-4">
                <div>
                  <label htmlFor="cancel-reason" className="block text-xs font-medium text-fg-muted mb-1">
                    Mansookhi ki wajah (Cancellation Reason) <span className="text-destructive">*</span>
                  </label>
                  <textarea
                    id="cancel-reason"
                    rows={3}
                    required
                    value={cancelReason}
                    onChange={(e) => setCancelReason(e.target.value)}
                    placeholder="e.g. Mareez clinic nahi pohanch saka, emergency..."
                    className="w-full px-3 py-2 bg-surface-raised border border-border rounded-md text-sm text-fg focus:outline-none focus:ring-1 focus:ring-accent resize-none"
                    aria-label="Cancellation reason"
                  />
                  <p className="text-xs text-fg-muted mt-1">Kam az kam 2 characters zaroori hain.</p>
                </div>

                <div className="flex justify-end gap-2 pt-2 border-t border-border">
                  <Button
                    type="button"
                    variant="secondary"
                    onClick={() => setCancellingToken(null)}
                    disabled={isCancelling}
                  >
                    Wapis (Cancel)
                  </Button>
                  <Button
                    type="submit"
                    variant="danger"
                    disabled={isCancelling || cancelReason.trim().length < 2}
                  >
                    {isCancelling ? "Mansookh ho raha hai..." : "Mansookh Karein"}
                  </Button>
                </div>
              </form>
            </div>
          </div>
        )}
      </LayoutShell>
    </RoleGuard>
  );
}
