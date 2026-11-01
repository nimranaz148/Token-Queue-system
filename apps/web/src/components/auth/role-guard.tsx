"use client";

import React from "react";
import Link from "next/link";
import { Role, useAuth } from "@/lib/auth/auth-context";

export interface RoleGuardProps {
  allowedRoles: Role[];
  children: React.ReactNode;
  fallback?: React.ReactNode;
  redirectToLogin?: boolean;
}

export const RoleGuard: React.FC<RoleGuardProps> = ({
  allowedRoles,
  children,
  fallback,
  redirectToLogin = false,
}) => {
  const { user, isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-8" data-testid="auth-loading">
        <div className="animate-spin h-6 w-6 border-2 border-accent border-t-transparent rounded-full" />
      </div>
    );
  }

  if (!isAuthenticated || !user) {
    if (fallback) return <>{fallback}</>;
    return (
      <div className="p-8 max-w-md mx-auto text-center" data-testid="auth-unauthenticated">
        <div className="bg-surface border border-border rounded-lg p-6 space-y-4">
          <h2 className="text-lg font-semibold text-fg">Login Required</h2>
          <p className="text-sm text-fg-muted">
            Please log in with your clinic credentials to access this screen.
          </p>
          <div>
            <Link
              href="/login"
              className="inline-flex items-center justify-center h-8.5 px-4 text-sm font-medium rounded-md bg-accent text-fg-inverse hover:bg-accent-hover transition-colors"
            >
              Go to Login
            </Link>
          </div>
        </div>
      </div>
    );
  }

  const hasRequiredRole = allowedRoles.includes(user.role);

  if (!hasRequiredRole) {
    if (fallback) return <>{fallback}</>;
    return (
      <div className="p-8 max-w-lg mx-auto" data-testid="auth-forbidden">
        <div className="bg-danger-subtle border border-danger-border rounded-lg p-6 text-center space-y-3">
          <h2 className="text-lg font-bold text-danger">403 — Access Forbidden</h2>
          <p className="text-sm text-fg-muted">
            Your role (<span className="font-mono font-medium text-fg capitalize">{user.role}</span>)
            is not authorized to access this resource.
          </p>
          <p className="text-xs text-fg-subtle">
            Required role: {allowedRoles.join(" or ")} (PRD §14.2)
          </p>
        </div>
      </div>
    );
  }

  return <>{children}</>;
};
