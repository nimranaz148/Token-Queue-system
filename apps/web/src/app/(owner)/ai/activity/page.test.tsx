import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { AIActivityView } from "./page";

// Mock LayoutShell & RoleGuard
vi.mock("@/components/auth/role-guard", () => ({
  RoleGuard: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

vi.mock("@/components/layout/layout-shell", () => ({
  LayoutShell: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

const mockRuns = [
  {
    id: "run-001",
    clinic_id: "clinic-123",
    feature: "chat",
    requested_by: "user-456",
    provider: "openrouter",
    model: "google/gemini-flash",
    tools_called: ["get_my_token_status"],
    input_tokens: 150,
    output_tokens: 60,
    cost_usd: "0.000065",
    status: "success",
    error: null,
    at: "2026-11-01T12:00:00Z",
  },
  {
    id: "run-002",
    clinic_id: "clinic-123",
    feature: "brief",
    requested_by: null,
    provider: "gemini",
    model: "gemini-1.5-flash",
    tools_called: ["get_daily_stats", "detect_anomalies"],
    input_tokens: 500,
    output_tokens: 180,
    cost_usd: "0.000210",
    status: "success",
    error: null,
    at: "2026-11-01T21:00:00Z",
  },
];

describe("AIActivityView (F-017)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders activity logs with provider, model, tokens, and cost", async () => {
    vi.spyOn(global, "fetch").mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        items: mockRuns,
        total: 2,
      }),
    } as Response);

    render(<AIActivityView />);

    expect(screen.getByText(/AI activity load ho rahi hai/i)).toBeDefined();

    await waitFor(() => {
      expect(screen.getByText("AI Activity Log")).toBeDefined();
      expect(screen.getByText("F-017")).toBeDefined();
      expect(screen.getByText("openrouter")).toBeDefined();
      expect(screen.getByText("gemini")).toBeDefined();
      expect(screen.getByText("$0.000065")).toBeDefined();
      expect(screen.getByText("Kul record: 2")).toBeDefined();
    });
  });

  it("displays empty state when no activity records exist", async () => {
    vi.spyOn(global, "fetch").mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        items: [],
        total: 0,
      }),
    } as Response);

    render(<AIActivityView />);

    await waitFor(() => {
      expect(screen.getByText(/Koi AI activity record nahi mila/i)).toBeDefined();
    });
  });

  it("handles filter changes and triggers refetch", async () => {
    const fetchSpy = vi.spyOn(global, "fetch").mockResolvedValue({
      ok: true,
      json: async () => ({ items: [], total: 0 }),
    } as Response);

    render(<AIActivityView />);

    await waitFor(() => {
      expect(fetchSpy).toHaveBeenCalledWith("/api/v1/ai/activity?");
    });

    // Change feature filter
    const select = screen.getByLabelText(/Feature:/i);
    fireEvent.change(select, { target: { value: "chat" } });

    await waitFor(() => {
      expect(fetchSpy).toHaveBeenCalledWith("/api/v1/ai/activity?feature=chat");
    });
  });

  it("handles API error and displays retry button", async () => {
    vi.spyOn(global, "fetch").mockResolvedValueOnce({
      ok: false,
      status: 500,
    } as Response);

    render(<AIActivityView />);

    await waitFor(() => {
      expect(
        screen.getByText(/AI activity record load karne mein masla pesh aya/i)
      ).toBeDefined();
      expect(screen.getByText(/Dobara Koshish/i)).toBeDefined();
    });
  });
});
