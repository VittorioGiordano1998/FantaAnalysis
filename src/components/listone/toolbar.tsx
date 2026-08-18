"use client";

import { UserCheck, UserMinus, Users } from "lucide-react";

import { GROUP_LABELS, type PlayerStatus, type RoleGroup } from "@/lib/types";
import { Select } from "@/components/ui/select";

export type GroupFilter = RoleGroup | "Tutti";

interface ToolbarProps {
  query: string;
  onQueryChange: (value: string) => void;
  teams: string[];
  team: string;
  onTeamChange: (value: string) => void;
  group: GroupFilter;
  onGroupChange: (value: GroupFilter) => void;
  totalShown: number;
  total: number;
  remaining: number;
  budget: number;
  onBudgetChange: (value: number) => void;
  price: number;
  onPriceChange: (value: number) => void;
  selectedCount: number;
  onMark: (owner: PlayerStatus) => void;
  onClearSelection: () => void;
  message: { text: string; kind: "error" | "ok" } | null;
}

export function Toolbar({
  query,
  onQueryChange,
  teams,
  team,
  onTeamChange,
  group,
  onGroupChange,
  totalShown,
  total,
  remaining,
  budget,
  onBudgetChange,
  price,
  onPriceChange,
  selectedCount,
  onMark,
  onClearSelection,
  message,
}: ToolbarProps) {
  const overBudget = remaining < 0;

  return (
    <div className="glass flex flex-col gap-3 p-3 sm:p-4">
      <div className="flex flex-wrap items-center gap-2">
        <input
          type="search"
          value={query}
          onChange={(event) => onQueryChange(event.target.value)}
          placeholder="Cerca giocatore…"
          className="h-9 min-w-40 flex-1 rounded-md border border-input bg-background/40 px-3 text-sm placeholder:text-muted-foreground focus:border-ring focus:outline-none"
          data-testid="search-input"
        />
        <Select
          value={team}
          onChange={(event) => onTeamChange(event.target.value)}
          data-testid="team-select"
        >
          <option value="Tutte">Tutte le squadre</option>
          {teams.map((name) => (
            <option key={name} value={name}>
              {name}
            </option>
          ))}
        </Select>
        <Select
          value={group}
          onChange={(event) => onGroupChange(event.target.value as GroupFilter)}
          data-testid="group-select"
        >
          <option value="Tutti">Tutti i ruoli</option>
          {Object.entries(GROUP_LABELS).map(([key, label]) => (
            <option key={key} value={key}>
              {label}
            </option>
          ))}
        </Select>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <label className="flex items-center gap-2 text-xs text-muted-foreground">
          <span>Prezzo</span>
          <input
            type="number"
            min={0}
            step={1}
            value={price}
            onChange={(event) => onPriceChange(Math.max(0, Number(event.target.value) || 0))}
            className="h-9 w-20 rounded-md border border-input bg-background/40 px-2 text-sm tabular-nums focus:border-ring focus:outline-none"
            data-testid="price-input"
          />
        </label>
        <label className="flex items-center gap-2 text-xs text-muted-foreground">
          <span>Budget</span>
          <input
            type="number"
            min={1}
            step={5}
            value={budget}
            onChange={(event) => onBudgetChange(Math.max(1, Number(event.target.value) || 1))}
            className="h-9 w-24 rounded-md border border-input bg-background/40 px-2 text-sm tabular-nums focus:border-ring focus:outline-none"
            data-testid="budget-input"
          />
        </label>

        <button
          type="button"
          onClick={() => onMark("noi")}
          className="inline-flex h-9 items-center gap-1.5 rounded-md bg-primary px-3 text-sm font-medium text-primary-foreground transition-opacity hover:opacity-90"
          data-testid="mark-noi"
        >
          <UserCheck className="size-4" />
          Preso da noi
        </button>
        <button
          type="button"
          onClick={() => onMark("altri")}
          className="inline-flex h-9 items-center gap-1.5 rounded-md border border-rose-800 bg-rose-900/40 px-3 text-sm font-medium text-rose-300 transition-colors hover:bg-rose-900/60"
          data-testid="mark-altri"
        >
          <UserMinus className="size-4" />
          Preso da altri
        </button>
        {selectedCount > 0 && (
          <button
            type="button"
            onClick={onClearSelection}
            className="inline-flex h-9 items-center gap-1.5 rounded-md border border-border/70 bg-muted/40 px-3 text-xs font-medium text-muted-foreground transition-colors hover:bg-muted/70 hover:text-foreground"
          >
            <Users className="size-3.5" />
            Deseleziona ({selectedCount})
          </button>
        )}
      </div>

      <div className="flex flex-wrap items-center justify-between gap-2 border-t border-border/60 pt-2">
        <p className="text-xs text-muted-foreground">
          <span className="tabular-nums">{totalShown}</span> di{" "}
          <span className="tabular-nums">{total}</span> giocatori
          {selectedCount > 0 && (
            <span className="ml-2 text-primary">· {selectedCount} selezionati</span>
          )}
        </p>
        <p
          className={`text-xs tabular-nums ${overBudget ? "text-rose-400" : "text-emerald-400"}`}
          data-testid="remaining"
        >
          {overBudget
            ? `Sei sopra budget di ${-remaining} crediti`
            : `Residuo: ${remaining} / ${budget} crediti`}
        </p>
      </div>

      {message && (
        <p
          className={`rounded-md border px-3 py-1.5 text-xs ${
            message.kind === "error"
              ? "border-rose-800/60 bg-rose-900/20 text-rose-300"
              : "border-emerald-800/60 bg-emerald-900/20 text-emerald-300"
          }`}
          data-testid="message"
        >
          {message.text}
        </p>
      )}
    </div>
  );
}
