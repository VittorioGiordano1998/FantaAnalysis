"use client";

import { useState } from "react";
import Image from "next/image";

import { FORMATION_TEAMS, formationImageUrl } from "@/lib/formazioni";
import { Select } from "@/components/ui/select";

/**
 * Selettore squadra + anteprima della probabile formazione (immagini in
 * public/formazioni, una PNG per squadra).
 */
export function FormationView() {
  const [team, setTeam] = useState("");

  return (
    <div className="glass flex flex-col gap-4 p-3 sm:p-5">
      <div className="flex flex-wrap items-center gap-2">
        <Select
          value={team}
          onChange={(event) => setTeam(event.target.value)}
          data-testid="formation-team-select"
        >
          <option value="">Seleziona squadra</option>
          {FORMATION_TEAMS.map((name) => (
            <option key={name} value={name}>
              {name}
            </option>
          ))}
        </Select>
      </div>

      {team ? (
        <div className="relative mx-auto aspect-[1/1] w-full max-w-[900px] overflow-hidden rounded-lg border border-border/70 bg-black/20">
          <Image
            fill
            src={formationImageUrl(team)}
            alt={`Probabile formazione ${team}`}
            sizes="(min-width: 960px) 900px, 100vw"
            className="object-contain"
            priority
            data-testid="formation-image"
          />
        </div>
      ) : (
        <p className="pb-4 text-center text-sm text-muted-foreground">
          Seleziona una squadra per vedere la probabile formazione.
        </p>
      )}
    </div>
  );
}
