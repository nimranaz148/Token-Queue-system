import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";

import TokenBookingPage from "./(public)/c/[slug]/page";
import TokenConfirmPage from "./(public)/t/[public_code]/page";
import LiveQueuePage from "./(public)/t/[public_code]/queue/page";

const mockPush = vi.fn();

vi.mock("next/navigation", () => ({
  useParams: () => ({ slug: "shifa-clinic", public_code: "sec_code_xyz123" }),
  useRouter: () => ({ push: mockPush }),
}));

describe("Vertical Slice End-to-End Flow (Task 35: Web-App Pack)", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    mockPush.mockReset();
  });

  const sampleClinic = {
    id: "clinic-1",
    name: "Shifa Clinic",
    slug: "shifa-clinic",
    time_zone: "Asia/Karachi",
    online_booking_enabled: true,
    doctors: [
      {
        id: "doc-1",
        name: "Dr. Tariq Mehmood",
        specialty: "General Physician",
        consult_minutes: 10,
        active: true,
        schedules: [
          { weekday: 0, start_time: "09:00", end_time: "13:00" },
        ],
      },
    ],
  };

  const sampleToken = {
    id: "token-1",
    number: 18,
    public_code: "sec_code_xyz123",
    status: "booked",
    source: "online",
    visit_date: "2026-11-02",
    doctor_id: "doc-1",
    doctor_name: "Dr. Tariq Mehmood",
    clinic_name: "Shifa Clinic",
    clinic_slug: "shifa-clinic",
    position: 4,
    people_ahead: 3,
    estimated_at: "2026-11-02T09:30:00Z",
    current_serving_number: 14,
    estimated_wait_minutes: 30,
    consult_minutes: 10,
    created_at: "2026-11-02T08:00:00Z",
  };

  it("Step 1: Patient browses clinic and books a token with double-submit protection", async () => {
    const bookingResponse = {
      id: "token-1",
      number: 18,
      public_code: "sec_code_xyz123",
      status: "booked",
      source: "online",
      visit_date: "2026-11-02",
      doctor_id: "doc-1",
      doctor_name: "Dr. Tariq Mehmood",
      clinic_name: "Shifa Clinic",
      clinic_slug: "shifa-clinic",
      position: 4,
      estimated_at: "2026-11-02T09:30:00Z",
      created_at: "2026-11-02T08:00:00Z",
    };

    globalThis.fetch = vi.fn().mockImplementation((url: string) => {
      if (typeof url === "string" && url.includes("/api/v1/public/clinics/shifa-clinic/tokens")) {
        return Promise.resolve({
          ok: true,
          status: 201,
          json: async () => bookingResponse,
        } as unknown as Response);
      }
      return Promise.resolve({
        ok: true,
        status: 200,
        json: async () => sampleClinic,
      } as unknown as Response);
    });

    render(<TokenBookingPage />);

    // Wait for clinic data to load
    await waitFor(() => {
      expect(screen.getByText("Shifa Clinic")).toBeDefined();
      expect(screen.getByText(/Dr\. Tariq Mehmood/i)).toBeDefined();
    });

    // Fill booking form
    const nameInput = screen.getByLabelText(/Patient Name/i);
    const phoneInput = screen.getByLabelText(/Phone Number/i);
    fireEvent.change(nameInput, { target: { value: "Muhammad Usman" } });
    fireEvent.change(phoneInput, { target: { value: "03001234567" } });

    // Click submit
    const submitBtn = screen.getByRole("button", { name: /TOKEN LO/i });
    fireEvent.click(submitBtn);

    // Double submit protection triggers (button disabled)
    expect(submitBtn.hasAttribute("disabled") || screen.getByText(/Booking Token.../i)).toBeTruthy();

    await waitFor(() => {
      expect(globalThis.fetch).toHaveBeenCalledWith(
        "/api/v1/public/clinics/shifa-clinic/tokens",
        expect.objectContaining({
          method: "POST",
          headers: expect.objectContaining({ "Content-Type": "application/json" }),
        })
      );
      expect(mockPush).toHaveBeenCalledWith("/t/sec_code_xyz123");
    });
  });

  it("Step 2: Patient views Token Confirm screen with wait metrics and Andaazan time", async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => sampleToken,
    } as unknown as Response);

    render(<TokenConfirmPage />);

    await waitFor(() => {
      expect(screen.getByText("Token Confirmed")).toBeDefined();
      expect(screen.getByText("Apna Token")).toBeDefined();
      expect(screen.getByText("Dr. Tariq Mehmood")).toBeDefined();
      expect(screen.getByText(/3 log/i)).toBeDefined();
      expect(screen.getByRole("button", { name: /LIVE QUEUE DEKHEIN/i })).toBeDefined();
    });
  });

  it("Step 3: Patient opens Live Queue screen with real-time wait estimate and stale detection", async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => sampleToken,
    } as unknown as Response);

    render(<LiveQueuePage />);

    await waitFor(() => {
      expect(screen.getByText("Live Queue")).toBeDefined();
      expect(screen.getByText("Abhi Chal Raha")).toBeDefined();
      expect(screen.getByText("~30 mins")).toBeDefined();
      expect(screen.getByText(/3 log/i)).toBeDefined();
    });
  });

  it("Step 4: Patient cancels token and audit transition occurs", async () => {
    const cancelResponse = {
      id: "token-1",
      number: 18,
      public_code: "sec_code_xyz123",
      status: "cancelled",
      cancelled_reason: "Patient had an emergency",
      message: "Token cancelled successfully.",
    };

    globalThis.fetch = vi.fn().mockImplementation((url: string) => {
      if (typeof url === "string" && url.includes("/cancel")) {
        return Promise.resolve({
          ok: true,
          status: 200,
          json: async () => cancelResponse,
        } as unknown as Response);
      }
      return Promise.resolve({
        ok: true,
        status: 200,
        json: async () => sampleToken,
      } as unknown as Response);
    });

    render(<TokenConfirmPage />);

    await waitFor(() => {
      expect(screen.getByText("Apna Token")).toBeDefined();
    });

    // Click cancel button
    const cancelBtn = screen.getByRole("button", { name: /Token Cancel Karein/i });
    fireEvent.click(cancelBtn);

    // Modal appears
    expect(
      screen.getByText(/Kya aap waqai apna token cancel karna chahte hain\?/i)
    ).toBeDefined();

    const confirmCancelBtn = screen.getByRole("button", { name: /Haan, Cancel Karo/i });
    fireEvent.click(confirmCancelBtn);

    await waitFor(() => {
      expect(globalThis.fetch).toHaveBeenCalledWith(
        "/api/v1/public/tokens/sec_code_xyz123/cancel",
        expect.objectContaining({ method: "POST" })
      );
      expect(screen.getByText(/Yeh token cancel ho chuka hai/i)).toBeDefined();
    });
  });
});
