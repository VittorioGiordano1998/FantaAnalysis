"use client";

import type { SelectHTMLAttributes } from "react";
import { ChevronDown } from "lucide-react";

interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  children: React.ReactNode;
}

/**
 * Select con aspetto Sphynx: rimuove l'aspetto nativo del browser e mostra
 * un chevron personalizzato coerente con il resto dell'interfaccia.
 */
export function Select({ children, className = "", ...props }: SelectProps) {
  return (
    <span className="relative inline-flex shrink-0 items-center">
      <select
        className={`h-9 cursor-pointer appearance-none rounded-md border border-input bg-background/40 pl-3 pr-9 text-sm text-foreground transition-colors hover:border-ring/50 focus:border-ring focus:outline-none ${className}`}
        {...props}
      >
        {children}
      </select>
      <ChevronDown className="pointer-events-none absolute right-2.5 size-4 text-muted-foreground" />
    </span>
  );
}
