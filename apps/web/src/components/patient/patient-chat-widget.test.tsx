import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { PatientChatWidget } from "./patient-chat-widget";

describe("PatientChatWidget (F-019)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Element.scrollIntoView mock
    window.HTMLElement.prototype.scrollIntoView = vi.fn();
  });

  it("renders collapsed chat button initially", () => {
    render(<PatientChatWidget publicCode="token-code-123" />);

    expect(screen.getByText("Queue Assistant (F-019)")).toBeDefined();
    expect(screen.getByText("Chat Shuru Karein")).toBeDefined();
  });

  it("opens chat and displays medical advice warning banner", async () => {
    vi.spyOn(global, "fetch").mockResolvedValueOnce({
      ok: true,
      json: async () => [],
    } as Response);

    render(<PatientChatWidget publicCode="token-code-123" />);

    fireEvent.click(screen.getByText("Chat Shuru Karein"));

    await waitFor(() => {
      expect(
        screen.getByText(/Yeh AI assistant sirf queue ki maloomat deta hai, tibbi mashwara nahi/i)
      ).toBeDefined();
      expect(screen.getByPlaceholderText(/Sawal likhein/i)).toBeDefined();
    });
  });

  it("sends message and renders assistant reply", async () => {
    const fetchSpy = vi.spyOn(global, "fetch");

    // History load
    fetchSpy.mockResolvedValueOnce({
      ok: true,
      json: async () => [],
    } as Response);

    // Chat reply
    fetchSpy.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => ({
        reply: "Aap se aagay 2 mareez hain.",
        tool_calls: ["get_my_token_status"],
      }),
    } as Response);

    render(<PatientChatWidget publicCode="token-code-123" />);

    fireEvent.click(screen.getByText("Chat Shuru Karein"));

    await waitFor(() => {
      expect(screen.getByPlaceholderText(/Sawal likhein/i)).toBeDefined();
    });

    const input = screen.getByPlaceholderText(/Sawal likhein/i);
    fireEvent.change(input, { target: { value: "Mera number kab aayega?" } });

    const submitBtn = screen.getByLabelText("Bheinjein");
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(fetchSpy).toHaveBeenCalledWith(
        "/api/v1/public/tokens/token-code-123/chat",
        expect.objectContaining({
          method: "POST",
          body: JSON.stringify({ message: "Mera number kab aayega?" }),
        })
      );
      expect(screen.getByText("Aap se aagay 2 mareez hain.")).toBeDefined();
    });
  });

  it("displays rate limit error message when 20 msgs exceeded", async () => {
    const fetchSpy = vi.spyOn(global, "fetch");

    fetchSpy.mockResolvedValueOnce({
      ok: true,
      json: async () => [],
    } as Response);

    fetchSpy.mockResolvedValueOnce({
      ok: false,
      status: 429,
      json: async () => ({
        detail: "Rozana 20 messages ki had poori ho chuki hai.",
      }),
    } as Response);

    render(<PatientChatWidget publicCode="token-code-123" />);

    fireEvent.click(screen.getByText("Chat Shuru Karein"));

    await waitFor(() => {
      expect(screen.getByPlaceholderText(/Sawal likhein/i)).toBeDefined();
    });

    const input = screen.getByPlaceholderText(/Sawal likhein/i);
    fireEvent.change(input, { target: { value: "Halat kaisi hai?" } });

    fireEvent.click(screen.getByLabelText("Bheinjein"));

    await waitFor(() => {
      expect(
        screen.getByText(/Rozana 20 messages ki had poori ho chuki hai/i)
      ).toBeDefined();
    });
  });
});
