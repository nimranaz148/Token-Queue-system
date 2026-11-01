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
  ArrowLeft,
  CheckCircle,
  Clock,
  Filter,
  PlusCircle,
  Printer,
  UserCheck,
} from "lucide-react";

export interface DoctorOption {
  id: string;
  name: string;
  specialty?: string | null;
  daily_online_limit?: number | null;
}

export interface CreatedWalkInToken {
  id: string;
  number: number;
  public_code: string;
  status: string;
  source: string;
  patient_id: string;
  patient_name: string;
  phone: string;
  doctor_id: string;
  doctor_name: string;
  visit_date: string;
  position: number;
  arrived_at: string;
  created_at: string;
}

interface WalkInPageProps {
  initialDoctors?: DoctorOption[];
  userRole?: string;
}

export default function WalkInEntryPage({
  initialDoctors = [],
  userRole = "reception",
}: WalkInPageProps) {
  const [doctors, setDoctors] = React.useState<DoctorOption[]>(initialDoctors);
  const [phone, setPhone] = React.useState("");
  const [patientName, setPatientName] = React.useState("");
  const [doctorId, setDoctorId] = React.useState("");
  const [existingPatientId, setExistingPatientId] = React.useState<string | null>(null);
  const [ignoreDailyLimit, setIgnoreDailyLimit] = React.useState(false);

  // Status & submission state
  const [isSubmitting, setIsSubmitting] = React.useState(false);
  const [formError, setFormError] = React.useState<string | null>(null);
  const [createdToken, setCreatedToken] = React.useState<CreatedWalkInToken | null>(null);

  // Autocomplete feedback
  const [patientFoundMessage, setPatientFoundMessage] = React.useState<string | null>(null);

  // Load doctors if not passed
  React.useEffect(() => {
    async function fetchDoctors() {
      try {
        const res = await fetch("/api/v1/doctors");
        if (res.ok) {
          const data = await res.json();
          const items = Array.isArray(data) ? data : data.items || [];
          setDoctors(items);
          if (items.length > 0 && !doctorId) {
            setDoctorId(items[0].id);
          }
        }
      } catch {
        // Non-blocking
      }
    }
    if (initialDoctors.length === 0) {
      fetchDoctors();
    } else if (!doctorId && initialDoctors.length > 0) {
      setDoctorId(initialDoctors[0].id);
    }
  }, [initialDoctors, doctorId]);

  // Phone lookup autocomplete
  const handlePhoneBlur = async () => {
    const cleanPhone = phone.trim();
    if (cleanPhone.length < 8) return;

    try {
      const res = await fetch(`/api/v1/patients?query=${encodeURIComponent(cleanPhone)}`);
      if (res.ok) {
        const data = await res.json();
        const matches = Array.isArray(data) ? data : data.items || [];
        if (matches.length > 0) {
          const matched = matches[0];
          setPatientName(matched.name);
          setExistingPatientId(matched.id);
          setPatientFoundMessage(`Pehly se mojood mareez mil gaya: ${matched.name}`);
        } else {
          setExistingPatientId(null);
          setPatientFoundMessage(null);
        }
      }
    } catch {
      // Non-blocking lookup failure
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);

    // Client-side validations (PRD §5.3 F-005)
    if (!phone.trim() || phone.trim().length < 7) {
      setFormError("Sahih phone number likhein (kam az kam 7 digits).");
      return;
    }
    if (!patientName.trim() || patientName.trim().length < 2 || patientName.trim().length > 60) {
      setFormError("Mareez ka naam 2 se 60 characters ke darmiyan hona chahiye.");
      return;
    }
    if (!doctorId) {
      setFormError("Doctor ka intekhab zaroori hai.");
      return;
    }

    setIsSubmitting(true);
    try {
      const payload = {
        doctor_id: doctorId,
        patient_name: patientName.trim(),
        phone: phone.trim(),
        existing_patient_id: existingPatientId,
        ignore_daily_limit: ignoreDailyLimit,
      };

      const res = await fetch("/api/v1/tokens", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Walk-in token banane mein masla pesh aya.");
      }

      const data: CreatedWalkInToken = await res.json();
      setCreatedToken(data);
    } catch (err: any) {
      setFormError(err.message || "Failed to create token. Dobara koshish karein.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleReset = () => {
    setCreatedToken(null);
    setPhone("");
    setPatientName("");
    setExistingPatientId(null);
    setIgnoreDailyLimit(false);
    setFormError(null);
    setPatientFoundMessage(null);
  };

  return (
    <RoleGuard allowedRoles={["reception", "owner"]}>
      <LayoutShell
        userRole={userRole}
        navItems={[
          { label: "Aaj ki List", href: "/tokens", icon: <Clock className="w-4 h-4" /> },
          { label: "Walk-in Entry", href: "/tokens/walk-in", icon: <CheckCircle className="w-4 h-4" />, active: true },
          { label: "Patients", href: "/patients", icon: <Filter className="w-4 h-4" /> },
        ]}
      >
        <div className="max-w-4xl mx-auto space-y-6">
          {/* Header */}
          <div className="flex items-center justify-between pb-4 border-b border-border">
            <div>
              <div className="flex items-center gap-2">
                <Link
                  href="/tokens"
                  className="text-fg-muted hover:text-fg p-1 rounded-md transition-colors"
                  aria-label="Back to Aaj ki List"
                >
                  <ArrowLeft className="w-5 h-5" />
                </Link>
                <h1 className="text-2xl font-bold tracking-tight text-fg">Walk-in Entry</h1>
                <span className="text-xs font-semibold px-2 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20 uppercase">
                  F-005
                </span>
              </div>
              <p className="text-sm text-fg-muted mt-1 ml-7">
                Clinic mein mojood mareez ka naya token banayein (Direct Walk-in Token)
              </p>
            </div>
            <Link href="/tokens">
              <Button variant="secondary" size="sm">
                Aaj ki List
              </Button>
            </Link>
          </div>

          {/* Form and Result Grid */}
          <div className="grid grid-cols-1 md:grid-cols-12 gap-6 items-start">
            {/* Form Section */}
            <div className="md:col-span-7 bg-surface border border-border rounded-lg p-6 space-y-5">
              <h2 className="text-base font-semibold text-fg flex items-center gap-2">
                <PlusCircle className="w-4 h-4 text-accent" />
                Mareez ki Maloomat (Patient Details)
              </h2>

              {formError && (
                <div className="p-3.5 rounded-md bg-destructive/10 border border-destructive/20 text-destructive text-sm flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 shrink-0" />
                  <span>{formError}</span>
                </div>
              )}

              {patientFoundMessage && (
                <div className="p-3 rounded-md bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs flex items-center gap-2">
                  <UserCheck className="w-4 h-4 shrink-0" />
                  <span>{patientFoundMessage}</span>
                </div>
              )}

              <form onSubmit={handleSubmit} className="space-y-4">
                {/* Phone */}
                <div>
                  <label htmlFor="walkin-phone" className="block text-xs font-medium text-fg-muted mb-1">
                    Phone Number (Mobile) <span className="text-destructive">*</span>
                  </label>
                  <Input
                    id="walkin-phone"
                    type="tel"
                    placeholder="e.g. 03001234567 ya +923001234567"
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    onBlur={handlePhoneBlur}
                    required
                    aria-label="Phone"
                  />
                  <p className="text-xs text-fg-muted mt-1">Phone number likh kar bahir click karein to naam khud ba khud aa jaye ga.</p>
                </div>

                {/* Patient Name */}
                <div>
                  <label htmlFor="walkin-name" className="block text-xs font-medium text-fg-muted mb-1">
                    Mareez ka Naam (Patient Name) <span className="text-destructive">*</span>
                  </label>
                  <Input
                    id="walkin-name"
                    type="text"
                    placeholder="2-60 characters (e.g. Muhammad Usman)"
                    value={patientName}
                    onChange={(e) => setPatientName(e.target.value)}
                    required
                    aria-label="Patient Name"
                  />
                </div>

                {/* Doctor Selection */}
                <div>
                  <label htmlFor="walkin-doctor" className="block text-xs font-medium text-fg-muted mb-1">
                    Doctor ka Intekhab (Select Doctor) <span className="text-destructive">*</span>
                  </label>
                  <select
                    id="walkin-doctor"
                    value={doctorId}
                    onChange={(e) => setDoctorId(e.target.value)}
                    required
                    className="w-full h-8.5 px-3 py-1 bg-surface-raised border border-border rounded-md text-sm text-fg focus:outline-none focus:ring-1 focus:ring-accent"
                    aria-label="Doctor"
                  >
                    <option value="">Doctor muntakhib karein</option>
                    {doctors.map((doc) => (
                      <option key={doc.id} value={doc.id}>
                        {doc.name} {doc.specialty ? `(${doc.specialty})` : ""}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Ignore Daily Limit Checkbox */}
                <div className="pt-2">
                  <label className="flex items-start gap-2.5 cursor-pointer text-xs text-fg select-none">
                    <input
                      type="checkbox"
                      checked={ignoreDailyLimit}
                      onChange={(e) => setIgnoreDailyLimit(e.target.checked)}
                      className="mt-0.5 rounded border-border text-accent focus:ring-accent"
                      aria-label="Ignore Daily Limit"
                    />
                    <div>
                      <span className="font-medium">Ignore Daily Limit (Rozana had se ziyada token)</span>
                      <p className="text-fg-muted text-xs mt-0.5">
                        Agar doctor ki rozana online limit poori ho chuki ho to ye tick kar ke token banaya ja sakta hai (audited).
                      </p>
                    </div>
                  </label>
                </div>

                <div className="pt-4 border-t border-border">
                  <Button
                    type="submit"
                    variant="primary"
                    disabled={isSubmitting}
                    className="w-full h-10 text-sm font-semibold tracking-wide"
                  >
                    {isSubmitting ? "TOKEN BAN RAHA HAI..." : "TOKEN BANAO"}
                  </Button>
                </div>
              </form>
            </div>

            {/* Result Section */}
            <div className="md:col-span-5 bg-surface border border-border rounded-lg p-6 space-y-5 text-center">
              <h2 className="text-base font-semibold text-fg">
                Naya Token (Generated Slip)
              </h2>

              {createdToken ? (
                <div className="space-y-5 animate-in fade-in zoom-in-95 duration-200">
                  <div className="p-6 rounded-lg bg-surface-raised border border-accent/30 space-y-3">
                    <span className="text-xs font-semibold text-accent uppercase tracking-wider">
                      Walk-in Token Issued
                    </span>
                    <div className="text-5xl font-black tracking-tight text-accent font-mono">
                      #{createdToken.number}
                    </div>
                    <div className="space-y-1 pt-2 border-t border-border text-xs text-left">
                      <div className="flex justify-between">
                        <span className="text-fg-muted">Mareez:</span>
                        <span className="font-semibold text-fg">{createdToken.patient_name}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-fg-muted">Doctor:</span>
                        <span className="font-semibold text-fg">{createdToken.doctor_name}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-fg-muted">Halat (Status):</span>
                        <StatusBadge variant="info">ARRIVED</StatusBadge>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-fg-muted">Source:</span>
                        <span className="font-mono text-fg">WALK-IN</span>
                      </div>
                    </div>
                  </div>

                  <div className="flex gap-2">
                    <Button
                      variant="secondary"
                      className="flex-1"
                      onClick={() => window.print()}
                    >
                      <Printer className="w-4 h-4 mr-1.5" />
                      Print Slip
                    </Button>
                    <Button
                      variant="primary"
                      className="flex-1"
                      onClick={handleReset}
                    >
                      <PlusCircle className="w-4 h-4 mr-1.5" />
                      Agla Token
                    </Button>
                  </div>
                </div>
              ) : (
                <div className="py-14 text-fg-muted space-y-3">
                  <div className="w-16 h-16 rounded-full bg-surface-raised border border-border mx-auto flex items-center justify-center text-fg-muted/40 font-mono text-2xl font-bold">
                    #--
                  </div>
                  <p className="text-sm font-medium text-fg">Koi token generate nahi hua</p>
                  <p className="text-xs text-fg-muted max-w-xs mx-auto">
                    Form bhar kar "TOKEN BANAO" dabayein to yahan token number aur print slip numayan ho gi.
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
