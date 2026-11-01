import * as React from "react";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";
import DoctorPanelPage, { DoctorQueueData } from "./page";

vi.mock("@/components/auth/role-guard", () => ({
  RoleGuard: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="role-guard-pass">{children}</div>
  ),
}));

const mockQueueData: DoctorQueueData = {
  doctor_id: "doc-111",
  doctor_name: "Dr. Ayesha Malik",
  visit_date: "2026-11-02",
  current_token: {
    id: "tok-cur-1",
    number: 12,
    public_code: "code-cur-12",
    status: "serving",
    source: "online",
    patient_id: "pat-101",
    patient_name: "Muhammad Usman",
    patient_age: 35,
    patient_gender: "male",
    position: 12,
    arrived_at: "2026-11-02T09:00:00Z",
    called_at: "2026-11-02T09:30:00Z",
    created_at: "2026-11-02T08:00:00Z",
  },
  next_tokens: [
    {
      id: "tok-next-2",
      number: 13,
      public_code: "code-next-13",
      status: "arrived",
      source: "walk_in",
      patient_id: "pat-102",
      patient_name: "Fatima Zahra",
      patient_age: 28,
      patient_gender: "female",
      position: 13,
      arrived_at: "2026-11-02T09:15:00Z",
      created_at: "2026-11-02T08:15:00Z",
    },
    {
      id: "tok-next-3",
      number: 14,
      public_code: "code-next-14",
      status: "booked",
      source: "online",
      patient_id: "pat-103",
      patient_name: "Bilal Ahmed",
      patient_age: 42,
      patient_gender: "male",
      position: 14,
      created_at: "2026-11-02T08:30:00Z",
    },
  ],
  waiting_tokens: [],
  skipped_tokens: [
    {
      id: "tok-skip-9",
      number: 9,
      public_code: "code-skip-9",
      status: "hold",
      source: "online",
      patient_id: "pat-109",
      patient_name: "Zainab Bibi",
      patient_age: 50,
      position: 9,
      cancelled_reason: "Waiting for blood reports",
      created_at: "2026-11-02T07:45:00Z",
    },
  ],
  counts: {
    total: 10,
    serving: 1,
    arrived: 4,
    booked: 3,
    hold: 1,
    skipped: 0,
    done: 2,
  },
};

describe("F-007 Next Patient Doctor Consultation Panel", () => {
  beforeEach(() => {
    vi.stubGlobal(
      "fetch",
      vi.fn((url: string | URL | Request, init?: RequestInit) => {
        const urlStr = url.toString();

        if (urlStr.includes("/api/v1/tokens/doctor/queue")) {
          return Promise.resolve({
            ok: true,
            json: async () => mockQueueData,
          });
        }

        if (urlStr.includes("/api/v1/tokens/doctor/next") && init?.method === "POST") {
          return Promise.resolve({
            ok: true,
            json: async () => ({
              success: true,
              message: "Called patient #13",
            }),
          });
        }

        if (urlStr.includes("/api/v1/tokens/doctor/skip") && init?.method === "POST") {
          return Promise.resolve({
            ok: true,
            json: async () => ({
              success: true,
              message: "Patient #12 has been skipped.",
            }),
          });
        }

        if (urlStr.includes("/api/v1/tokens/doctor/hold") && init?.method === "POST") {
          return Promise.resolve({
            ok: true,
            json: async () => ({
              success: true,
              message: "Patient #12 placed on hold.",
            }),
          });
        }

        if (urlStr.includes("/api/v1/tokens/doctor/recall") && init?.method === "POST") {
          return Promise.resolve({
            ok: true,
            json: async () => ({
              success: true,
              message: "Patient #9 recalled to front of queue.",
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

  it("renders doctor panel with active serving patient, next in line, and queue counts", () => {
    render(<DoctorPanelPage initialQueue={mockQueueData} />);

    expect(
      screen.getByRole("heading", { name: "Doctor Consultation Panel" })
    ).toBeDefined();
    expect(screen.getByText("#12")).toBeDefined();
    expect(screen.getByText("Muhammad Usman")).toBeDefined();
    expect(screen.getByText(/35 saal/)).toBeDefined();
    expect(screen.getByText("Fatima Zahra")).toBeDefined();
    expect(screen.getByText("Bilal Ahmed")).toBeDefined();
    expect(screen.getByRole("button", { name: "Call next patient button" })).toBeDefined();
    expect(screen.getByRole("button", { name: "Skip patient button" })).toBeDefined();
    expect(screen.getByRole("button", { name: "Hold patient button" })).toBeDefined();
  });

  it("calls next patient when NEXT button is clicked with quick consult note", async () => {
    render(<DoctorPanelPage initialQueue={mockQueueData} />);

    const noteInput = screen.getByLabelText("Quick consult note");
    fireEvent.change(noteInput, { target: { value: "Blood pressure normal, prescribe multivitamins" } });

    const nextBtn = screen.getByRole("button", { name: "Call next patient button" });
    fireEvent.click(nextBtn);

    await waitFor(() => {
      expect(screen.getByText("Called patient #13")).toBeDefined();
    });
  });

  it("skips current patient when Skip button is clicked", async () => {
    render(<DoctorPanelPage initialQueue={mockQueueData} />);

    const skipBtn = screen.getByRole("button", { name: "Skip patient button" });
    fireEvent.click(skipBtn);

    await waitFor(() => {
      expect(screen.getByText("Patient #12 has been skipped.")).toBeDefined();
    });
  });

  it("opens hold dialog, enters reason, and submits hold action", async () => {
    render(<DoctorPanelPage initialQueue={mockQueueData} />);

    const holdBtn = screen.getByRole("button", { name: "Hold patient button" });
    fireEvent.click(holdBtn);

    await waitFor(() => {
      expect(screen.getByRole("dialog", { name: "Hold Patient Dialog" })).toBeDefined();
    });

    const reasonInput = screen.getByLabelText("Hold reason");
    fireEvent.change(reasonInput, { target: { value: "Waiting for chest X-ray" } });

    const confirmBtn = screen.getByRole("button", { name: "Confirm Hold" });
    fireEvent.click(confirmBtn);

    await waitFor(() => {
      expect(screen.getByText("Patient #12 placed on hold.")).toBeDefined();
    });
  });

  it("recalls a skipped or hold patient back to the queue", async () => {
    render(<DoctorPanelPage initialQueue={mockQueueData} />);

    expect(screen.getByText("Zainab Bibi")).toBeDefined();
    expect(screen.getByText(/Wajah: Waiting for blood reports/)).toBeDefined();

    const recallBtn = screen.getByRole("button", { name: "Recall token 9" });
    fireEvent.click(recallBtn);

    await waitFor(() => {
      expect(screen.getByText("Patient #9 recalled to front of queue.")).toBeDefined();
    });
  });
});
