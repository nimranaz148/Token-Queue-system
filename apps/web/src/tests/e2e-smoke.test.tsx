import React, { act } from "react";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";

import { AuthProvider, useAuth } from "@/lib/auth/auth-context";
import LoginPage from "@/app/(auth)/login/page";
import DoctorManagementPage from "@/app/(owner)/settings/doctors/page";
import TokenBookingPage from "@/app/(public)/c/[slug]/page";
import TokenConfirmPage from "@/app/(public)/t/[public_code]/page";
import LiveQueuePage from "@/app/(public)/t/[public_code]/queue/page";

// Mock Next.js navigation hooks
const pushMock = vi.fn();
const backMock = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({
    push: pushMock,
    back: backMock,
  }),
  useParams: () => ({
    slug: "al-shifa",
    public_code: "TK-20261102-001",
  }),
}));

function createJwt(role: string, clinicId: string, email: string): string {
  const header = btoa(JSON.stringify({ alg: "HS256", typ: "JWT" }));
  const payload = btoa(
    JSON.stringify({
      sub: "usr-smoke-1",
      email,
      name: "Dr. Owner",
      role,
      clinic_id: clinicId,
      exp: Math.floor(Date.now() / 1000) + 7200,
    })
  );
  return `${header}.${payload}.signature`;
}

