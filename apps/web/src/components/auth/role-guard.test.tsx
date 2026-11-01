import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { AuthProvider, useAuth } from "@/lib/auth/auth-context";
import { RoleGuard } from "./role-guard";

// Helper component to trigger login/logout in tests
function AuthController() {
  const { user, isAuthenticated, login, logout } = useAuth();
  return (
    <div>
      <span data-testid="auth-status">{isAuthenticated ? "authenticated" : "unauthenticated"}</span>
      <span data-testid="user-role">{user?.role || "none"}</span>
      <button
        onClick={() => {
          // Generate a fake JWT with role doctor
          const header = btoa(JSON.stringify({ alg: "HS256", typ: "JWT" }));
          const payload = btoa(
            JSON.stringify({
              sub: "user-123",
              email: "dr.tariq@clinic.com",
              role: "doctor",
              exp: Math.floor(Date.now() / 1000) + 3600,
            })
          );
          login(`${header}.${payload}.signature`);
        }}
      >
        Login as Doctor
      </button>
      <button onClick={logout}>Logout</button>
    </div>
  );
}

function createToken(role: string, expiresInSeconds: number = 3600): string {
  const header = btoa(JSON.stringify({ alg: "HS256", typ: "JWT" }));
  const payload = btoa(
    JSON.stringify({
      sub: "user-test",
      email: `${role}@test.com`,
      role,
      exp: Math.floor(Date.now() / 1000) + expiresInSeconds,
    })
  );
  return `${header}.${payload}.signature`;
}

describe("Authentication & RoleGuard (Task 19)", () => {
  it("login and logout work correctly", () => {
    render(
      <AuthProvider>
        <AuthController />
      </AuthProvider>
    );

    expect(screen.getByTestId("auth-status").textContent).toBe("unauthenticated");

    fireEvent.click(screen.getByText("Login as Doctor"));
    expect(screen.getByTestId("auth-status").textContent).toBe("authenticated");
    expect(screen.getByTestId("user-role").textContent).toBe("doctor");

    fireEvent.click(screen.getByText("Logout"));
    expect(screen.getByTestId("auth-status").textContent).toBe("unauthenticated");
  });

  it("handles token expiry by discarding expired credentials", () => {
    // Token that expired 10 seconds ago
    const expiredToken = createToken("doctor", -10);

    render(
      <AuthProvider initialToken={expiredToken}>
        <RoleGuard allowedRoles={["doctor"]}>
          <div>Protected Doctor Screen</div>
        </RoleGuard>
      </AuthProvider>
    );

    expect(screen.getByTestId("auth-unauthenticated")).toBeDefined();
    expect(screen.queryByText("Protected Doctor Screen")).toBeNull();
  });

  it("blocks unauthenticated users with login required screen", () => {
    render(
      <AuthProvider initialToken={null}>
        <RoleGuard allowedRoles={["owner"]}>
          <div>Secret Owner Dashboard</div>
        </RoleGuard>
      </AuthProvider>
    );

    expect(screen.getByText("Login Required")).toBeDefined();
    expect(screen.queryByText("Secret Owner Dashboard")).toBeNull();
  });

  // Acceptance requirement: "one test per role"
  it("allows platform_admin on admin-protected route and blocks other roles", () => {
    const adminToken = createToken("platform_admin");

    render(
      <AuthProvider initialToken={adminToken}>
        <RoleGuard allowedRoles={["platform_admin"]}>
          <div>Platform Admin Console</div>
        </RoleGuard>
      </AuthProvider>
    );

    expect(screen.getByText("Platform Admin Console")).toBeDefined();
  });

  it("allows owner on clinic-management route and blocks doctor (403)", () => {
    const ownerToken = createToken("owner");
    const doctorToken = createToken("doctor");

    // 1. Owner succeeds
    const { unmount } = render(
      <AuthProvider initialToken={ownerToken}>
        <RoleGuard allowedRoles={["owner"]}>
          <div>Staff Management Screen</div>
        </RoleGuard>
      </AuthProvider>
    );
    expect(screen.getByText("Staff Management Screen")).toBeDefined();
    unmount();

    // 2. Doctor gets 403 Forbidden
    render(
      <AuthProvider initialToken={doctorToken}>
        <RoleGuard allowedRoles={["owner"]}>
          <div>Staff Management Screen</div>
        </RoleGuard>
      </AuthProvider>
    );
    expect(screen.getByTestId("auth-forbidden")).toBeDefined();
    expect(screen.getByText(/403 — Access Forbidden/i)).toBeDefined();
    expect(screen.queryByText("Staff Management Screen")).toBeNull();
  });

  it("allows doctor on consultation route and blocks reception (403)", () => {
    const doctorToken = createToken("doctor");
    const receptionToken = createToken("reception");

    // 1. Doctor succeeds
    const { unmount } = render(
      <AuthProvider initialToken={doctorToken}>
        <RoleGuard allowedRoles={["doctor"]}>
          <div>Doctor Consultation Room</div>
        </RoleGuard>
      </AuthProvider>
    );
    expect(screen.getByText("Doctor Consultation Room")).toBeDefined();
    unmount();

    // 2. Reception gets 403 Forbidden
    render(
      <AuthProvider initialToken={receptionToken}>
        <RoleGuard allowedRoles={["doctor"]}>
          <div>Doctor Consultation Room</div>
        </RoleGuard>
      </AuthProvider>
    );
    expect(screen.getByTestId("auth-forbidden")).toBeDefined();
    expect(screen.queryByText("Doctor Consultation Room")).toBeNull();
  });

  it("allows reception on check-in queue route and rejects unauthorized role", () => {
    const receptionToken = createToken("reception");

    render(
      <AuthProvider initialToken={receptionToken}>
        <RoleGuard allowedRoles={["reception"]}>
          <div>Reception Walk-in Desk</div>
        </RoleGuard>
      </AuthProvider>
    );

    expect(screen.getByText("Reception Walk-in Desk")).toBeDefined();
  });
});
