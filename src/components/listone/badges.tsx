import { cn } from "@/lib/utils";
import type { PlayerStatus } from "@/lib/types";

/** Badge di stato in stile Sphynx: dot + etichetta (TASK_STATUS_COLOR). */
export function StatusBadge({ status }: { status: PlayerStatus }) {
  const map: Record<PlayerStatus, string> = {
    "": "border-border/70 bg-muted/40 text-muted-foreground",
    noi: "border-emerald-700 bg-emerald-900/30 text-emerald-400",
    altri: "border-rose-700 bg-rose-900/30 text-rose-400",
  };
  const dot: Record<PlayerStatus, string> = {
    "": "bg-muted-foreground/60",
    noi: "bg-emerald-500",
    altri: "bg-rose-500",
  };
  const label: Record<PlayerStatus, string> = { "": "Libero", noi: "Noi", altri: "Altri" };
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 whitespace-nowrap rounded-full border px-2 py-0.5 text-[11px] font-medium",
        map[status],
      )}
    >
      <span className={cn("size-1.5 rounded-full", dot[status])} />
      {label[status]}
    </span>
  );
}

/** Chip priorità specialità (1 primo, 2 secondo, 3 terzo tiratore/battitore). */
export function PriorityChip({ value }: { value: number | null }) {
  if (value === null) {
    return <span className="text-muted-foreground/40">—</span>;
  }
  const classes: Record<number, string> = {
    1: "border-amber-700 bg-amber-900/30 text-amber-400",
    2: "border-sky-700 bg-sky-900/30 text-sky-400",
    3: "border-border bg-muted/40 text-muted-foreground",
  };
  const numeric = value >= 1 && value <= 3 ? value : 3;
  return (
    <span
      className={cn(
        "inline-flex size-5 items-center justify-center rounded-full border text-[11px] font-semibold tabular-nums",
        classes[numeric],
      )}
    >
      {value}
    </span>
  );
}

/** Colore di cella FMV, stessi significati del file Excel (≥6 verde, <6 rosso). */
export function fmvTextClass(fmv: number | null): string {
  if (fmv === null) {
    return "text-muted-foreground/40";
  }
  return fmv >= 6 ? "text-emerald-400" : "text-rose-400";
}

/** Colore di cella titolarità per soglia, come nel file Excel. */
export function titolaritaTextClass(titolarita: number | null): string {
  if (titolarita === null) {
    return "text-muted-foreground/40";
  }
  if (titolarita >= 95) {
    return "text-emerald-400";
  }
  if (titolarita >= 75) {
    return "text-amber-400";
  }
  if (titolarita >= 50) {
    return "text-orange-400";
  }
  return "text-rose-400";
}
