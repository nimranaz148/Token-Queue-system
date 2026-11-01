import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import TokenBookingPage from "./page";

const mockPush = vi.fn();

vi.mock("next/navigation", () => ({
  useParams: () => ({ slug: "shifa-clinic" }),
  useRouter: () => ({ push: mockPush }),
}));

describe("TokenBookingPage (F-001 Token Booking)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation((url: string) => {
        if (url.includes("/api/v1/public/clinics/shifa-clinic/tokens")) {
          return Promise.resolve({
            ok: true,
            status: 201,
            json: async () => ({
              id: "token-123",
              number: 1,
              public_code: "pub-code-xyz",
              status: "booked",
              doctor_name: "Dr. Tariq Khan",
              clinic_name: "Shifa Clinic",
            }),
          });
        }
        return Promise.resolve({
          ok: true,
          json: async () => ({
            id: "clinic-1",
            name: "Shifa Clinic",
            slug: "shifa-clinic",
            time_zone: "Asia/Karachi",
            online_booking_enabled: true,
            doctors: [
              {
                id: "doc-1",
                name: "Dr. Tariq Khan",
                specialty: "General Medicine",
                daily_online_limit: 30,
              },
            ],
          }),
        });
      })
    );
  });

  it("renders booking screen with clinic name and F-001 fields", async () => {
    render(<TokenBookingPage />);

    await waitFor(() => {
      expect(screen.getByText("Shifa Clinic")).toBeDefined();
    });

    expect(screen.getByLabelText(/Doctor \/ OPD/i)).toBeDefined();
    expect(screen.getByText(/Aaj \(Today\)/i)).toBeDefined();
    expect(screen.getByText(/Kal \(Tomorrow\)/i)).toBeDefined();
    expect(screen.getByLabelText(/Patient Name/i)).toBeDefined();
    expect(screen.getByLabelText(/Phone Number/i)).toBeDefined();
    expect(screen.getByRole("button", { name: /TOKEN LO/i })).toBeDefined();
  });

  it("validates short patient name and prevents submission", async () => {
    render(<TokenBookingPage />);

    await waitFor(() => {
      expect(screen.getByText("Shifa Clinic")).toBeDefined();
    });

    const submitBtn = screen.getByRole("button", { name: /TOKEN LO/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(
        screen.getByText(/Patient name must be at least 2 characters/i)
      ).toBeDefined();
    });
  });

  it("submits booking form and redirects to /t/{public_code}", async () => {
    render(<TokenBookingPage />);

    await waitFor(() => {
      expect(screen.getByText("Shifa Clinic")).toBeDefined();
    });

    const nameInput = screen.getByLabelText(/Patient Name/i);
    const phoneInput = screen.getByLabelText(/Phone Number/i);

    fireEvent.change(nameInput, { target: { value: "Muhammad Usman" } });
    fireEvent.change(phoneInput, { target: { value: "03001234567" } });

    const submitBtn = screen.getByRole("button", { name: /TOKEN LO/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith("/t/pub-code-xyz");
    });
  });

  it("displays booking closed banner when online booking is disabled", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({
          id: "clinic-1",
          name: "Shifa Clinic",
          slug: "shifa-clinic",
          time_zone: "Asia/Karachi",
          online_booking_enabled: false,
          doctors: [],
        }),
      })
    );

    render(<TokenBookingPage />);

    await waitFor(() => {
      expect(screen.getByText("Booking Band Hai")).toBeDefined();
    });
  });
});
