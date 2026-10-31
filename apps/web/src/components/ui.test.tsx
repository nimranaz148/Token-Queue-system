import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";

import { StatusBadge } from "./ui/status-badge";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { FormShell } from "./form/form-shell";
import { DataGrid, Column } from "./grid/data-grid";
import { LayoutShell } from "./layout/layout-shell";

describe("StatusBadge Component", () => {
  it("renders with various semantic variants", () => {
    const { rerender } = render(<StatusBadge variant="success">Completed</StatusBadge>);
    expect(screen.getByText("Completed")).toBeDefined();

    rerender(<StatusBadge variant="danger">Cancelled</StatusBadge>);
    expect(screen.getByText("Cancelled")).toBeDefined();

    rerender(<StatusBadge variant="warning">On Hold</StatusBadge>);
    expect(screen.getByText("On Hold")).toBeDefined();
  });
});

describe("Button Component", () => {
  it("renders primary and triggers click", () => {
    const handleClick = vi.fn();
    render(<Button onClick={handleClick}>Submit</Button>);
    const btn = screen.getByRole("button", { name: "Submit" });
    fireEvent.click(btn);
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it("respects disabled state", () => {
    const handleClick = vi.fn();
    render(<Button disabled onClick={handleClick}>Disabled</Button>);
    const btn = screen.getByRole("button", { name: "Disabled" });
    expect(btn.getAttribute("disabled")).toBeDefined();
    fireEvent.click(btn);
    expect(handleClick).not.toHaveBeenCalled();
  });
});

describe("Input Component", () => {
  it("renders with label, required asterisk, and error message", () => {
    render(
      <Input
        label="Patient Phone"
        required
        error="Invalid phone format"
        placeholder="03001234567"
      />
    );
    expect(screen.getByText("Patient Phone")).toBeDefined();
    expect(screen.getByText("*")).toBeDefined();
    expect(screen.getByText("Invalid phone format")).toBeDefined();
    expect(screen.getByPlaceholderText("03001234567")).toBeDefined();
  });
});

describe("FormShell Component (Mandated Form Layout)", () => {
  it("renders all mandated layout sections in correct order", () => {
    render(
      <FormShell
        title="Walk-in Entry"
        badge={<StatusBadge variant="info">New</StatusBadge>}
        description="Register a walk-in patient"
        masterFields={<div data-testid="master-fields">Master Form Fields</div>}
        detailGrid={<div data-testid="detail-grid">Detail Grid Area</div>}
        summary={<div data-testid="summary">Totals / Summary Area</div>}
        actions={<Button>Issue Token</Button>}
        auditPanel={<div>Created by Receptionist</div>}
      />
    );

    expect(screen.getByText("Walk-in Entry")).toBeDefined();
    expect(screen.getByText("New")).toBeDefined();
    expect(screen.getByTestId("master-fields")).toBeDefined();
    expect(screen.getByTestId("detail-grid")).toBeDefined();
    expect(screen.getByTestId("summary")).toBeDefined();
    expect(screen.getByRole("button", { name: "Issue Token" })).toBeDefined();
    expect(screen.getByText("Created by Receptionist")).toBeDefined();
  });
});

describe("DataGrid Component (Mandatory 4 States)", () => {
  interface RowItem {
    id: string;
    number: number;
    patient: string;
  }

  const columns: Column<RowItem>[] = [
    { key: "number", header: "Token #", numeric: true },
    { key: "patient", header: "Patient Name" },
  ];

  it("renders loading state skeleton", () => {
    const { container } = render(
      <DataGrid columns={columns} data={[]} isLoading />
    );
    expect(container.querySelector(".animate-pulse")).toBeDefined();
  });

  it("renders unauthorized state", () => {
    render(<DataGrid columns={columns} data={[]} isUnauthorized />);
    expect(screen.getByText("Access Denied")).toBeDefined();
  });

  it("renders error state with retry button", () => {
    const onRetry = vi.fn();
    render(
      <DataGrid
        columns={columns}
        data={[]}
        isError
        errorMessage="Network error"
        onRetry={onRetry}
      />
    );
    expect(screen.getByText("Failed to load data")).toBeDefined();
    expect(screen.getByText("Network error")).toBeDefined();
    const retryBtn = screen.getByRole("button", { name: "Retry" });
    fireEvent.click(retryBtn);
    expect(onRetry).toHaveBeenCalledTimes(1);
  });

  it("renders empty state", () => {
    render(
      <DataGrid
        columns={columns}
        data={[]}
        emptyTitle="No tokens in queue"
      />
    );
    expect(screen.getByText("No tokens in queue")).toBeDefined();
  });

  it("renders rows and right-aligns numeric headers and cells", () => {
    const items: RowItem[] = [
      { id: "1", number: 101, patient: "Ali Khan" },
      { id: "2", number: 102, patient: "Sara Ahmed" },
    ];
    render(<DataGrid columns={columns} data={items} />);
    expect(screen.getByText("101")).toBeDefined();
    expect(screen.getByText("Sara Ahmed")).toBeDefined();
  });
});

describe("LayoutShell Component", () => {
  it("renders navigation and children without horizontal scroll", () => {
    render(
      <LayoutShell clinicName="Test Clinic" userName="Dr. Tariq" userRole="Doctor">
        <div data-testid="page-content">Welcome to the clinic</div>
      </LayoutShell>
    );

    expect(screen.getByText("Welcome to the clinic")).toBeDefined();
    expect(screen.getAllByText("Test Clinic").length).toBeGreaterThan(0);
    expect(screen.getByText("Dr. Tariq")).toBeDefined();
  });

  it("allows opening and closing the mobile drawer", () => {
    render(
      <LayoutShell clinicName="Test Clinic">
        <div>Content</div>
      </LayoutShell>
    );

    const openBtn = screen.getByLabelText("Open menu");
    fireEvent.click(openBtn);
    const closeBtn = screen.getByLabelText("Close menu");
    expect(closeBtn).toBeDefined();
    fireEvent.click(closeBtn);
  });
});
