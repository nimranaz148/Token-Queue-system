import React from "react";
import { cn } from "@/lib/utils";

export interface FormShellProps {
  title: string;
  badge?: React.ReactNode;
  description?: string;
  masterFields?: React.ReactNode;
  detailGrid?: React.ReactNode;
  summary?: React.ReactNode;
  actions?: React.ReactNode;
  auditPanel?: React.ReactNode;
  className?: string;
  maxFormWidth?: boolean;
}

export const FormShell: React.FC<FormShellProps> = ({
  title,
  badge,
  description,
  masterFields,
  detailGrid,
  summary,
  actions,
  auditPanel,
  className,
  maxFormWidth = true,
}) => {
  return (
    <div
      className={cn(
        "flex flex-col gap-4 w-full",
        maxFormWidth && "max-w-[960px]",
        className
      )}
    >
      {/* 1. Header / Title */}
      <div className="flex items-center justify-between pb-3 border-b border-border">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-xl font-semibold text-fg tracking-tight">{title}</h1>
            {badge && <div>{badge}</div>}
          </div>
          {description && <p className="text-xs text-fg-muted mt-1">{description}</p>}
        </div>
      </div>

      {/* 2. Filters / Master fields */}
      {masterFields && (
        <div className="p-4 rounded-lg border border-border bg-surface">
          {masterFields}
        </div>
      )}

      {/* 3. Detail grid */}
      {detailGrid && <div className="w-full">{detailGrid}</div>}

      {/* 4. Totals / summary */}
      {summary && (
        <div className="p-3 rounded-md border border-border bg-surface-sunken">
          {summary}
        </div>
      )}

      {/* 5. Actions (action bar) */}
      {actions && (
        <div className="flex items-center justify-end gap-3 pt-2">
          {actions}
        </div>
      )}

      {/* 6. Audit / status panel */}
      {auditPanel && (
        <div className="mt-4 pt-3 border-t border-border text-xs text-fg-subtle">
          {auditPanel}
        </div>
      )}
    </div>
  );
};
