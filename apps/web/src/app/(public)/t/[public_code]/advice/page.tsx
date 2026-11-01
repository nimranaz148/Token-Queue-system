"use client";

import * as React from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import {
  AlertCircle,
  ArrowLeft,
  Calendar,
  Clock,
  Download,
  FileText,
  Lock,
  Pill,
  Printer,
  ShieldCheck,
  Stethoscope,
} from "lucide-react";

export interface SharedVisitAdviceData {
  shared: boolean;
  public_code: string;
  token_number?: number | null;
  visit_date?: string | null;
  doctor_name?: string | null;
  medicines_advice?: string | null;
  message?: string | null;
}

interface AdvicePageProps {
  initialData?: SharedVisitAdviceData;
}

export default function SharedAdvicePage({ initialData }: AdvicePageProps) {
  const params = useParams();
  const publicCode = (params?.public_code as string) || initialData?.public_code;

  const [data, setData] = React.useState<SharedVisitAdviceData | null>(initialData || null);
  const [isLoading, setIsLoading] = React.useState(!initialData);
  const [loadError, setLoadError] = React.useState<string | null>(null);

  React.useEffect(() => {
    async function fetchAdvice() {
      if (!publicCode) return;
      try {
        const res = await fetch(`/api/v1/public/tokens/${publicCode}/advice`);
        if (!res.ok) {
          throw new Error("Prescription advice load karne mein masla pesh aya.");
        }
        const result: SharedVisitAdviceData = await res.json();
        setData(result);
      } catch (err: any) {
        setLoadError(err.message || "Failed to load advice.");
      } finally {
        setIsLoading(false);
      }
    }

    if (!initialData && publicCode) {
      fetchAdvice();
    }
  }, [initialData, publicCode]);

  return (
    <div className="min-h-screen bg-canvas text-fg py-8 px-4 sm:px-6">
      <div className="max-w-xl mx-auto space-y-6">
        {/* Navigation Bar */}
        <div className="flex items-center justify-between pb-3 border-b border-border">
          <Link
            href={`/t/${publicCode}`}
            className="flex items-center gap-1.5 text-xs text-fg-muted hover:text-fg font-medium transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            Wapis Token Par Jayein
          </Link>
          <span className="text-xs font-semibold px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 uppercase">
            F-021
          </span>
        </div>

        {loadError && (
          <div className="p-4 rounded-lg bg-destructive/10 border border-destructive/20 text-destructive text-sm flex items-center gap-2">
            <AlertCircle className="w-5 h-5 shrink-0" />
            <span>{loadError}</span>
          </div>
        )}

        {isLoading ? (
          <div className="py-20 text-center text-fg-muted space-y-2">
            <Clock className="w-8 h-8 mx-auto animate-spin text-accent" />
            <p className="text-sm">Doctor ki hidayat load ho rahi hai...</p>
          </div>
        ) : data && data.shared ? (
          /* Shared Advice Card */
          <div className="bg-surface border border-border rounded-2xl p-6 sm:p-8 space-y-6 shadow-md print:border-none print:shadow-none">
            {/* Header */}
            <div className="text-center space-y-2 pb-5 border-b border-border">
              <div className="w-12 h-12 rounded-full bg-accent/10 border border-accent/20 mx-auto flex items-center justify-center text-accent">
                <Pill className="w-6 h-6" />
              </div>
              <h1 className="text-2xl font-black tracking-tight text-fg">
                Doctor ki Hidayat (Prescription)
              </h1>
              <p className="text-xs text-fg-muted">
                Clinic visit ke doran doctor ki tajweez kardah dawa aur ahtiyati tadabeer
              </p>
            </div>

            {/* Visit Details Meta */}
            <div className="grid grid-cols-2 gap-4 bg-surface-raised p-4 rounded-xl text-xs">
              <div>
                <span className="text-fg-muted block">Doctor:</span>
                <span className="text-sm font-bold text-fg flex items-center gap-1 mt-0.5">
                  <Stethoscope className="w-3.5 h-3.5 text-accent" />
                  {data.doctor_name || "Doctor"}
                </span>
              </div>
              <div>
                <span className="text-fg-muted block">Tareekh (Visit Date):</span>
                <span className="text-sm font-medium text-fg flex items-center gap-1 mt-0.5">
                  <Calendar className="w-3.5 h-3.5 text-fg-muted" />
                  {data.visit_date || "—"}
                </span>
              </div>
              {data.token_number && (
                <div>
                  <span className="text-fg-muted block">Token Number:</span>
                  <span className="font-mono text-sm font-bold text-accent">
                    #{data.token_number}
                  </span>
                </div>
              )}
              <div>
                <span className="text-fg-muted block">Verified Record:</span>
                <span className="text-emerald-400 font-semibold flex items-center gap-1 mt-0.5">
                  <ShieldCheck className="w-3.5 h-3.5" /> Direct from Doctor
                </span>
              </div>
            </div>

            {/* Medicines & Advice Text */}
            <div className="space-y-2">
              <span className="text-xs font-semibold text-fg-muted uppercase tracking-wider block">
                Dawa aur Hidayat (Medicines & Advice):
              </span>
              <div className="p-4 rounded-xl bg-surface-raised border border-accent/30 text-sm font-mono text-fg whitespace-pre-wrap leading-relaxed">
                {data.medicines_advice}
              </div>
            </div>

            {/* Print & Action Buttons */}
            <div className="flex gap-3 pt-3 border-t border-border print:hidden">
              <Button
                variant="primary"
                className="flex-1 h-11 font-semibold"
                onClick={() => window.print()}
                aria-label="Print or save prescription button"
              >
                <Printer className="w-4 h-4 mr-2" />
                Print / Save as PDF
              </Button>
            </div>
          </div>
        ) : (
          /* Unshared State Message (PRD §5.3 F-021) */
          <div className="bg-surface border border-border rounded-2xl p-8 text-center space-y-4 shadow-sm">
            <div className="w-14 h-14 rounded-full bg-surface-raised border border-border mx-auto flex items-center justify-center text-fg-muted">
              <Lock className="w-6 h-6" />
            </div>
            <div className="space-y-1">
              <h2 className="text-lg font-bold text-fg">Hidayat Dastyab Nahi Hai</h2>
              <p className="text-sm font-medium text-accent">
                {data?.message || "Clinic se rabta karein"}
              </p>
            </div>
            <p className="text-xs text-fg-muted max-w-sm mx-auto leading-relaxed">
              Agar aap ko apna nuskha ya hidayat darkar hain to barah-e-karam reception ya apne doctor se direct rabta karein.
            </p>
            <div className="pt-2">
              <Link href={`/t/${publicCode}`}>
                <Button variant="secondary" size="sm">
                  Token Status Dekhein
                </Button>
              </Link>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
