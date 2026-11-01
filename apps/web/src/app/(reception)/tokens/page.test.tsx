import * as React from "react";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";
import ReceptionTokensPage, { ReceptionTokenItem } from "./page";

vi.mock("@/components/auth/role-guard", () => ({
  RoleGuard: ({ children }: { children: React.ReactNode }) => <div data-testid="role-guard-pass">{children}</div>,
}));

const mockTokensData: ReceptionTokenItem[] = [
  {
    id: "tk-001",
    number: 1,
    patient_id: "p-001",
    patient_name: "Muhammad Usman",
    phone: "***4567",
    source: "online",
    status: "booked",
    doctor_id: "doc-001",
    doctor_name: "Dr. Tariq Khan",
    visit_date: "2026-11-02",
    position: 1,
    created_at: "2026-11-02T08:00:00Z",
  },
  {
    id: "tk-002",
    number: 2,
    patient_id: "p-002",
    patient_name: "Fatima Zahra",
    phone: "***6543",
    source: "walk_in",
    status: "arrived",
    doctor_id: "doc-002",
    doctor_name: "Dr. Ayesha Malik",
    visit_date: "2026-11-02",
    position: 2,
    created_at: "2026-11-02T08:15:00Z",
  },
];

const mockDoctorsData = [
  { id: "doc-001", name: "Dr. Tariq Khan" },
  { id: "doc-002", name: "Dr. Ayesha Malik" },
];

describe("F-004 Aaj ki List Reception Screen", () => {
  beforeEach(() => {
    vi.stubGlobal(
      "fetch",
      vi.fn((url: string | URL | Request, init?: RequestInit) => {
        const urlStr = url.toString();

        if (urlStr.includes("/api/v1/doctors")) {
          return Promise.resolve({
            ok: true,
            json: async () => mockDoctorsData,
          });
        }

        if (urlStr.includes("/api/v1/tokens/tk-001/arrive")) {
          return Promise.resolve({
            ok: true,
            json: async () => ({
              ...mockTokensData[0],
              status: "arrived",
              arrived_at: "2026-11-02T09:00:00Z",
            }),
          });
        }

        if (urlStr.includes("/api/v1/tokens/tk-001/cancel")) {
          const body = JSON.parse(init?.body as string);
          return Promise.resolve({
            ok: true,
            json: async () => ({
              ...mockTokensData[0],
              status: "cancelled",
              cancelled_reason: body.reason,
            }),
          });
        }

        if (urlStr.includes("/api/v1/tokens")) {
          return Promise.resolve({
            ok: true,
            json: async () => ({
              items: mockTokensData,
              total: 2,
              date: "2026-11-02",
            }),
          });
        }

        return Promise.reject(new Error(`Unhandled fetch: ${urlStr}`));
      })
    );
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("renders Aaj ki List with header, counts, and filters", () => {
    render(<ReceptionTokensPage initialTokens={mockTokensData} />);

    expect(screen.getByRole("heading", { name: /Aaj ki List/i })).toBeDefined();
    expect(screen.getByText(/2 Tokens/i)).toBeDefined();

    // Filters
    expect(screen.getByLabelText(/Visit Date/i)).toBeDefined();
    expect(screen.getByLabelText(/Doctor Filter/i)).toBeDefined();
    expect(screen.getByLabelText(/Status Filter/i)).toBeDefined();
    expect(screen.getByLabelText(/Search tokens/i)).toBeDefined();
  });

  it("renders tokens table with masked phone, badges, and doctor name", async () => {
    render(<ReceptionTokensPage initialTokens={mockTokensData} />);

    await waitFor(() => {
      expect(screen.getByText("#1")).toBeDefined();
      expect(screen.getByText("Muhammad Usman")).toBeDefined();
      expect(screen.getByText("***4567")).toBeDefined();
      expect(screen.getByText("Online")).toBeDefined();
      expect(screen.getByText("BOOKED")).toBeDefined();

      expect(screen.getByText("#2")).toBeDefined();
      expect(screen.getByText("Fatima Zahra")).toBeDefined();
      expect(screen.getByText("***6543")).toBeDefined();
      expect(screen.getByText("Walk-in")).toBeDefined();
      expect(screen.getByText("ARRIVED")).toBeDefined();
    });
  });

  it("triggers Mark Arrived on a booked token and updates state", async () => {
    render(<ReceptionTokensPage initialTokens={mockTokensData} />);

    const markArrivedBtn = screen.getByLabelText("Mark arrived for token 1");
    expect(markArrivedBtn).toBeDefined();

    fireEvent.click(markArrivedBtn);

    await waitFor(() => {
      expect(screen.getByText(/arrived mark ho gaya/i)).toBeDefined();
    });
  });

  it("opens cancel dialog, enforces reason, and submits cancel action", async () => {
    render(<ReceptionTokensPage initialTokens={mockTokensData} />);

    const cancelBtn = screen.getByLabelText("Cancel token 1");
    fireEvent.click(cancelBtn);

    // Modal opens
    expect(screen.getByText(/Token Mansookh Karein/i)).toBeDefined();
    const reasonInput = screen.getByLabelText(/Cancellation reason/i);

    // Type valid reason
    fireEvent.change(reasonInput, { target: { value: "Patient emergency" } });
    const confirmBtn = screen.getByRole("button", { name: "Mansookh Karein" });
    fireEvent.click(confirmBtn);

    await waitFor(() => {
      expect(screen.getByText(/mansookh \(cancelled\) ho gaya/i)).toBeDefined();
    });
  });
});
