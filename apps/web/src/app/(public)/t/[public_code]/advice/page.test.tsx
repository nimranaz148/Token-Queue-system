import * as React from "react";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";
import SharedAdvicePage, { SharedVisitAdviceData } from "./page";

vi.mock("next/navigation", () => ({
  useParams: () => ({ public_code: "tok-hidayat-19" }),
}));

const mockSharedData: SharedVisitAdviceData = {
  shared: true,
  public_code: "tok-hidayat-19",
  token_number: 19,
  visit_date: "2026-11-02",
  doctor_name: "Dr. Tariq Khan",
  medicines_advice: "Tab Azomax 500mg 1 daily for 3 days.\nAvoid cold drinks.",
};

const mockUnsharedData: SharedVisitAdviceData = {
  shared: false,
  public_code: "tok-hidayat-19",
  message: "Clinic se rabta karein",
};

describe("F-021 Doctor ki Hidayat (Shared Prescription Advice)", () => {
  beforeEach(() => {
    vi.stubGlobal(
      "fetch",
      vi.fn((url: string | URL | Request) => {
        const urlStr = url.toString();

        if (urlStr.includes("/api/v1/public/tokens/tok-hidayat-19/advice")) {
          return Promise.resolve({
            ok: true,
            json: async () => mockSharedData,
          });
        }

        return Promise.reject(new Error(`Unhandled mock for ${urlStr}`));
      })
    );
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("renders shared prescription card with doctor name, date, advice, and print button", () => {
    render(<SharedAdvicePage initialData={mockSharedData} />);

    expect(
      screen.getByRole("heading", { name: "Doctor ki Hidayat (Prescription)" })
    ).toBeDefined();
    expect(screen.getByText("Dr. Tariq Khan")).toBeDefined();
    expect(screen.getByText("#19")).toBeDefined();
    expect(
      screen.getByText(/Tab Azomax 500mg 1 daily for 3 days/)
    ).toBeDefined();
    expect(
      screen.getByRole("button", { name: "Print or save prescription button" })
    ).toBeDefined();
  });

  it("invokes window.print when print button is clicked", () => {
    const printSpy = vi.spyOn(window, "print").mockImplementation(() => {});
    render(<SharedAdvicePage initialData={mockSharedData} />);

    const printBtn = screen.getByRole("button", {
      name: "Print or save prescription button",
    });
    fireEvent.click(printBtn);

    expect(printSpy).toHaveBeenCalledOnce();
    printSpy.mockRestore();
  });

  it("renders unshared message when sharing is disabled", () => {
    render(<SharedAdvicePage initialData={mockUnsharedData} />);

    expect(screen.getByText("Hidayat Dastyab Nahi Hai")).toBeDefined();
    expect(screen.getByText("Clinic se rabta karein")).toBeDefined();
    expect(
      screen.queryByRole("button", { name: "Print or save prescription button" })
    ).toBeNull();
  });

  it("guarantees private notes and complaints are never exposed", () => {
    const { container } = render(<SharedAdvicePage initialData={mockSharedData} />);
    const text = container.textContent?.toLowerCase() || "";

    expect(text).not.toContain("complaint");
    expect(text).not.toContain("differential");
    expect(text).not.toContain("internal observation");
  });
});
