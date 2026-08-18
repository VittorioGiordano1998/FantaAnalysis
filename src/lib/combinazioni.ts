import combinazioniData from "@/data/combinazioni_portieri.json";

export interface GoalkeeperCombo {
  team1: string;
  team2: string;
  rating: number | null;
  src: string;
}

interface CombinazioniPayload {
  version: number;
  combos: GoalkeeperCombo[];
}

const DATA = combinazioniData as CombinazioniPayload;

export const COMBINAZIONI_PORTIERI: GoalkeeperCombo[] = DATA.combos;

export const GOALKEEPER_TEAMS: string[] = Array.from(
  new Set(COMBINAZIONI_PORTIERI.flatMap((combo) => [combo.team1, combo.team2])),
).sort();

export function comboLabel(combo: GoalkeeperCombo): string {
  return `${combo.team1} · ${combo.team2}`;
}
