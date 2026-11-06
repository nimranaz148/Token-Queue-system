import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import LoginPage from "./page";

vi.mock("next/navigation", () => ({
  useRouter: () => ({
    push: vi.fn(),
    back: vi.fn(),
  }),
}));

describe("LoginPage (F-012 Staff Login)", () => {
  it("renders Staff Login header and email input using FormShell", () => {
    render(<LoginPage />);

    expect(screen.getByText("Aapka Clinic")).toBeDefined();
    expect(screen.getByText("Staff Login")).toBeDefined();
    expect(screen.getByLabelText(/Email/i)).toBeDefined();
    expect(screen.getByRole("button", { name: /Login Link Bhejein|LOGIN/i })).toBeDefined();
  });

  it("validates empty email and prevents submission", async () => {
    render(<LoginPage />);

    const submitBtn = screen.getByRole("button", { name: /Login Link Bhejein|LOGIN/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(screen.getByText(/Email zaroori hai|Valid email required/i)).toBeDefined();
    });
  });

  it("validates invalid email format", async () => {
    render(<LoginPage />);

    const emailInput = screen.getByLabelText(/Email/i);
    fireEvent.change(emailInput, { target: { value: "not-an-email" } });

    const submitBtn = screen.getByRole("button", { name: /Login Link Bhejein|LOGIN/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(screen.getByText(/Durust email darj karein|Invalid email address/i)).toBeDefined();
    });
  });

  it("submits valid email and shows 'Login link email kar diya' confirmation message", async () => {
    // Mock global fetch for magic link request
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({
          message: "Login link email kar diya",
          success: true,
        }),
      })
    );

    render(<LoginPage />);

    const emailInput = screen.getByLabelText(/Email/i);
    fireEvent.change(emailInput, { target: { value: "doctor@example.com" } });

    const submitBtn = screen.getByRole("button", { name: /Login Link Bhejein|LOGIN/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(screen.getByText("Login link email kar diya")).toBeDefined();
    });

    vi.unstubAllGlobals();
  });

  it("displays conditional clinic selection when multiple clinics exist", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({
          message: "Login link email kar diya",
          success: true,
          memberships: [
            { clinic_id: "11111111-1111-1111-1111-111111111111", clinic_name: "City Clinic", role: "doctor" },
            { clinic_id: "22222222-2222-2222-2222-222222222222", clinic_name: "Central Health", role: "owner" },
          ],
        }),
      })
    );

    render(<LoginPage />);

    const emailInput = screen.getByLabelText(/Email/i);
    fireEvent.change(emailInput, { target: { value: "multiclinic@example.com" } });

    const submitBtn = screen.getByRole("button", { name: /Login Link Bhejein|LOGIN/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(screen.getByText("City Clinic")).toBeDefined();
      expect(screen.getByText("Central Health")).toBeDefined();
    });

    vi.unstubAllGlobals();
  });
});
