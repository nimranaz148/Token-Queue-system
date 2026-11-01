import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import NewClinicPage from "./page";

// Mock next/navigation
vi.mock("next/navigation", () => ({
  useRouter: () => ({
    push: vi.fn(),
  }),
}));

describe("NewClinicPage (F-013 New Clinic Onboarding)", () => {
  it("renders all required onboarding fields per PRD §5.3", () => {
    render(<NewClinicPage />);

    expect(screen.getByText("New Clinic (Naya Clinic Onboarding)")).toBeDefined();
    expect(screen.getByLabelText(/Clinic Name/i)).toBeDefined();
    expect(screen.getByLabelText(/Slug/i)).toBeDefined();
    expect(screen.getByLabelText(/Owner Full Name/i)).toBeDefined();
    expect(screen.getByLabelText(/Owner Email/i)).toBeDefined();
    expect(screen.getByLabelText(/Owner Phone/i)).toBeDefined();
    expect(screen.getByLabelText(/Time Zone/i)).toBeDefined();
    expect(screen.getByLabelText(/Initial Status/i)).toBeDefined();
    expect(screen.getByRole("button", { name: /Create Clinic/i })).toBeDefined();
  });

  it("validates empty required fields and invalid slug regex", async () => {
    render(<NewClinicPage />);

    const submitBtn = screen.getByRole("button", { name: /Create Clinic/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(screen.getByText(/Clinic name 2 se 80 characters/i)).toBeDefined();
      expect(screen.getByText(/Slug mein sirf chotay angrezi huroof/i)).toBeDefined();
      expect(screen.getByText(/Owner ka mukammal naam darj karna zaroori hai/i)).toBeDefined();
      expect(screen.getByText(/Durust owner email darj karein/i)).toBeDefined();
    });
  });

  it("submits valid form and displays success confirmation with public link", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({
          id: "123e4567-e89b-12d3-a456-426614174000",
          name: "Care Family Clinic",
          slug: "care-family",
          status: "trial",
          owner_name: "Dr. Bilal",
          owner_email: "bilal@carefamily.com",
        }),
      })
    );

    render(<NewClinicPage />);

    fireEvent.change(screen.getByLabelText(/Clinic Name/i), {
      target: { value: "Care Family Clinic" },
    });
    fireEvent.change(screen.getByLabelText(/Slug/i), {
      target: { value: "care-family" },
    });
    fireEvent.change(screen.getByLabelText(/Owner Full Name/i), {
      target: { value: "Dr. Bilal" },
    });
    fireEvent.change(screen.getByLabelText(/Owner Email/i), {
      target: { value: "bilal@carefamily.com" },
    });

    const submitBtn = screen.getByRole("button", { name: /Create Clinic/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(screen.getByText(/kamyabi se create ho gaya/i)).toBeDefined();
      expect(screen.getByText("/c/care-family")).toBeDefined();
    });

    vi.unstubAllGlobals();
  });

  it("handles duplicate slug conflict (409) with inline error", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 409,
        json: async () => ({
          code: "SLUG_EXISTS",
          detail: "Clinic with slug already exists",
        }),
      })
    );

    render(<NewClinicPage />);

    fireEvent.change(screen.getByLabelText(/Clinic Name/i), {
      target: { value: "Care Family Clinic" },
    });
    fireEvent.change(screen.getByLabelText(/Slug/i), {
      target: { value: "care-family" },
    });
    fireEvent.change(screen.getByLabelText(/Owner Full Name/i), {
      target: { value: "Dr. Bilal" },
    });
    fireEvent.change(screen.getByLabelText(/Owner Email/i), {
      target: { value: "bilal@carefamily.com" },
    });

    const submitBtn = screen.getByRole("button", { name: /Create Clinic/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(screen.getByText(/Yeh slug pehle se kisi doosray clinic ke paas hai/i)).toBeDefined();
    });

    vi.unstubAllGlobals();
  });
});
