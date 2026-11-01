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
  CheckCircle,
  Copy,
  Clock,
  PlusCircle,
  Settings,
  Trash2,
  Tv,
  Users,
  X,
} from "lucide-react";

export interface DisplayDeviceItem {
  id: string;
  name: string;
  doctor_ids: string[];
  paired_at: string;
  revoked_at?: string | null;
  is_active: boolean;
}

export interface DoctorOption {
  id: string;
  name: string;
  specialty?: string | null;
}

interface TVSettingsPageProps {
  initialDevices?: DisplayDeviceItem[];
  initialDoctors?: DoctorOption[];
  userRole?: string;
}

export default function TVSettingsPage({
  initialDevices = [],
  initialDoctors = [],
  userRole = "owner",
}: TVSettingsPageProps) {
  const [devices, setDevices] = React.useState<DisplayDeviceItem[]>(initialDevices);
  const [doctors, setDoctors] = React.useState<DoctorOption[]>(initialDoctors);
  const [isLoading, setIsLoading] = React.useState(initialDevices.length === 0);
  const [pageError, setPageError] = React.useState<string | null>(null);
  const [pageSuccess, setPageSuccess] = React.useState<string | null>(null);

  // Pairing modal state
  const [showPairModal, setShowPairModal] = React.useState(false);
  const [deviceName, setDeviceName] = React.useState("");
  const [selectedDoctorIds, setSelectedDoctorIds] = React.useState<string[]>([]);
  const [isInitiating, setIsInitiating] = React.useState(false);
  const [modalError, setModalError] = React.useState<string | null>(null);
  const [generatedCode, setGeneratedCode] = React.useState<string | null>(null);
  const [codeExpiresAt, setCodeExpiresAt] = React.useState<string | null>(null);

  const fetchDevicesAndDoctors = React.useCallback(async () => {
    try {
      const [devRes, docRes] = await Promise.all([
        fetch("/api/v1/display/devices"),
        fetch("/api/v1/doctors"),
      ]);
      if (devRes.ok) {
        const devData = await devRes.json();
        setDevices(Array.isArray(devData) ? devData : devData.items || []);
      }
      if (docRes.ok) {
        const docData = await docRes.json();
        setDoctors(Array.isArray(docData) ? docData : docData.items || []);
      }
    } catch {
      // Non-blocking
    } finally {
      setIsLoading(false);
    }
  }, []);

  React.useEffect(() => {
    if (initialDevices.length === 0 || initialDoctors.length === 0) {
      fetchDevicesAndDoctors();
    }
  }, [initialDevices, initialDoctors, fetchDevicesAndDoctors]);

  const handleToggleDoctor = (docId: string) => {
    setSelectedDoctorIds((prev) =>
      prev.includes(docId) ? prev.filter((id) => id !== docId) : [...prev, docId]
    );
  };

  const handleInitiatePairing = async (e: React.FormEvent) => {
    e.preventDefault();
    setModalError(null);

    if (!deviceName.trim() || deviceName.trim().length < 2) {
      setModalError("Device ka naam kam az kam 2 characters hona chahiye.");
      return;
    }
    if (selectedDoctorIds.length === 0 || selectedDoctorIds.length > 4) {
      setModalError("Kam az kam 1 aur ziyada se ziyada 4 doctors muntakhib karein.");
      return;
    }

    setIsInitiating(true);
    try {
      const res = await fetch("/api/v1/display/pairing/initiate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          device_name: deviceName.trim(),
          doctor_ids: selectedDoctorIds,
        }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Pairing code banane mein masla pesh aya.");
      }

      const data = await res.json();
      setGeneratedCode(data.pairing_code);
      setCodeExpiresAt(data.expires_at);
    } catch (err: any) {
      setModalError(err.message || "Failed to initiate pairing.");
    } finally {
      setIsInitiating(false);
    }
  };

  const handleRevokeDevice = async (deviceId: string) => {
    setPageError(null);
    setPageSuccess(null);

    try {
      const res = await fetch(`/api/v1/display/devices/${deviceId}/revoke`, {
        method: "POST",
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Display device revoke karne mein masla pesh aya.");
      }

      const updated = await res.json();
      setDevices((prev) => prev.map((d) => (d.id === updated.id ? updated : d)));
      setPageSuccess("TV device authorization kamyabi se revoke ho gayi.");
    } catch (err: any) {
      setPageError(err.message || "Failed to revoke device.");
    }
  };

  const handleCloseModal = () => {
    setShowPairModal(false);
    setDeviceName("");
    setSelectedDoctorIds([]);
    setGeneratedCode(null);
    setCodeExpiresAt(null);
    setModalError(null);
    fetchDevicesAndDoctors();
  };

  return (
    <RoleGuard allowedRoles={["owner"]}>
      <LayoutShell
        userRole={userRole}
        navItems={[
          { label: "Clinic Settings", href: "/settings", icon: <Settings className="w-4 h-4" /> },
          { label: "Doctors", href: "/settings/doctors", icon: <Users className="w-4 h-4" /> },
          { label: "TV Screens (F-020)", href: "/settings/tv", icon: <Tv className="w-4 h-4" />, active: true },
        ]}
      >
        <div className="max-w-5xl mx-auto space-y-6">
          {/* Header */}
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-4 border-b border-border">
            <div>
              <div className="flex items-center gap-2">
                <Tv className="w-6 h-6 text-accent" />
                <h1 className="text-2xl font-bold tracking-tight text-fg">
                  TV Display Pairing & Screens
                </h1>
                <span className="text-xs font-semibold px-2 py-0.5 rounded bg-purple-500/10 text-purple-400 border border-purple-500/20 uppercase">
                  F-020
                </span>
              </div>
              <p className="text-sm text-fg-muted mt-1">
                Waiting room TV screens ko connect karein aur un par dikhaye jane waly doctors assign karein
              </p>
            </div>

            <Button
              variant="primary"
              onClick={() => setShowPairModal(true)}
              aria-label="Pair New TV button"
            >
              <PlusCircle className="w-4 h-4 mr-1.5" />
              Naya TV Connect Karein
            </Button>
          </div>

          {/* Feedback Alerts */}
          {pageError && (
            <div className="p-3.5 rounded-md bg-destructive/10 border border-destructive/20 text-destructive text-sm flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{pageError}</span>
            </div>
          )}

          {pageSuccess && (
            <div className="p-3.5 rounded-md bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-sm flex items-center gap-2">
              <CheckCircle className="w-4 h-4 shrink-0" />
              <span>{pageSuccess}</span>
            </div>
          )}

          {/* Connected TV Devices List */}
          <div className="bg-surface border border-border rounded-lg overflow-hidden">
            <div className="px-4 py-3 border-b border-border bg-surface-raised flex items-center justify-between">
              <span className="text-xs font-semibold text-fg-muted uppercase tracking-wider">
                Paired TV Screens ({devices.length})
              </span>
              <Link href="/tv" target="_blank" className="text-xs text-accent hover:underline flex items-center gap-1">
                Open /tv in new tab
              </Link>
            </div>

            {devices.length > 0 ? (
              <div className="divide-y divide-border">
                {devices.map((dev) => (
                  <div
                    key={dev.id}
                    className="p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4 hover:bg-surface-hover/40 transition-colors"
                  >
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <Tv className="w-4 h-4 text-accent" />
                        <span className="font-semibold text-sm text-fg">{dev.name}</span>
                        <StatusBadge variant={dev.is_active ? "success" : "danger"}>
                          {dev.is_active ? "CONNECTED" : "REVOKED"}
                        </StatusBadge>
                      </div>
                      <div className="text-xs text-fg-muted flex items-center gap-3">
                        <span>Doctors: <strong className="text-fg">{dev.doctor_ids.length} assigned</strong></span>
                        <span>•</span>
                        <span>Paired: {new Date(dev.paired_at).toLocaleDateString()}</span>
                      </div>
                    </div>

                    {dev.is_active && (
                      <Button
                        variant="secondary"
                        size="sm"
                        onClick={() => handleRevokeDevice(dev.id)}
                        className="text-destructive hover:bg-destructive/10 self-start sm:self-center"
                        aria-label={`Revoke device ${dev.name}`}
                      >
                        <Trash2 className="w-3.5 h-3.5 mr-1" />
                        Revoke Access
                      </Button>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="py-14 text-center text-fg-muted space-y-2">
                <Tv className="w-10 h-10 mx-auto text-fg-muted/40" />
                <p className="text-sm font-medium text-fg">Koi TV screen connect nahi hai</p>
                <p className="text-xs text-fg-muted max-w-sm mx-auto">
                  Apne clinic ke waiting room TV ko connect karne ke liye "Naya TV Connect Karein" dabayein.
                </p>
              </div>
            )}
          </div>

          {/* Pairing Modal */}
          {showPairModal && (
            <div
              className="fixed inset-0 z-50 bg-black/60 backdrop-blur-xs flex items-center justify-center p-4 animate-in fade-in duration-150"
              role="dialog"
              aria-modal="true"
              aria-label="Pair TV Modal"
            >
              <div className="bg-surface border border-border rounded-lg shadow-xl max-w-md w-full p-6 space-y-4">
                <div className="flex items-center justify-between border-b border-border pb-3">
                  <h3 className="text-base font-bold text-fg flex items-center gap-2">
                    <Tv className="w-5 h-5 text-accent" />
                    Waiting Room TV Connect Karein
                  </h3>
                  <button
                    onClick={handleCloseModal}
                    className="p-1 rounded text-fg-muted hover:text-fg"
                    aria-label="Close modal"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>

                {modalError && (
                  <div className="p-3 rounded-md bg-destructive/10 border border-destructive/20 text-destructive text-xs flex items-center gap-2">
                    <AlertCircle className="w-4 h-4 shrink-0" />
                    <span>{modalError}</span>
                  </div>
                )}

                {!generatedCode ? (
                  <form onSubmit={handleInitiatePairing} className="space-y-4">
                    <div>
                      <label htmlFor="tv-device-name" className="block text-xs font-medium text-fg-muted mb-1">
                        Device Name (e.g. Waiting Room 55 inch TV) <span className="text-destructive">*</span>
                      </label>
                      <Input
                        id="tv-device-name"
                        value={deviceName}
                        onChange={(e) => setDeviceName(e.target.value)}
                        placeholder="Waiting Room TV"
                        required
                        aria-label="Device name input"
                      />
                    </div>

                    <div>
                      <label className="block text-xs font-medium text-fg-muted mb-1.5">
                        Doctors Select Karein (1 se 4 doctors) <span className="text-destructive">*</span>
                      </label>
                      <div className="space-y-1.5 max-h-48 overflow-y-auto p-2 bg-surface-raised rounded-md border border-border">
                        {doctors.map((doc) => (
                          <label
                            key={doc.id}
                            className="flex items-center gap-2.5 p-2 rounded hover:bg-surface-hover/60 cursor-pointer text-xs"
                          >
                            <input
                              type="checkbox"
                              checked={selectedDoctorIds.includes(doc.id)}
                              onChange={() => handleToggleDoctor(doc.id)}
                              className="rounded border-border text-accent focus:ring-accent"
                              aria-label={`Doctor ${doc.name}`}
                            />
                            <span className="font-medium text-fg">
                              {doc.name} {doc.specialty ? `(${doc.specialty})` : ""}
                            </span>
                          </label>
                        ))}
                      </div>
                      <p className="text-xs text-fg-muted mt-1">
                        Muntakhib kardah: {selectedDoctorIds.length} / 4
                      </p>
                    </div>

                    <div className="flex justify-end gap-2 pt-2 border-t border-border">
                      <Button type="button" variant="secondary" onClick={handleCloseModal}>
                        Cancel
                      </Button>
                      <Button
                        type="submit"
                        variant="primary"
                        disabled={isInitiating}
                        aria-label="Generate code button"
                      >
                        {isInitiating ? "Code ban raha hai..." : "Pairing Code Banao"}
                      </Button>
                    </div>
                  </form>
                ) : (
                  <div className="text-center space-y-4 py-2">
                    <div className="p-5 rounded-lg bg-surface-raised border border-accent/40 space-y-2">
                      <span className="text-xs font-semibold text-fg-muted uppercase tracking-wider block">
                        6-Digit Pairing Code
                      </span>
                      <div className="text-4xl font-mono font-black tracking-widest text-accent">
                        {generatedCode}
                      </div>
                      <span className="text-xs text-fg-muted block">
                        Ye code 10 minutes tak qabil-e-istemal hai.
                      </span>
                    </div>

                    <div className="text-xs text-fg-muted bg-surface-raised/50 p-3 rounded-md text-left space-y-1">
                      <p className="font-semibold text-fg">Pairing ka tareeqa:</p>
                      <p>1. Apne Smart TV ya TV Browser par <strong className="text-accent font-mono">/tv</strong> kholein.</p>
                      <p>2. Screen par ye 6-digit code darj karein.</p>
                      <p>3. TV foran live queue screen mein tabdeel ho jaye ga.</p>
                    </div>

                    <Button variant="primary" className="w-full" onClick={handleCloseModal}>
                      Mukammal (Done)
                    </Button>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </LayoutShell>
    </RoleGuard>
  );
}
