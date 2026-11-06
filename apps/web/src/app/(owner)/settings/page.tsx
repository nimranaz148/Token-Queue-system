"use client";

import * as React from "react";
import Link from "next/link";
import { RoleGuard } from "@/components/auth/role-guard";
import { LayoutShell } from "@/components/layout/layout-shell";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { StatusBadge } from "@/components/ui/status-badge";
import {
  Settings as SettingsIcon,
  Globe,
  Sliders,
  ShieldCheck,
  Save,
  CheckCircle2,
  AlertCircle,
  Building2,
  Bot,
  ExternalLink,
  Phone,
  MapPin,
  Clock,
  Sparkles,
  Users,
  Check,
} from "lucide-react";

export interface ClinicSettingsData {
  clinic_id: string;
  clinic_name: string;
  slug: string;
  time_zone: string;
  address?: string | null;
  phone?: string | null;
  maps_url?: string | null;
  logo_path?: string | null;

  online_booking_enabled: boolean;
  daily_online_limit: number;
  advance_days: number;
  default_consult_minutes: number;
  call_only_arrived: boolean;
  language_default: string;
  share_advice_with_patient: boolean;
  ai_notes_enabled: boolean;
  ai_consent_accepted_by?: string | null;
  ai_consent_accepted_at?: string | null;
  version: number;
  updated_at?: string;
}

interface ClinicSettingsPageProps {
  initialSettings?: ClinicSettingsData | null;
  userRole?: string;
}

const defaultSettings: ClinicSettingsData = {
  clinic_id: "demo-clinic-id",
  clinic_name: "Shifa Clinic",
  slug: "shifa-clinic",
  time_zone: "Asia/Karachi",
  address: "Block 4, Gulshan-e-Iqbal, Karachi",
  phone: "+92 300 1234567",
  maps_url: "https://maps.google.com/?q=shifa",
  logo_path: null,

  online_booking_enabled: true,
  daily_online_limit: 50,
  advance_days: 1,
  default_consult_minutes: 10,
  call_only_arrived: false,
  language_default: "en",
  share_advice_with_patient: false,
  ai_notes_enabled: false,
  version: 1,
  updated_at: new Date().toISOString(),
};

