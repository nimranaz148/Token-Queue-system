"use client";

import * as React from "react";
import { RoleGuard } from "@/components/auth/role-guard";
import { LayoutShell } from "@/components/layout/layout-shell";
import { Button } from "@/components/ui/button";
import {
  FileText,
  Calendar,
  Sparkles,
  ThumbsUp,
  ThumbsDown,
  AlertTriangle,
  RefreshCw,
  AlertCircle,
  CheckCircle2,
} from "lucide-react";

export interface AnomalyItem {
  type: string;
  doctor?: string;
  wait_min?: number;
  message?: string;
  [key: string]: any;
}

export interface DailyBriefData {
  id: string;
  clinic_id: string;
  date: string;
  body_md: string;
  anomalies: AnomalyItem[] | null;
  feedback: "up" | "down" | null;
  created_at: string;
}

export function DailyBriefView() {
  const [selectedDate, setSelectedDate] = React.useState(
    () => new Date().toISOString().split("T")[0]
  );
  const [brief, setBrief] = React.useState<DailyBriefData | null>(null);
  const [isLoading, setIsLoading] = React.useState(true);
  const [isGenerating, setIsGenerating] = React.useState(false);
  const [isSubmittingFeedback, setIsSubmittingFeedback] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [feedbackSuccess, setFeedbackSuccess] = React.useState(false);

  const fetchBrief = React.useCallback(async (dateToFetch: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await fetch(`/api/v1/ai/daily-brief?date=${dateToFetch}`);
      if (res.status === 404) {
        setBrief(null);
        return;
      }
      if (!res.ok) {
        throw new Error("Daily brief load karne mein masla pesh aya.");
      }
      const data = await res.json();
      setBrief(data);
    } catch (err: any) {
      setError(err.message || "Failed to load brief");
    } finally {
      setIsLoading(false);
    }
  }, []);

  React.useEffect(() => {
    fetchBrief(selectedDate);
  }, [selectedDate, fetchBrief]);

  const handleGenerateBrief = async () => {
    setIsGenerating(true);
    setError(null);
    try {
      const res = await fetch(`/api/v1/ai/daily-brief/generate?date=${selectedDate}`, {
        method: "POST",
      });
      if (!res.ok) {
        throw new Error("Brief generate karne mein masla pesh aya.");
      }
      const data = await res.json();
      setBrief(data);
    } catch (err: any) {
      setError(err.message || "Failed to generate brief");
    } finally {
      setIsGenerating(false);
    }
  };

  const handleFeedback = async (type: "up" | "down") => {
    if (!brief) return;
    setIsSubmittingFeedback(true);
    try {
      const res = await fetch(`/api/v1/ai/daily-brief/${brief.id}/feedback`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ feedback: type }),
      });
      if (!res.ok) throw new Error("Feedback submit nahi ho saka.");
      const updated = await res.json();
      setBrief(updated);
      setFeedbackSuccess(true);
      setTimeout(() => setFeedbackSuccess(false), 3000);
    } catch (err: any) {
      setError(err.message || "Feedback failed");
    } finally {
      setIsSubmittingFeedback(false);
    }
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight">Daily Brief</h1>
            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-mono font-medium bg-accent/10 text-accent">
              F-018
            </span>
          </div>
          <p className="text-sm text-fg-muted mt-1">
            Rozana raat 9:00 baje ka AI tajzia: mareezon ki tadad, wait times, aur operational anomalies.
          </p>
        </div>

        {/* Date Selector & Action */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 bg-surface-raised border border-border px-3 py-1.5 rounded-md">
            <Calendar className="w-4 h-4 text-fg-muted" />
            <input
              type="date"
              aria-label="Tareekh (Date)"
              value={selectedDate}
              onChange={(e) => setSelectedDate(e.target.value)}
              className="bg-transparent text-sm text-fg focus:outline-none"
            />
          </div>
          <Button
            variant="secondary"
            onClick={handleGenerateBrief}
            disabled={isGenerating || isLoading}
            className="gap-2"
          >
            <Sparkles className={`w-4 h-4 text-accent ${isGenerating ? "animate-spin" : ""}`} />
            {isGenerating ? "Tajzia ban raha hai..." : "Naya Tajzia Banao"}
          </Button>
        </div>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="p-4 bg-red-500/10 border border-red-500/30 rounded-lg flex items-center justify-between">
          <div className="flex items-center gap-2 text-red-500">
            <AlertCircle className="w-5 h-5 flex-shrink-0" />
            <p className="text-sm font-medium">{error}</p>
          </div>
          <Button variant="secondary" onClick={() => fetchBrief(selectedDate)} className="text-xs h-8">
            Dobara Koshish
          </Button>
        </div>
      )}

      {/* Content */}
      {isLoading ? (
        <div className="p-16 text-center text-fg-muted flex flex-col items-center gap-3 bg-surface-raised border border-border rounded-lg">
          <RefreshCw className="w-6 h-6 animate-spin text-accent" />
          <p className="text-sm">Daily brief load ho raha hai...</p>
        </div>
      ) : !brief ? (
        <div className="p-16 text-center text-fg-muted flex flex-col items-center gap-4 bg-surface-raised border border-border rounded-lg">
          <FileText className="w-12 h-12 text-fg-muted/40" />
          <div>
            <p className="text-base font-medium text-fg">Is tareekh ka koi daily brief mojood nahi hai</p>
            <p className="text-xs text-fg-muted mt-1 max-w-sm">
              Schedule ke mutabiq yeh har raat 21:00 baje banta hai, ya aap abhi foran naya brief generate kar saktay hain.
            </p>
          </div>
          <Button
            variant="primary"
            onClick={handleGenerateBrief}
            disabled={isGenerating}
            className="gap-2"
          >
            <Sparkles className="w-4 h-4" />
            {isGenerating ? "Tajzia ban raha hai..." : "Abhi Tajzia Generate Karein"}
          </Button>
        </div>
      ) : (
        <div className="space-y-6">
          {/* Main Brief Card */}
          <div className="bg-surface-raised border border-border rounded-lg p-6 space-y-4 shadow-sm">
            <div className="flex items-center justify-between border-b border-border pb-3">
              <div className="flex items-center gap-2">
                <FileText className="w-5 h-5 text-accent" />
                <h2 className="text-lg font-semibold text-fg">Clinic Nightly Summary</h2>
              </div>
              <span className="text-xs text-fg-muted">
                Tareekh: <strong className="text-fg">{brief.date}</strong>
              </span>
            </div>

            {/* Markdown Body */}
            <div className="prose prose-invert max-w-none text-sm text-fg leading-relaxed whitespace-pre-line">
              {brief.body_md}
            </div>

            {/* Anomalies section */}
            {brief.anomalies && brief.anomalies.length > 0 && (
              <div className="mt-6 pt-4 border-t border-border space-y-3">
                <div className="flex items-center gap-2 text-warning">
                  <AlertTriangle className="w-4 h-4" />
                  <h3 className="text-sm font-semibold">Detected Anomalies ({brief.anomalies.length})</h3>
                </div>
                <div className="grid gap-2">
                  {brief.anomalies.map((anom, idx) => (
                    <div
                      key={idx}
                      className="p-3 bg-surface border border-warning/30 rounded-md text-xs flex items-start gap-2"
                    >
                      <span className="inline-block w-2 h-2 rounded-full bg-warning mt-1 flex-shrink-0" />
                      <div>
                        <span className="font-semibold text-fg capitalize">
                          {anom.type ? anom.type.replace(/_/g, " ") : "Notice"}:
                        </span>{" "}
                        <span className="text-fg-muted">
                          {anom.message || (anom.doctor ? `${anom.doctor} wait time was ${anom.wait_min} min` : JSON.stringify(anom))}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Thumbs Feedback */}
            <div className="mt-6 pt-4 border-t border-border flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-xs text-fg-muted">Kya yeh tajzia faida-mand tha? (Feedback):</span>
                {feedbackSuccess && (
                  <span className="text-xs text-success flex items-center gap-1">
                    <CheckCircle2 className="w-3.5 h-3.5" /> Shukriya!
                  </span>
                )}
              </div>
              <div className="flex items-center gap-2">
                <Button
                  variant={brief.feedback === "up" ? "primary" : "secondary"}
                  onClick={() => handleFeedback("up")}
                  disabled={isSubmittingFeedback}
                  className="h-8 px-3 text-xs gap-1.5"
                >
                  <ThumbsUp className="w-3.5 h-3.5" />
                  Haan (Helpful)
                </Button>
                <Button
                  variant={brief.feedback === "down" ? "danger" : "secondary"}
                  onClick={() => handleFeedback("down")}
                  disabled={isSubmittingFeedback}
                  className="h-8 px-3 text-xs gap-1.5"
                >
                  <ThumbsDown className="w-3.5 h-3.5" />
                  Nahi
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default function DailyBriefPage() {
  return (
    <RoleGuard allowedRoles={["owner", "platform_admin"]}>
      <LayoutShell userRole="owner">
        <DailyBriefView />
      </LayoutShell>
    </RoleGuard>
  );
}
