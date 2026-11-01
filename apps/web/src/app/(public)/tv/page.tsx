"use client";

import * as React from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  AlertCircle,
  Clock,
  Radio,
  Tv,
  Volume2,
  VolumeX,
  Wifi,
  WifiOff,
} from "lucide-react";

export interface DisplayDoctorFeed {
  doctor_id: string;
  doctor_name: string;
  specialty?: string | null;
  current_token?: number | null;
  next_tokens: number[];
}

export interface DisplayFeedResponse {
  clinic_name: string;
  doctors: DisplayDoctorFeed[];
  server_time: string;
}

interface TVPageProps {
  initialToken?: string | null;
  initialFeed?: DisplayFeedResponse;
}

export default function TVDisplayPage({
  initialToken = null,
  initialFeed,
}: TVPageProps) {
  const [deviceToken, setDeviceToken] = React.useState<string | null>(initialToken);
  const [feed, setFeed] = React.useState<DisplayFeedResponse | null>(initialFeed || null);
  const [pairingCode, setPairingCode] = React.useState("");
  const [isPairing, setIsPairing] = React.useState(false);
  const [pairingError, setPairingError] = React.useState<string | null>(null);

  // Connection & audio state
  const [lastUpdated, setLastUpdated] = React.useState<Date>(new Date());
  const [currentTime, setCurrentTime] = React.useState<string>("");
  const [isOffline, setIsOffline] = React.useState(false);
  const [isAudioEnabled, setIsAudioEnabled] = React.useState(false);

  // Check stored device token on client mount
  React.useEffect(() => {
    if (!deviceToken && typeof window !== "undefined") {
      const stored = localStorage.getItem("tv_device_token");
      if (stored) {
        setDeviceToken(stored);
      }
    }
  }, [deviceToken]);

  // Live digital clock
  React.useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setCurrentTime(
        now.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" })
      );
      // Connection indicator: offline after 30s without update (PRD §5.3 F-009)
      const diffSecs = (Date.now() - lastUpdated.getTime()) / 1000;
      setIsOffline(diffSecs > 30);
    };

    updateTime();
    const timer = setInterval(updateTime, 1000);
    return () => clearInterval(timer);
  }, [lastUpdated]);

  // Fetch live TV feed
  const fetchFeed = React.useCallback(async (token: string) => {
    try {
      const res = await fetch("/api/v1/display/feed", {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (!res.ok) {
        if (res.status === 401) {
          // Token revoked or invalid
          if (typeof window !== "undefined") {
            localStorage.removeItem("tv_device_token");
          }
          setDeviceToken(null);
          setFeed(null);
          setPairingError("TV access revoked. Please re-pair the device.");
          return;
        }
        throw new Error("Failed to fetch feed");
      }

      const data: DisplayFeedResponse = await res.json();
      setFeed(data);
      setLastUpdated(new Date());
      setIsOffline(false);
    } catch {
      // Non-blocking poll failure
    }
  }, []);

  // Polling loop
  React.useEffect(() => {
    if (!deviceToken) return;

    fetchFeed(deviceToken);
    const interval = setInterval(() => {
      fetchFeed(deviceToken);
    }, 4000);

    return () => clearInterval(interval);
  }, [deviceToken, fetchFeed]);

  // Complete pairing handler
  const handlePairSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setPairingError(null);

    const clean = pairingCode.trim().toUpperCase();
    if (clean.length < 6) {
      setPairingError("6-digit pairing code darj karein.");
      return;
    }

    setIsPairing(true);
    try {
      const res = await fetch("/api/v1/display/pairing/complete", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ pairing_code: clean }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Pairing code ghalat hai ya expire ho chuka hai.");
      }

      const data = await res.json();
      const token = data.device_token;
      if (typeof window !== "undefined") {
        localStorage.setItem("tv_device_token", token);
      }
      setDeviceToken(token);
      setPairingCode("");
      await fetchFeed(token);
    } catch (err: any) {
      setPairingError(err.message || "Pairing fail ho gayi.");
    } finally {
      setIsPairing(false);
    }
  };

  const handleUnpair = () => {
    if (typeof window !== "undefined") {
      localStorage.removeItem("tv_device_token");
    }
    setDeviceToken(null);
    setFeed(null);
  };

  // If not paired, show TV pairing prompt
  if (!deviceToken) {
    return (
      <div className="min-h-screen bg-canvas text-fg flex items-center justify-center p-6">
        <div className="max-w-md w-full bg-surface border border-border rounded-2xl p-8 space-y-6 shadow-2xl text-center">
          <div className="w-16 h-16 rounded-full bg-accent/10 border border-accent/20 mx-auto flex items-center justify-center text-accent">
            <Tv className="w-8 h-8" />
          </div>

          <div>
            <h1 className="text-2xl font-black tracking-tight text-fg">Waiting Room TV Display</h1>
            <p className="text-xs text-fg-muted mt-1.5">
              Clinic settings se 6-digit pairing code hasil kar ke yahan darj karein (F-020).
            </p>
          </div>

          {pairingError && (
            <div className="p-3.5 rounded-md bg-destructive/10 border border-destructive/20 text-destructive text-xs flex items-center gap-2 text-left">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{pairingError}</span>
            </div>
          )}

          <form onSubmit={handlePairSubmit} className="space-y-4">
            <div>
              <label htmlFor="tv-code-input" className="sr-only">
                6-Digit Pairing Code
              </label>
              <Input
                id="tv-code-input"
                type="text"
                placeholder="e.g. ABC999"
                value={pairingCode}
                onChange={(e) => setPairingCode(e.target.value.toUpperCase())}
                maxLength={8}
                className="text-center font-mono text-2xl tracking-widest uppercase h-14 bg-surface-raised border-border font-bold text-accent"
                aria-label="Pairing code input"
                autoFocus
              />
            </div>

            <Button
              type="submit"
              variant="primary"
              disabled={isPairing}
              className="w-full h-12 text-sm font-bold tracking-wider uppercase"
              aria-label="Connect TV button"
            >
              {isPairing ? "CONNECT HO RAHA HAI..." : "CONNECT TV DISPLAY"}
            </Button>
          </form>
        </div>
      </div>
    );
  }

  // Active TV Display (Full screen waiting room mode)
  const doctors = feed?.doctors || [];

  return (
    <div className="min-h-screen bg-[#070b12] text-white flex flex-col justify-between p-6 sm:p-10 select-none">
      {/* Top Header Bar */}
      <header className="flex items-center justify-between pb-6 border-b border-white/10">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-accent/20 border border-accent/40 flex items-center justify-center text-accent">
            <Radio className="w-7 h-7 animate-pulse" />
          </div>
          <div>
            <h1 className="text-3xl sm:text-4xl font-black tracking-tight text-white uppercase">
              {feed?.clinic_name || "Clinic Queue"}
            </h1>
            <span className="text-xs font-semibold tracking-wider text-accent uppercase">
              Waiting Room Live Token Display
            </span>
          </div>
        </div>

        {/* Live Clock & Status */}
        <div className="flex items-center gap-6">
          <div className="text-right">
            <div className="text-2xl sm:text-3xl font-mono font-bold text-white tracking-wider">
              {currentTime}
            </div>
            <div className="flex items-center justify-end gap-1.5 text-xs text-white/60">
              {isOffline ? (
                <span className="flex items-center gap-1 text-amber-400 font-medium">
                  <WifiOff className="w-3.5 h-3.5" /> Offline
                </span>
              ) : (
                <span className="flex items-center gap-1 text-emerald-400 font-medium">
                  <Wifi className="w-3.5 h-3.5" /> Live Connected
                </span>
              )}
            </div>
          </div>

          {/* Sound Announcement Toggle */}
          <button
            onClick={() => setIsAudioEnabled(!isAudioEnabled)}
            className="p-3 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 transition-colors"
            title={isAudioEnabled ? "Chime On" : "Chime Muted"}
            aria-label="Toggle chime audio"
          >
            {isAudioEnabled ? (
              <Volume2 className="w-6 h-6 text-emerald-400" />
            ) : (
              <VolumeX className="w-6 h-6 text-white/40" />
            )}
          </button>
        </div>
      </header>

      {/* Main Doctors Queue Grid (Up to 4 doctors) */}
      <main className="flex-1 my-8">
        {doctors.length > 0 ? (
          <div
            className={`grid gap-6 h-full ${
              doctors.length === 1
                ? "grid-cols-1 max-w-2xl mx-auto"
                : doctors.length === 2
                ? "grid-cols-1 md:grid-cols-2"
                : "grid-cols-1 md:grid-cols-2 lg:grid-cols-4"
            }`}
          >
            {doctors.map((doc) => (
              <div
                key={doc.doctor_id}
                className="bg-white/5 border border-white/10 rounded-2xl p-6 sm:p-8 flex flex-col justify-between shadow-xl backdrop-blur-xs"
              >
                {/* Doctor Title */}
                <div className="pb-4 border-b border-white/10 text-center">
                  <h2 className="text-xl sm:text-2xl font-black text-white truncate">
                    {doc.doctor_name}
                  </h2>
                  {doc.specialty && (
                    <span className="text-xs font-medium text-accent tracking-wide uppercase">
                      {doc.specialty}
                    </span>
                  )}
                </div>

                {/* Current Token Number (Large Focal Point) */}
                <div className="my-8 text-center space-y-2">
                  <span className="text-xs sm:text-sm font-bold tracking-widest uppercase text-white/60">
                    Now Serving / Abhi Number
                  </span>
                  <div className="text-8xl sm:text-9xl font-black tracking-tight text-accent font-mono drop-shadow-md">
                    {doc.current_token ? `#${doc.current_token}` : "--"}
                  </div>
                </div>

                {/* Next Up Tokens (Next 3) */}
                <div className="pt-4 border-t border-white/10 space-y-2">
                  <span className="text-xs font-semibold tracking-wider uppercase text-white/50 block text-center">
                    Next Tokens / Agle Number
                  </span>
                  <div className="flex items-center justify-center gap-3">
                    {doc.next_tokens.length > 0 ? (
                      doc.next_tokens.map((num) => (
                        <span
                          key={num}
                          className="px-4 py-2 rounded-lg bg-white/10 border border-white/15 font-mono font-bold text-lg text-white"
                        >
                          #{num}
                        </span>
                      ))
                    ) : (
                      <span className="text-xs text-white/40 italic py-2">
                        Koi agla token nahi
                      </span>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="h-full flex items-center justify-center text-center text-white/40 py-20">
            <div className="space-y-3">
              <Clock className="w-16 h-16 mx-auto opacity-30" />
              <p className="text-xl font-bold text-white/70">Queue is currently inactive</p>
              <p className="text-sm">Assigned doctors have no active OPD sessions today.</p>
            </div>
          </div>
        )}
      </main>

      {/* Footer Info */}
      <footer className="pt-4 border-t border-white/10 flex items-center justify-between text-xs text-white/40">
        <div>
          <span>Token number bolny par barah-e-karam mutaliqa doctor ke kamray mein tashreef le jayein.</span>
        </div>
        <button
          onClick={handleUnpair}
          className="text-white/30 hover:text-white/70 transition-colors"
          title="Unpair Display Device"
          aria-label="Unpair TV Display"
        >
          Unpair Device
        </button>
      </footer>
    </div>
  );
}
