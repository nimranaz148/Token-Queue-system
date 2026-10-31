import React from "react";
import { cn } from "@/lib/utils";

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "danger" | "ghost";
  size?: "sm" | "md" | "lg";
}

const variantStyles = {
  primary:
    "bg-accent text-fg-inverse hover:bg-accent-hover active:bg-accent-active border border-transparent shadow-xs",
  secondary:
    "bg-surface text-fg border border-border hover:bg-surface-hover active:bg-surface-active",
  danger:
    "bg-danger text-fg-inverse hover:bg-danger-hover border border-transparent shadow-xs",
  ghost:
    "bg-transparent text-fg-muted hover:text-fg hover:bg-surface-hover border border-transparent",
};

const sizeStyles = {
  sm: "h-7 px-2.5 text-xs rounded-sm",
  md: "h-8.5 px-3.5 text-sm rounded-md",
  lg: "h-10 px-4 text-base rounded-md",
};

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "primary", size = "md", disabled, children, ...props }, ref) => {
    return (
      <button
        ref={ref}
        disabled={disabled}
        className={cn(
          "inline-flex items-center justify-center font-medium transition-colors focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-border-focus disabled:opacity-50 disabled:pointer-events-none cursor-pointer",
          variantStyles[variant],
          sizeStyles[size],
          className
        )}
        {...props}
      >
        {children}
      </button>
    );
  }
);

Button.displayName = "Button";
