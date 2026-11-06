"use client";

import React, { useState, useContext } from "react";
import { useRouter } from "next/navigation";
import { FormShell } from "@/components/form/form-shell";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { StatusBadge } from "@/components/ui/status-badge";
import { AuthContext } from "@/lib/auth/auth-context";

interface ClinicMembership {
  clinic_id: string;
  clinic_name: string;
  role: string;
}

export default function LoginPage() {
  let router: ReturnType<typeof useRouter> | null = null;
  try {
    // eslint-disable-next-line react-hooks/rules-of-hooks
    router = useRouter();
  } catch {
    // Graceful fallback for non-Next router environments (e.g. testing)
  }

  const authContext = useContext(AuthContext);

  const [mode, setMode] = useState<"magic_link" | "password">("magic_link");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [emailError, setEmailError] = useState("");
  const [passwordError, setPasswordError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [successMessage, setSuccessMessage] = useState("");
  const [generalError, setGeneralError] = useState("");
  const [memberships, setMemberships] = useState<ClinicMembership[]>([]);
  const [selectedClinicId, setSelectedClinicId] = useState<string>("");

  const getApiBase = (): string => {
    const raw = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    return raw.replace(/\/api\/v1\/?$/, "");
  };

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

  const handleRoleRedirect = (token: string) => {
    if (authContext?.login) {
      authContext.login(token);
    } else if (typeof window !== "undefined") {
      localStorage.setItem("auth_token", token);
    }

    try {
      const parts = token.split(".");
      if (parts.length === 3) {
        const payload = JSON.parse(
          decodeURIComponent(
            atob(parts[1].replace(/-/g, "+").replace(/_/g, "/"))
              .split("")
              .map((c) => "%" + ("00" + c.charCodeAt(0).toString(16)).slice(-2))
              .join("")
          )
        );
        const role = payload.role;
        const target =
          role === "doctor"
            ? "/doctor"
            : role === "reception"
            ? "/tokens"
            : role === "owner"
            ? "/settings"
            : role === "platform_admin" || payload.is_platform_admin
            ? "/admin/overview"
            : "/doctor";

        if (router && typeof router.push === "function") {
          router.push(target);
        } else if (typeof window !== "undefined") {
          window.location.href = target;
        }
      }
    } catch {
      if (router && typeof router.push === "function") {
        router.push("/doctor");
      }
    }
  };

  const handlePasswordLogin = async (e?: React.FormEvent, customEmail?: string, customPassword?: string) => {
    if (e) e.preventDefault();
    const loginEmail = customEmail || email;
    const loginPass = customPassword || password;

    if (!validateEmail(loginEmail)) return;
    if (!loginPass.trim()) {
      setPasswordError("Password zaroori hai (Password required)");
      return;
    }
    setPasswordError("");
    setIsLoading(true);
    setGeneralError("");
    setSuccessMessage("");

    try {
      const apiUrl = getApiBase();
      const res = await fetch(`${apiUrl}/api/v1/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: loginEmail.trim(),
          password: loginPass,
        }),
      });

      const data = await res.json();
      if (!res.ok) {
        setGeneralError(data.detail || "Ghalat email ya password. Dobara check karein.");
        return;
      }

      if (data.access_token) {
        setSuccessMessage("Login kamyab! Redirecting...");
        handleRoleRedirect(data.access_token);
      }
    } catch {
      setGeneralError("Network error. Baraye meherbani dobara koshish karein.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleMagicLinkSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validateEmail(email)) {
      return;
    }

    setIsLoading(true);
    setGeneralError("");
    setSuccessMessage("");

    try {
      const apiUrl = getApiBase();
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

      if (data.token) {
        if (authContext?.login) {
          authContext.login(data.token);
        } else if (typeof window !== "undefined") {
          localStorage.setItem("auth_token", data.token);
        }
      }

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

  const handleQuickLogin = (roleEmail: string, rolePass: string) => {
    setEmail(roleEmail);
    setPassword(rolePass);
    void handlePasswordLogin(undefined, roleEmail, rolePass);
  };

  return (
    <main className="min-h-screen w-full flex items-center justify-center p-4 bg-surface-sunken">
      <div className="w-full max-w-[480px] bg-surface p-6 rounded-xl border border-border shadow-xs">
        {/* Toggle Login Method */}
        <div className="flex border-b border-border mb-6">
          <button
            type="button"
            onClick={() => {
              setMode("magic_link");
              setGeneralError("");
              setSuccessMessage("");
            }}
            className={`pb-2.5 px-4 text-sm font-semibold border-b-2 transition-colors ${
              mode === "magic_link"
                ? "border-accent text-accent font-bold"
                : "border-transparent text-fg-muted hover:text-fg"
            }`}
          >
            Magic Link
          </button>
          <button
            type="button"
            onClick={() => {
              setMode("password");
              setGeneralError("");
              setSuccessMessage("");
            }}
            className={`pb-2.5 px-4 text-sm font-semibold border-b-2 transition-colors ${
              mode === "password"
                ? "border-accent text-accent font-bold"
                : "border-transparent text-fg-muted hover:text-fg"
            }`}
          >
            Password
          </button>
        </div>

        <form onSubmit={mode === "password" ? handlePasswordLogin : handleMagicLinkSubmit} noValidate>
          <FormShell
            title="Aapka Clinic"
            badge={<StatusBadge variant="info">Staff Login</StatusBadge>}
            description={
              mode === "password"
                ? "Staff portal mein dakhil honay ke liye apna registered email aur password darj karein."
                : "Staff portal mein dakhil honay ke liye apna registered email darj karein."
            }
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

                {mode === "password" && (
                  <Input
                    label="Password"
                    type="password"
                    placeholder="••••••••••••"
                    value={password}
                    disabled={isLoading}
                    error={passwordError}
                    onChange={(e) => {
                      setPassword(e.target.value);
                      if (passwordError) setPasswordError("");
                    }}
                    required
                  />
                )}

                {successMessage && (
                  <div className="p-3 rounded-md bg-success-subtle border border-success text-success text-sm flex flex-col gap-1">
                    <span className="font-medium">{successMessage}</span>
                    {mode === "magic_link" && (
                      <span className="text-xs opacity-90">
                        Apni email inbox check karein aur magic link par click karein. Link 15 minute ke liye karamad hai.
                      </span>
                    )}
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
                {mode === "magic_link" && successMessage ? (
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
                    {isLoading
                      ? "Process ho raha hai..."
                      : mode === "password"
                      ? "LOGIN"
                      : "Login Link Bhejein"}
                  </Button>
                )}
              </div>
            }
            auditPanel={
              <div className="flex flex-col gap-3 pt-3">
                <span className="text-xs text-fg-muted">
                  Single-use 15-minute link · 5 requests per hour per email · PECA 2016 Compliant
                </span>

                {/* Quick 1-Click Demo Login Bar */}
                <div className="p-3 rounded-lg border border-border bg-surface-sunken">
                  <span className="text-xs font-semibold text-fg block mb-2">
                    ⚡ Quick Demo Login (1-Click):
                  </span>
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <Button
                      type="button"
                      variant="secondary"
                      size="sm"
                      className="text-xs justify-start h-8"
                      disabled={isLoading}
                      onClick={() => handleQuickLogin("doctor@example.com", "DoctorPass123!")}
                    >
                      👨‍⚕️ Doctor
                    </Button>
                    <Button
                      type="button"
                      variant="secondary"
                      size="sm"
                      className="text-xs justify-start h-8"
                      disabled={isLoading}
                      onClick={() => handleQuickLogin("reception@example.com", "ReceptionPass123!")}
                    >
                      👩‍💼 Reception
                    </Button>
                    <Button
                      type="button"
                      variant="secondary"
                      size="sm"
                      className="text-xs justify-start h-8"
                      disabled={isLoading}
                      onClick={() => handleQuickLogin("owner@example.com", "OwnerPass123!")}
                    >
                      👑 Clinic Owner
                    </Button>
                    <Button
                      type="button"
                      variant="secondary"
                      size="sm"
                      className="text-xs justify-start h-8"
                      disabled={isLoading}
                      onClick={() => handleQuickLogin("admin@example.com", "AdminPass123!")}
                    >
                      🛡️ Super Admin
                    </Button>
                  </div>
                </div>
              </div>
            }
          />
        </form>
      </div>
    </main>
  );
}
