import React from "react";
import { cn } from "@/lib/utils";

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  required?: boolean;
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, label, error, required, id, disabled, readOnly, ...props }, ref) => {
    const inputId = id || (label ? label.toLowerCase().replace(/\s+/g, "-") : undefined);

    return (
      <div className="w-full flex flex-col gap-1">
        {label && (
          <label htmlFor={inputId} className="text-xs text-fg-muted font-medium">
            {label}
            {required && <span className="text-danger ml-0.5">*</span>}
          </label>
        )}
        <input
          id={inputId}
          ref={ref}
          disabled={disabled}
          readOnly={readOnly}
          className={cn(
            "h-8.5 px-3 text-sm rounded-md border border-border bg-surface text-fg placeholder:text-fg-subtle transition-colors focus:outline-hidden focus:border-border-focus focus:ring-1 focus:ring-border-focus",
            readOnly && "bg-surface-sunken cursor-default",
            disabled && "text-fg-subtle cursor-not-allowed opacity-60 bg-surface-sunken",
            error && "border-danger focus:border-danger focus:ring-danger",
            className
          )}
          {...props}
        />
        {error && <span className="text-xs text-danger">{error}</span>}
      </div>
    );
  }
);

Input.displayName = "Input";