export default function ClinicSettingsPage({
  initialSettings = null,
  userRole = "owner",
}: ClinicSettingsPageProps) {
  const [settings, setSettings] = React.useState<ClinicSettingsData>(
    initialSettings || defaultSettings
  );
  const [isLoading, setIsLoading] = React.useState(false);
  const [isSaving, setIsSaving] = React.useState(false);
  const [saveSuccess, setSaveSuccess] = React.useState(false);
  const [errorMessage, setErrorMessage] = React.useState<string | null>(null);

  // Active Category Tab
  const [activeTab, setActiveTab] = React.useState<"queue" | "profile" | "privacy">("queue");

  // AI Consent Modal State (PRD §5.3 F-011 / Q-004)
  const [showAIConsentModal, setShowAIConsentModal] = React.useState(false);

  // Fetch settings from API on mount if not provided
  React.useEffect(() => {
    if (!initialSettings) {
      setIsLoading(true);
      const token = typeof window !== "undefined" ? localStorage.getItem("auth_token") : null;
      fetch("/api/v1/settings", {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      })
        .then((res) => {
          if (!res.ok) throw new Error(`HTTP ${res.status}`);
          return res.json();
        })
        .then((data: ClinicSettingsData) => {
          setSettings(data);
        })
        .catch((err) => {
          if (err instanceof Error && !err.message.includes("404")) {
            setErrorMessage("Settings load failed.");
          }
        })
        .finally(() => setIsLoading(false));
    }
  }, [initialSettings]);

  const handleToggleAIOption = (checked: boolean) => {
    if (checked) {
      setShowAIConsentModal(true);
    } else {
      setSettings((prev) => ({ ...prev, ai_notes_enabled: false }));
    }
  };

  const handleConfirmAIConsent = () => {
    setSettings((prev) => ({
      ...prev,
      ai_notes_enabled: true,
      ai_consent_accepted_at: new Date().toISOString(),
    }));
    setShowAIConsentModal(false);
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);
    setErrorMessage(null);
    setSaveSuccess(false);

    try {
      const payload = {
        version: settings.version,
        clinic_name: settings.clinic_name,
        time_zone: settings.time_zone,
        address: settings.address,
        phone: settings.phone,
        maps_url: settings.maps_url,
        logo_path: settings.logo_path,
        online_booking_enabled: settings.online_booking_enabled,
        daily_online_limit: Number(settings.daily_online_limit),
        advance_days: Number(settings.advance_days),
        default_consult_minutes: Number(settings.default_consult_minutes),
        call_only_arrived: settings.call_only_arrived,
        language_default: settings.language_default,
        share_advice_with_patient: settings.share_advice_with_patient,
        ai_notes_enabled: settings.ai_notes_enabled,
      };

      const token = typeof window !== "undefined" ? localStorage.getItem("auth_token") : null;
      const res = await fetch("/api/v1/settings", {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify(payload),
      });

      if (res.status === 409) {
        throw new Error(
          "Settings conflict: Version changed by another user. Please refresh and try again."
        );
      }

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || `Save failed with status ${res.status}`);
      }

      const updated: ClinicSettingsData = await res.json();
      setSettings(updated);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 4000);
    } catch (err: unknown) {
      if (err instanceof Error) {
        setErrorMessage(err.message);
      } else {
        setErrorMessage("Unexpected error occurred while saving.");
      }
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <RoleGuard allowedRoles={["owner"]}>
      <LayoutShell
        userRole={userRole}
        clinicName={settings.clinic_name}
        userName="Clinic Owner"
        navItems={[
          {
            label: "Clinic Settings",
            href: "/settings",
            icon: <SettingsIcon className="w-4 h-4" />,
            active: true,
          },
          { label: "Doctors", href: "/settings/doctors", icon: <Users className="w-4 h-4" /> },
          { label: "Staff", href: "/settings/staff", icon: <Users className="w-4 h-4" /> },
          { label: "TV Screens", href: "/settings/tv", icon: <SettingsIcon className="w-4 h-4" /> },
        ]}
      >
        <div className="max-w-5xl space-y-6 mx-auto w-full">
          {/* Header Card */}
          <div className="p-6 rounded-2xl bg-surface border border-border shadow-xs flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <div className="flex items-start gap-4">
              <div className="w-12 h-12 rounded-xl bg-accent/10 border border-accent/20 flex items-center justify-center text-accent shrink-0">
                <Building2 className="w-6 h-6" />
              </div>
              <div>
                <div className="flex items-center gap-2.5 flex-wrap">
                  <h1 className="text-2xl font-bold tracking-tight text-fg">
                    Clinic Settings
                  </h1>
                  <StatusBadge variant="info">Owner Portal</StatusBadge>
                  <span className="text-xs text-fg-muted font-mono font-medium bg-surface-sunken border border-border px-2.5 py-0.5 rounded-full">
                    Version v{settings.version}
                  </span>
                </div>
                <p className="text-xs text-fg-muted mt-1">
                  Configure OPD queue rules, public booking parameters, and privacy policies (F-011)
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2 self-start md:self-auto">
              {settings.slug && (
                <Link
                  href={`/c/${settings.slug}`}
                  target="_blank"
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg border border-border hover:border-accent hover:text-accent bg-surface-sunken transition-colors"
                >
                  <Globe className="w-3.5 h-3.5" />
                  <span>Public Booking Page</span>
                  <ExternalLink className="w-3 h-3 ml-0.5 text-fg-muted" />
                </Link>
              )}
            </div>
          </div>

          {/* KPI / Live Status Strip */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="p-3.5 rounded-xl border border-border bg-surface flex flex-col gap-1 shadow-xs">
              <span className="text-[11px] font-semibold text-fg-muted flex items-center gap-1">
                <Sliders className="w-3 h-3 text-accent" />
                Online OPD
              </span>
              <span className="text-sm font-bold flex items-center gap-1.5">
                <span
                  className={`w-2 h-2 rounded-full ${
                    settings.online_booking_enabled ? "bg-status-success animate-pulse" : "bg-fg-muted"
                  }`}
                />
                <span className={settings.online_booking_enabled ? "text-status-success" : "text-fg-muted"}>
                  {settings.online_booking_enabled ? "Booking Active" : "Disabled"}
                </span>
              </span>
            </div>

            <div className="p-3.5 rounded-xl border border-border bg-surface flex flex-col gap-1 shadow-xs">
              <span className="text-[11px] font-semibold text-fg-muted flex items-center gap-1">
                <Users className="w-3 h-3 text-info" />
                Roz ka Token Limit
              </span>
              <span className="text-sm font-bold text-fg font-mono">
                {settings.daily_online_limit} / Doctor
              </span>
            </div>

            <div className="p-3.5 rounded-xl border border-border bg-surface flex flex-col gap-1 shadow-xs">
              <span className="text-[11px] font-semibold text-fg-muted flex items-center gap-1">
                <Clock className="w-3 h-3 text-warning" />
                Avg Consult Time
              </span>
              <span className="text-sm font-bold text-fg font-mono">
                {settings.default_consult_minutes} mins
              </span>
            </div>

            <div className="p-3.5 rounded-xl border border-border bg-surface flex flex-col gap-1 shadow-xs">
              <span className="text-[11px] font-semibold text-fg-muted flex items-center gap-1">
                <Bot className="w-3 h-3 text-purple-600" />
                AI Assistant
              </span>
              <span className="text-sm font-bold text-fg">
                {settings.ai_notes_enabled ? (
                  <span className="text-purple-600 font-semibold">Enabled</span>
                ) : (
                  <span className="text-fg-muted">Inactive</span>
                )}
              </span>
            </div>
          </div>

          {/* Feedback Alerts */}
          {errorMessage && (
            <div className="p-4 rounded-xl bg-status-danger/10 border border-status-danger/20 text-status-danger text-sm flex items-center gap-3">
              <AlertCircle className="w-5 h-5 shrink-0" />
              <span className="font-medium">{errorMessage}</span>
            </div>
          )}

          {saveSuccess && (
            <div className="p-4 rounded-xl bg-status-success/10 border border-status-success/20 text-status-success text-sm flex items-center gap-3 animate-in fade-in">
              <CheckCircle2 className="w-5 h-5 shrink-0 text-status-success" />
              <span className="font-semibold">
                Settings kamyabi se mehfooz kar li gayi hain (Settings saved successfully).
              </span>
            </div>
          )}

          {/* Section Category Tabs */}
          <div className="flex border-b border-border gap-2">
            <button
              type="button"
              onClick={() => setActiveTab("queue")}
              className={`pb-3 px-4 text-xs font-semibold flex items-center gap-2 border-b-2 transition-all ${
                activeTab === "queue"
                  ? "border-accent text-accent font-bold"
                  : "border-transparent text-fg-muted hover:text-fg"
              }`}
            >
              <Sliders className="w-4 h-4" />
              <span>OPD Queue &amp; Tokens</span>
            </button>
            <button
              type="button"
              onClick={() => setActiveTab("profile")}
              className={`pb-3 px-4 text-xs font-semibold flex items-center gap-2 border-b-2 transition-all ${
                activeTab === "profile"
                  ? "border-accent text-accent font-bold"
                  : "border-transparent text-fg-muted hover:text-fg"
              }`}
            >
              <Building2 className="w-4 h-4" />
              <span>Clinic Profile &amp; Contact</span>
            </button>
            <button
              type="button"
              onClick={() => setActiveTab("privacy")}
              className={`pb-3 px-4 text-xs font-semibold flex items-center gap-2 border-b-2 transition-all ${
                activeTab === "privacy"
                  ? "border-accent text-accent font-bold"
                  : "border-transparent text-fg-muted hover:text-fg"
              }`}
            >
              <ShieldCheck className="w-4 h-4" />
              <span>Privacy &amp; AI Policies</span>
            </button>
          </div>

          <form onSubmit={handleSave} className="space-y-6">
            {/* TAB 1: OPD Queue & Token Rules */}
            <div className={activeTab === "queue" ? "space-y-5" : "hidden"}>
              <div className="bg-surface rounded-2xl border border-border p-6 shadow-xs space-y-6">
                <div className="flex items-center gap-2.5 pb-4 border-b border-border">
                  <div className="p-2 rounded-lg bg-accent/10 text-accent">
                    <Sliders className="w-5 h-5" />
                  </div>
                  <div>
                    <h2 className="text-base font-bold text-fg">
                      OPD Queue &amp; Token Rules
                    </h2>
                    <p className="text-xs text-fg-muted mt-0.5">
                      Token issuing limits, OPD consultation duration, and patient check-in requirements
                    </p>
                  </div>
                </div>

                {/* Online booking switch */}
                <div className="flex items-start justify-between gap-4 p-4 rounded-xl border border-border bg-surface-sunken hover:border-accent/30 transition-colors">
                  <div>
                    <label
                      htmlFor="online_booking_enabled"
                      className="text-sm font-bold text-fg cursor-pointer flex items-center gap-2"
                    >
                      Online token ON/OFF
                      {settings.online_booking_enabled ? (
                        <span className="text-[10px] bg-status-success/15 text-status-success font-semibold px-2 py-0.5 rounded-full">
                          ONLINE OPEN
                        </span>
                      ) : (
                        <span className="text-[10px] bg-fg-muted/20 text-fg-muted font-semibold px-2 py-0.5 rounded-full">
                          BAND HAI
                        </span>
                      )}
                    </label>
                    <p className="text-xs text-fg-muted mt-1 max-w-xl">
                      When switched OFF, the public booking link displays &ldquo;Booking band hai&rdquo; and blocks new online tokens.
                    </p>
                  </div>
                  <input
                    id="online_booking_enabled"
                    type="checkbox"
                    aria-label="Online token booking ON/OFF"
                    checked={settings.online_booking_enabled}
                    onChange={(e) =>
                      setSettings((prev) => ({
                        ...prev,
                        online_booking_enabled: e.target.checked,
                      }))
                    }
                    className="w-5 h-5 rounded text-accent focus:ring-accent cursor-pointer mt-1"
                  />
                </div>

                {/* Daily online limit & Default Consult minutes */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-5 pt-1">
                  <div className="p-4 rounded-xl border border-border bg-surface space-y-2">
                    <label
                      htmlFor="daily_online_limit"
                      className="text-xs font-bold text-fg block"
                    >
                      Roz ka token limit (Daily Online Limit)
                    </label>
                    <p className="text-xs text-fg-muted">
                      Maximum online tokens allowed per doctor each day (1 - 500).
                    </p>
                    <Input
                      id="daily_online_limit"
                      type="number"
                      min={1}
                      max={500}
                      value={settings.daily_online_limit}
                      onChange={(e) =>
                        setSettings((prev) => ({
                          ...prev,
                          daily_online_limit: parseInt(e.target.value) || 1,
                        }))
                      }
                      className="font-mono text-sm"
                      required
                    />
                  </div>

                  <div className="p-4 rounded-xl border border-border bg-surface space-y-2">
                    <label
                      htmlFor="default_consult_minutes"
                      className="text-xs font-bold text-fg block"
                    >
                      Default consult time (minutes)
                    </label>
                    <p className="text-xs text-fg-muted">
                      Estimated consultation duration used for wait time calculation (2 - 60 min).
                    </p>
                    <Input
                      id="default_consult_minutes"
                      type="number"
                      min={2}
                      max={60}
                      value={settings.default_consult_minutes}
                      onChange={(e) =>
                        setSettings((prev) => ({
                          ...prev,
                          default_consult_minutes: parseInt(e.target.value) || 2,
                        }))
                      }
                      className="font-mono text-sm"
                      required
                    />
                  </div>
                </div>

                {/* Advance booking days & Call only arrived */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-5 pt-1">
                  <div className="p-4 rounded-xl border border-border bg-surface space-y-2">
                    <label
                      htmlFor="advance_days"
                      className="text-xs font-bold text-fg block"
                    >
                      Advance booking window
                    </label>
                    <p className="text-xs text-fg-muted">
                      Choose whether patients can only book for today or today and tomorrow.
                    </p>
                    <select
                      id="advance_days"
                      aria-label="Advance Booking Days"
                      value={settings.advance_days}
                      onChange={(e) =>
                        setSettings((prev) => ({
                          ...prev,
                          advance_days: parseInt(e.target.value),
                        }))
                      }
                      className="w-full h-9 px-3 text-sm rounded-lg border border-border bg-surface text-fg focus:outline-none focus:ring-2 focus:ring-accent"
                    >
                      <option value={0}>0 — Sirf Aaj (Today only)</option>
                      <option value={1}>1 — Aaj aur Kal (Today &amp; Tomorrow)</option>
                    </select>
                  </div>

                  <div className="p-4 rounded-xl border border-border bg-surface-sunken flex items-start justify-between gap-4">
                    <div>
                      <label
                        htmlFor="call_only_arrived"
                        className="text-xs font-bold text-fg block cursor-pointer"
                      >
                        Call only arrived patients
                      </label>
                      <p className="text-xs text-fg-muted mt-1">
                        Doctor can only call patients who have checked in as arrived at reception.
                      </p>
                    </div>
                    <input
                      id="call_only_arrived"
                      type="checkbox"
                      aria-label="Call only arrived patients"
                      checked={settings.call_only_arrived}
                      onChange={(e) =>
                        setSettings((prev) => ({
                          ...prev,
                          call_only_arrived: e.target.checked,
                        }))
                      }
                      className="w-5 h-5 rounded text-accent focus:ring-accent cursor-pointer mt-1"
                    />
                  </div>
                </div>
              </div>
            </div>

            {/* TAB 2: Clinic Profile & Contact */}
            <div className={activeTab === "profile" ? "space-y-5" : "hidden"}>
              <div className="bg-surface rounded-2xl border border-border p-6 shadow-xs space-y-6">
                <div className="flex items-center gap-2.5 pb-4 border-b border-border">
                  <div className="p-2 rounded-lg bg-info/10 text-info">
                    <Building2 className="w-5 h-5" />
                  </div>
                  <div>
                    <h2 className="text-base font-bold text-fg">
                      Clinic Profile &amp; Contact Info
                    </h2>
                    <p className="text-xs text-fg-muted mt-0.5">
                      Clinic display name, contact phone, physical location, and localized timezone
                    </p>
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
                  <div className="space-y-1.5">
                    <label
                      htmlFor="clinic_name"
                      className="text-xs font-bold text-fg block"
                    >
                      Clinic Name
                    </label>
                    <Input
                      id="clinic_name"
                      type="text"
                      minLength={2}
                      maxLength={80}
                      value={settings.clinic_name}
                      onChange={(e) =>
                        setSettings((prev) => ({ ...prev, clinic_name: e.target.value }))
                      }
                      className="h-10 text-sm font-medium"
                      required
                    />
                  </div>

                  <div className="space-y-1.5">
                    <label
                      htmlFor="phone"
                      className="text-xs font-bold text-fg block"
                    >
                      Contact Phone Number
                    </label>
                    <Input
                      id="phone"
                      type="tel"
                      placeholder="+92 300 1234567"
                      value={settings.phone || ""}
                      onChange={(e) =>
                        setSettings((prev) => ({ ...prev, phone: e.target.value }))
                      }
                      className="h-10 text-sm font-mono"
                    />
                  </div>
                </div>

                <div className="space-y-1.5">
                  <label
                    htmlFor="address"
                    className="text-xs font-bold text-fg block"
                  >
                    Clinic Address
                  </label>
                  <Input
                    id="address"
                    type="text"
                    placeholder="Street, Area, City"
                    value={settings.address || ""}
                    onChange={(e) =>
                      setSettings((prev) => ({ ...prev, address: e.target.value }))
                    }
                    className="h-10 text-sm"
                  />
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-5">
                  <div className="space-y-1.5">
                    <label
                      htmlFor="time_zone"
                      className="text-xs font-bold text-fg block"
                    >
                      Time Zone
                    </label>
                    <select
                      id="time_zone"
                      aria-label="Clinic Timezone"
                      value={settings.time_zone}
                      onChange={(e) =>
                        setSettings((prev) => ({ ...prev, time_zone: e.target.value }))
                      }
                      className="w-full h-10 px-3 text-sm rounded-lg border border-border bg-surface text-fg focus:outline-none focus:ring-2 focus:ring-accent"
                    >
                      <option value="Asia/Karachi">Asia/Karachi (PKT +05:00)</option>
                      <option value="UTC">UTC (+00:00)</option>
                    </select>
                  </div>

                  <div className="space-y-1.5">
                    <label
                      htmlFor="language_default"
                      className="text-xs font-bold text-fg block"
                    >
                      Default Language
                    </label>
                    <select
                      id="language_default"
                      aria-label="Default Language"
                      value={settings.language_default}
                      onChange={(e) =>
                        setSettings((prev) => ({ ...prev, language_default: e.target.value }))
                      }
                      className="w-full h-10 px-3 text-sm rounded-lg border border-border bg-surface text-fg focus:outline-none focus:ring-2 focus:ring-accent"
                    >
                      <option value="en">English (en)</option>
                      <option value="roman_ur">Roman Urdu (roman_ur)</option>
                    </select>
                  </div>

                  <div className="space-y-1.5">
                    <label
                      htmlFor="maps_url"
                      className="text-xs font-bold text-fg block"
                    >
                      Google Maps Link
                    </label>
                    <Input
                      id="maps_url"
                      type="url"
                      placeholder="https://maps.google.com/..."
                      value={settings.maps_url || ""}
                      onChange={(e) =>
                        setSettings((prev) => ({ ...prev, maps_url: e.target.value }))
                      }
                      className="h-10 text-sm font-mono"
                    />
                  </div>
                </div>
              </div>
            </div>

            {/* TAB 3: Privacy & AI Policies */}
            <div className={activeTab === "privacy" ? "space-y-5" : "hidden"}>
              <div className="bg-surface rounded-2xl border border-border p-6 shadow-xs space-y-6">
                <div className="flex items-center gap-2.5 pb-4 border-b border-border">
                  <div className="p-2 rounded-lg bg-status-success/10 text-status-success">
                    <ShieldCheck className="w-5 h-5" />
                  </div>
                  <div>
                    <h2 className="text-base font-bold text-fg">
                      Privacy &amp; AI Integration
                    </h2>
                    <p className="text-xs text-fg-muted mt-0.5">
                      Patient medical advice transparency, PECA compliance, and LLM clinical notes consent
                    </p>
                  </div>
                </div>

                {/* Share prescription advice switch (F-021 / W-011) */}
                <div className="flex items-start justify-between gap-4 p-4 rounded-xl border border-border bg-surface-sunken hover:border-status-success/30 transition-colors">
                  <div>
                    <label
                      htmlFor="share_advice_with_patient"
                      className="text-sm font-bold text-fg cursor-pointer flex items-center gap-2"
                    >
                      Mareez ko dawa/hidayat dikhayein (Share visit advice)
                      {settings.share_advice_with_patient ? (
                        <span className="text-[10px] bg-status-success/15 text-status-success font-semibold px-2 py-0.5 rounded-full">
                          SHARED WITH PATIENTS
                        </span>
                      ) : (
                        <span className="text-[10px] bg-fg-muted/20 text-fg-muted font-semibold px-2 py-0.5 rounded-full">
                          CLINIC ONLY
                        </span>
                      )}
                    </label>
                    <p className="text-xs text-fg-muted mt-1 max-w-xl">
                      Allow patients to view prescription medicines &amp; doctor instructions on their <code className="px-1 py-0.5 rounded bg-surface border border-border text-[11px] font-mono">/t/&#123;code&#125;/advice</code> page. Turning this OFF hides advice clinic-wide immediately.
                    </p>
                  </div>
                  <input
                    id="share_advice_with_patient"
                    type="checkbox"
                    aria-label="Share visit advice with patient"
                    checked={settings.share_advice_with_patient}
                    onChange={(e) =>
                      setSettings((prev) => ({
                        ...prev,
                        share_advice_with_patient: e.target.checked,
                      }))
                    }
                    className="w-5 h-5 rounded text-status-success focus:ring-status-success cursor-pointer mt-1"
                  />
                </div>

                {/* AI Notes switch (Q-004) */}
                <div className="flex items-start justify-between gap-4 p-4 rounded-xl border border-purple-200/50 bg-purple-50/20 hover:border-purple-300 transition-colors">
                  <div>
                    <div className="flex items-center gap-2">
                      <Bot className="w-4 h-4 text-purple-600" />
                      <label
                        htmlFor="ai_notes_enabled"
                        className="text-sm font-bold text-fg cursor-pointer"
                      >
                        AI ko notes istemal karne dein (AI Clinical Notes Processing)
                      </label>
                    </div>
                    <p className="text-xs text-fg-muted mt-1 max-w-xl">
                      Enables doctors to generate visit summaries using AI models. Requires explicit clinic owner consent (Q-004).
                    </p>
                    {settings.ai_notes_enabled && settings.ai_consent_accepted_at && (
                      <span className="inline-flex items-center gap-1.5 mt-2 text-[11px] font-semibold text-purple-700 bg-purple-100/70 border border-purple-200 px-2.5 py-1 rounded-md">
                        <Check className="w-3.5 h-3.5 text-purple-600" />
                        Consent accepted on {new Date(settings.ai_consent_accepted_at).toLocaleDateString()}
                      </span>
                    )}
                  </div>
                  <input
                    id="ai_notes_enabled"
                    type="checkbox"
                    aria-label="Enable AI clinical notes processing"
                    checked={settings.ai_notes_enabled}
                    onChange={(e) => handleToggleAIOption(e.target.checked)}
                    className="w-5 h-5 rounded text-purple-600 focus:ring-purple-500 cursor-pointer mt-1"
                  />
                </div>
              </div>
            </div>

            {/* Action Bar */}
            <div className="sticky bottom-4 z-20 flex flex-col sm:flex-row items-center justify-between gap-4 bg-surface/95 backdrop-blur-md p-4 rounded-2xl border border-border shadow-lg">
              <div className="text-xs text-fg-muted flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-status-success shrink-0" />
                <span>Optimistic lock active · Settings version {settings.version}</span>
              </div>
              <div className="flex items-center gap-3 w-full sm:w-auto">
                <Button
                  type="submit"
                  variant="primary"
                  disabled={isSaving}
                  className="w-full sm:w-auto flex items-center justify-center gap-2 px-8 h-10 font-bold shadow-xs tracking-wide"
                >
                  <Save className="w-4 h-4" />
                  <span>{isSaving ? "Mehfooz ho raha hai..." : "Save Settings (Mehfooz Karein)"}</span>
                </Button>
              </div>
            </div>
          </form>

          {/* AI Consent Confirmation Modal (PRD §5.3 / Q-004) */}
          {showAIConsentModal && (
            <div
              role="dialog"
              aria-modal="true"
              aria-labelledby="consent-title"
              className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4 animate-in fade-in"
            >
              <div className="bg-surface rounded-2xl border border-border max-w-md w-full p-6 shadow-2xl space-y-4">
                <div className="flex items-center gap-3 text-purple-600">
                  <div className="p-2 rounded-lg bg-purple-50 border border-purple-200">
                    <Bot className="w-6 h-6" />
                  </div>
                  <h3 id="consent-title" className="text-lg font-bold text-fg">
                    AI Clinical Notes Consent (Q-004)
                  </h3>
                </div>

                <div className="text-xs text-fg-muted space-y-2.5 bg-purple-50/40 p-4 rounded-xl border border-purple-100">
                  <p className="font-medium text-fg">
                    By enabling AI Clinical Notes processing, you agree that consultation notes may be processed by enterprise LLM providers strictly under zero-data-retention terms.
                  </p>
                  <p>
                    • No patient name, phone number, or direct identifiers are ever sent.
                  </p>
                  <p>
                    • AI suggestions are purely assistive and not substitutes for doctor diagnosis.
                  </p>
                </div>

                <div className="flex items-center justify-end gap-3 pt-2">
                  <Button
                    type="button"
                    variant="secondary"
                    onClick={() => setShowAIConsentModal(false)}
                  >
                    Cancel
                  </Button>
                  <Button
                    type="button"
                    variant="primary"
                    onClick={handleConfirmAIConsent}
                  >
                    Accept &amp; Enable AI
                  </Button>
                </div>
              </div>
            </div>
          )}
        </div>
      </LayoutShell>
    </RoleGuard>
  );
}
