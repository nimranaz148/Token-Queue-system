import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";
import DoctorManagementPage, { DoctorItem } from "./page";

describe("DoctorManagementPage (F-016 Doctor Management)", () => {
  const sampleDoctors: DoctorItem[] = [
    {
      id: "doc-1",
      clinic_id: "clinic-1",
      name: "Dr. Tariq Mehmood",
      specialty: "General Physician",
      daily_online_limit: 30,
      consult_minutes: 10,
      active: true,
      schedules: [
        { weekday: 0, start_time: "09:00", end_time: "13:00" },
        { weekday: 2, start_time: "14:00", end_time: "18:00" },
      ],
      created_at: "2026-10-31T00:00:00Z",
    },
    {
      id: "doc-2",
      clinic_id: "clinic-1",
      name: "Dr. Ayesha Khan",
      specialty: "Pediatrics",
      daily_online_limit: 20,
      consult_minutes: 15,
      active: false,
      schedules: [],
      created_at: "2026-10-31T01:00:00Z",
    },
  ];

  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("renders page title, columns, and doctors list", () => {
    render(
      <DoctorManagementPage
        initialDoctors={sampleDoctors}
        userRole="owner"
      />
    );

    expect(screen.getByText("Doctor Management")).toBeDefined();
    expect(screen.getByText("Dr. Tariq Mehmood")).toBeDefined();
    expect(screen.getByText("General Physician")).toBeDefined();
    expect(screen.getByText("Dr. Ayesha Khan")).toBeDefined();
    expect(screen.getByText("Pediatrics")).toBeDefined();
    expect(screen.getByText("Active")).toBeDefined();
    expect(screen.getByText("Inactive")).toBeDefined();
    expect(screen.getByText("10 min/consult")).toBeDefined();
    expect(screen.getByText("30 tokens/day")).toBeDefined();
  });

  it("filters doctors using search input", () => {
    render(
      <DoctorManagementPage
        initialDoctors={sampleDoctors}
        userRole="owner"
      />
    );

    const searchInput = screen.getByPlaceholderText(/search by name or specialty/i);
    fireEvent.change(searchInput, { target: { value: "Pediatrics" } });

    expect(screen.getByText("Dr. Ayesha Khan")).toBeDefined();
    expect(screen.queryByText("Dr. Tariq Mehmood")).toBeNull();
  });

  it("shows unauthorized state when user is not owner", () => {
    render(
      <DoctorManagementPage
        initialDoctors={sampleDoctors}
        userRole="doctor"
      />
    );

    expect(screen.getByText("Access Denied")).toBeDefined();
  });

  it("shows empty state when no doctors exist", async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ items: [], total: 0 }),
    } as unknown as Response);

    render(
      <DoctorManagementPage
        initialDoctors={[]}
        userRole="owner"
      />
    );

    await waitFor(() => {
      expect(screen.getByText("No doctors found")).toBeDefined();
    });
  });

  it("opens add modal and creates a doctor", async () => {
    const newDoc: DoctorItem = {
      id: "doc-new",
      clinic_id: "clinic-1",
      name: "Dr. Bilal Siddiqui",
      specialty: "Cardiology",
      daily_online_limit: 15,
      consult_minutes: 20,
      active: true,
      schedules: [],
      created_at: "2026-11-01T00:00:00Z",
    };

    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => newDoc,
    } as unknown as Response);

    render(
      <DoctorManagementPage
        initialDoctors={sampleDoctors}
        userRole="owner"
      />
    );

    fireEvent.click(screen.getByRole("button", { name: "Add Doctor" }));
    expect(screen.getByText("Add New Doctor")).toBeDefined();

    const nameInput = screen.getByPlaceholderText(/e\.g\. Dr\. Ayesha Ahmed/i);
    fireEvent.change(nameInput, { target: { value: "Dr. Bilal Siddiqui" } });

    const submitBtn = screen.getByRole("button", { name: "Save Doctor" });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(screen.getByText("Dr. Bilal Siddiqui")).toBeDefined();
    });
  });

  it("opens edit modal and saves changes", async () => {
    const updatedDoc: DoctorItem = {
      ...sampleDoctors[0],
      name: "Dr. Tariq Updated",
    };

    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => updatedDoc,
    } as unknown as Response);

    render(
      <DoctorManagementPage
        initialDoctors={sampleDoctors}
        userRole="owner"
      />
    );

    const editBtn = screen.getByRole("button", {
      name: `Edit ${sampleDoctors[0].name}`,
    });
    fireEvent.click(editBtn);

    expect(screen.getByText("Edit Doctor Profile")).toBeDefined();

    const saveBtn = screen.getByRole("button", { name: "Save Changes" });
    fireEvent.click(saveBtn);

    await waitFor(() => {
      expect(screen.getByText("Dr. Tariq Updated")).toBeDefined();
    });
  });

  it("opens OPD timings modal and manages schedules", async () => {
    const updatedSchedules = [
      { weekday: 1, start_time: "10:00", end_time: "14:00" },
    ];

    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => updatedSchedules,
    } as unknown as Response);

    render(
      <DoctorManagementPage
        initialDoctors={sampleDoctors}
        userRole="owner"
      />
    );

    const opdBtn = screen.getByRole("button", {
      name: `Manage schedule for ${sampleDoctors[0].name}`,
    });
    fireEvent.click(opdBtn);

    expect(screen.getByText(/OPD Schedule — Dr. Tariq Mehmood/i)).toBeDefined();

    const saveBtn = screen.getByRole("button", { name: "Save Schedule" });
    fireEvent.click(saveBtn);

    await waitFor(() => {
      expect(screen.queryByText(/OPD Schedule — Dr. Tariq Mehmood/i)).toBeNull();
    });
  });

  it("deactivates/deletes a doctor on confirmation", async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 204,
    } as unknown as Response);

    render(
      <DoctorManagementPage
        initialDoctors={sampleDoctors}
        userRole="owner"
      />
    );

    const deleteBtn = screen.getByRole("button", {
      name: `Delete ${sampleDoctors[0].name}`,
    });
    fireEvent.click(deleteBtn);

    expect(screen.getByText("Deactivate Doctor?")).toBeDefined();

    const confirmBtn = screen.getByRole("button", { name: "Deactivate" });
    fireEvent.click(confirmBtn);

    await waitFor(() => {
      expect(screen.queryByText("Dr. Tariq Mehmood")).toBeNull();
    });
  });
});
