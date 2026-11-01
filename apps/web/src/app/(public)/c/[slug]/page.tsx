"use client";

import React, { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

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

  const todayStr = new Date().toISOString().split("T")[0];
  const tomorrowDate = new Date();
  tomorrowDate.setDate(tomorrowDate.getDate() + 1);
  const tomorrowStr = tomorrowDate.toISOString().split("T")[0];

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
    <main className="flex min-h-screen flex-col items-center justify-center p-4 bg-surface-sunken">
      <div className="w-full max-w-[440px] bg-surface rounded-xl border border-border shadow-sm p-6 sm:p-8">
        {/* Header */}
        <div className="text-center pb-6 border-b border-border mb-6">
          <span className="text-2xl mb-1 block" role="img" aria-label="clinic logo">
            🏥
          </span>
          <h1 className="text-xl font-bold text-fg tracking-tight">
            {clinic?.name || "Clinic Token Booking"}
          </h1>
          <p className="text-xs text-fg-muted mt-1">Online OPD Token Booking</p>
        </div>

        {/* Booking closed banner */}
        {isBookingClosed && (
          <div className="mb-6 p-4 rounded-lg bg-status-danger/10 border border-status-danger/20 text-center">
            <p className="text-sm font-semibold text-status-danger">Booking Band Hai</p>
            <p className="text-xs text-status-danger/80 mt-1">
              Online booking is currently disabled for this clinic.
            </p>
          </div>
        )}

        {/* Error message */}
        {error && (
          <div className="mb-6 p-3 rounded-lg bg-status-danger/10 border border-status-danger/20 text-xs text-status-danger">
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
                className="w-full rounded-md border border-border bg-surface px-3 py-2 text-sm text-fg focus:outline-none focus:ring-2 focus:ring-accent"
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
                      ? "border-accent bg-accent/10 text-accent font-semibold"
                      : "border-border bg-surface text-fg-muted hover:bg-surface-sunken"
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
                      ? "border-accent bg-accent/10 text-accent font-semibold"
                      : "border-border bg-surface text-fg-muted hover:bg-surface-sunken"
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
              <span className="text-[11px] text-fg-muted">
                SMS and queue updates will be sent to this number.
              </span>
            </div>

            {/* 5. Turnstile Security Note */}
            <div className="p-2.5 rounded-md bg-surface-sunken border border-border flex items-center justify-between text-[11px] text-fg-muted">
              <span>Cloudflare Turnstile Verified</span>
              <span className="text-status-success font-semibold">✓ Protected</span>
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
      </div>
    </main>
  );
}
