"use client";

import { useMemo, useState } from "react";
import Image from "next/image";

import {
  COMBINAZIONI_PORTIERI,
  GOALKEEPER_TEAMS,
  comboLabel,
  type GoalkeeperCombo,
} from "@/lib/combinazioni";
import { Select } from "@/components/ui/select";

const TEAM_FILTERS = ["Tutte"] as const;

/**
 * Griglia delle combinazioni portieri (una banda per coppia di squadre, in
 * public/combinazioni_portieri) con ricerca per squadra e filtro a tendina.
 */
export function CombinazioniView() {
  const [query, setQuery] = useState("");
  const [team, setTeam] = useState<string>("Tutte");

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return COMBINAZIONI_PORTIERI.filter((combo) => {
      if (q && !(combo.team1.toLowerCase().includes(q) || combo.team2.toLowerCase().includes(q))) {
        return false;
      }
      if (team !== "Tutte" && combo.team1 !== team && combo.team2 !== team) {
        return false;
      }
      return true;
    });
  }, [query, team]);

  return (
    <div className="flex flex-col gap-3">
      <div className="glass flex flex-col gap-3 p-3 sm:p-4">
        <div className="flex flex-wrap items-center gap-2">
          <input
            type="search"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Cerca squadra…"
            className="h-9 min-w-40 flex-1 rounded-md border border-input bg-background/40 px-3 text-sm placeholder:text-muted-foreground focus:border-ring focus:outline-none"
            data-testid="combo-search-input"
          />
          <Select
            value={team}
            onChange={(event) => setTeam(event.target.value)}
            data-testid="combo-team-select"
          >
            {TEAM_FILTERS.map((name) => (
              <option key={name} value={name}>
                {name === "Tutte" ? "Tutte le squadre" : name}
              </option>
            ))}
            {GOALKEEPER_TEAMS.map((name) => (
              <option key={name} value={name}>
                {name}
              </option>
            ))}
          </Select>
        </div>
        <p className="border-t border-border/60 pt-2 text-xs text-muted-foreground">
          <span className="tabular-nums">{filtered.length}</span> di{" "}
          <span className="tabular-nums">{COMBINAZIONI_PORTIERI.length}</span> combinazioni
          {query && <span className="ml-2 text-primary">· ricerca: “{query}”</span>}
        </p>
      </div>

      {filtered.length > 0 ? (
        <div className="grid grid-cols-1 gap-3">
          {filtered.map((combo) => (
            <ComboCard key={combo.src} combo={combo} />
          ))}
        </div>
      ) : (
        <div className="glass p-6 text-center text-sm text-muted-foreground">
          Nessuna combinazione trovata per questa ricerca.
        </div>
      )}
    </div>
  );
}

function ComboCard({ combo }: { combo: GoalkeeperCombo }) {
  return (
    <article className="glass flex flex-col gap-2 p-3">
      <div className="flex items-center justify-between gap-2">
        <h2 className="text-sm font-medium">{comboLabel(combo)}</h2>
        {combo.rating != null && (
          <span
            className="inline-flex shrink-0 items-center rounded-full border border-primary/40 bg-primary/10 px-2 py-0.5 text-xs font-semibold tabular-nums text-primary"
            data-testid="combo-rating"
          >
            {combo.rating}/100
          </span>
        )}
      </div>
      <div className="relative aspect-[40/3] overflow-hidden rounded-md border border-border/70 bg-black/20">
        <Image
          fill
          src={combo.src}
          alt={`Combinazione portieri ${comboLabel(combo)}`}
          sizes="100vw"
          className="object-contain"
          data-testid="combo-image"
        />
      </div>
    </article>
  );
}
