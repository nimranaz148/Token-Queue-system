"use client";

import React, { useState, useEffect, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { StatusBadge } from "@/components/ui/status-badge";

interface QueueTokenDetails {
  id: string;
  number: number;
  public_code: string;
  status: string;
  source: string;
  visit_date: string;
  doctor_name: string;
  specialty?: string;
  clinic_name: string;
  estimated_at?: string;
  people_ahead: number;
  estimated_wait_minutes: number;
  current_serving_number?: number;
  created_at: string;
}

export default function LiveQueuePage(): React.ReactElement {
  const params = useParams();
  const router = useRouter();
  const publicCode = params?.public_code as string;

  const [token, setToken] = useState<QueueTokenDetails | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());
  const [secondsAgo, setSecondsAgo] = useState<number>(0);
  const [reminderEnabled, setReminderEnabled] = useState(false);

  const fetchQueueData = useCallback(async (): Promise<void> => {
    if (!publicCode) return;
    try {
      const res = await fetch(`/api/v1/public/tokens/${publicCode}`);
      if (!res.ok) {
        throw new Error("Unable to fetch live queue data.");
      }
      const data: QueueTokenDetails = await res.json();
      setToken(data);
      setLastUpdated(new Date());
      setSecondsAgo(0);
      setError(null);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Error connecting to queue.";
      setError(message);
    } finally {
      setLoading(false);
    }
  }, [publicCode]);

  useEffect(() => {
    void fetchQueueData();
    // Auto refresh every 5 seconds per PRD live queue requirements
    const interval = setInterval(() => {
      void fetchQueueData();
    }, 5000);
    return () => clearInterval(interval);
  }, [fetchQueueData]);

  // Tick the "seconds ago" clock
  useEffect(() => {
    const timer = setInterval(() => {
      const diff = Math.floor((Date.now() - lastUpdated.getTime()) / 1000);
      setSecondsAgo(diff);
    }, 1000);
    return () => clearInterval(timer);
  }, [lastUpdated]);

  const handleReminderToggle = (): void => {
    if (!reminderEnabled && typeof window !== "undefined" && "Notification" in window) {
      if (Notification.permission === "default") {
        void Notification.requestPermission();
      }
    }
    setReminderEnabled((prev) => !prev);
  };

  if (loading) {
    return (
      <main className="flex min-h-screen items-center justify-center p-4 bg-surface-sunken">
        <div className="text-sm font-medium text-fg-muted">Loading live queue...</div>
      </main>
    );
  }

  if (error && !token) {
    return (
      <main className="flex min-h-screen flex-col items-center justify-center p-4 bg-surface-sunken">
        <div className="w-full max-w-[420px] bg-surface rounded-xl border border-border p-6 text-center shadow-sm">
          <p className="text-sm font-semibold text-status-danger">{error}</p>
          <Button
            variant="secondary"
            onClick={() => router.push(`/t/${publicCode}`)}
            className="mt-4 w-full"
          >
            Back to Token
          </Button>
        </div>
      </main>
    );
  }

  const isStale = secondsAgo > 60;

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-4 bg-surface-sunken">
      <div className="w-full max-w-[440px] bg-surface rounded-xl border border-border shadow-sm p-6 sm:p-8">
        {/* Header (F-003) */}
        <div className="flex items-center justify-between pb-4 border-b border-border mb-6">
          <div>
            <h1 className="text-lg font-bold text-fg tracking-tight">Live Queue</h1>
            <p className="text-xs text-fg-muted">{token?.clinic_name || "Clinic"}</p>
          </div>
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-status-success/10 text-status-success text-xs font-semibold">
            <span className="w-2 h-2 rounded-full bg-status-success animate-pulse" />
            <span>LIVE</span>
          </div>
        </div>

        {/* Stale warning banner */}
        {isStale && (
          <div className="mb-4 p-3 rounded-lg bg-status-warning/10 border border-status-warning/30 text-xs text-status-warning text-center">
            ⚠️ Connection slow. Last updated {secondsAgo}s ago. Reconnecting...
          </div>
        )}

        {/* Main Queue Dashboard Card */}
        <div className="grid grid-cols-2 gap-3 mb-6">
          {/* Current Serving */}
          <div className="p-4 rounded-xl bg-status-info/10 border border-status-info/20 text-center flex flex-col justify-center">
            <span className="text-[11px] font-semibold text-status-info uppercase tracking-wider">
              Abhi Chal Raha
            </span>
            <span className="text-3xl font-black text-status-info font-mono my-1">
              {token?.current_serving_number ? `#${token.current_serving_number}` : "—"}
            </span>
            <span className="text-[10px] text-fg-muted">Current Serving</span>
          </div>

          {/* My Token */}
          <div className="p-4 rounded-xl bg-accent/10 border border-accent/20 text-center flex flex-col justify-center">
            <span className="text-[11px] font-semibold text-accent uppercase tracking-wider">
              Apna Token
            </span>
            <span className="text-3xl font-black text-accent font-mono my-1">
              #{token?.number}
            </span>
            <span className="text-[10px] text-fg-muted">Your Position</span>
          </div>
        </div>

        {/* Detailed Wait Metrics */}
        <div className="space-y-3 mb-6 bg-surface-sunken p-4 rounded-xl border border-border text-sm">
          <div className="flex justify-between items-center">
            <span className="text-fg-muted text-xs">Doctor</span>
            <span className="font-semibold text-fg">
              {token?.doctor_name}
              {token?.specialty ? ` (${token.specialty})` : ""}
            </span>
          </div>

          <div className="flex justify-between items-center">
            <span className="text-fg-muted text-xs">People Ahead</span>
            <span className="font-bold text-fg font-mono">
              {token?.people_ahead ?? 0} log
            </span>
          </div>

          <div className="flex justify-between items-center">
            <span className="text-fg-muted text-xs">Estimated Wait Time</span>
            <span className="font-bold text-accent font-mono">
              ~{token?.estimated_wait_minutes ?? 0} mins
            </span>
          </div>

          <div className="flex justify-between items-center pt-2 border-t border-border">
            <span className="text-fg-muted text-xs">Token Status</span>
            <StatusBadge
              variant={token?.status === "serving" ? "info" : "neutral"}
            >
              {token?.status?.toUpperCase() || "BOOKED"}
            </StatusBadge>
          </div>
        </div>

        {/* Live status line */}
        <div className="flex items-center justify-between text-[11px] text-fg-muted mb-6 px-1">
          <span>Auto-refreshes every 5s</span>
          <span>Updated {secondsAgo}s ago</span>
        </div>

        {/* Browser Reminder Switch (P2) */}
        <div className="p-3 rounded-lg bg-surface-sunken border border-border flex items-center justify-between mb-5">
          <div className="flex flex-col">
            <span className="text-xs font-semibold text-fg">Browser Reminder</span>
            <span className="text-[10px] text-fg-muted">
              Notify me when 3 people ahead
            </span>
          </div>
          <button
            type="button"
            role="switch"
            aria-label="Browser queue reminder"
            aria-checked={reminderEnabled}
            onClick={handleReminderToggle}
            className={`w-10 h-5 flex items-center rounded-full p-1 cursor-pointer transition-colors ${
              reminderEnabled ? "bg-accent justify-end" : "bg-neutral-muted justify-start"
            }`}
          >
            <div className="bg-surface w-3.5 h-3.5 rounded-full shadow-md" />
          </button>
        </div>

        {/* Navigation Action */}
        <div className="flex gap-2">
          <Button
            variant="secondary"
            className="w-full"
            onClick={() => router.push(`/t/${publicCode}`)}
          >
            Apna Token Slip
          </Button>
        </div>
      </div>
    </main>
  );
}
