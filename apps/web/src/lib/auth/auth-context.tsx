"use client";

import React, { createContext, useContext, useEffect, useState, useMemo } from "react";

export type Role = "platform_admin" | "owner" | "doctor" | "reception";

export interface AuthUser {
  userId: string;
  email: string;
  name: string;
  role: Role;
  clinicId?: string | null;
  exp: number; // Unix timestamp in seconds
}

export interface AuthContextType {
  user: AuthUser | null;
  role: Role | null;
  clinicId: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (token: string) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

function parseJwtPayload(token: string): AuthUser | null {
  try {
    const parts = token.split(".");
    if (parts.length !== 3) return null;
    const base64Url = parts[1];
    const base64 = base64Url.replace(/-/g, "+").replace(/_/g, "/");
    const jsonPayload = decodeURIComponent(
      atob(base64)
        .split("")
        .map((c) => "%" + ("00" + c.charCodeAt(0).toString(16)).slice(-2))
        .join("")
    );
    const parsed = JSON.parse(jsonPayload);

    const now = Math.floor(Date.now() / 1000);
    const exp = parsed.exp || now + 3600;

    return {
      userId: parsed.sub || parsed.user_id || "unknown-user",
      email: parsed.email || "",
      name: parsed.name || parsed.email?.split("@")[0] || "User",
      role: parsed.role || "reception",
      clinicId: parsed.clinic_id || null,
      exp,
    };
  } catch {
    return null;
  }
}

export interface AuthProviderProps {
  children: React.ReactNode;
  initialToken?: string | null;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({
  children,
  initialToken = null,
}) => {
  const [token, setToken] = useState<string | null>(initialToken);
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // If no initialToken, check localStorage or cookie in browser
    const storedToken =
      initialToken ||
      (typeof window !== "undefined" ? localStorage.getItem("auth_token") : null);

    if (storedToken) {
      const parsedUser = parseJwtPayload(storedToken);
      const now = Math.floor(Date.now() / 1000);

      if (parsedUser && parsedUser.exp > now) {
        setUser(parsedUser);
        setToken(storedToken);
      } else {
        // Expired
        setUser(null);
        setToken(null);
        if (typeof window !== "undefined") {
          localStorage.removeItem("auth_token");
        }
      }
    } else {
      setUser(null);
      setToken(null);
    }
    setIsLoading(false);
  }, [initialToken]);

  const login = (newToken: string) => {
    const parsedUser = parseJwtPayload(newToken);
    if (!parsedUser) return;

    setUser(parsedUser);
    setToken(newToken);
    if (typeof window !== "undefined") {
      localStorage.setItem("auth_token", newToken);
    }
  };

  const logout = () => {
    setUser(null);
    setToken(null);
    if (typeof window !== "undefined") {
      localStorage.removeItem("auth_token");
    }
  };

  const value = useMemo(
    () => ({
      user,
      role: user?.role || null,
      clinicId: user?.clinicId || null,
      isAuthenticated: !!user && user.exp > Math.floor(Date.now() / 1000),
      isLoading,
      login,
      logout,
    }),
    [user, isLoading]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
