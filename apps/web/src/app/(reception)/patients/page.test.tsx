import * as React from "react";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";
import PatientSearchPage, { PatientItem } from "./page";

vi.mock("@/components/auth/role-guard", () => ({
  RoleGuard: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="role-guard-pass">{children}</div>
  ),
}));

const mockPatientsList: PatientItem[] = [
  {
    id: "pat-101",
    name: "Muhammad Usman",
    phone: "+923001234567",
    date_of_birth: "1990-05-15",
    gender: "male",
    visit_count: 4,
    last_visit_date: "2026-10-25",
    notes: "Patient has asthma history",
  },
  {
    id: "pat-102",
    name: "Ayesha Bibi",
    phone: "+923007654321",
    date_of_birth: "1996-08-20",
    gender: "female",
    visit_count: 1,
    last_visit_date: "2026-11-01",
    notes: null,
  },
];

describe("F-006 Patient Search & Profile Screen", () => {
  beforeEach(() => {
    vi.stubGlobal(
      "fetch",
      vi.fn((url: string | URL | Request, init?: RequestInit) => {
        const urlStr = url.toString();

        if (urlStr.includes("/api/v1/patients?query=")) {
          if (urlStr.includes("Usman")) {
            return Promise.resolve({
              ok: true,
              json: async () => [mockPatientsList[0]],
            });
          }
          return Promise.resolve({
            ok: true,
            json: async () => mockPatientsList,
          });
        }

        if (urlStr.includes("/api/v1/patients/pat-101") && init?.method === "PUT") {
          const body = JSON.parse(init.body as string);
          return Promise.resolve({
            ok: true,
            json: async () => ({
              ...mockPatientsList[0],
              ...body,
            }),
          });
        }

        if (urlStr.includes("/api/v1/patients/pat-101")) {
          return Promise.resolve({
            ok: true,
            json: async () => mockPatientsList[0],
          });
        }

        return Promise.reject(new Error(`Unhandled mock for ${urlStr}`));
      })
    );
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("renders patient search header, input, and empty state", () => {
    render(<PatientSearchPage />);

    expect(screen.getByRole("heading", { name: "Patients Directory" })).toBeDefined();
    expect(screen.getByLabelText("Patient search input")).toBeDefined();
    expect(screen.getByRole("button", { name: "Search button" })).toBeDefined();
    expect(screen.getByText("Koi mareez nahi mila")).toBeDefined();
  });

  it("shows error when search query is shorter than 2 characters", async () => {
    render(<PatientSearchPage />);

    const input = screen.getByLabelText("Patient search input");
    fireEvent.change(input, { target: { value: "A" } });

    const searchBtn = screen.getByRole("button", { name: "Search button" });
    fireEvent.click(searchBtn);

    await waitFor(() => {
      expect(
        screen.getByText("Search karne ke liye kam az kam 2 characters likhein.")
      ).toBeDefined();
    });
  });

  it("searches and renders patient results in table", async () => {
    render(<PatientSearchPage />);

    const input = screen.getByLabelText("Patient search input");
    fireEvent.change(input, { target: { value: "Usman" } });

    const searchBtn = screen.getByRole("button", { name: "Search button" });
    fireEvent.click(searchBtn);

    await waitFor(() => {
      expect(screen.getByText("Muhammad Usman")).toBeDefined();
      expect(screen.getByText("+923001234567")).toBeDefined();
      expect(screen.getByText("4 visits")).toBeDefined();
      expect(screen.getByText("2026-10-25")).toBeDefined();
      expect(screen.getByRole("button", { name: "Open profile for Muhammad Usman" })).toBeDefined();
    });
  });

  it("opens profile modal and displays details and private clinic notes", async () => {
    render(<PatientSearchPage initialPatients={[mockPatientsList[0]]} />);

    const profileBtn = screen.getByRole("button", { name: "Open profile for Muhammad Usman" });
    fireEvent.click(profileBtn);

    await waitFor(() => {
      expect(screen.getByRole("dialog", { name: "Patient Profile Modal" })).toBeDefined();
      expect(screen.getByText("Patient has asthma history")).toBeDefined();
      expect(screen.getByRole("button", { name: "Edit Profile" })).toBeDefined();
    });
  });

  it("allows reception to edit profile and save changes via PUT /api/v1/patients/{id}", async () => {
    render(<PatientSearchPage initialPatients={[mockPatientsList[0]]} userRole="reception" />);

    fireEvent.click(screen.getByRole("button", { name: "Open profile for Muhammad Usman" }));

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Edit Profile" })).toBeDefined();
    });

    fireEvent.click(screen.getByRole("button", { name: "Edit Profile" }));

    const nameInput = screen.getByLabelText("Edit patient name");
    fireEvent.change(nameInput, { target: { value: "Muhammad Usman Updated" } });

    const notesInput = screen.getByLabelText("Edit notes");
    fireEvent.change(notesInput, { target: { value: "Updated asthma diagnosis and meds" } });

    const saveBtn = screen.getByRole("button", { name: "Save Profile" });
    fireEvent.click(saveBtn);

    await waitFor(() => {
      expect(screen.getByText("Profile kamyabi se update ho gaya.")).toBeDefined();
    });
  });

  it("does not show edit button when viewed by doctor role", async () => {
    render(<PatientSearchPage initialPatients={[mockPatientsList[0]]} userRole="doctor" />);

    fireEvent.click(screen.getByRole("button", { name: "Open profile for Muhammad Usman" }));

    await waitFor(() => {
      expect(screen.getByRole("dialog", { name: "Patient Profile Modal" })).toBeDefined();
      expect(screen.queryByRole("button", { name: "Edit Profile" })).toBeNull();
    });
  });
});
