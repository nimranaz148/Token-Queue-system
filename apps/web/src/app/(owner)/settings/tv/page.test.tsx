import * as React from "react";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";
import TVSettingsPage, { DisplayDeviceItem, DoctorOption } from "./page";

vi.mock("@/components/auth/role-guard", () => ({
  RoleGuard: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="role-guard-pass">{children}</div>
  ),
}));

const mockDoctors: DoctorOption[] = [
  { id: "doc-1", name: "Dr. Tariq Khan", specialty: "Cardiologist" },
  { id: "doc-2", name: "Dr. Ayesha Malik", specialty: "Pediatrician" },
];

const mockDevices: DisplayDeviceItem[] = [
  {
    id: "dev-001",
    name: "Main Waiting Room TV",
    doctor_ids: ["doc-1", "doc-2"],
    paired_at: "2026-11-01T10:00:00Z",
    revoked_at: null,
    is_active: true,
  },
];

describe("F-020 Display Device Pairing Screen", () => {
  beforeEach(() => {
    vi.stubGlobal(
      "fetch",
      vi.fn((url: string | URL | Request, init?: RequestInit) => {
        const urlStr = url.toString();

        if (urlStr.includes("/api/v1/display/devices") && init?.method === "POST") {
          return Promise.resolve({
            ok: true,
            json: async () => ({
              ...mockDevices[0],
              revoked_at: "2026-11-02T12:00:00Z",
              is_active: false,
            }),
          });
        }

        if (urlStr.includes("/api/v1/display/devices")) {
          return Promise.resolve({
            ok: true,
            json: async () => mockDevices,
          });
        }

        if (urlStr.includes("/api/v1/doctors")) {
          return Promise.resolve({
            ok: true,
            json: async () => mockDoctors,
          });
        }

        if (urlStr.includes("/api/v1/display/pairing/initiate") && init?.method === "POST") {
          return Promise.resolve({
            ok: true,
            json: async () => ({
              pairing_code: "ABC999",
              expires_at: "2026-11-02T12:10:00Z",
              device_name: "Waiting Room 2",
            }),
          });
        }

        return Promise.reject(new Error(`Unhandled mock for ${urlStr}`));
      })
    );
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("renders TV settings page with paired device and status", () => {
    render(<TVSettingsPage initialDevices={mockDevices} initialDoctors={mockDoctors} />);

    expect(screen.getByRole("heading", { name: "TV Display Pairing & Screens" })).toBeDefined();
    expect(screen.getByText("Main Waiting Room TV")).toBeDefined();
    expect(screen.getByText("CONNECTED")).toBeDefined();
    expect(screen.getByRole("button", { name: "Pair New TV button" })).toBeDefined();
  });

  it("opens pairing modal and generates 6-digit pairing code", async () => {
    render(<TVSettingsPage initialDevices={mockDevices} initialDoctors={mockDoctors} />);

    fireEvent.click(screen.getByRole("button", { name: "Pair New TV button" }));

    await waitFor(() => {
      expect(screen.getByRole("dialog", { name: "Pair TV Modal" })).toBeDefined();
    });

    const nameInput = screen.getByLabelText("Device name input");
    fireEvent.change(nameInput, { target: { value: "Waiting Room 2" } });

    const docCheckbox = screen.getByLabelText("Doctor Dr. Tariq Khan");
    fireEvent.click(docCheckbox);

    const submitBtn = screen.getByRole("button", { name: "Generate code button" });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(screen.getByText("ABC999")).toBeDefined();
      expect(screen.getByText("6-Digit Pairing Code")).toBeDefined();
    });
  });

  it("revokes display device access on click", async () => {
    render(<TVSettingsPage initialDevices={mockDevices} initialDoctors={mockDoctors} />);

    const revokeBtn = screen.getByRole("button", { name: "Revoke device Main Waiting Room TV" });
    fireEvent.click(revokeBtn);

    await waitFor(() => {
      expect(screen.getByText("TV device authorization kamyabi se revoke ho gayi.")).toBeDefined();
    });
  });
});
