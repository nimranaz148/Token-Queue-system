import * as React from "react";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";
import WalkInEntryPage from "./page";

vi.mock("@/components/auth/role-guard", () => ({
  RoleGuard: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="role-guard-pass">{children}</div>
  ),
}));

const mockDoctorsData = [
  { id: "doc-001", name: "Dr. Tariq Khan", specialty: "Cardiologist" },
  { id: "doc-002", name: "Dr. Ayesha Malik", specialty: "Pediatrician" },
];

const mockPatientLookupResult = [
  {
    id: "pat-999",
    name: "Zainab Bibi",
    phone: "+923001234567",
  },
];

const mockCreatedToken = {
  id: "tok-1234",
  number: 19,
  public_code: "tc-walk-19",
  status: "arrived",
  source: "walk_in",
  patient_id: "pat-999",
  patient_name: "Zainab Bibi",
  phone: "+923001234567",
  doctor_id: "doc-001",
  doctor_name: "Dr. Tariq Khan",
  visit_date: "2026-11-02",
  position: 19,
  arrived_at: "2026-11-02T10:00:00Z",
  created_at: "2026-11-02T10:00:00Z",
};

describe("F-005 Walk-in Entry Screen", () => {
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

        if (urlStr.includes("/api/v1/patients?query=")) {
          if (urlStr.includes("03001234567")) {
            return Promise.resolve({
              ok: true,
              json: async () => mockPatientLookupResult,
            });
          }
          return Promise.resolve({
            ok: true,
            json: async () => [],
          });
        }

        if (urlStr.includes("/api/v1/tokens") && init?.method === "POST") {
          const body = JSON.parse(init.body as string);
          return Promise.resolve({
            ok: true,
            json: async () => ({
              ...mockCreatedToken,
              patient_name: body.patient_name,
              phone: body.phone,
              doctor_id: body.doctor_id,
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

  it("renders walk-in entry form with all required inputs and doctors loaded", async () => {
    render(<WalkInEntryPage initialDoctors={mockDoctorsData} />);

    expect(screen.getByRole("heading", { name: "Walk-in Entry" })).toBeDefined();
    expect(screen.getByLabelText("Phone")).toBeDefined();
    expect(screen.getByLabelText("Patient Name")).toBeDefined();
    expect(screen.getByLabelText("Doctor")).toBeDefined();
    expect(screen.getByLabelText("Ignore Daily Limit")).toBeDefined();
    expect(screen.getByRole("button", { name: "TOKEN BANAO" })).toBeDefined();

    expect(screen.getByText("Dr. Tariq Khan (Cardiologist)")).toBeDefined();
    expect(screen.getByText("Dr. Ayesha Malik (Pediatrician)")).toBeDefined();
  });

  it("auto-fills patient name when phone input loses focus and match is found", async () => {
    render(<WalkInEntryPage initialDoctors={mockDoctorsData} />);

    const phoneInput = screen.getByLabelText("Phone") as HTMLInputElement;
    fireEvent.change(phoneInput, { target: { value: "03001234567" } });
    fireEvent.blur(phoneInput);

    await waitFor(() => {
      const nameInput = screen.getByLabelText("Patient Name") as HTMLInputElement;
      expect(nameInput.value).toBe("Zainab Bibi");
      expect(screen.getByText(/Pehly se mojood mareez mil gaya: Zainab Bibi/)).toBeDefined();
    });
  });

  it("validates invalid phone number and prevents submission", async () => {
    render(<WalkInEntryPage initialDoctors={mockDoctorsData} />);

    const phoneInput = screen.getByLabelText("Phone");
    const nameInput = screen.getByLabelText("Patient Name");

    fireEvent.change(phoneInput, { target: { value: "123" } });
    fireEvent.change(nameInput, { target: { value: "Valid Name" } });

    const submitBtn = screen.getByRole("button", { name: "TOKEN BANAO" });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(screen.getByText("Sahih phone number likhein (kam az kam 7 digits).")).toBeDefined();
    });
  });

  it("submits walk-in token and displays generated token number slip", async () => {
    render(<WalkInEntryPage initialDoctors={mockDoctorsData} />);

    const phoneInput = screen.getByLabelText("Phone");
    const nameInput = screen.getByLabelText("Patient Name");

    fireEvent.change(phoneInput, { target: { value: "+923001234567" } });
    fireEvent.change(nameInput, { target: { value: "Muhammad Usman" } });

    const submitBtn = screen.getByRole("button", { name: "TOKEN BANAO" });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(screen.getByText("#19")).toBeDefined();
      expect(screen.getByText("Walk-in Token Issued")).toBeDefined();
      expect(screen.getByText("ARRIVED")).toBeDefined();
      expect(screen.getByRole("button", { name: "Print Slip" })).toBeDefined();
      expect(screen.getByRole("button", { name: "Agla Token" })).toBeDefined();
    });
  });

  it("resets form when 'Agla Token' is clicked", async () => {
    render(<WalkInEntryPage initialDoctors={mockDoctorsData} />);

    const phoneInput = screen.getByLabelText("Phone") as HTMLInputElement;
    const nameInput = screen.getByLabelText("Patient Name") as HTMLInputElement;

    fireEvent.change(phoneInput, { target: { value: "+923001234567" } });
    fireEvent.change(nameInput, { target: { value: "Muhammad Usman" } });

    fireEvent.click(screen.getByRole("button", { name: "TOKEN BANAO" }));

    await waitFor(() => {
      expect(screen.getByText("#19")).toBeDefined();
    });

    fireEvent.click(screen.getByRole("button", { name: "Agla Token" }));

    await waitFor(() => {
      expect(screen.queryByText("#19")).toBeNull();
      expect(screen.getByText("Koi token generate nahi hua")).toBeDefined();
      expect(phoneInput.value).toBe("");
      expect(nameInput.value).toBe("");
    });
  });
});
