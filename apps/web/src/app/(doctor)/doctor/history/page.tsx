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
  Calendar,
  Clock,
  FileText,
  History,
  Phone,
  Search,
  Stethoscope,
  User,
  Users,
} from "lucide-react";

export interface PatientSearchResult {
  id: string;
  name: string;
  phone: string;
  date_of_birth?: string | null;
  gender?: string | null;
  visit_count?: number;
  last_visit_date?: string | null;
  notes?: string | null;
}

export default function DoctorPatientHistorySearchPage() {
  const [query, setQuery] = React.useState("");
  const [patients, setPatients] = React.useState<PatientSearchResult[]>([]);
  const [isLoading, setIsLoading] = React.useState(false);
  const [errorMessage, setErrorMessage] = React.useState<string | null>(null);
  const [searched, setSearched] = React.useState(false);

  const handleSearch = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    const cleanQuery = query.trim();

    if (cleanQuery.length < 2) {
      setErrorMessage("Search karne ke liye kam az kam 2 characters likhein.");
      return;
    }

    setErrorMessage(null);
    setIsLoading(true);
    setSearched(true);

    try {
      const res = await fetch(`/api/v1/patients?query=${encodeURIComponent(cleanQuery)}`);
      if (!res.ok) {
        throw new Error("Mareez daryaft karne mein masla pesh aya.");
      }
      const data = await res.json();
      setPatients(Array.isArray(data) ? data : data.items || []);
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to search patients.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <RoleGuard allowedRoles={["doctor", "owner"]}>
      <LayoutShell
        userRole="doctor"
        userName="Dr. Ahmed Khan"
        clinicName="Shifa Clinic"
        activePath="/doctor/history"
        sidebarNav={[
          {
            label: "Doctor Panel",
            href: "/doctor",
            icon: <Stethoscope className="w-4 h-4" />,
          },
          {
            label: "Patient History",
            href: "/doctor/history",
            icon: <History className="w-4 h-4" />,
            active: true,
          },
        ]}
      >
        <div className="flex flex-col gap-6 max-w-5xl mx-auto w-full">
          {/* Header */}
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 border-b border-border pb-4">
            <div>
              <div className="flex items-center gap-3">
                <h1 className="text-xl font-bold tracking-tight text-fg">
                  Patient Medical History (F-008)
                </h1>
                <StatusBadge variant="info">Doctor Portal</StatusBadge>
              </div>
              <p className="text-xs text-fg-muted mt-1">
                Kisee bhi mareez ka naam ya phone number likh kar uski purani visits, bimarion ka record aur prescriptions check karein.
              </p>
            </div>
            <Link href="/doctor">
              <Button variant="secondary" size="sm" className="flex items-center gap-1.5 text-xs">
                <Stethoscope className="w-3.5 h-3.5" />
                Live OPD Queue Mein Wapas Jayein
              </Button>
            </Link>
          </div>

          {/* Search Box */}
          <div className="bg-surface rounded-xl border border-border p-5 shadow-xs">
            <form onSubmit={handleSearch} className="flex flex-col sm:flex-row gap-3">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-fg-muted" />
                <Input
                  type="text"
                  placeholder="Mareez ka naam ya phone (e.g. Muhammad Ali ya 0300...)"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  className="pl-9 h-10 w-full text-sm"
                  aria-label="Search patients by name or phone"
                />
              </div>
              <Button
                type="submit"
                variant="primary"
                disabled={isLoading}
                className="h-10 px-6 font-semibold"
              >
                {isLoading ? "Dhoond rahe hain..." : "Mareez Dhoondein"}
              </Button>
            </form>

            {errorMessage && (
              <div className="mt-3 flex items-center gap-2 p-3 rounded-md bg-status-danger/10 border border-status-danger/20 text-xs text-status-danger">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{errorMessage}</span>
              </div>
            )}
          </div>

          {/* Results List */}
          <div className="flex flex-col gap-3">
            <div className="flex items-center justify-between text-xs text-fg-muted px-1">
              <span>Search Results ({patients.length})</span>
              {searched && patients.length > 0 && (
                <span>Mareez ki file dekhne ke liye &quot;View Full History&quot; par click karein</span>
              )}
            </div>

            {patients.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {patients.map((p) => (
                  <div
                    key={p.id}
                    className="p-5 rounded-xl border border-border bg-surface shadow-xs hover:border-accent/40 transition-colors flex flex-col justify-between gap-4"
                  >
                    <div>
                      <div className="flex items-start justify-between gap-2 mb-2">
                        <div className="flex items-center gap-2">
                          <div className="w-8 h-8 rounded-full bg-accent/10 text-accent flex items-center justify-center font-bold text-sm">
                            {p.name.charAt(0).toUpperCase()}
                          </div>
                          <div>
                            <h3 className="font-semibold text-sm text-fg">{p.name}</h3>
                            <div className="flex items-center gap-1.5 text-xs text-fg-muted mt-0.5">
                              <Phone className="w-3 h-3" />
                              <span>{p.phone}</span>
                            </div>
                          </div>
                        </div>
                        {p.gender && (
                          <span className="text-[11px] px-2 py-0.5 rounded-full bg-surface-sunken text-fg-muted capitalize">
                            {p.gender}
                          </span>
                        )}
                      </div>

                      {p.notes && (
                        <p className="text-xs text-fg-muted bg-surface-sunken p-2.5 rounded-md mt-2 line-clamp-2">
                          <span className="font-medium text-fg">Notes:</span> {p.notes}
                        </p>
                      )}
                    </div>

                    <div className="pt-3 border-t border-border flex items-center justify-between">
                      <div className="flex items-center gap-1 text-xs text-fg-muted">
                        <FileText className="w-3.5 h-3.5" />
                        <span>Visits: {p.visit_count ?? "0"}</span>
                      </div>
                      <Link href={`/doctor/patients/${p.id}`}>
                        <Button
                          variant="secondary"
                          size="sm"
                          className="text-xs font-semibold hover:border-accent hover:text-accent"
                        >
                          View Full History (F-008) →
                        </Button>
                      </Link>
                    </div>
                  </div>
                ))}
              </div>
            ) : searched ? (
              <div className="p-8 text-center bg-surface rounded-xl border border-border">
                <Users className="w-10 h-10 mx-auto text-fg-muted/40 mb-2" />
                <p className="text-sm font-semibold text-fg">Koi mareez nahi mila</p>
                <p className="text-xs text-fg-muted mt-1">
                  &quot;{query}&quot; ke naam ya number se koi mareez registered nahi mila. Spelling check karein.
                </p>
              </div>
            ) : (
              <div className="p-8 text-center bg-surface rounded-xl border border-dashed border-border">
                <History className="w-10 h-10 mx-auto text-accent/50 mb-2" />
                <p className="text-sm font-semibold text-fg">Mareez ka Medical Record Check Karein</p>
                <p className="text-xs text-fg-muted mt-1 max-w-md mx-auto">
                  Upar search bar mein mareez ka naam ya phone number darj karein taake uski tamam purani visits, bimariyon ki tafseel, aur doctor ke prescription notes dekh sakein.
                </p>
              </div>
            )}
          </div>
        </div>
      </LayoutShell>
    </RoleGuard>
  );
}
