/**
 * Entità condivise del layer web — mirror di `entities.py` (layer logic).
 *
 * `ListoneRow` è display-only (come nel progetto Streamlit) e non partecipa
 * alle proiezioni né all'ottimizzazione (fase futura, rewrite TS.
 *
 * @fileoverview Tipi del mega listone (stesso schema di `fetch_listone.py` +
 * `state.py` v2: nessuna colonna aggiunta, nessuna priorità manuale).
 */

export const ROLES = [
  "por",
  "dc",
  "b",
  "dd",
  "ds",
  "e",
  "m",
  "c",
  "w",
  "t",
  "a",
  "pc",
] as const;

export type Role = (typeof ROLES)[number];

export const ROLE_LABELS: Record<Role, string> = {
  por: "Portiere",
  dc: "Difensore centrale",
  b: "Braccetto",
  dd: "Difensore destro",
  ds: "Difensore sinistro",
  e: "Esterno",
  m: "Mediano",
  c: "Centrocampista centrale",
  w: "Ala",
  t: "Trequartista",
  a: "Attaccante",
  pc: "Punta centrale",
};

export type RoleGroup = "P" | "D" | "C" | "A";

export const GROUP_BY_ROLE: Record<Role, RoleGroup> = {
  por: "P",
  dc: "D",
  b: "D",
  dd: "D",
  ds: "D",
  e: "C",
  m: "C",
  c: "C",
  w: "C",
  t: "C",
  a: "A",
  pc: "A",
};

export const GROUP_LABELS: Record<RoleGroup, string> = {
  P: "Portieri",
  D: "Difensori",
  C: "Centrocampisti",
  A: "Attaccanti",
};

/** Stato di presa di un giocatore (stessi 3 stati del listone Streamlit). */
export type PlayerStatus = "noi" | "altri" | "";

/** Riga del listone completo (file Excel dell'utente, display-only). */
export interface ListoneRow {
  name: string;
  teamName: string;
  roles: Role[];
  titolarita: number | null;
  fmv: number | null;
  rigorista: number | null;
  punizioni: number | null;
  angoli: number | null;
  presoNoi: boolean;
  presoAltri: boolean;
}

/** Stato delle prese del listone (mirror di `ListoneState` / `state.py` v2). */
export interface ListoneState {
  budget: number;
  /** nome giocatore → "noi" | "altri" | "" (libero esplicito). */
  flags: Record<string, PlayerStatus>;
  /** nome giocatore → crediti pagati (solo presi da noi). */
  prices: Record<string, number>;
}

/** Stato di presa effettivo di una riga: sessione se presente, poi file. */
export function mergedStatus(
  row: ListoneRow,
  state: ListoneState,
): PlayerStatus {
  const session = state.flags[row.name];
  if (session !== undefined) {
    return session;
  }
  if (row.presoNoi) {
    return "noi";
  }
  if (row.presoAltri) {
    return "altri";
  }
  return "";
}

/** Codici ruolo compatti come sul listone (es. "E", "E/W"). */
export function roleCodes(roles: Role[]): string {
  return roles.map((role) => role.toUpperCase()).join("/");
}
