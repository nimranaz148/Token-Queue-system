import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import HomePage from "./page";

describe("HomePage", () => {
  it("renders the clinic title", () => {
    render(<HomePage />);
    expect(
      screen.getByRole("heading", { name: /Clinic Token & Queue SaaS/i })
    ).toBeDefined();
  });

  it("renders staff login link", () => {
    render(<HomePage />);
    expect(screen.getByRole("link", { name: /Staff Login/i })).toBeDefined();
  });
});
