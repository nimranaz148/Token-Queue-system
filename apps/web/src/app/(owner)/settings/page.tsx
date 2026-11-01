"use client";

import * as React from "react";
import { RoleGuard } from "@/components/auth/role-guard";
import { LayoutShell } from "@/components/layout/layout-shell";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
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
  FileText,
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

  // AI Consent Modal State (PRD §5.3 F-011 / Q-004)
  const [showAIConsentModal, setShowAIConsentModal] = React.useState(false);

  // Fetch settings from API on mount if not provided
  React.useEffect(() => {
    if (!initialSettings) {
      setIsLoading(true);
      fetch("/api/v1/settings")
        .then((res) => {
          if (!res.ok) throw new Error(`HTTP ${res.status}`);
          return res.json();
        })
        .then((data: ClinicSettingsData) => {
          setSettings(data);
        })
        .catch((err) => {
          // Keep default settings in test/mock
          if (err instanceof Error && !err.message.includes("404")) {
            setErrorMessage("Settings load failed.");
          }
        })
        .finally(() => setIsLoading(false));
    }
  }, [initialSettings]);

  const handleToggleAIOption = (checked: boolean) => {
    if (checked) {
      // Show consent prompt
      setShowAIConsentModal(true);
    } else {
      setSettings((prev) => ({ ...prev, ai_notes_enabled: false }));
    }
  };

  const handleConfirmAIConsent = () => {
    setSettings((prev) => ({ ...prev, ai_notes_enabled: true }));
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

      const res = await fetch("/api/v1/settings", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
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
      setTimeout(() => setSaveSuccess(false), 3000);
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
      >
        <div className="max-w-4xl space-y-6">
          {/* Header */}
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-4 border-b border-gray-200">
            <div>
              <div className="flex items-center gap-2">
                <SettingsIcon className="w-5 h-5 text-teal-600" />
                <span className="text-xs font-semibold text-teal-700 uppercase tracking-wider">
                  Clinic Management
                </span>
              </div>
              <h1 className="text-2xl sm:text-3xl font-extrabold text-gray-900 tracking-tight mt-1">
                Clinic Settings
              </h1>
              <p className="text-sm text-gray-500 mt-0.5">
                Configure OPD queue rules, public booking parameters, and privacy policies (F-011)
              </p>
            </div>

            <div className="flex items-center gap-2">
              <span className="text-xs text-gray-500 font-medium bg-gray-100 px-2.5 py-1 rounded-md">
                Version v{settings.version}
              </span>
            </div>
          </div>

          {errorMessage && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{errorMessage}</span>
            </div>
          )}

          {saveSuccess && (
            <div className="bg-emerald-50 border border-emerald-200 text-emerald-800 px-4 py-3 rounded-lg text-sm flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-600" />
              <span>Settings kamyabi se mehfooz kar li gayi hain (Settings saved successfully).</span>
            </div>
          )}

          <form onSubmit={handleSave} className="space-y-6">
            {/* Section 1: OPD Queue & Token Rules */}
            <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm space-y-5">
              <div className="flex items-center gap-2 pb-3 border-b border-gray-100">
                <Sliders className="w-5 h-5 text-teal-600" />
                <h2 className="text-base font-bold text-gray-900">
                  OPD Queue & Token Rules
                </h2>
              </div>

              {/* Online booking switch */}
              <div className="flex items-start justify-between gap-4 pt-1">
                <div>
                  <label
                    htmlFor="online_booking_enabled"
                    className="text-sm font-semibold text-gray-900 block"
                  >
                    Online token ON/OFF
                  </label>
                  <p className="text-xs text-gray-500 mt-0.5">
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
                  className="w-5 h-5 rounded text-teal-600 focus:ring-teal-500 cursor-pointer mt-1"
                />
              </div>

              {/* Daily online limit */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
                <div>
                  <label
                    htmlFor="daily_online_limit"
                    className="text-sm font-semibold text-gray-900 block"
                  >
                    Roz ka token limit (Daily Online Limit)
                  </label>
                  <p className="text-xs text-gray-500 mt-0.5 mb-1.5">
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
                    required
                  />
                </div>

                <div>
                  <label
                    htmlFor="default_consult_minutes"
                    className="text-sm font-semibold text-gray-900 block"
                  >
                    Default consult time (minutes)
                  </label>
                  <p className="text-xs text-gray-500 mt-0.5 mb-1.5">
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
                    required
                  />
                </div>
              </div>

              {/* Advance booking days & Call only arrived */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
                <div>
                  <label
                    htmlFor="advance_days"
                    className="text-sm font-semibold text-gray-900 block"
                  >
                    Advance booking window
                  </label>
                  <p className="text-xs text-gray-500 mt-0.5 mb-1.5">
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
                    className="w-full h-8.5 px-3 text-sm rounded-md border border-gray-300 bg-white focus:outline-none focus:ring-2 focus:ring-teal-500"
                  >
                    <option value={0}>0 — Sirf Aaj (Today only)</option>
                    <option value={1}>1 — Aaj aur Kal (Today &amp; Tomorrow)</option>
                  </select>
                </div>

                <div className="flex items-start justify-between gap-4 pt-4 sm:pt-6">
                  <div>
                    <label
                      htmlFor="call_only_arrived"
                      className="text-sm font-semibold text-gray-900 block"
                    >
                      Call only arrived patients
                    </label>
                    <p className="text-xs text-gray-500 mt-0.5">
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
                    className="w-5 h-5 rounded text-teal-600 focus:ring-teal-500 cursor-pointer mt-1"
                  />
                </div>
              </div>
            </div>

            {/* Section 2: Clinic Profile */}
            <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm space-y-4">
              <div className="flex items-center gap-2 pb-3 border-b border-gray-100">
                <Building2 className="w-5 h-5 text-teal-600" />
                <h2 className="text-base font-bold text-gray-900">
                  Clinic Profile &amp; Contact Info
                </h2>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label
                    htmlFor="clinic_name"
                    className="text-sm font-semibold text-gray-900 block mb-1.5"
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
                    required
                  />
                </div>

                <div>
                  <label
                    htmlFor="phone"
                    className="text-sm font-semibold text-gray-900 block mb-1.5"
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
                  />
                </div>
              </div>

              <div>
                <label
                  htmlFor="address"
                  className="text-sm font-semibold text-gray-900 block mb-1.5"
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
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div>
                  <label
                    htmlFor="time_zone"
                    className="text-sm font-semibold text-gray-900 block mb-1.5"
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
                    className="w-full h-8.5 px-3 text-sm rounded-md border border-gray-300 bg-white focus:outline-none focus:ring-2 focus:ring-teal-500"
                  >
                    <option value="Asia/Karachi">Asia/Karachi (PKT +05:00)</option>
                    <option value="UTC">UTC (+00:00)</option>
                  </select>
                </div>

                <div>
                  <label
                    htmlFor="language_default"
                    className="text-sm font-semibold text-gray-900 block mb-1.5"
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
                    className="w-full h-8.5 px-3 text-sm rounded-md border border-gray-300 bg-white focus:outline-none focus:ring-2 focus:ring-teal-500"
                  >
                    <option value="en">English (en)</option>
                    <option value="roman_ur">Roman Urdu (roman_ur)</option>
                  </select>
                </div>

                <div>
                  <label
                    htmlFor="maps_url"
                    className="text-sm font-semibold text-gray-900 block mb-1.5"
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
                  />
                </div>
              </div>
            </div>

            {/* Section 3: Privacy & AI Sharing Settings */}
            <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm space-y-5">
              <div className="flex items-center gap-2 pb-3 border-b border-gray-100">
                <ShieldCheck className="w-5 h-5 text-teal-600" />
                <h2 className="text-base font-bold text-gray-900">
                  Privacy &amp; AI Integration
                </h2>
              </div>

              {/* Share prescription advice switch (F-021 / W-011) */}
              <div className="flex items-start justify-between gap-4 pt-1">
                <div>
                  <label
                    htmlFor="share_advice_with_patient"
                    className="text-sm font-semibold text-gray-900 block"
                  >
                    Mareez ko dawa/hidayat dikhayein (Share visit advice)
                  </label>
                  <p className="text-xs text-gray-500 mt-0.5">
                    Allow patients to view prescription medicines &amp; doctor instructions on their `/t/&#123;code&#125;/advice` page. Turning this OFF hides advice clinic-wide immediately.
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
                  className="w-5 h-5 rounded text-teal-600 focus:ring-teal-500 cursor-pointer mt-1"
                />
              </div>

              {/* AI Notes switch (Q-004) */}
              <div className="flex items-start justify-between gap-4 pt-3 border-t border-gray-100">
                <div>
                  <div className="flex items-center gap-2">
                    <Bot className="w-4 h-4 text-purple-600" />
                    <label
                      htmlFor="ai_notes_enabled"
                      className="text-sm font-semibold text-gray-900"
                    >
                      AI ko notes istemal karne dein (AI Clinical Notes Processing)
                    </label>
                  </div>
                  <p className="text-xs text-gray-500 mt-0.5">
                    Enables doctors to generate visit summaries using AI models. Requires explicit clinic owner consent (Q-004).
                  </p>
                  {settings.ai_notes_enabled && settings.ai_consent_accepted_at && (
                    <span className="inline-block mt-1 text-[11px] font-medium text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded">
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

            {/* Action Bar */}
            <div className="flex flex-col sm:flex-row items-center justify-between gap-4 bg-gray-50 p-4 rounded-xl border border-gray-200">
              <div className="text-xs text-gray-500">
                Optimistic lock active · Settings version {settings.version}
              </div>
              <Button
                type="submit"
                variant="primary"
                disabled={isSaving}
                className="w-full sm:w-auto flex items-center justify-center gap-2 px-6"
              >
                <Save className="w-4 h-4" />
                <span>{isSaving ? "Saving..." : "Save Settings (Mehfooz Karein)"}</span>
              </Button>
            </div>
          </form>

          {/* AI Consent Confirmation Modal (PRD §5.3 / Q-004) */}
          {showAIConsentModal && (
            <div
              role="dialog"
              aria-modal="true"
              aria-labelledby="consent-title"
              className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
            >
              <div className="bg-white rounded-xl max-w-md w-full p-6 shadow-xl space-y-4">
                <div className="flex items-center gap-3 text-purple-700">
                  <Bot className="w-6 h-6" />
                  <h3 id="consent-title" className="text-lg font-bold">
                    AI Clinical Notes Consent (Q-004)
                  </h3>
                </div>

                <div className="text-xs text-gray-600 space-y-2 bg-purple-50/50 p-3 rounded-lg border border-purple-100">
                  <p>
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
