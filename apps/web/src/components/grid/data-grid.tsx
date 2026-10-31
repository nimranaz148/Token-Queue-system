import React from "react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";

export interface Column<T> {
  key: string;
  header: string;
  align?: "left" | "center" | "right";
  numeric?: boolean;
  render?: (row: T) => React.ReactNode;
  width?: string;
}

export interface DataGridProps<T> {
  columns: Column<T>[];
  data: T[];
  isLoading?: boolean;
  isError?: boolean;
  isUnauthorized?: boolean;
  emptyTitle?: string;
  emptyAction?: React.ReactNode;
  errorMessage?: string;
  onRetry?: () => void;
  selectedId?: string | number;
  onRowClick?: (row: T) => void;
  className?: string;
}

export function DataGrid<T extends Record<string, any>>({
  columns,
  data,
  isLoading,
  isError,
  isUnauthorized,
  emptyTitle = "No records found",
  emptyAction,
  errorMessage = "Failed to load data",
  onRetry,
  selectedId,
  onRowClick,
  className,
}: DataGridProps<T>) {
  // 1. Loading State (Skeleton rows, never bare spinner)
  if (isLoading) {
    return (
      <div className={cn("w-full border border-border rounded-md bg-surface overflow-hidden", className)}>
        <div className="flex bg-surface-sunken border-b border-border text-xs font-medium text-fg-muted py-2.5 px-3">
          {columns.map((col) => (
            <div key={col.key} className={cn("flex-1", col.numeric ? "text-right" : "text-left")}>
              {col.header}
            </div>
          ))}
        </div>
        <div className="divide-y divide-border">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="flex items-center px-3 h-9 animate-pulse gap-4">
              {columns.map((col) => (
                <div
                  key={col.key}
                  className={cn(
                    "h-3.5 bg-neutral-subtle rounded-sm",
                    col.numeric ? "ml-auto w-16" : "w-3/4"
                  )}
                />
              ))}
            </div>
          ))}
        </div>
      </div>
    );
  }

  // 2. Unauthorized State
  if (isUnauthorized) {
    return (
      <div className="w-full p-8 border border-border rounded-md bg-surface text-center flex flex-col items-center justify-center gap-2">
        <h3 className="text-sm font-semibold text-danger">Access Denied</h3>
        <p className="text-xs text-fg-muted">You do not have permission to view these records.</p>
      </div>
    );
  }

  // 3. Error State
  if (isError) {
    return (
      <div className="w-full p-8 border border-danger-border rounded-md bg-danger-subtle text-center flex flex-col items-center justify-center gap-3">
        <h3 className="text-sm font-semibold text-danger">Failed to load data</h3>
        <p className="text-xs text-danger">{errorMessage}</p>
        {onRetry && (
          <Button variant="secondary" size="sm" onClick={onRetry}>
            Retry
          </Button>
        )}
      </div>
    );
  }

  // 4. Empty State
  if (data.length === 0) {
    return (
      <div className="w-full p-10 border border-border rounded-md bg-surface text-center flex flex-col items-center justify-center gap-3">
        <h3 className="text-sm font-medium text-fg">{emptyTitle}</h3>
        <p className="text-xs text-fg-muted">There are no records to display at this time.</p>
        {emptyAction && <div className="mt-2">{emptyAction}</div>}
      </div>
    );
  }

  // 5. Standard Grid Content
  return (
    <div className={cn("w-full border border-border rounded-md bg-surface overflow-x-auto", className)}>
      <table className="w-full border-collapse text-left text-sm">
        <thead className="bg-surface-sunken border-b border-border text-xs font-medium text-fg-muted sticky top-0">
          <tr>
            {columns.map((col) => {
              const align = col.numeric ? "right" : col.align || "left";
              return (
                <th
                  key={col.key}
                  style={col.width ? { width: col.width } : undefined}
                  className={cn(
                    "px-3 py-2 font-medium tracking-normal",
                    align === "right" && "text-right",
                    align === "center" && "text-center",
                    align === "left" && "text-left"
                  )}
                >
                  {col.header}
                </th>
              );
            })}
          </tr>
        </thead>
        <tbody className="divide-y divide-border">
          {data.map((row, index) => {
            const isSelected = selectedId !== undefined && row.id === selectedId;
            return (
              <tr
                key={row.id || index}
                onClick={() => onRowClick?.(row)}
                className={cn(
                  "h-9 transition-colors text-fg",
                  onRowClick && "cursor-pointer hover:bg-surface-hover",
                  isSelected && "bg-surface-active"
                )}
              >
                {columns.map((col) => {
                  const align = col.numeric ? "right" : col.align || "left";
                  const value = col.render ? col.render(row) : row[col.key];
                  return (
                    <td
                      key={col.key}
                      className={cn(
                        "px-3 py-1.5",
                        align === "right" && "text-right font-mono",
                        align === "center" && "text-center",
                        align === "left" && "text-left"
                      )}
                    >
                      {value}
                    </td>
                  );
                })}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
