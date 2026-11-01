import React from "react";
import { render, waitFor } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";
import axe from "axe-core";

import TokenBookingPage from "@/app/(public)/c/[slug]/page";
import TokenConfirmPage from "@/app/(public)/t/[public_code]/page";
import LiveQueuePage from "@/app/(public)/t/[public_code]/queue/page";

const mockPush = vi.fn();

vi.mock("next/navigation", () => ({
  useParams: () => ({ slug: "shifa-clinic", public_code: "sec_code_xyz123" }),
  useRouter: () => ({ push: mockPush }),
}));

describe("Accessibility and Performance Gates (Task 37)", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
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

  it("Axe audit: Public Token Booking screen has zero critical/serious a11y issues", async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => sampleClinic,
    } as unknown as Response);

    const { container } = render(<TokenBookingPage />);

    await waitFor(() => {
      expect(container.querySelector("h1")).not.toBeNull();
    });

    const results = await axe.run(container, {
      rules: {
        // In jsdom unit tests, page landmark/region rules require full HTML doc
        region: { enabled: false },
        "color-contrast": { enabled: false }, // jsdom does not calculate CSS render colors
      },
    });

    const seriousViolations = results.violations.filter(
      (v) => v.impact === "critical" || v.impact === "serious"
    );

    expect(seriousViolations).toEqual([]);
  });

  it("Axe audit: Token Confirm screen has zero critical/serious a11y issues", async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => sampleToken,
    } as unknown as Response);

    const { container } = render(<TokenConfirmPage />);

    await waitFor(() => {
      expect(container.querySelector("h1")).not.toBeNull();
    });

    const results = await axe.run(container, {
      rules: {
        region: { enabled: false },
        "color-contrast": { enabled: false },
      },
    });

    const seriousViolations = results.violations.filter(
      (v) => v.impact === "critical" || v.impact === "serious"
    );

    expect(seriousViolations).toEqual([]);
  });

  it("Axe audit: Live Queue screen has zero critical/serious a11y issues", async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => sampleToken,
    } as unknown as Response);

    const { container } = render(<LiveQueuePage />);

    await waitFor(() => {
      expect(container.querySelector("h1")).not.toBeNull();
    });

    const results = await axe.run(container, {
      rules: {
        region: { enabled: false },
        "color-contrast": { enabled: false },
      },
    });

    const seriousViolations = results.violations.filter(
      (v) => v.impact === "critical" || v.impact === "serious"
    );

    expect(seriousViolations).toEqual([]);
  });

  it("Performance budget gate: Rendered DOM tree is lightweight (< 200 DOM nodes per view)", async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => sampleToken,
    } as unknown as Response);

    const { container: bookingContainer } = render(<TokenBookingPage />);
    const { container: queueContainer } = render(<LiveQueuePage />);

    // Count DOM elements
    const bookingNodes = bookingContainer.querySelectorAll("*").length;
    const queueNodes = queueContainer.querySelectorAll("*").length;

    // Strict DOM budget: < 200 elements ensures high performance and instant first render on mobile
    expect(bookingNodes).toBeLessThan(200);
    expect(queueNodes).toBeLessThan(200);
  });
});
