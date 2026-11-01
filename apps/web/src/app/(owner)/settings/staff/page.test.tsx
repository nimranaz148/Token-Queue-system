import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import StaffManagementPage, { StaffMemberItem, DoctorOption } from "./page";

describe("StaffManagementPage (F-015 Staff Management)", () => {
  const sampleDoctors: DoctorOption[] = [
    { id: "doc-1", name: "Dr. Tariq Mehmood", specialty: "General Physician" },
    { id: "doc-2", name: "Dr. Ayesha Khan", specialty: "Pediatrics" },
  ];

  const sampleMembers: StaffMemberItem[] = [
    {
      id: "m-1",
      clinic_id: "clinic-1",
      user_id: "user-1",
      name: "Tariq Owner",
      email: "tariq@clinic.com",
      phone: "+923001112233",
      role: "owner",
      active: true,
      created_at: "2026-10-31T00:00:00Z",
    },
    {
      id: "m-2",
      clinic_id: "clinic-1",
      user_id: "user-2",
      name: "Dr. Ayesha",
      email: "ayesha@clinic.com",
      phone: "+923004445566",
      role: "doctor",
      doctor_id: "doc-2",
      doctor_name: "Dr. Ayesha Khan",
      active: true,
      created_at: "2026-10-31T01:00:00Z",
    },
    {
      id: "m-3",
      clinic_id: "clinic-1",
      user_id: "user-3",
      name: "Ali Receptionist",
      email: "ali@clinic.com",
      phone: "+923007778899",
      role: "reception",
      active: false,
      created_at: "2026-10-31T02:00:00Z",
    },
  ];

  it("renders page title, layout header, columns, and staff members", () => {
    render(
      <StaffManagementPage
        initialMembers={sampleMembers}
        initialDoctors={sampleDoctors}
        userRole="owner"
      />
    );

    expect(screen.getByText("Staff Management")).toBeDefined();
    expect(screen.getByText("Tariq Owner")).toBeDefined();
    expect(screen.getByText("tariq@clinic.com")).toBeDefined();
    expect(screen.getByText("Dr. Ayesha")).toBeDefined();
    expect(screen.getByText("Dr. Ayesha Khan")).toBeDefined();
    expect(screen.getByText("Ali Receptionist")).toBeDefined();
    expect(screen.getAllByText("Active").length).toBeGreaterThan(0);
    expect(screen.getByText("Deactivated")).toBeDefined();
  });

  it("filters staff members using search input", () => {
    render(
      <StaffManagementPage
        initialMembers={sampleMembers}
        initialDoctors={sampleDoctors}
        userRole="owner"
      />
    );

    const searchInput = screen.getByPlaceholderText(/search by name, email/i);
    fireEvent.change(searchInput, { target: { value: "Ayesha" } });

    expect(screen.queryByText("Tariq Owner")).toBeNull();
    expect(screen.getByText("Dr. Ayesha")).toBeDefined();
  });

  it("blocks non-owner roles with 403 Forbidden screen", () => {
    render(
      <StaffManagementPage
        initialMembers={sampleMembers}
        initialDoctors={sampleDoctors}
        userRole="reception"
      />
    );

    expect(screen.getByText(/403 — Unauthorized Access/i)).toBeDefined();
    expect(screen.queryByText("Staff Management")).toBeNull();
  });

  it("opens invite modal with required fields per PRD §5.3", () => {
    render(
      <StaffManagementPage
        initialMembers={sampleMembers}
        initialDoctors={sampleDoctors}
        userRole="owner"
      />
    );

    fireEvent.click(screen.getByRole("button", { name: /\+ Add Staff/i }));

    expect(screen.getByRole("heading", { name: /Invite Staff Member/i })).toBeDefined();
    expect(screen.getByLabelText(/Staff Name/i)).toBeDefined();
    expect(screen.getByLabelText(/Email Address/i)).toBeDefined();
    expect(screen.getByLabelText(/Contact Phone/i)).toBeDefined();
    expect(screen.getByLabelText(/Staff Role/i)).toBeDefined();
  });

  it("conditionally shows linked doctor selector when role is doctor", () => {
    render(
      <StaffManagementPage
        initialMembers={sampleMembers}
        initialDoctors={sampleDoctors}
        userRole="owner"
      />
    );

    fireEvent.click(screen.getByRole("button", { name: /\+ Add Staff/i }));

    // Default role is reception, doctor selector should not be present
    expect(screen.queryByLabelText(/Linked Doctor/i)).toBeNull();

    // Select doctor role
    const roleSelect = screen.getByLabelText(/Staff Role/i);
    fireEvent.change(roleSelect, { target: { value: "doctor" } });

    // Doctor selector should now be visible with options
    expect(screen.getByLabelText(/Linked Doctor/i)).toBeDefined();
    expect(screen.getByText(/Dr\. Tariq Mehmood/i)).toBeDefined();
    expect(screen.getAllByText(/Dr\. Ayesha Khan/i).length).toBeGreaterThan(0);
  });

  it("submits invite form calling POST /api/v1/members and updates list", async () => {
    const newMember: StaffMemberItem = {
      id: "m-new",
      clinic_id: "clinic-1",
      user_id: "user-new",
      name: "Bilal Receptionist",
      email: "bilal@clinic.com",
      phone: "+923009990011",
      role: "reception",
      active: true,
      created_at: "2026-11-01T00:00:00Z",
    };

    global.fetch = vi.fn().mockResolvedValueOnce({
      ok: true,
      json: async () => newMember,
    } as Response);

    render(
      <StaffManagementPage
        initialMembers={sampleMembers}
        initialDoctors={sampleDoctors}
        userRole="owner"
      />
    );

    fireEvent.click(screen.getByRole("button", { name: /\+ Add Staff/i }));

    fireEvent.change(screen.getByLabelText(/Staff Name/i), {
      target: { value: "Bilal Receptionist" },
    });
    fireEvent.change(screen.getByLabelText(/Email Address/i), {
      target: { value: "bilal@clinic.com" },
    });
    fireEvent.change(screen.getByLabelText(/Contact Phone/i), {
      target: { value: "+923009990011" },
    });

    fireEvent.click(screen.getByRole("button", { name: /Send Invite/i }));

    await waitFor(() => {
      expect(screen.getByText("Bilal Receptionist")).toBeDefined();
    });

    expect(global.fetch).toHaveBeenCalledWith(
      "/api/v1/members",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({
          name: "Bilal Receptionist",
          email: "bilal@clinic.com",
          phone: "+923009990011",
          role: "reception",
          doctor_id: null,
        }),
      })
    );
  });
});
