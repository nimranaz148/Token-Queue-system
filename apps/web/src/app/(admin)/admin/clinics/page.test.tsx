import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import ClinicsPage, { ClinicItem } from "./page";

describe("ClinicsPage (F-013 & F-014 Vertical Slice)", () => {
  const sampleClinics: ClinicItem[] = [
    {
      id: "c-1",
      name: "Al-Shifa Clinic",
      slug: "al-shifa",
      status: "active",
      created_at: "2026-10-31T00:00:00Z",
    },
    {
      id: "c-2",
      name: "City Care",
      slug: "city-care",
      status: "trial",
      created_at: "2026-10-30T00:00:00Z",
    },
  ];

  it("renders page title, layout header, and clinic rows", () => {
    render(<ClinicsPage initialClinics={sampleClinics} />);

    expect(screen.getByText("Platform Administration")).toBeDefined();
    expect(screen.getByText("Al-Shifa Clinic")).toBeDefined();
    expect(screen.getByText("City Care")).toBeDefined();
    expect(screen.getByText("ACTIVE")).toBeDefined();
    expect(screen.getByText("TRIAL")).toBeDefined();
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
    expect(screen.getByText("Create First Clinic")).toBeDefined();
  });

  it("displays unauthorized state when caller lacks platform_admin role", () => {
    render(<ClinicsPage initialClinics={sampleClinics} userRole="doctor" />);

    expect(screen.getByText("Access Denied")).toBeDefined();
    expect(
      screen.getByText("You do not have permission to view these records.")
    ).toBeDefined();
  });

  it("toggles onboarding form and validates minimum input length", () => {
    render(<ClinicsPage initialClinics={sampleClinics} />);

    const newBtn = screen.getByText("+ New Clinic");
    fireEvent.click(newBtn);

    expect(screen.getByText("Onboard New Clinic")).toBeDefined();

    const saveBtn = screen.getByText("Save Clinic");
    fireEvent.click(saveBtn);

    expect(
      screen.getByText("Clinic name must be at least 2 characters.")
    ).toBeDefined();
  });
});
