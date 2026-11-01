import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { DailyBriefView } from "./page";

// Mock LayoutShell & RoleGuard
vi.mock("@/components/auth/role-guard", () => ({
  RoleGuard: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

vi.mock("@/components/layout/layout-shell", () => ({
  LayoutShell: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

const mockBrief = {
  id: "brief-001",
  clinic_id: "clinic-123",
  date: "2026-11-01",
  body_md: "## Nightly Operations Summary\n- 45 patients served today.\n- Average wait was 14 minutes.",
  anomalies: [
    {
      type: "high_wait",
      doctor: "Dr. Tariq",
      wait_min: 52,
    },
  ],
  feedback: null,
  created_at: "2026-11-01T21:00:00Z",
};

describe("DailyBriefView (F-018)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders daily brief with summary markdown and detected anomalies", async () => {
    vi.spyOn(global, "fetch").mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => mockBrief,
    } as Response);

    render(<DailyBriefView />);

    expect(screen.getByText(/Daily brief load ho raha hai/i)).toBeDefined();

    await waitFor(() => {
      expect(screen.getByText("Daily Brief")).toBeDefined();
      expect(screen.getByText("F-018")).toBeDefined();
      expect(screen.getByText(/45 patients served today/i)).toBeDefined();
      expect(screen.getByText(/Detected Anomalies \(1\)/i)).toBeDefined();
      expect(screen.getByText(/Dr. Tariq wait time was 52 min/i)).toBeDefined();
    });
  });

  it("displays empty state when no brief exists and triggers generation", async () => {
    const fetchSpy = vi.spyOn(global, "fetch");

    // Initial fetch returns 404
    fetchSpy.mockResolvedValueOnce({
      ok: false,
      status: 404,
    } as Response);

    render(<DailyBriefView />);

    await waitFor(() => {
      expect(
        screen.getByText(/Is tareekh ka koi daily brief mojood nahi hai/i)
      ).toBeDefined();
      expect(screen.getByText(/Abhi Tajzia Generate Karein/i)).toBeDefined();
    });

    // Generate request
    fetchSpy.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => mockBrief,
    } as Response);

    fireEvent.click(screen.getByText(/Abhi Tajzia Generate Karein/i));

    await waitFor(() => {
      expect(fetchSpy).toHaveBeenCalledWith(
        expect.stringContaining("/api/v1/ai/daily-brief/generate"),
        expect.objectContaining({ method: "POST" })
      );
      expect(screen.getByText(/45 patients served today/i)).toBeDefined();
    });
  });

  it("submits thumbs up feedback", async () => {
    const fetchSpy = vi.spyOn(global, "fetch");

    // Initial fetch
    fetchSpy.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => mockBrief,
    } as Response);

    // Feedback response
    fetchSpy.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => ({ ...mockBrief, feedback: "up" }),
    } as Response);

    render(<DailyBriefView />);

    await waitFor(() => {
      expect(screen.getByText(/Haan \(Helpful\)/i)).toBeDefined();
    });

    fireEvent.click(screen.getByText(/Haan \(Helpful\)/i));

    await waitFor(() => {
      expect(fetchSpy).toHaveBeenCalledWith(
        "/api/v1/ai/daily-brief/brief-001/feedback",
        expect.objectContaining({
          method: "POST",
          body: JSON.stringify({ feedback: "up" }),
        })
      );
      expect(screen.getByText(/Shukriya!/i)).toBeDefined();
    });
  });
});
