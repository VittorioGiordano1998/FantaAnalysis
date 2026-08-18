import listoneData from "@/data/listone.json";

interface ListonePayload {
  version: number;
  players: { teamName: string }[];
}

const LISTONE = listoneData as ListonePayload;

const PRIMARY_TEAMS = Array.from(
  new Set(LISTONE.players.map((player) => player.teamName)),
).sort();

export const FORMATION_TEAMS: string[] = PRIMARY_TEAMS;

export function formationImageUrl(team: string): string {
  return `/formazioni/${team}.png`;
}
