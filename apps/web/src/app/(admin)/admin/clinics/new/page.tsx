"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormShell } from "@/components/form/form-shell";
import { LayoutShell } from "@/components/layout/layout-shell";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { StatusBadge } from "@/components/ui/status-badge";

export default function NewClinicPage() {
  const router = useRouter();
  const [clinicName, setClinicName] = useState("");
  const [slug, setSlug] = useState("");
  const [ownerName, setOwnerName] = useState("");
  const [ownerEmail, setOwnerEmail] = useState("");
  const [ownerPhone, setOwnerPhone] = useState("");
  const [timeZone, setTimeZone] = useState("Asia/Karachi");
  const [status, setStatus] = useState("trial");

  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [apiError, setApiError] = useState("");
  const [successClinic, setSuccessClinic] = useState<{ name: string; slug: string } | null>(null);

  const autoGenerateSlug = (name: string) => {
    return name
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-+|-+$/g, "")
      .slice(0, 40);
  };

  const validate = (): boolean => {
    const errs: Record<string, string> = {};

    if (!clinicName.trim() || clinicName.trim().length < 2) {
      errs.clinicName = "Clinic name 2 se 80 characters ke darmiyan hona chahiye";
    }

    const slugRegex = /^[a-z0-9-]{3,40}$/;
    if (!slug.trim() || !slugRegex.test(slug.trim())) {
      errs.slug = "Slug mein sirf chotay angrezi huroof, numbers aur hyphen (-) ho saktay hain (3-40 chars)";
    }

    if (!ownerName.trim()) {
      errs.ownerName = "Owner ka mukammal naam darj karna zaroori hai";
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!ownerEmail.trim() || !emailRegex.test(ownerEmail.trim())) {
      errs.ownerEmail = "Durust owner email darj karein (Valid email required)";
    }

    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;

    setIsSubmitting(true);
    setApiError("");

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const token = typeof window !== "undefined" ? localStorage.getItem("token") || "" : "";

      const res = await fetch(`${apiUrl}/api/v1/admin/clinics`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          clinic_name: clinicName.trim(),
          slug: slug.trim(),
          owner_name: ownerName.trim(),
          owner_email: ownerEmail.trim(),
          owner_phone: ownerPhone.trim() || undefined,
          time_zone: timeZone,
          status,
        }),
      });

      const data = await res.json();

      if (!res.ok) {
        if (res.status === 409) {
          setErrors((prev) => ({ ...prev, slug: "Yeh slug pehle se kisi doosray clinic ke paas hai" }));
        } else {
          setApiError(data.detail || "Clinic create karne mein masla pesh aya");
        }
        return;
      }

      setSuccessClinic({ name: data.name, slug: data.slug });
    } catch {
      setApiError("Network error. Baraye meherbani dobara koshish karein.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <LayoutShell
      clinicName="Platform Admin"
      userName="Admin User"
      userRole="platform_admin"
    >
      <div className="max-w-[720px] mx-auto py-6">
        <form onSubmit={handleSubmit} noValidate>
          <FormShell
            title="New Clinic (Naya Clinic Onboarding)"
            badge={<StatusBadge variant="info">F-013</StatusBadge>}
            description="Naya clinic create karein aur clinic owner ko platform access magic link bhaijein."
            masterFields={
              <div className="flex flex-col gap-4">
                {apiError && (
                  <div className="p-3 rounded-md bg-danger-subtle border border-danger text-danger text-sm">
                    {apiError}
                  </div>
                )}

                {successClinic && (
                  <div className="p-4 rounded-md bg-success-subtle border border-success text-success text-sm flex flex-col gap-2">
                    <span className="font-semibold text-base">
                      🎉 Clinic &ldquo;{successClinic.name}&rdquo; kamyabi se create ho gaya!
                    </span>
                    <span className="text-xs text-fg-muted">
                      Owner ko portal ka magic login link email kar diya gaya hai. Booking URL:{" "}
                      <span className="font-mono text-fg font-medium">/c/{successClinic.slug}</span>
                    </span>
                    <div className="pt-2">
                      <Button
                        type="button"
                        variant="primary"
                        size="sm"
                        onClick={() => router.push("/admin/clinics")}
                      >
                        Clinics List Par Wapis Jayein
                      </Button>
                    </div>
                  </div>
                )}

                {!successClinic && (
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <Input
                      label="Clinic Name"
                      placeholder="e.g. Al-Shifa Family Clinic"
                      value={clinicName}
                      error={errors.clinicName}
                      disabled={isSubmitting}
                      onChange={(e) => {
                        setClinicName(e.target.value);
                        if (!slug || slug === autoGenerateSlug(clinicName)) {
                          setSlug(autoGenerateSlug(e.target.value));
                        }
                      }}
                      required
                    />

                    <Input
                      label="Slug (URL identifier)"
                      placeholder="al-shifa-family"
                      value={slug}
                      error={errors.slug}
                      disabled={isSubmitting}
                      onChange={(e) => setSlug(e.target.value.toLowerCase())}
                      required
                    />

                    <Input
                      label="Owner Full Name"
                      placeholder="Dr. Tariq Khan"
                      value={ownerName}
                      error={errors.ownerName}
                      disabled={isSubmitting}
                      onChange={(e) => setOwnerName(e.target.value)}
                      required
                    />

                    <Input
                      label="Owner Email"
                      type="email"
                      placeholder="owner@alshifaclinic.com"
                      value={ownerEmail}
                      error={errors.ownerEmail}
                      disabled={isSubmitting}
                      onChange={(e) => setOwnerEmail(e.target.value)}
                      required
                    />

                    <Input
                      label="Owner Phone (Contact)"
                      placeholder="+92 300 1234567"
                      value={ownerPhone}
                      disabled={isSubmitting}
                      onChange={(e) => setOwnerPhone(e.target.value)}
                    />

                    <div className="flex flex-col gap-1">
                      <label htmlFor="time-zone" className="text-xs text-fg-muted font-medium">
                        Time Zone <span className="text-danger ml-0.5">*</span>
                      </label>
                      <select
                        id="time-zone"
                        value={timeZone}
                        disabled={isSubmitting}
                        onChange={(e) => setTimeZone(e.target.value)}
                        className="h-8.5 px-3 text-sm rounded-md border border-border bg-surface text-fg focus:outline-hidden focus:border-border-focus"
                      >
                        <option value="Asia/Karachi">Asia/Karachi (PKT +05:00)</option>
                      </select>
                    </div>

                    <div className="flex flex-col gap-1 sm:col-span-2">
                      <label htmlFor="status" className="text-xs text-fg-muted font-medium">
                        Initial Status <span className="text-danger ml-0.5">*</span>
                      </label>
                      <select
                        id="status"
                        value={status}
                        disabled={isSubmitting}
                        onChange={(e) => setStatus(e.target.value)}
                        className="h-8.5 px-3 text-sm rounded-md border border-border bg-surface text-fg focus:outline-hidden focus:border-border-focus"
                      >
                        <option value="trial">Trial (Default trial period)</option>
                        <option value="active">Active (Full operational status)</option>
                        <option value="suspended">Suspended</option>
                      </select>
                    </div>
                  </div>
                )}
              </div>
            }
            summary={
              !successClinic ? (
                <div className="text-xs text-fg-muted flex flex-col gap-1">
                  <div>
                    <span className="font-medium text-fg">Public Booking Link: </span>
                    <span className="font-mono text-accent">/c/{slug || "slug"}</span>
                  </div>
                  <div>
                    <span className="font-medium text-fg">Owner Invitation: </span>
                    <span>{ownerName || "Owner"} &lt;{ownerEmail || "email"}&gt;</span>
                  </div>
                </div>
              ) : null
            }
            actions={
              !successClinic ? (
                <div className="flex items-center gap-3">
                  <Link href="/admin/clinics">
                    <Button type="button" variant="secondary" disabled={isSubmitting}>
                      Cancel
                    </Button>
                  </Link>
                  <Button type="submit" variant="primary" disabled={isSubmitting}>
                    {isSubmitting ? "Creating Clinic..." : "Create Clinic"}
                  </Button>
                </div>
              ) : null
            }
            auditPanel={
              <span>
                Audited action: `clinic.create` + `member.invite`. Only accessible by platform_admin.
              </span>
            }
          />
        </form>
      </div>
    </LayoutShell>
  );
}
