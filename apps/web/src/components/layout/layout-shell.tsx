"use client";

import React, { useState } from "react";
import { cn } from "@/lib/utils";
import {
  Menu,
  X,
  Building2,
  Users,
  Activity,
  Tv,
  Settings,
  LogOut,
  Stethoscope,
} from "lucide-react";

export interface NavItem {
  label: string;
  href: string;
  icon: React.ReactNode;
  active?: boolean;
}

export interface LayoutShellProps {
  children: React.ReactNode;
  clinicName?: string;
  userName?: string;
  userRole?: string;
  navItems?: NavItem[];
  onLogout?: () => void;
}

const defaultNav: NavItem[] = [
  { label: "Today's Queue", href: "/aaj-ki-list", icon: <Activity className="w-4 h-4" />, active: true },
  { label: "Doctor Panel", href: "/doctor-panel", icon: <Stethoscope className="w-4 h-4" /> },
  { label: "TV Display", href: "/tv", icon: <Tv className="w-4 h-4" /> },
  { label: "Patients", href: "/patients", icon: <Users className="w-4 h-4" /> },
  { label: "Clinic Settings", href: "/settings", icon: <Settings className="w-4 h-4" /> },
];

export const LayoutShell: React.FC<LayoutShellProps> = ({
  children,
  clinicName = "Shifa Clinic",
  userName = "Staff User",
  userRole = "Owner",
  navItems = defaultNav,
  onLogout,
}) => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [collapsed, setCollapsed] = useState(false);

  return (
    <div className="min-h-screen w-full flex bg-canvas text-fg overflow-x-hidden">
      {/* Mobile Drawer Backdrop */}
      {mobileMenuOpen && (
        <div
          aria-label="Close mobile menu"
          className="fixed inset-0 bg-neutral/40 z-40 lg:hidden"
          onClick={() => setMobileMenuOpen(false)}
        />
      )}

      {/* Sidebar Navigation */}
      <aside
        className={cn(
          "fixed top-0 bottom-0 left-0 z-50 flex flex-col border-r border-border bg-surface transition-all duration-200",
          collapsed ? "w-14" : "w-60",
          mobileMenuOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"
        )}
      >
        {/* Sidebar Header */}
        <div className="h-14 flex items-center justify-between px-3 border-b border-border">
          <div className="flex items-center gap-2 overflow-hidden">
            <Building2 className="w-5 h-5 text-accent shrink-0" />
            {!collapsed && (
              <span className="font-semibold text-sm truncate text-fg">
                {clinicName}
              </span>
            )}
          </div>
          <button
            onClick={() => setMobileMenuOpen(false)}
            className="p-1 rounded-md text-fg-muted hover:bg-surface-hover lg:hidden"
            aria-label="Close menu"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Navigation Items */}
        <nav className="flex-1 px-2 py-3 flex flex-col gap-1 overflow-y-auto">
          {navItems.map((item) => (
            <a
              key={item.label}
              href={item.href}
              className={cn(
                "flex items-center gap-3 px-2.5 py-2 rounded-md text-xs font-medium transition-colors",
                item.active
                  ? "bg-accent-subtle text-accent border border-accent-border"
                  : "text-fg-muted hover:text-fg hover:bg-surface-hover"
              )}
              title={collapsed ? item.label : undefined}
            >
              <span className="shrink-0">{item.icon}</span>
              {!collapsed && <span className="truncate">{item.label}</span>}
            </a>
          ))}
        </nav>

        {/* Sidebar Footer / User Profile */}
        <div className="p-2 border-t border-border flex flex-col gap-1">
          <button
            onClick={() => setCollapsed(!collapsed)}
            className="hidden lg:flex items-center justify-center py-1 text-2xs text-fg-subtle hover:text-fg"
          >
            {collapsed ? "→" : "← Collapse"}
          </button>
          <div className="flex items-center justify-between px-2 py-1.5 rounded-md bg-surface-sunken">
            <div className="flex flex-col overflow-hidden">
              {!collapsed && (
                <>
                  <span className="text-xs font-medium truncate text-fg">{userName}</span>
                  <span className="text-2xs text-fg-subtle truncate uppercase">{userRole}</span>
                </>
              )}
            </div>
            {onLogout && (
              <button
                onClick={onLogout}
                className="p-1 text-fg-muted hover:text-danger rounded-md hover:bg-surface-hover"
                title="Logout"
              >
                <LogOut className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>
      </aside>

      {/* Main Page Area */}
      <div
        className={cn(
          "flex-1 flex flex-col min-w-0 transition-all duration-200",
          collapsed ? "lg:ml-14" : "lg:ml-60"
        )}
      >
        {/* Topbar */}
        <header className="h-14 border-b border-border bg-surface px-4 lg:px-6 flex items-center justify-between sticky top-0 z-30">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setMobileMenuOpen(true)}
              className="p-1.5 rounded-md text-fg-muted hover:bg-surface-hover lg:hidden"
              aria-label="Open menu"
            >
              <Menu className="w-5 h-5" />
            </button>
            <span className="text-sm font-medium text-fg">{clinicName}</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs text-fg-muted hidden sm:inline">Role: {userRole}</span>
          </div>
        </header>

        {/* Content Body */}
        <main className="flex-1 p-4 lg:p-6 w-full flex flex-col gap-4">
          {children}
        </main>
      </div>
    </div>
  );
};
