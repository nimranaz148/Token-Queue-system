"use client";

import React, { useState } from "react";
import { FormShell } from "@/components/form/form-shell";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { StatusBadge } from "@/components/ui/status-badge";

interface ClinicMembership {
  clinic_id: string;
  clinic_name: string;
  role: string;
}

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [emailError, setEmailError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [successMessage, setSuccessMessage] = useState("");
  const [generalError, setGeneralError] = useState("");
  const [memberships, setMemberships] = useState<ClinicMembership[]>([]);
  const [selectedClinicId, setSelectedClinicId] = useState<string>("");

  const validateEmail = (val: string): boolean => {
    if (!val.trim()) {
      setEmailError("Email zaroori hai (Valid email required)");
      return false;
    }
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(val.trim())) {
      setEmailError("Durust email darj karein (Invalid email address)");
      return false;
    }
    setEmailError("");
    return true;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validateEmail(email)) {
      return;
    }

    setIsLoading(true);
    setGeneralError("");
    setSuccessMessage("");

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const res = await fetch(`${apiUrl}/api/v1/auth/magic-link`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: email.trim() }),
      });

      const data = await res.json();

      if (!res.ok) {
        if (res.status === 429) {
          setGeneralError("Bohat ziyada koshishein. 1 ghante mein sirf 5 dafa link mangwa sakte hain.");
        } else {
          setGeneralError(data.detail || "Login link bhaijne mein masla pesh aya.");
        }
        return;
      }

      setSuccessMessage(data.message || "Login link email kar diya");

      if (data.memberships && Array.isArray(data.memberships) && data.memberships.length > 0) {
        setMemberships(data.memberships);
        setSelectedClinicId(data.memberships[0].clinic_id);
      }
    } catch {
      setGeneralError("Network error. Baraye meherbani dobara koshish karein.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <main className="min-h-screen w-full flex items-center justify-center p-4 bg-surface-sunken">
      <div className="w-full max-w-[480px] bg-surface p-6 rounded-xl border border-border shadow-xs">
        <form onSubmit={handleSubmit} noValidate>
          <FormShell
            title="Aapka Clinic"
            badge={<StatusBadge variant="info">Staff Login</StatusBadge>}
            description="Staff portal mein dakhil honay ke liye apna registered email darj karein."
            maxFormWidth={false}
            masterFields={
              <div className="flex flex-col gap-4">
                <Input
                  label="Email"
                  type="email"
                  placeholder="doctor@example.com"
                  value={email}
                  disabled={isLoading}
                  error={emailError}
                  onChange={(e) => {
                    setEmail(e.target.value);
                    if (emailError) validateEmail(e.target.value);
                  }}
                  required
                />

                {successMessage && (
                  <div className="p-3 rounded-md bg-success-subtle border border-success text-success text-sm flex flex-col gap-1">
                    <span className="font-medium">{successMessage}</span>
                    <span className="text-xs opacity-90">
                      Apni email inbox check karein aur magic link par click karein. Link 15 minute ke liye karamad hai.
                    </span>
                  </div>
                )}

                {generalError && (
                  <div className="p-3 rounded-md bg-danger-subtle border border-danger text-danger text-sm">
                    {generalError}
                  </div>
                )}

                {/* Conditional Clinic Choice (PRD §5.3 F-012) */}
                {memberships.length > 1 && (
                  <div className="flex flex-col gap-2 pt-2 border-t border-border">
                    <label className="text-xs font-medium text-fg-muted">
                      Apna clinic muntakhib karein (Select active clinic):
                    </label>
                    <div className="flex flex-col gap-1.5">
                      {memberships.map((m) => (
                        <label
                          key={m.clinic_id}
                          className="flex items-center gap-2 p-2 rounded-md border border-border bg-surface-sunken cursor-pointer hover:border-border-focus"
                        >
                          <input
                            type="radio"
                            name="clinic_choice"
                            value={m.clinic_id}
                            checked={selectedClinicId === m.clinic_id}
                            onChange={() => setSelectedClinicId(m.clinic_id)}
                            className="text-accent focus:ring-accent"
                          />
                          <span className="text-sm font-medium text-fg">{m.clinic_name}</span>
                          <span className="text-xs text-fg-muted ml-auto capitalize">({m.role})</span>
                        </label>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            }
            actions={
              <div className="w-full flex flex-col sm:flex-row gap-2 justify-end">
                {successMessage ? (
                  <Button
                    type="button"
                    variant="secondary"
                    onClick={() => {
                      setSuccessMessage("");
                      setGeneralError("");
                    }}
                  >
                    Dobara Bhejein (Resend)
                  </Button>
                ) : (
                  <Button type="submit" variant="primary" disabled={isLoading} className="w-full sm:w-auto">
                    {isLoading ? "Bheja ja raha hai..." : "Login Link Bhejein"}
                  </Button>
                )}
              </div>
            }
            auditPanel={
              <span>
                Single-use 15-minute link · 5 requests per hour per email · PECA 2016 Compliant
              </span>
            }
          />
        </form>
      </div>
    </main>
  );
}
