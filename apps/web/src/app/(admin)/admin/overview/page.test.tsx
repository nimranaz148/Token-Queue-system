import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import PlatformOverviewPage, { PlatformOverviewData } from "./page";

// Mock LayoutShell to render children
vi.mock("@/components/layout/layout-shell", () => ({
  LayoutShell: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

// Mock RoleGuard to render children
vi.mock("@/components/auth/role-guard", () => ({
  RoleGuard: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

const mockData: PlatformOverviewData = {
  kpis: {
    active_clinics: 12,
    total_clinics: 15,
    tokens_today: 420,
    tokens_7_days: 2840,
    idle_clinics: 2,
    ai_spend_this_month: "4.20",
  },
  clinics: [
    {
      id: "clinic-1",
      name: "Shifa Family Clinic",
      slug: "shifa-family",
      status: "active",
      tokens_7d: 840,
      tokens_today: 125,
      last_activity: "2026-11-02T12:00:00Z",
    },
    {
      id: "clinic-2",
      name: "Al-Razi Medical Complex",
      slug: "al-razi",
      status: "active",
      tokens_7d: 620,
      tokens_today: 95,
      last_activity: "2026-11-02T11:00:00Z",
    },
  ],
};

const emptyData: PlatformOverviewData = {
  kpis: {
    active_clinics: 0,
    total_clinics: 0,
    tokens_today: 0,
    tokens_7_days: 0,
    idle_clinics: 0,
    ai_spend_this_month: "0.00",
  },
  clinics: [],
};

describe("D-002 Platform Overview (Platform Admin Dashboard)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    global.fetch = vi.fn().mockImplementation((url: string) => {
      if (url.includes("/api/v1/admin/overview")) {
        return Promise.resolve({
          ok: true,
          status: 200,
          json: () => Promise.resolve(mockData),
        });
      }
      return Promise.reject(new Error("Unknown route"));
    });
  });

  it("renders all 5 top KPI cards matching PRD wireframe D-002", () => {
    render(<PlatformOverviewPage initialData={mockData} />);

    expect(screen.getByRole("heading", { name: "Platform Overview" })).toBeDefined();

    // Check KPI 1: Active Clinics
    expect(screen.getByText("12")).toBeDefined();
    expect(screen.getByText("of 15 registered")).toBeDefined();

    // Check KPI 2: Tokens Today
    expect(screen.getByText("420")).toBeDefined();

    // Check KPI 3: Tokens 7d
    expect(screen.getByText("2840")).toBeDefined();

    // Check KPI 4: Idle Clinics
    expect(screen.getByText("2")).toBeDefined();
    expect(screen.getByText("Zero activity 3+ days")).toBeDefined();

    // Check KPI 5: AI Spend
    expect(screen.getByText("$4.20")).toBeDefined();
  });

  it("renders clinics table with clinic records, statuses, and volume", () => {
    render(<PlatformOverviewPage initialData={mockData} />);

    expect(screen.getByText("Shifa Family Clinic")).toBeDefined();
    expect(screen.getByText("/c/shifa-family")).toBeDefined();
    expect(screen.getByText("840")).toBeDefined();

    expect(screen.getByText("Al-Razi Medical Complex")).toBeDefined();
    expect(screen.getByText("/c/al-razi")).toBeDefined();
    expect(screen.getByText("620")).toBeDefined();
  });

  it("filters clinics table in real-time by search query", () => {
    render(<PlatformOverviewPage initialData={mockData} />);

    const searchInput = screen.getByPlaceholderText("Search clinics...");
    fireEvent.change(searchInput, { target: { value: "Al-Razi" } });

    expect(screen.getByText("Al-Razi Medical Complex")).toBeDefined();
    expect(screen.queryByText("Shifa Family Clinic")).toBeNull();
  });

  it("renders clean empty state when dataset has 0 clinics without error", () => {
    render(<PlatformOverviewPage initialData={emptyData} />);

    expect(screen.getByText("Koi clinic register nahi hua")).toBeDefined();
    expect(
      screen.getByText("No clinic records found matching current query.")
    ).toBeDefined();
  });

  it("fetches overview telemetry when refresh button is clicked", async () => {
    render(<PlatformOverviewPage initialData={mockData} />);

    const refreshButton = screen.getByRole("button", { name: /Refresh Telemetry/i });
    fireEvent.click(refreshButton);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith("/api/v1/admin/overview");
    });
  });
});
