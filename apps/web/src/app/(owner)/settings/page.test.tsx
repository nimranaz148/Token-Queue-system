import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import ClinicSettingsPage, { ClinicSettingsData } from "./page";

// Mock LayoutShell to render children
vi.mock("@/components/layout/layout-shell", () => ({
  LayoutShell: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

// Mock RoleGuard to render children
vi.mock("@/components/auth/role-guard", () => ({
  RoleGuard: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

const mockInitialSettings: ClinicSettingsData = {
  clinic_id: "clinic-test-123",
  clinic_name: "Al-Razi Health Center",
  slug: "al-razi",
  time_zone: "Asia/Karachi",
  address: "123 Main Clinic Boulevard",
  phone: "+92 300 9876543",
  maps_url: "https://maps.google.com/?q=al-razi",
  logo_path: null,

  online_booking_enabled: true,
  daily_online_limit: 45,
  advance_days: 1,
  default_consult_minutes: 12,
  call_only_arrived: false,
  language_default: "en",
  share_advice_with_patient: true,
  ai_notes_enabled: false,
  version: 2,
  updated_at: "2026-11-01T10:00:00Z",
};

describe("F-011 Clinic Settings (Owner Settings)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    global.fetch = vi.fn().mockImplementation((url: string, options?: RequestInit) => {
      if (url.includes("/api/v1/settings")) {
        if (options && options.method === "PUT") {
          const body = JSON.parse(options.body as string);
          return Promise.resolve({
            ok: true,
            status: 200,
            json: () =>
              Promise.resolve({
                ...mockInitialSettings,
                ...body,
                version: body.version + 1,
              }),
          });
        }
        return Promise.resolve({
          ok: true,
          status: 200,
          json: () => Promise.resolve(mockInitialSettings),
        });
      }
      return Promise.reject(new Error("Unknown route"));
    });
  });

  it("renders all mandated operational and profile fields per PRD §5.3 F-011", () => {
    render(<ClinicSettingsPage initialSettings={mockInitialSettings} />);

    expect(screen.getByRole("heading", { name: "Clinic Settings" })).toBeDefined();
    expect(screen.getByText("Version v2")).toBeDefined();

    // Section 1: Queue rules
    expect(screen.getByLabelText("Online token booking ON/OFF")).toBeDefined();
    expect(screen.getByDisplayValue("45")).toBeDefined();
    expect(screen.getByDisplayValue("12")).toBeDefined();
    expect(screen.getByLabelText("Advance Booking Days")).toBeDefined();
    expect(screen.getByLabelText("Call only arrived patients")).toBeDefined();

    // Section 2: Clinic profile
    expect(screen.getByDisplayValue("Al-Razi Health Center")).toBeDefined();
    expect(screen.getByDisplayValue("+92 300 9876543")).toBeDefined();
    expect(screen.getByDisplayValue("123 Main Clinic Boulevard")).toBeDefined();
    expect(screen.getByLabelText("Clinic Timezone")).toBeDefined();
    expect(screen.getByLabelText("Default Language")).toBeDefined();

    // Section 3: Privacy & AI
    expect(screen.getByLabelText("Share visit advice with patient")).toBeDefined();
    expect(screen.getByLabelText("Enable AI clinical notes processing")).toBeDefined();
  });

  it("shows AI consent modal when ai_notes_enabled is toggled ON (Q-004)", async () => {
    render(<ClinicSettingsPage initialSettings={mockInitialSettings} />);

    const aiSwitch = screen.getByLabelText("Enable AI clinical notes processing") as HTMLInputElement;
    expect(aiSwitch.checked).toBe(false);

    // Toggle switch ON
    fireEvent.click(aiSwitch);

    // Verify modal is displayed
    expect(screen.getByText("AI Clinical Notes Consent (Q-004)")).toBeDefined();
    expect(
      screen.getByText(/zero-data-retention terms/i)
    ).toBeDefined();

    // Click Accept & Enable
    const acceptButton = screen.getByRole("button", { name: /Accept & Enable AI/i });
    fireEvent.click(acceptButton);

    // Modal closed and switch is ON
    expect(screen.queryByText("AI Clinical Notes Consent (Q-004)")).toBeNull();
    expect(aiSwitch.checked).toBe(true);
  });

  it("submits updated values via PUT /api/v1/settings with optimistic lock version", async () => {
    render(<ClinicSettingsPage initialSettings={mockInitialSettings} />);

    // Modify daily limit
    const limitInput = screen.getByLabelText(/Roz ka token limit/i);
    fireEvent.change(limitInput, { target: { value: "60" } });

    // Submit form
    const saveButton = screen.getByRole("button", { name: /Save Settings/i });
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        "/api/v1/settings",
        expect.objectContaining({
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: expect.stringContaining('"version":2'),
        })
      );
    });

    // Check version incremented to v3
    await waitFor(() => {
      expect(screen.getByText("Version v3")).toBeDefined();
    });
  });

  it("displays version conflict error when API returns 409 Conflict", async () => {
    global.fetch = vi.fn().mockImplementation((url: string, options?: RequestInit) => {
      if (options && options.method === "PUT") {
        return Promise.resolve({
          ok: false,
          status: 409,
          json: () => Promise.resolve({ detail: "Version conflict" }),
        });
      }
      return Promise.resolve({
        ok: true,
        status: 200,
        json: () => Promise.resolve(mockInitialSettings),
      });
    });

    render(<ClinicSettingsPage initialSettings={mockInitialSettings} />);

    const saveButton = screen.getByRole("button", { name: /Save Settings/i });
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(
        screen.getByText(/Settings conflict: Version changed by another user/i)
      ).toBeDefined();
    });
  });
});
