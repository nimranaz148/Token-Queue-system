"use client";

import React, { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { StatusBadge } from "@/components/ui/status-badge";

interface TokenDetails {
  id: string;
  number: number;
  public_code: string;
  status: string;
  source: string;
  visit_date: string;
  doctor_id: string;
  doctor_name: string;
  specialty?: string;
  clinic_id: string;
  clinic_name: string;
  clinic_slug: string;
  position: number;
  estimated_at?: string;
  people_ahead: number;
  current_serving_number?: number;
  cancelled_reason?: string;
  created_at: string;
}

export default function TokenConfirmPage(): React.ReactElement {
  const params = useParams();
  const router = useRouter();
  const publicCode = params?.public_code as string;

  const [token, setToken] = useState<TokenDetails | null>(null);
  const [loading, setLoading] = useState(true);
  const [cancelling, setCancelling] = useState(false);
  const [showCancelDialog, setShowCancelDialog] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (!publicCode) return;
    const fetchToken = async (): Promise<void> => {
      try {
        const res = await fetch(`/api/v1/public/tokens/${publicCode}`);
        if (!res.ok) {
          throw new Error("Token not found or invalid link.");
        }
        const data: TokenDetails = await res.json();
        setToken(data);
      } catch (err: unknown) {
        const message = err instanceof Error ? err.message : "Failed to load token details.";
        setError(message);
      } finally {
        setLoading(false);
      }
    };
    void fetchToken();
  }, [publicCode]);

  const handleCancel = async (): Promise<void> => {
    if (!publicCode) return;
    setCancelling(true);
    setError(null);
    try {
      const res = await fetch(`/api/v1/public/tokens/${publicCode}/cancel`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
      });
      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || "Failed to cancel token.");
      }
      setToken((prev) => (prev ? { ...prev, status: "cancelled" } : null));
      setShowCancelDialog(false);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Error cancelling token.";
      setError(message);
    } finally {
      setCancelling(false);
    }
  };

  const handleCopyLink = async (): Promise<void> => {
    if (typeof window !== "undefined") {
      await navigator.clipboard.writeText(window.location.href);
      setCopied(true);
      setTimeout(() => setCopied(false), 2500);
    }
  };

  if (loading) {
    return (
      <main className="flex min-h-screen items-center justify-center p-4 bg-surface-sunken">
        <div className="text-sm font-medium text-fg-muted">Loading your token...</div>
      </main>
    );
  }

  if (error && !token) {
    return (
      <main className="flex min-h-screen flex-col items-center justify-center p-4 bg-surface-sunken">
        <div className="w-full max-w-[420px] bg-surface rounded-xl border border-border shadow-sm p-6 text-center">
          <span className="text-3xl mb-2 block" role="img" aria-label="error">
            ⚠️
          </span>
          <h1 className="text-lg font-bold text-fg">Token Not Found</h1>
          <p className="text-xs text-fg-muted mt-2 mb-5">{error}</p>
          <Button variant="secondary" onClick={() => router.push("/")} className="w-full">
            Home Page
          </Button>
        </div>
      </main>
    );
  }

  const formatEstimatedTime = (iso?: string): string => {
    if (!iso) return "Shortly";
    try {
      const d = new Date(iso);
      return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    } catch {
      return "Shortly";
    }
  };

  const isCancelled = token?.status === "cancelled";
  const canCancel = token?.status === "booked" || token?.status === "arrived";

  const getStatusVariant = (status?: string): "success" | "warning" | "danger" | "info" | "neutral" => {
    switch (status) {
      case "serving":
        return "info";
      case "done":
        return "success";
      case "cancelled":
      case "no_show":
        return "danger";
      case "arrived":
        return "warning";
      default:
        return "neutral";
    }
  };

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-4 bg-surface-sunken">
      <div className="w-full max-w-[440px] bg-surface rounded-xl border border-border shadow-sm p-6 sm:p-8">
        {/* Header (F-002) */}
        <div className="text-center pb-5 border-b border-border">
          <div className="inline-flex items-center gap-1.5 text-status-success text-xs font-bold uppercase tracking-wider mb-1">
            <span role="img" aria-label="confirm check">
              ✓
            </span>
            <span>Token Confirmed</span>
          </div>
          <h1 className="text-sm font-semibold text-fg-muted uppercase tracking-wider">
            {token?.clinic_name || "Clinic"}
          </h1>
        </div>

        {/* Big Token Number Banner */}
        <div className="my-6 p-6 rounded-2xl bg-accent/5 border border-accent/20 text-center flex flex-col items-center">
          <span className="text-xs font-semibold text-accent uppercase tracking-widest">
            Apna Token
          </span>
          <span className="text-6xl font-black text-fg font-mono my-2">#{token?.number}</span>
          <StatusBadge variant={getStatusVariant(token?.status)} className="mt-1">
            {token?.status?.toUpperCase() || "BOOKED"}
          </StatusBadge>
        </div>

        {/* Token Details Matrix */}
        <div className="space-y-3 mb-6 bg-surface-sunken p-4 rounded-xl border border-border text-sm">
          <div className="flex justify-between items-center">
            <span className="text-fg-muted text-xs">Doctor</span>
            <span className="font-semibold text-fg text-right">
              {token?.doctor_name}
              {token?.specialty ? ` (${token.specialty})` : ""}
            </span>
          </div>

          <div className="flex justify-between items-center">
            <span className="text-fg-muted text-xs">Andaazan Time</span>
            <span className="font-semibold text-fg font-mono">
              {formatEstimatedTime(token?.estimated_at)}
            </span>
          </div>

          <div className="flex justify-between items-center">
            <span className="text-fg-muted text-xs">People Ahead</span>
            <span className="font-bold text-accent font-mono">
              {token?.people_ahead ?? 0} log
            </span>
          </div>

          {token?.current_serving_number && (
            <div className="flex justify-between items-center pt-2 border-t border-border">
              <span className="text-fg-muted text-xs">Abhi Chal Raha</span>
              <span className="font-bold text-status-info font-mono">
                #{token.current_serving_number}
              </span>
            </div>
          )}
        </div>

        {/* Primary Action Button: LIVE QUEUE DEKHEIN */}
        <div className="flex flex-col gap-3">
          <Button
            size="lg"
            className="w-full font-bold tracking-wide"
            onClick={() => router.push(`/t/${publicCode}/queue`)}
          >
            LIVE QUEUE DEKHEIN
          </Button>

          {/* Copy / Bookmark hint */}
          <Button
            variant="secondary"
            size="sm"
            onClick={handleCopyLink}
            className="w-full text-xs font-medium"
          >
            {copied ? "Link Copied! ✓" : "Copy Token Link"}
          </Button>

          {/* Cancel Option (W-005) */}
          {canCancel && !isCancelled && !showCancelDialog && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowCancelDialog(true)}
              className="w-full text-xs text-status-danger hover:bg-status-danger/10"
            >
              Token Cancel Karein
            </Button>
          )}

          {/* Cancel Confirmation Dialog */}
          {showCancelDialog && (
            <div className="p-4 rounded-lg bg-status-danger/10 border border-status-danger/30 text-center space-y-3">
              <p className="text-xs font-semibold text-status-danger">
                Kya aap waqai apna token cancel karna chahte hain?
              </p>
              <div className="flex gap-2">
                <Button
                  variant="secondary"
                  size="sm"
                  className="flex-1 text-xs"
                  onClick={() => setShowCancelDialog(false)}
                  disabled={cancelling}
                >
                  Wapis
                </Button>
                <Button
                  variant="danger"
                  size="sm"
                  className="flex-1 text-xs"
                  onClick={handleCancel}
                  disabled={cancelling}
                >
                  {cancelling ? "Cancelling..." : "Haan, Cancel Karo"}
                </Button>
              </div>
            </div>
          )}

          {isCancelled && (
            <div className="p-3 rounded-lg bg-status-danger/10 border border-status-danger/20 text-center">
              <p className="text-xs font-semibold text-status-danger">
                Yeh token cancel ho chuka hai.
              </p>
            </div>
          )}
        </div>
      </div>
    </main>
  );
}
