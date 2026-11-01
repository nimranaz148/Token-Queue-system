import * as React from "react";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";
import PatientHistoryPage, { PatientHistoryData } from "./page";

vi.mock("@/components/auth/role-guard", () => ({
  RoleGuard: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="role-guard-pass">{children}</div>
  ),
}));

vi.mock("next/navigation", () => ({
  useParams: () => ({ patient_id: "pat-555" }),
}));

const mockHistoryData: PatientHistoryData = {
  patient_id: "pat-555",
  patient_name: "Muhammad Usman",
  phone: "+923001234567",
  date_of_birth: "1990-01-01",
  gender: "male",
  notes: "Asthma patient",
  share_advice_clinic_setting: true,
  visits: [
    {
      id: "vis-002",
      doctor_id: "doc-1",
      doctor_name: "Dr. Tariq Khan",
      complaint: "Seasonal allergy and mild cough",
      notes: "Private note: Patient should avoid dust exposure",
      medicines_advice: "Tab Rigix 10mg OD at night for 7 days",
      share_with_patient: true,
      token_id: "tok-2",
      token_number: 15,
      created_at: "2026-11-01T10:00:00Z",
    },
    {
      id: "vis-001",
      doctor_id: "doc-1",
      doctor_name: "Dr. Tariq Khan",
      complaint: "High grade fever",
      notes: "Private note: Suspected viral infection",
      medicines_advice: "Tab Panadol 500mg SOS",
      share_with_patient: false,
      token_id: "tok-1",
      token_number: 3,
      created_at: "2026-10-15T09:00:00Z",
    },
  ],
};

describe("F-008 Patient History & Visit Note", () => {
  beforeEach(() => {
    vi.stubGlobal(
      "fetch",
      vi.fn((url: string | URL | Request, init?: RequestInit) => {
        const urlStr = url.toString();

        if (urlStr.includes("/api/v1/visits/patient/pat-555")) {
          return Promise.resolve({
            ok: true,
            json: async () => mockHistoryData,
          });
        }

        if (urlStr.includes("/api/v1/visits") && init?.method === "POST") {
          return Promise.resolve({
            ok: true,
            json: async () => ({
              id: "vis-003",
              doctor_id: "doc-1",
              doctor_name: "Dr. Tariq Khan",
              complaint: "Follow-up visit",
              notes: "Condition improved",
              medicines_advice: "Continue Rigix for 3 more days",
              share_with_patient: true,
              created_at: "2026-11-02T11:00:00Z",
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

  it("renders patient profile card and visit history timeline newest first", () => {
    render(<PatientHistoryPage initialData={mockHistoryData} />);

    expect(screen.getByRole("heading", { name: "Patient History & Visit Note" })).toBeDefined();
    expect(screen.getByText("Muhammad Usman")).toBeDefined();
    expect(screen.getByText("+923001234567")).toBeDefined();
    expect(screen.getByText("Asthma patient")).toBeDefined();

    // Timeline items
    expect(screen.getByText("Seasonal allergy and mild cough")).toBeDefined();
    expect(screen.getByText("Private note: Patient should avoid dust exposure")).toBeDefined();
    expect(screen.getByText("Tab Rigix 10mg OD at night for 7 days")).toBeDefined();
    expect(screen.getByText("High grade fever")).toBeDefined();
  });

  it("shows share-with-patient checkbox when clinic setting share_advice_clinic_setting is ON", () => {
    render(<PatientHistoryPage initialData={mockHistoryData} />);

    expect(screen.getByLabelText("Share with patient checkbox")).toBeDefined();
  });

  it("hides share-with-patient checkbox when clinic setting is OFF", () => {
    const disabledSettingData = {
      ...mockHistoryData,
      share_advice_clinic_setting: false,
    };
    render(<PatientHistoryPage initialData={disabledSettingData} />);

    expect(screen.queryByLabelText("Share with patient checkbox")).toBeNull();
  });

  it("submits visit note and calls POST /api/v1/visits", async () => {
    render(<PatientHistoryPage initialData={mockHistoryData} />);

    const complaintInput = screen.getByLabelText("Complaint input");
    fireEvent.change(complaintInput, { target: { value: "Follow-up visit" } });

    const notesInput = screen.getByLabelText("Private notes input");
    fireEvent.change(notesInput, { target: { value: "Condition improved" } });

    const medsInput = screen.getByLabelText("Medicines advice input");
    fireEvent.change(medsInput, { target: { value: "Continue Rigix for 3 more days" } });

    const saveBtn = screen.getByRole("button", { name: "Save visit note button" });
    fireEvent.click(saveBtn);

    await waitFor(() => {
      expect(screen.getByText("Visit note kamyabi se mahfooz ho gaya.")).toBeDefined();
    });
  });
});
