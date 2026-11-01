import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { AICommandCenterView } from "./page";

// Mock LayoutShell & RoleGuard
vi.mock("@/components/auth/role-guard", () => ({
  RoleGuard: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

vi.mock("@/components/layout/layout-shell", () => ({
  LayoutShell: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

const mockCommandCenterData = {
  ai_calls: 142,
  failures: 3,
  fallback_rate: 0.021,
  total_cost_usd: "0.084200",
  thumbs_down_rate: 0.045,
  recent_runs: [
    {
      id: "run-101",
      feature: "chat",
      provider: "openrouter",
      model: "google/gemini-flash",
      cost_usd: "0.000045",
      status: "success",
      at: "2026-11-01T14:30:00Z",
      tools_called: ["get_my_token_status"],
    },
  ],
};

describe("AICommandCenterView (D-003)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders 5 KPI cards with live metrics and recent runs table", async () => {
    vi.spyOn(global, "fetch").mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => mockCommandCenterData,
    } as Response);

    render(<AICommandCenterView />);

    expect(screen.getByText(/Command Center data load ho raha hai/i)).toBeDefined();

    await waitFor(() => {
      expect(screen.getByText("AI Command Center")).toBeDefined();
      expect(screen.getByText("D-003")).toBeDefined();
      expect(screen.getByText("142")).toBeDefined(); // AI Calls
      expect(screen.getByText("3")).toBeDefined(); // Failures
      expect(screen.getByText("2.1%")).toBeDefined(); // Fallback Rate
      expect(screen.getByText("$0.0842")).toBeDefined(); // AI Spend
      expect(screen.getByText("4.5%")).toBeDefined(); // Thumbs-down
      expect(screen.getByText("chat")).toBeDefined();
    });
  });

  it("handles empty dataset without errors", async () => {
    vi.spyOn(global, "fetch").mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => ({
        ai_calls: 0,
        failures: 0,
        fallback_rate: 0.0,
        total_cost_usd: "0.000000",
        thumbs_down_rate: 0.0,
        recent_runs: [],
      }),
    } as Response);

    render(<AICommandCenterView />);

    await waitFor(() => {
      expect(screen.getAllByText("0").length).toBeGreaterThanOrEqual(2);
      expect(screen.getAllByText("0.0%").length).toBe(2);
      expect(screen.getByText(/Abhi tak koi AI run record nahi hua/i)).toBeDefined();
    });
  });

  it("handles API failure with retry option", async () => {
    vi.spyOn(global, "fetch").mockResolvedValueOnce({
      ok: false,
      status: 500,
    } as Response);

    render(<AICommandCenterView />);

    await waitFor(() => {
      expect(
        screen.getByText(/Command Center KPIs load karne mein masla pesh aya/i)
      ).toBeDefined();
      expect(screen.getByText("Dobara Koshish")).toBeDefined();
    });
  });
});
