import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import ClinicsPage, { ClinicItem } from "./page";

describe("ClinicsPage (F-014 Clinics List)", () => {
  const sampleClinics: ClinicItem[] = [
    {
      id: "c-1",
      name: "Al-Shifa Clinic",
      slug: "al-shifa",
      status: "active",
      doctors_count: 5,
      tokens_last_7d: 142,
      created_at: "2026-10-31T00:00:00Z",
    },
    {
      id: "c-2",
      name: "City Care",
      slug: "city-care",
      status: "trial",
      doctors_count: 2,
      tokens_last_7d: 38,
      created_at: "2026-10-30T00:00:00Z",
    },
  ];

  it("renders page title, layout header, columns, and telemetry", () => {
    render(<ClinicsPage initialClinics={sampleClinics} />);

    expect(screen.getByText("Clinics Directory")).toBeDefined();
    expect(screen.getByText("Al-Shifa Clinic")).toBeDefined();
    expect(screen.getByText("City Care")).toBeDefined();
    expect(screen.getByText("ACTIVE")).toBeDefined();
    expect(screen.getByText("TRIAL")).toBeDefined();
    expect(screen.getByText("5")).toBeDefined();
    expect(screen.getByText("142")).toBeDefined();
  });

  it("filters clinics when typing in the search box", () => {
    render(<ClinicsPage initialClinics={sampleClinics} />);

    const searchInput = screen.getByPlaceholderText("Search by clinic name or slug...");
    fireEvent.change(searchInput, { target: { value: "City" } });

    expect(screen.queryByText("Al-Shifa Clinic")).toBeNull();
    expect(screen.getByText("City Care")).toBeDefined();
  });

  it("displays empty state when no clinics exist", () => {
    render(<ClinicsPage initialClinics={[]} />);

    expect(screen.getByText("No clinics registered")).toBeDefined();
    expect(screen.getByText("+ Onboard First Clinic")).toBeDefined();
  });

  it("displays unauthorized state when caller lacks platform_admin role", () => {
    render(<ClinicsPage initialClinics={sampleClinics} userRole="doctor" />);

    expect(screen.getByText("Access Denied")).toBeDefined();
    expect(
      screen.getByText("You do not have permission to view these records.")
    ).toBeDefined();
  });

  it("opens audited status change modal and validates mandatory reason", async () => {
    render(<ClinicsPage initialClinics={sampleClinics} />);

    // Click Suspend on active clinic
    const suspendButtons = screen.getAllByRole("button", { name: "Suspend" });
    fireEvent.click(suspendButtons[0]);

    expect(screen.getByText(/Clinic Status Change: Al-Shifa Clinic/i)).toBeDefined();

    // Attempt to submit without reason
    const confirmBtn = screen.getByRole("button", { name: /Confirm suspended/i });
    fireEvent.click(confirmBtn);

    await waitFor(() => {
      expect(screen.getByText(/Wajah \(reason\) darj karna zaroori hai/i)).toBeDefined();
    });
  });
});
