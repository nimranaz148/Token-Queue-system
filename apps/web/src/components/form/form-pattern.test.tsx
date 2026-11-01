import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";

import TokenBookingPage from "@/app/(public)/c/[slug]/page";
import DoctorManagementPage, { DoctorItem } from "@/app/(owner)/settings/doctors/page";

const mockPush = vi.fn();

vi.mock("next/navigation", () => ({
  useParams: () => ({ slug: "shifa-clinic", public_code: "code-123" }),
  useRouter: () => ({ push: mockPush }),
}));

describe("Form Pattern: Validation, Error Display, Double-Submit Protection (Task 36)", () => {
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

  it("Client and Server reject identical invalid inputs (Token Booking validation)", async () => {
    globalThis.fetch = vi.fn().mockImplementation((url: string) => {
      if (typeof url === "string" && url.includes("/tokens")) {
        return Promise.resolve({
          ok: false,
          status: 422,
          json: async () => ({
            code: "VALIDATION_ERROR",
            detail: "Invalid Pakistani mobile phone number format",
          }),
        } as unknown as Response);
      }
      return Promise.resolve({
        ok: true,
        status: 200,
        json: async () => sampleClinic,
      } as unknown as Response);
    });

    render(<TokenBookingPage />);

    await waitFor(() => {
      expect(screen.getByText("Shifa Clinic")).toBeDefined();
    });

    // 1. Client-side validation: <10 digits rejected before network call
    const submitBtn = screen.getByRole("button", { name: /TOKEN LO/i });
    const nameInput = screen.getByLabelText(/Patient Name/i);
    const phoneInput = screen.getByLabelText(/Phone Number/i);

    fireEvent.change(nameInput, { target: { value: "Usman" } });
    fireEvent.change(phoneInput, { target: { value: "12345" } });
    fireEvent.click(submitBtn);

    expect(
      screen.getByText(/Please enter a valid phone number/i)
    ).toBeDefined();

    // 2. Server-side validation: valid length submitted but server rejects
    fireEvent.change(phoneInput, { target: { value: "03009999999" } });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(
        screen.getByText(/Invalid Pakistani mobile phone number format/i)
      ).toBeDefined();
    });
  });

  it("Double-submit protection: second click during flight does not create a second record", async () => {
    let callCount = 0;
    // Delay resolution to simulate in-flight request
    globalThis.fetch = vi.fn().mockImplementation((url: string) => {
      if (typeof url === "string" && url.includes("/tokens")) {
        callCount++;
        return new Promise((resolve) =>
          setTimeout(
            () =>
              resolve({
                ok: true,
                status: 201,
                json: async () => ({
                  id: "tok-1",
                  number: 1,
                  public_code: "code-1",
                  status: "booked",
                  doctor_name: "Dr. Tariq",
                  clinic_name: "Shifa Clinic",
                }),
              } as unknown as Response),
            200
          )
        );
      }
      return Promise.resolve({
        ok: true,
        status: 200,
        json: async () => sampleClinic,
      } as unknown as Response);
    });

    render(<TokenBookingPage />);

    await waitFor(() => {
      expect(screen.getByText("Shifa Clinic")).toBeDefined();
    });

    const nameInput = screen.getByLabelText(/Patient Name/i);
    const phoneInput = screen.getByLabelText(/Phone Number/i);
    fireEvent.change(nameInput, { target: { value: "Ali Khan" } });
    fireEvent.change(phoneInput, { target: { value: "03001234567" } });

    const submitBtn = screen.getByRole("button", { name: /TOKEN LO/i });

    // First click initiates booking
    fireEvent.click(submitBtn);

    // Submit button immediately disabled
    expect(submitBtn.hasAttribute("disabled")).toBe(true);

    // Rapid second click during flight
    fireEvent.click(submitBtn);
    fireEvent.click(submitBtn);

    // Await completion
    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith("/t/code-1");
    });

    // Exactly one POST call was made, preventing double booking
    const postCalls = (globalThis.fetch as any).mock.calls.filter((call: any[]) =>
      call[0].includes("/tokens")
    );
    expect(postCalls.length).toBe(1);
    expect(callCount).toBe(1);
  });

  it("Doctor Management form: client validation on schedule end_time > start_time", async () => {
    const existingDoctor: DoctorItem = {
      id: "doc-1",
      clinic_id: "clinic-1",
      name: "Dr. Tariq Mehmood",
      specialty: "General Physician",
      daily_online_limit: 20,
      consult_minutes: 10,
      active: true,
      schedules: [],
      created_at: "2026-11-01T00:00:00Z",
    };

    render(
      <DoctorManagementPage
        initialDoctors={[existingDoctor]}
        userRole="owner"
      />
    );

    // Open schedule modal
    const opdBtn = screen.getByRole("button", { name: /Manage schedule for Dr. Tariq Mehmood/i });
    fireEvent.click(opdBtn);

    // Add a slot
    const addSlotBtn = screen.getByRole("button", { name: /\+ Add Slot/i });
    fireEvent.click(addSlotBtn);

    // Invert times: start 14:00, end 09:00
    const startInput = screen.getByLabelText(/Start time for slot 1/i);
    const endInput = screen.getByLabelText(/End time for slot 1/i);
    fireEvent.change(startInput, { target: { value: "14:00" } });
    fireEvent.change(endInput, { target: { value: "09:00" } });

    // Click Save Schedule
    const saveBtn = screen.getByRole("button", { name: /Save Schedule/i });
    fireEvent.click(saveBtn);

    // Client-side validation prevents API request and displays clean error
    expect(
      screen.getByText(/End time must be after start time for all OPD slots/i)
    ).toBeDefined();
  });
});
