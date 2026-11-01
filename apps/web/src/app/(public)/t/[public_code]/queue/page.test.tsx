import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import LiveQueuePage from "./page";

const mockPush = vi.fn();

vi.mock("next/navigation", () => ({
  useParams: () => ({ public_code: "live-pub-18" }),
  useRouter: () => ({ push: mockPush }),
}));

describe("LiveQueuePage (F-003 Live Queue)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({
          id: "token-18",
          number: 18,
          public_code: "live-pub-18",
          status: "booked",
          doctor_name: "Dr. Mansoor",
          specialty: "General OPD",
          clinic_name: "Aapka Clinic",
          people_ahead: 6,
          estimated_wait_minutes: 35,
          current_serving_number: 12,
        }),
      })
    );
  });

  it("renders live queue dashboard with current serving, my token, and wait metrics per wireframe §30.3", async () => {
    render(<LiveQueuePage />);

    await waitFor(() => {
      expect(screen.getByText("Live Queue")).toBeDefined();
    });

    expect(screen.getByText("#12")).toBeDefined();
    expect(screen.getByText("#18")).toBeDefined();
    expect(screen.getByText("Aapka Clinic")).toBeDefined();
    expect(screen.getByText(/6 log/i)).toBeDefined();
    expect(screen.getByText(/~35 mins/i)).toBeDefined();
    expect(screen.getByText("LIVE")).toBeDefined();
  });

  it("toggles the reminder switch when clicked", async () => {
    render(<LiveQueuePage />);

    await waitFor(() => {
      expect(screen.getByText("Live Queue")).toBeDefined();
    });

    const switchBtn = screen.getByRole("switch");
    expect(switchBtn.getAttribute("aria-checked")).toBe("false");

    fireEvent.click(switchBtn);
    expect(switchBtn.getAttribute("aria-checked")).toBe("true");

    fireEvent.click(switchBtn);
    expect(switchBtn.getAttribute("aria-checked")).toBe("false");
  });

  it("navigates back to token slip screen", async () => {
    render(<LiveQueuePage />);

    await waitFor(() => {
      expect(screen.getByText("Live Queue")).toBeDefined();
    });

    const backBtn = screen.getByRole("button", { name: /Apna Token Slip/i });
    fireEvent.click(backBtn);

    expect(mockPush).toHaveBeenCalledWith("/t/live-pub-18");
  });
});
