import * as React from "react";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";
import TVDisplayPage, { DisplayFeedResponse } from "./page";

const mockFeedData: DisplayFeedResponse = {
  clinic_name: "Al-Shifa Family Clinic",
  server_time: "2026-11-02T10:00:00Z",
  doctors: [
    {
      doctor_id: "doc-1",
      doctor_name: "Dr. Tariq Khan",
      specialty: "General Physician",
      current_token: 12,
      next_tokens: [13, 14, 15],
    },
    {
      doctor_id: "doc-2",
      doctor_name: "Dr. Ayesha Malik",
      specialty: "Pediatrician",
      current_token: null,
      next_tokens: [5, 6],
    },
  ],
};

describe("F-009 TV Waiting Room Screen", () => {
  beforeEach(() => {
    vi.stubGlobal(
      "fetch",
      vi.fn((url: string | URL | Request, init?: RequestInit) => {
        const urlStr = url.toString();

        if (urlStr.includes("/api/v1/display/pairing/complete") && init?.method === "POST") {
          return Promise.resolve({
            ok: true,
            json: async () => ({
              device_id: "dev-999",
              device_token: "mock_paired_token_123",
              clinic_id: "cl-1",
              clinic_name: "Al-Shifa Family Clinic",
            }),
          });
        }

        if (urlStr.includes("/api/v1/display/feed")) {
          return Promise.resolve({
            ok: true,
            json: async () => mockFeedData,
          });
        }

        return Promise.reject(new Error(`Unhandled mock for ${urlStr}`));
      })
    );
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("shows pairing screen when no device token is provided", () => {
    render(<TVDisplayPage initialToken={null} />);

    expect(screen.getByRole("heading", { name: "Waiting Room TV Display" })).toBeDefined();
    expect(screen.getByLabelText("Pairing code input")).toBeDefined();
    expect(screen.getByRole("button", { name: "Connect TV button" })).toBeDefined();
  });

  it("submits pairing code and connects TV display", async () => {
    render(<TVDisplayPage initialToken={null} />);

    const input = screen.getByLabelText("Pairing code input");
    fireEvent.change(input, { target: { value: "ABC999" } });

    const submitBtn = screen.getByRole("button", { name: "Connect TV button" });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(screen.getByText("Al-Shifa Family Clinic")).toBeDefined();
    });
  });

  it("renders live waiting room feed with large token numbers and zero patient names", () => {
    const { container } = render(
      <TVDisplayPage initialToken="mock_token" initialFeed={mockFeedData} />
    );

    expect(screen.getByText("Al-Shifa Family Clinic")).toBeDefined();
    expect(screen.getByText("Dr. Tariq Khan")).toBeDefined();
    expect(screen.getByText("#12")).toBeDefined();
    expect(screen.getByText("#13")).toBeDefined();
    expect(screen.getByText("#14")).toBeDefined();
    expect(screen.getByText("Dr. Ayesha Malik")).toBeDefined();

    // Security assertion: PRD Rule 10 strictly forbids patient names or phone numbers on TV
    const fullText = container.textContent || "";
    expect(fullText.toLowerCase()).not.toContain("patient");
    expect(fullText.toLowerCase()).not.toContain("phone");
    expect(fullText.toLowerCase()).not.toContain("usman");
  });

  it("toggles audio chime announcement button", () => {
    render(<TVDisplayPage initialToken="mock_token" initialFeed={mockFeedData} />);

    const audioBtn = screen.getByRole("button", { name: "Toggle chime audio" });
    fireEvent.click(audioBtn);
    expect(screen.getByTitle("Chime On")).toBeDefined();

    fireEvent.click(audioBtn);
    expect(screen.getByTitle("Chime Muted")).toBeDefined();
  });

  it("unpairs device and returns to pairing screen on unpair click", async () => {
    render(<TVDisplayPage initialToken="mock_token" initialFeed={mockFeedData} />);

    const unpairBtn = screen.getByRole("button", { name: "Unpair TV Display" });
    fireEvent.click(unpairBtn);

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "Waiting Room TV Display" })).toBeDefined();
    });
  });
});
