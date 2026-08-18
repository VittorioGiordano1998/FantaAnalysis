"use client";

import type { ListoneRow, PlayerStatus } from "@/lib/types";
import { roleCodes } from "@/lib/types";
import { cn } from "@/lib/utils";
import {
  PriorityChip,
  StatusBadge,
  fmvTextClass,
  titolaritaTextClass,
} from "./badges";

export interface ListoneRowView {
  player: ListoneRow;
  status: PlayerStatus;
  price: number | null;
}

interface ListoneTableProps {
  rows: ListoneRowView[];
  selected: Set<string>;
  onToggle: (name: string) => void;
  onToggleAll: (checked: boolean) => void;
}

/** Tabella dati del listone in stile Sphynx (stesso schema del file Excel). */
export function ListoneTable({ rows, selected, onToggle, onToggleAll }: ListoneTableProps) {
  const allSelected = rows.length > 0 && rows.every((row) => selected.has(row.player.name));

  return (
    <div className="glass overflow-hidden">
      <div className="max-h-[calc(100dvh-19rem)] min-h-64 overflow-auto">
        <table className="w-full min-w-[58rem] border-collapse text-sm">
          <thead className="sticky top-0 z-10 bg-card">
            <tr className="border-b border-border/70">
              <th className="px-2 py-2 text-left">
                <input
                  type="checkbox"
                  checked={allSelected}
                  onChange={(event) => onToggleAll(event.target.checked)}
                  aria-label="Seleziona tutti i giocatori mostrati"
                  className="size-4 accent-[var(--primary)]"
                  data-testid="select-all"
                />
              </th>
              {["Giocatore", "Ruolo", "Squadra", "Stato", "Titolarità", "FMV", "Rigorista", "Punizioni", "Angoli", "Prezzo"].map(
                (label) => (
                  <th
                    key={label}
                    className="whitespace-nowrap px-3 py-2 text-left text-[11px] font-semibold uppercase tracking-[0.12em] text-muted-foreground"
                  >
                    {label}
                  </th>
                ),
              )}
            </tr>
          </thead>
          <tbody>
            {rows.map(({ player, status, price }) => {
              const isSelected = selected.has(player.name);
              return (
                <tr
                  key={player.name}
                  onClick={() => onToggle(player.name)}
                  className={cn(
                    "cursor-pointer border-b border-border/40 transition-colors",
                    status === "noi"
                      ? "bg-emerald-500/10 hover:bg-emerald-500/15"
                      : status === "altri"
                        ? "bg-rose-500/10 hover:bg-rose-500/15"
                        : "hover:bg-muted/40",
                    isSelected && "bg-primary/10",
                  )}
                >
                  <td className="px-2 py-1.5">
                    <input
                      type="checkbox"
                      checked={isSelected}
                      onChange={() => onToggle(player.name)}
                      onClick={(event) => event.stopPropagation()}
                      aria-label={`Seleziona ${player.name}`}
                      className="size-4 accent-[var(--primary)]"
                    />
                  </td>
                  <td className="whitespace-nowrap px-3 py-1.5 font-medium">{player.name}</td>
                  <td className="whitespace-nowrap px-3 py-1.5 text-xs uppercase text-muted-foreground">
                    {roleCodes(player.roles)}
                  </td>
                  <td className="whitespace-nowrap px-3 py-1.5 text-muted-foreground">
                    {player.teamName}
                  </td>
                  <td className="px-3 py-1.5">
                    <StatusBadge status={status} />
                  </td>
                  <td
                    className={cn(
                      "whitespace-nowrap px-3 py-1.5 tabular-nums",
                      titolaritaTextClass(player.titolarita),
                    )}
                  >
                    {player.titolarita === null ? "—" : `${Math.round(player.titolarita)}%`}
                  </td>
                  <td
                    className={cn(
                      "whitespace-nowrap px-3 py-1.5 tabular-nums",
                      fmvTextClass(player.fmv),
                    )}
                  >
                    {player.fmv === null ? "—" : player.fmv.toFixed(2)}
                  </td>
                  <td className="px-3 py-1.5">
                    <PriorityChip value={player.rigorista} />
                  </td>
                  <td className="px-3 py-1.5">
                    <PriorityChip value={player.punizioni} />
                  </td>
                  <td className="px-3 py-1.5">
                    <PriorityChip value={player.angoli} />
                  </td>
                  <td className="whitespace-nowrap px-3 py-1.5 text-right tabular-nums">
                    {price === null ? (
                      <span className="text-muted-foreground/40">—</span>
                    ) : (
                      <span className="font-medium text-emerald-400">{price}</span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
        {rows.length === 0 && (
          <p className="px-4 py-8 text-center text-sm text-muted-foreground">
            Nessun giocatore corrisponde ai filtri.
          </p>
        )}
      </div>
    </div>
  );
}
