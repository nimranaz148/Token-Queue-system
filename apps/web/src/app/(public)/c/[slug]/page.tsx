"use client";

import React, { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ArrowRight, Check, Clock3, ShieldCheck, Stethoscope } from "lucide-react";

interface DoctorSchedule {
  weekday: number;
  start_time: string;
  end_time: string;
}

interface Doctor {
  id: string;
  name: string;
  specialty?: string;
  daily_online_limit?: number;
  consult_minutes?: number;
  schedules?: DoctorSchedule[];
}

interface ClinicInfo {
  id: string;
  name: string;
  slug: string;
  time_zone: string;
  address?: string;
  phone?: string;
  online_booking_enabled: boolean;
  doctors: Doctor[];
}

export default function TokenBookingPage(): React.ReactElement {
  const params = useParams();
  const router = useRouter();
  const slug = params?.slug as string;

  const [clinic, setClinic] = useState<ClinicInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [existingTokenUrl, setExistingTokenUrl] = useState<string | null>(null);

  // Form states
  const [doctorId, setDoctorId] = useState<string>("");
  const [visitDate, setVisitDate] = useState<string>("today");
  const [patientName, setPatientName] = useState<string>("");
  const [phone, setPhone] = useState<string>("");
  const [turnstileToken] = useState<string>(
    "1x0000000000000000000000000000000AA"
  );

  const formatLocalDate = (d: Date): string => {
    const year = d.getFullYear();
    const month = String(d.getMonth() + 1).padStart(2, "0");
    const day = String(d.getDate()).padStart(2, "0");
    return `${year}-${month}-${day}`;
  };

  const todayStr = formatLocalDate(new Date());
  const tomorrowDate = new Date();
  tomorrowDate.setDate(tomorrowDate.getDate() + 1);
  const tomorrowStr = formatLocalDate(tomorrowDate);

  useEffect(() => {
    if (!slug) return;
    const fetchClinic = async (): Promise<void> => {
      try {
        const res = await fetch(`/api/v1/public/clinics/${slug}`);
        if (!res.ok) {
          throw new Error("Clinic not found or inactive");
        }
        const data: ClinicInfo = await res.json();
        setClinic(data);
        if (data.doctors && data.doctors.length > 0) {
          setDoctorId(data.doctors[0].id);
        }
      } catch (err: unknown) {
        const message = err instanceof Error ? err.message : "Failed to load clinic information";
        setError(message);
      } finally {
        setLoading(false);
      }
    };
    void fetchClinic();
  }, [slug]);

  const handleSubmit = async (e: React.FormEvent): Promise<void> => {
    e.preventDefault();
    setError(null);
    setExistingTokenUrl(null);

    if (!doctorId) {
      setError("Please select a doctor.");
      return;
    }
    if (!patientName.trim() || patientName.trim().length < 2) {
      setError("Patient name must be at least 2 characters.");
      return;
    }
    if (!phone.trim() || phone.replace(/\D/g, "").length < 10) {
      setError("Please enter a valid phone number (at least 10 digits).");
      return;
    }

    setSubmitting(true);
    const selectedDate = visitDate === "today" ? todayStr : tomorrowStr;

    try {
      const res = await fetch(`/api/v1/public/clinics/${slug}/tokens`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Idempotency-Key": `web-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`,
        },
        body: JSON.stringify({
          doctor_id: doctorId,
          visit_date: selectedDate,
          patient_name: patientName.trim(),
          phone: phone.trim(),
          turnstile_token: turnstileToken,
        }),
      });

      const data = await res.json();

      if (!res.ok) {
        if (res.status === 409 && data.code === "ACTIVE_TOKEN_EXISTS") {
          setError(data.detail || "An active token already exists for today.");
          if (data.existing_token_url) {
            setExistingTokenUrl(data.existing_token_url);
          }
          return;
        }
        throw new Error(data.detail || "Token booking failed. Please try again.");
      }

      // Success: redirect to F-002 Token Confirm
      router.push(`/t/${data.public_code}`);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Network error. Please try again.";
      setError(message);
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center p-4 bg-surface-sunken">
        <div className="text-sm font-medium text-fg-muted">Loading clinic details...</div>
      </div>
    );
  }

  const isBookingClosed = clinic && !clinic.online_booking_enabled;

  return (
    <main className="min-h-screen bg-canvas px-4 py-5 sm:px-6 sm:py-8 lg:px-10">
      <div className="mx-auto max-w-6xl">
        <header className="mb-8 flex items-center justify-between sm:mb-12">
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-lg bg-accent text-fg-inverse shadow-sm"><Stethoscope className="h-5 w-5" aria-hidden="true" /></div>
            <div><p className="text-sm font-semibold tracking-tight text-fg">{clinic?.name || "Clinic Token Booking"}</p><p className="mt-0.5 text-2xs font-semibold uppercase tracking-[0.18em] text-fg-muted">OPD · online token</p></div>
          </div>
          <div className="hidden items-center gap-2 rounded-full border border-accent-border bg-surface px-3 py-1.5 text-xs font-medium text-accent sm:flex"><span className="h-1.5 w-1.5 rounded-full bg-success" />Patient booking</div>
        </header>
        <div className="grid items-start gap-8 lg:grid-cols-[0.9fr_1.1fr] lg:gap-16">
          <section className="pt-1 sm:pt-4" aria-label="How token booking works">
          <div className="mb-5 inline-flex items-center gap-2 text-2xs font-semibold uppercase tracking-[0.2em] text-accent"><span className="h-px w-7 bg-accent" />Aasan clinic visit</div>
          <h1 className="max-w-xl font-display text-4xl leading-[1.08] tracking-[-0.04em] text-fg sm:text-5xl lg:text-5xl">Apna token lein.<br /><span className="text-accent">Bari phone par dekhein.</span></h1>
          <p className="mt-5 max-w-md text-sm leading-6 text-fg-muted sm:text-base sm:leading-7">Doctor aur din chunein, token book karein, aur clinic aane se pehle live queue ka haal jaan lein.</p>
          <div className="mt-8 grid gap-3 sm:grid-cols-3 lg:grid-cols-1">
            {[
              { number: "01", title: "Doctor chunein", detail: "Apni OPD select karein" },
              { number: "02", title: "Token confirm karein", detail: "Apna number foran paayein" },
              { number: "03", title: "Queue follow karein", detail: "Phone par live update dekhein" },
            ].map((step) => (
              <div key={step.number} className="flex items-center gap-3 rounded-lg border border-border bg-surface/70 p-3 sm:p-3.5">
                <span className="font-mono text-2xs font-semibold tracking-widest text-accent">{step.number}</span>
                <div className="min-w-0"><p className="text-xs font-semibold text-fg">{step.title}</p><p className="mt-0.5 text-2xs text-fg-muted">{step.detail}</p></div>
                <Check className="ml-auto h-4 w-4 shrink-0 text-success" aria-hidden="true" />
              </div>
            ))}
          </div>
          <div className="mt-6 hidden items-center gap-3 border-t border-border pt-5 text-xs text-fg-muted sm:flex"><div className="flex h-9 w-9 items-center justify-center rounded-full bg-accent-subtle text-accent"><Clock3 className="h-4 w-4" aria-hidden="true" /></div><span>Clinic aane se pehle apni bari ka andaza rakhein.</span><ArrowRight className="ml-auto h-4 w-4 text-accent" aria-hidden="true" /></div>
        </section>
          <section className="rounded-lg border border-border bg-surface p-5 shadow-lg sm:rounded-lg sm:p-8 lg:p-8" aria-labelledby="booking-title">
        <div className="mb-6 flex items-start justify-between gap-4 border-b border-border pb-5">
          <div>
            <p className="text-2xs font-semibold uppercase tracking-[0.2em] text-accent">Aaj ya kal</p>
            <h2 id="booking-title" className="mt-2 font-display text-3xl tracking-tight text-fg">Token book karein</h2>
            <p className="mt-1 text-xs leading-5 text-fg-muted">Apni maloomat likhein — token link aap ko foran mil jayega.</p>
          </div>
          <div className="hidden h-10 w-10 items-center justify-center rounded-lg bg-accent-subtle text-accent sm:flex">
            <Stethoscope className="h-5 w-5" aria-hidden="true" />
          </div>
        </div>

        {/* Booking closed banner */}
        {isBookingClosed && (
          <div className="mb-6 rounded-lg border border-danger-border bg-danger-subtle p-4 text-center">
            <p className="text-sm font-semibold text-danger">Booking Band Hai</p>
            <p className="text-xs text-danger mt-1">
              Online booking is currently disabled for this clinic.
            </p>
          </div>
        )}

        {/* Error message */}
        {error && (
          <div className="mb-6 rounded-lg border border-danger-border bg-danger-subtle p-3 text-xs text-danger">
            <p>{error}</p>
            {existingTokenUrl && (
              <Button
                variant="secondary"
                size="sm"
                className="mt-2 w-full text-xs font-medium"
                onClick={() => router.push(existingTokenUrl)}
              >
                View Existing Token
              </Button>
            )}
          </div>
        )}

        {/* Booking Form (F-001) */}
        {!isBookingClosed && (
          <form onSubmit={handleSubmit} className="flex flex-col gap-5">
            {/* 1. Doctor Select */}
            <div className="flex flex-col gap-1.5">
              <label htmlFor="doctor-select" className="text-xs font-semibold text-fg">
                Doctor / OPD
              </label>
              <select
                id="doctor-select"
                aria-label="Doctor / OPD"
                className="w-full rounded-md border border-border bg-surface px-3 py-2.5 text-sm text-fg focus:outline-none focus:ring-2 focus:ring-border-focus"
                value={doctorId}
                onChange={(e) => setDoctorId(e.target.value)}
                required
              >
                {clinic?.doctors.map((doc) => (
                  <option key={doc.id} value={doc.id}>
                    {doc.name} {doc.specialty ? `(${doc.specialty})` : ""}
                  </option>
                ))}
              </select>
            </div>

            {/* 2. Visit Date Radio (Aaj / Kal) */}
            <fieldset className="flex flex-col gap-1.5">
              <legend className="text-xs font-semibold text-fg">Visit Date (Aaj / Kal)</legend>
              <div className="grid grid-cols-2 gap-3">
                <label
                  className={`flex items-center justify-center gap-2 p-2.5 rounded-lg border text-sm font-medium cursor-pointer transition-colors ${
                    visitDate === "today"
                      ? "border-accent bg-accent-subtle text-accent font-semibold"
                      : "border-border bg-surface text-fg-muted hover:bg-surface-hover"
                  }`}
                >
                  <input
                    type="radio"
                    name="visit_date"
                    value="today"
                    checked={visitDate === "today"}
                    onChange={() => setVisitDate("today")}
                    className="sr-only"
                  />
                  <span>Aaj (Today)</span>
                </label>
                <label
                  className={`flex items-center justify-center gap-2 p-2.5 rounded-lg border text-sm font-medium cursor-pointer transition-colors ${
                    visitDate === "tomorrow"
                      ? "border-accent bg-accent-subtle text-accent font-semibold"
                      : "border-border bg-surface text-fg-muted hover:bg-surface-hover"
                  }`}
                >
                  <input
                    type="radio"
                    name="visit_date"
                    value="tomorrow"
                    checked={visitDate === "tomorrow"}
                    onChange={() => setVisitDate("tomorrow")}
                    className="sr-only"
                  />
                  <span>Kal (Tomorrow)</span>
                </label>
              </div>
            </fieldset>

            {/* 3. Patient Name */}
            <div className="flex flex-col gap-1.5">
              <label htmlFor="patient-name" className="text-xs font-semibold text-fg">
                Patient Name
              </label>
              <Input
                id="patient-name"
                placeholder="e.g. Muhammad Ali"
                value={patientName}
                onChange={(e) => setPatientName(e.target.value)}
                minLength={2}
                maxLength={60}
                required
              />
            </div>

            {/* 4. Phone Number */}
            <div className="flex flex-col gap-1.5">
              <label htmlFor="phone" className="text-xs font-semibold text-fg">
                Phone Number (+92 E.164)
              </label>
              <Input
                id="phone"
                type="tel"
                placeholder="0300 1234567"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                required
              />
              <span className="text-2xs text-fg-muted">
                Queue updates will be available on your token link.
              </span>
            </div>

            {/* 5. Turnstile Security Note */}
            <div className="p-2.5 rounded-md bg-surface-sunken border border-border flex items-center justify-between text-2xs text-fg-muted">
              <span>Cloudflare Turnstile Verified</span>
              <span className="inline-flex items-center gap-1.5 font-semibold text-success"><ShieldCheck className="h-3.5 w-3.5" aria-hidden="true" />Protected</span>
            </div>

            {/* 6. Primary Action: TOKEN LO */}
            <Button
              type="submit"
              size="lg"
              className="w-full font-bold tracking-wide mt-2"
              disabled={submitting}
            >
              {submitting ? "TOKEN ISSUING..." : "TOKEN LO"}
            </Button>
          </form>
        )}
        </section>
        </div>
        <footer className="mx-auto mt-8 max-w-6xl border-t border-border pt-4 text-center text-2xs text-fg-muted sm:mt-10">Online OPD token booking · Live queue updates on your token link.</footer>
      </div>
    </main>
  );
}