describe("E2E Smoke Test of the Critical Flow (Task 38)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  it("completes full critical flow: staff sign-in -> doctor schedule management -> patient token booking -> token confirmation -> live queue", async () => {
    // -------------------------------------------------------------
    // Step 1: Staff Magic Link Sign-In (F-012)
    // -------------------------------------------------------------
    const mockAuthToken = createJwt("owner", "clinic-alshifa-id", "owner@alshifa.pk");

    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation((url: string, options?: RequestInit) => {
        // Staff Magic Link
        if (typeof url === "string" && url.includes("/api/v1/auth/magic-link")) {
          return Promise.resolve({
            ok: true,
            status: 200,
            json: async () => ({
              message: "Login link email kar diya",
              success: true,
              token: mockAuthToken,
              memberships: [
                {
                  clinic_id: "clinic-alshifa-id",
                  clinic_name: "Al-Shifa Clinic",
                  role: "owner",
                },
              ],
            }),
          });
        }

        // Doctor Management API
        if (typeof url === "string" && url.includes("/api/v1/doctors")) {
          return Promise.resolve({
            ok: true,
            status: 200,
            json: async () => ({
              items: [
                {
                  id: "doc-1",
                  name: "Dr. Tariq Khan",
                  specialty: "General Physician",
                  is_active: true,
                  consult_duration_minutes: 15,
                  daily_online_limit: 20,
                  schedule: [
                    { day_of_week: "monday", start_time: "09:00", end_time: "14:00" },
                    { day_of_week: "wednesday", start_time: "09:00", end_time: "14:00" },
                  ],
                },
              ],
              total: 1,
            }),
          });
        }

        // Clinic Public Details (F-001)
        if (typeof url === "string" && url.endsWith("/al-shifa")) {
          return Promise.resolve({
            ok: true,
            status: 200,
            json: async () => ({
              id: "clinic-alshifa-id",
              name: "Al-Shifa Clinic",
              slug: "al-shifa",
              time_zone: "Asia/Karachi",
              address: "Shop 4, Main Commercial, DHA Phase 5, Lahore",
              phone: "+923001234567",
              online_booking_enabled: true,
              doctors: [
                {
                  id: "doc-1",
                  name: "Dr. Tariq Khan",
                  specialty: "General Physician",
                  consult_minutes: 15,
                  daily_online_limit: 20,
                  schedules: [
                    { weekday: 0, start_time: "09:00", end_time: "17:00" },
                  ],
                },
              ],
            }),
          });
        }

        // Token Booking API
        if (typeof url === "string" && url.includes("/tokens") && options?.method === "POST") {
          return Promise.resolve({
            ok: true,
            status: 201,
            json: async () => ({
              public_code: "TK-20261102-001",
              token_number: 1,
              status: "BOOKED",
              tracking_url: "/t/TK-20261102-001",
              doctor_name: "Dr. Tariq Khan",
              andaazan_time: "10:00 AM",
              people_ahead: 0,
            }),
          });
        }

        // Token Details / Live Queue API
        if (typeof url === "string" && url.includes("/api/v1/public/tokens/TK-20261102-001")) {
          return Promise.resolve({
            ok: true,
            status: 200,
            json: async () => ({
              id: "token-1",
              number: 1,
              public_code: "TK-20261102-001",
              status: "BOOKED",
              source: "ONLINE",
              visit_date: "2026-11-02",
              doctor_id: "doc-1",
              doctor_name: "Dr. Tariq Khan",
              specialty: "General Physician",
              clinic_id: "clinic-alshifa-id",
              clinic_name: "Al-Shifa Clinic",
              clinic_slug: "al-shifa",
              position: 1,
              people_ahead: 0,
              estimated_wait_minutes: 0,
              current_serving_number: 1,
              estimated_at: "10:00 AM",
              created_at: new Date().toISOString(),
            }),
          });
        }

        return Promise.resolve({
          ok: true,
          status: 200,
          json: async () => ({}),
        });
      })
    );

    // 1. Render login screen and submit email
    const { unmount: unmountLogin } = render(<LoginPage />);
    expect(screen.getByText("Staff Login")).toBeDefined();

    const emailInput = screen.getByLabelText(/Email/i);
    fireEvent.change(emailInput, { target: { value: "owner@alshifa.pk" } });

    const loginBtn = screen.getByRole("button", { name: /Login Link Bhejein|LOGIN/i });
    fireEvent.click(loginBtn);

    await waitFor(() => {
      expect(screen.getByText("Login link email kar diya")).toBeDefined();
    });
    unmountLogin();

    // -------------------------------------------------------------
    // Step 2: Authenticated Session & Doctor Management Screen (F-016)
    // -------------------------------------------------------------
    // Store token in localStorage and render Doctor Management under AuthProvider
    localStorage.setItem("auth_token", mockAuthToken);

    const { unmount: unmountDoctor } = render(
      <AuthProvider initialToken={mockAuthToken}>
        <DoctorManagementPage
          initialDoctors={[
            {
              id: "doc-1",
              clinic_id: "clinic-alshifa-id",
              name: "Dr. Tariq Khan",
              specialty: "General Physician",
              active: true,
              consult_minutes: 15,
              daily_online_limit: 20,
              schedules: [
                { weekday: 0, start_time: "09:00", end_time: "14:00" },
                { weekday: 2, start_time: "09:00", end_time: "14:00" },
              ],
              created_at: "2026-11-01T00:00:00Z",
            },
          ]}
        />
      </AuthProvider>
    );

    // Verify doctor management screen loads with doctor details and schedule
    expect(screen.getByText("Doctor Management")).toBeDefined();
    expect(screen.getByText("Dr. Tariq Khan")).toBeDefined();
    expect(screen.getByText("General Physician")).toBeDefined();
    expect(screen.getByText(/20 tokens\/day/i)).toBeDefined(); // Daily limit
    unmountDoctor();

    // -------------------------------------------------------------
    // Step 3: Patient Token Booking (F-001)
    // -------------------------------------------------------------
    const { unmount: unmountBooking } = render(<TokenBookingPage />);

    // Wait for booking page to finish loading data
    await waitFor(() => {
      expect(screen.getByText(/Dr\. Tariq Khan/i)).toBeDefined();
    });

    // Fill booking form
    const nameInput = screen.getByLabelText(/Patient Name/i);
    fireEvent.change(nameInput, { target: { value: "Muhammad Bilal" } });

    const phoneInput = screen.getByLabelText(/Phone Number/i);
    fireEvent.change(phoneInput, { target: { value: "03001234567" } });

    // Submit booking form
    const bookBtn = screen.getByRole("button", { name: /TOKEN LO/i });
    fireEvent.click(bookBtn);

    await waitFor(() => {
      expect(pushMock).toHaveBeenCalledWith("/t/TK-20261102-001");
    });
    unmountBooking();

    // -------------------------------------------------------------
    // Step 4: Token Confirmation View (F-002)
    // -------------------------------------------------------------
    const { unmount: unmountConfirm } = render(<TokenConfirmPage />);

    await waitFor(() => {
      expect(screen.getAllByText("#1").length).toBeGreaterThan(0);
    });

    // Verify token confirmation details
    expect(screen.getByText(/Token Confirmed/i)).toBeDefined();
    expect(screen.getByText("Al-Shifa Clinic")).toBeDefined();
    expect(screen.getByText(/LIVE QUEUE DEKHEIN/i)).toBeDefined();

    // Click Live Queue Dekhein
    const liveQueueBtn = screen.getByRole("button", { name: /LIVE QUEUE DEKHEIN/i });
    fireEvent.click(liveQueueBtn);
    expect(pushMock).toHaveBeenCalledWith("/t/TK-20261102-001/queue");
    unmountConfirm();

    // -------------------------------------------------------------
    // Step 5: Live Queue Status View (F-003)
    // -------------------------------------------------------------
    const { unmount: unmountQueue } = render(<LiveQueuePage />);

    await waitFor(() => {
      expect(screen.getByText(/Abhi Chal Raha/i)).toBeDefined();
    });

    // Verify live queue view
    expect(screen.getByText("Live Queue")).toBeDefined();
    expect(screen.getByText("Your Position")).toBeDefined();

    // Toggle browser reminder switch
    const reminderSwitch = screen.getByRole("switch", { name: /Browser queue reminder/i });
    expect(reminderSwitch).toBeDefined();
    fireEvent.click(reminderSwitch);

    unmountQueue();
    vi.unstubAllGlobals();
  });
});
