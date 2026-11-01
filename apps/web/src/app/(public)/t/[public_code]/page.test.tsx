import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import TokenConfirmPage from "./page";

const mockPush = vi.fn();

vi.mock("next/navigation", () => ({
  useParams: () => ({ public_code: "token-pub-code-18" }),
  useRouter: () => ({ push: mockPush }),
}));

describe("TokenConfirmPage (F-002 Token Confirm)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation((url: string) => {
        if (url.includes("/cancel")) {
          return Promise.resolve({
            ok: true,
            json: async () => ({
              id: "token-18",
              number: 18,
              public_code: "token-pub-code-18",
              status: "cancelled",
            }),
          });
        }
        return Promise.resolve({
          ok: true,
          json: async () => ({
            id: "token-18",
            number: 18,
            public_code: "token-pub-code-18",
            status: "booked",
            doctor_name: "Dr. Sarah Tariq",
            specialty: "Pediatrics",
            clinic_name: "Shifa Clinic",
            people_ahead: 3,
            current_serving_number: 14,
            estimated_at: "2026-11-01T11:40:00Z",
          }),
        });
      })
    );
  });

  it("renders large token number, doctor name, and queue metrics per F-002 wireframe", async () => {
    render(<TokenConfirmPage />);

    await waitFor(() => {
      expect(screen.getByText("#18")).toBeDefined();
    });

    expect(screen.getByText("Shifa Clinic")).toBeDefined();
    expect(screen.getByText(/Dr\. Sarah Tariq/i)).toBeDefined();
    expect(screen.getByText(/3 log/i)).toBeDefined();
    expect(screen.getByText("#14")).toBeDefined();
    expect(screen.getByRole("button", { name: /LIVE QUEUE DEKHEIN/i })).toBeDefined();
  });

  it("navigates to live queue screen when 'LIVE QUEUE DEKHEIN' is clicked", async () => {
    render(<TokenConfirmPage />);

    await waitFor(() => {
      expect(screen.getByText("#18")).toBeDefined();
    });

    const liveBtn = screen.getByRole("button", { name: /LIVE QUEUE DEKHEIN/i });
    fireEvent.click(liveBtn);

    expect(mockPush).toHaveBeenCalledWith("/t/token-pub-code-18/queue");
  });

  it("shows cancellation confirmation dialog and executes cancellation", async () => {
    render(<TokenConfirmPage />);

    await waitFor(() => {
      expect(screen.getByText("#18")).toBeDefined();
    });

    const cancelBtn = screen.getByRole("button", { name: /Token Cancel Karein/i });
    fireEvent.click(cancelBtn);

    expect(
      screen.getByText(/Kya aap waqai apna token cancel karna chahte hain\?/i)
    ).toBeDefined();

    const confirmCancelBtn = screen.getByRole("button", { name: /Haan, Cancel Karo/i });
    fireEvent.click(confirmCancelBtn);

    await waitFor(() => {
      expect(screen.getByText(/Yeh token cancel ho chuka hai/i)).toBeDefined();
    });
  });
});
