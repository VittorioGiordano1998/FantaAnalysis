/**
 * Stato del mega listone — local-first senza auth (mirror di `state.py` v2).
 *
 * Le mutazioni sono funzioni pure su `ListoneState` (stesso comportamento di
 * `main.py: _toggle_flags` / `_needs_price`); la persistenza nel browser avviene
 * via `localStorage`. Su device diversi lo stato si sposta con export/import
 * del JSON: niente backend, niente account.
 */

import { create } from "zustand";
import { persist } from "zustand/middleware";

import type { ListoneState, PlayerStatus } from "./types";

export const DEFAULT_BUDGET = 500;

/** Chiave localStorage, versionata (schema v2). */
const PERSIST_KEY = "fanta-listone-v2";
const VIEW_VERSION = 2;
const VALID_OWNERS: readonly PlayerStatus[] = ["noi", "altri", ""];

export function defaultListoneState(): ListoneState {
  return { budget: DEFAULT_BUDGET, flags: {}, prices: {} };
}

/** Crediti spesi per la propria squadra (prese "noi" con prezzo). */
export function listoneSpent(state: ListoneState): number {
  let spent = 0;
  for (const [name, price] of Object.entries(state.prices)) {
    if (state.flags[name] === "noi") {
      spent += price;
    }
  }
  return spent;
}

/** Crediti residui: budget totale meno quanto speso. */
export function listoneRemaining(state: ListoneState): number {
  return state.budget - listoneSpent(state);
}

/** Vero se il mark "noi" richiede un prezzo (almeno un giocatore nuovo). */
export function needsPrice(
  state: ListoneState,
  names: readonly string[],
  price: number,
): boolean {
  return price <= 0 && names.some((name) => state.flags[name] !== "noi");
}

/**
 * Alterna le prese dei giocatori selezionati (noi/altri/libero).
 *
 * Segnando "noi" con un prezzo il prezzo viene registrato; liberando o
 * passando ad "altri" il prezzo viene rimosso. — copia di `_toggle_flags`.
 */
export function toggleFlags(
  state: ListoneState,
  names: readonly string[],
  owner: PlayerStatus,
  price: number,
): ListoneState {
  const flags = { ...state.flags };
  const prices = { ...state.prices };
  for (const name of names) {
    if (flags[name] === owner) {
      flags[name] = "";
      delete prices[name];
    } else {
      flags[name] = owner;
      if (owner === "noi" && price > 0) {
        prices[name] = price;
      } else {
        delete prices[name];
      }
    }
  }
  return { budget: state.budget, flags, prices };
}

/** Stato → stringa JSON versionata (schema v2, round-trip tra device). */
export function serializeListoneState(state: ListoneState): string {
  return JSON.stringify(
    {
      version: VIEW_VERSION,
      budget: state.budget,
      flags: state.flags,
      prices: state.prices,
    },
    null,
    2,
  );
}

/**
 * Stringa JSON → stato, con validazione (a schema v2).
 *
 * Args:
 *     text: JSON prodotto da `serializeListoneState`.
 *
 * Returns:
 *     Lo stato importato.
 *
 * Throws:
 *     Error se il payload è malformato (JSON, versione o forma).
 */
export function deserializeListoneState(text: string): ListoneState {
  let payload: unknown;
  try {
    payload = JSON.parse(text);
  } catch {
    throw new Error("file di stato non valido: JSON malformato");
  }
  if (typeof payload !== "object" || payload === null) {
    throw new Error("file di stato non valido: forma inattesa");
  }
  const record = payload as Record<string, unknown>;
  if (record.version !== VIEW_VERSION) {
    throw new Error(`formato di stato non supportato (atteso v${VIEW_VERSION})`);
  }

  let budget = DEFAULT_BUDGET;
  if (typeof record.budget === "number" && Number.isFinite(record.budget) && record.budget > 0) {
    budget = Math.trunc(record.budget);
  }

  const flags: Record<string, PlayerStatus> = {};
  if (typeof record.flags === "object" && record.flags !== null) {
    for (const [name, owner] of Object.entries(record.flags as object)) {
      if (VALID_OWNERS.includes(owner as PlayerStatus)) {
        flags[name] = owner as PlayerStatus;
      }
    }
  }

  const prices: Record<string, number> = {};
  if (typeof record.prices === "object" && record.prices !== null) {
    for (const [name, value] of Object.entries(record.prices as object)) {
      if (typeof value === "number" && Number.isFinite(value) && value >= 0) {
        prices[name] = Math.trunc(value);
      }
    }
  }

  return { budget, flags, prices };
}

interface ListoneStore {
  state: ListoneState;
  setBudget: (budget: number) => void;
  /**
   * Alterna le prese per i nomi selezionati (noi/altri).
   *
   * Returns:
   *     null in caso di successo; un messaggio d'errore (italiano) altrimenti.
   */
  toggle: (names: readonly string[], owner: PlayerStatus, price: number) => string | null;
  /** Sostituisce lo stato dal JSON importato (device diverso). */
  importFromJson: (text: string) => string | null;
  exportJson: () => string;
}

export const useListone = create<ListoneStore>()(
  persist(
    (set, get) => ({
      state: defaultListoneState(),
      setBudget: (budget) =>
        set(({ state }) => ({
          state: { ...state, budget: Math.max(1, Math.trunc(budget)) },
        })),
      toggle: (names, owner, price) => {
        if (names.length === 0) {
          return "Seleziona prima una o più righe dalla tabella.";
        }
        if (owner === "noi" && needsPrice(get().state, names, price)) {
          return "Inserisci il prezzo pagato (crediti) prima di segnare 'Preso da noi'.";
        }
        set(({ state }) => ({ state: toggleFlags(state, names, owner, price) }));
        return null;
      },
      importFromJson: (text) => {
        try {
          set({ state: deserializeListoneState(text) });
          return null;
        } catch (error) {
          return error instanceof Error ? error.message : "file di stato non valido";
        }
      },
      exportJson: () => serializeListoneState(get().state),
    }),
    { name: PERSIST_KEY, partialize: (store) => ({ state: store.state }) },
  ),
);
