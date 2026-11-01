import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import RozKiReportPage, { DailyReportData } from "./page";

// Mock LayoutShell to render children
vi.mock("@/components/layout/layout-shell", () => ({
  LayoutShell: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

// Mock RoleGuard to render children
vi.mock("@/components/auth/role-guard", () => ({
  RoleGuard: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

const mockData: DailyReportData = {
  clinic_id: "clinic-test-1",
  date: "2026-11-02",
  doctor_id: null,
  doctor_name: null,
  kpis: {
    patients_seen: 54,
    avg_wait_minutes: "14.0",
    no_shows: 6,
    online_share_pct: "38.0",
    total_tokens: 60,
    online_count: 23,
    walk_in_count: 37,
    cancelled_count: 2,
  },
  trend_7_days: [
    { date: "2026-10-27", day_name: "Tue", patients_seen: 42, no_shows: 4, total_tokens: 46 },
    { date: "2026-10-28", day_name: "Wed", patients_seen: 48, no_shows: 5, total_tokens: 53 },
    { date: "2026-10-29", day_name: "Thu", patients_seen: 51, no_shows: 3, total_tokens: 54 },
    { date: "2026-10-30", day_name: "Fri", patients_seen: 38, no_shows: 7, total_tokens: 45 },
    { date: "2026-10-31", day_name: "Sat", patients_seen: 55, no_shows: 4, total_tokens: 59 },
    { date: "2026-11-01", day_name: "Sun", patients_seen: 30, no_shows: 2, total_tokens: 32 },
    { date: "2026-11-02", day_name: "Mon", patients_seen: 54, no_shows: 6, total_tokens: 60 },
  ],
};

const mockDoctors = [
  { id: "doc-1", name: "Dr. Ayesha" },
  { id: "doc-2", name: "Dr. Bilal" },
];

describe("F-010 / D-001 Roz ki Report (Owner Dashboard)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    global.fetch = vi.fn().mockImplementation((url: string) => {
      if (url.includes("/api/v1/doctors")) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockDoctors),
        });
      }
      if (url.includes("/api/v1/reports/daily")) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockData),
        });
      }
      return Promise.reject(new Error("Unknown route"));
    });
  });

  it("renders report title, live dot, and all 4 core KPI cards matching PRD wireframe D-001", () => {
    render(<RozKiReportPage initialData={mockData} initialDoctors={mockDoctors} />);

    expect(screen.getByRole("heading", { name: "Roz ki Report" })).toBeDefined();
    expect(screen.getByText("Live Analytics")).toBeDefined();

    // Check KPI 1: Patients seen
    expect(screen.getAllByText("54").length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText("Mareez dekhe gaye")).toBeDefined();

    // Check KPI 2: Avg wait
    expect(screen.getByText("14.0m")).toBeDefined();

    // Check KPI 3: No-shows
    expect(screen.getByText("6")).toBeDefined();
    expect(screen.getByText("Ghair hazir tokens")).toBeDefined();

    // Check KPI 4: Online share
    expect(screen.getByText("38.0 %")).toBeDefined();
    expect(screen.getByText("23 online · 37 walk-in")).toBeDefined();
  });

  it("renders 7-day trend chart with weekday labels and values", () => {
    render(<RozKiReportPage initialData={mockData} initialDoctors={mockDoctors} />);

    expect(screen.getByText("7 din ka chart")).toBeDefined();
    expect(screen.getByText("Peak: 55 patients")).toBeDefined();

    // Verify weekday abbreviations are rendered
    expect(screen.getByText("Tue")).toBeDefined();
    expect(screen.getByText("Wed")).toBeDefined();
    expect(screen.getByText("Thu")).toBeDefined();
    expect(screen.getByText("Fri")).toBeDefined();
    expect(screen.getByText("Sat")).toBeDefined();
    expect(screen.getByText("Sun")).toBeDefined();
    expect(screen.getByText("Mon")).toBeDefined();
  });

  it("filters report by doctor when selection changes", async () => {
    render(<RozKiReportPage initialData={mockData} initialDoctors={mockDoctors} />);

    const doctorSelect = screen.getByLabelText("Doctor Filter");
    expect(doctorSelect).toBeDefined();

    fireEvent.change(doctorSelect, { target: { value: "doc-1" } });

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining("doctor_id=doc-1")
      );
    });
  });

  it("changes report date when date input is modified or Aaj button clicked", async () => {
    render(<RozKiReportPage initialData={mockData} initialDoctors={mockDoctors} />);

    const dateInput = screen.getByLabelText("Report Date");
    fireEvent.change(dateInput, { target: { value: "2026-10-31" } });

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining("date=2026-10-31")
      );
    });

    const aajButton = screen.getByRole("button", { name: "Aaj" });
    fireEvent.click(aajButton);

    const todayStr = new Date().toISOString().split("T")[0];
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining(`date=${todayStr}`)
      );
    });
  });

  it("renders download month CSV button and triggers download action", () => {
    render(<RozKiReportPage initialData={mockData} initialDoctors={mockDoctors} />);

    const downloadButton = screen.getByRole("button", {
      name: /Mahine ki report download \(CSV\)/i,
    });
    expect(downloadButton).toBeDefined();

    const appendChildSpy = vi.spyOn(document.body, "appendChild");
    const removeChildSpy = vi.spyOn(document.body, "removeChild");

    fireEvent.click(downloadButton);

    expect(appendChildSpy).toHaveBeenCalled();
    expect(removeChildSpy).toHaveBeenCalled();
  });
});
