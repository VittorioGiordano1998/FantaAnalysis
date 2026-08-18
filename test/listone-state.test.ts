import { describe, expect, it } from "vitest";

import {
  DEFAULT_BUDGET,
  defaultListoneState,
  deserializeListoneState,
  listoneRemaining,
  listoneSpent,
  needsPrice,
  serializeListoneState,
  toggleFlags,
} from "@/lib/listone-state";
import { mergedStatus, type ListoneRow, type ListoneState } from "@/lib/types";

function row(overrides: Partial<ListoneRow> = {}): ListoneRow {
  return {
    name: "Dimarco",
    teamName: "Inter",
    roles: ["dd", "w"],
    titolarita: 95,
    fmv: 7.64,
    rigorista: null,
    punizioni: 1,
    angoli: 2,
    presoNoi: false,
    presoAltri: false,
    ...overrides,
  };
}

describe("listone-state", () => {
  it("defaultListoneState ha budget pieno e nessuna presa", () => {
    const state = defaultListoneState();
    expect(state.budget).toBe(DEFAULT_BUDGET);
    expect(state.flags).toEqual({});
    expect(state.prices).toEqual({});
  });

  it("toggleFlags segna 'noi' con prezzo e libera togliendo il prezzo", () => {
    const state = toggleFlags(defaultListoneState(), ["Dimarco"], "noi", 30);
    expect(state.flags.Dimarco).toBe("noi");
    expect(state.prices.Dimarco).toBe(30);

    const freed = toggleFlags(state, ["Dimarco"], "noi", 0);
    expect(freed.flags.Dimarco).toBe("");
    expect(freed.prices.Dimarco).toBeUndefined();
  });

  it("toggleFlags passando ad 'altri' rimuove il prezzo", () => {
    const ours = toggleFlags(defaultListoneState(), ["Dimarco"], "noi", 30);
    const others = toggleFlags(ours, ["Dimarco"], "altri", 0);
    expect(others.flags.Dimarco).toBe("altri");
    expect(others.prices.Dimarco).toBeUndefined();
  });

  it("needsPrice richiede prezzo solo per giocatori nuovi", () => {
    const state = toggleFlags(defaultListoneState(), ["Dimarco"], "noi", 30);
    expect(needsPrice(state, ["Dimarco"], 0)).toBe(false);
    expect(needsPrice(state, ["Dimarco", "Lautaro"], 0)).toBe(true);
  });

  it("listoneSpent conta solo le prese 'noi' con prezzo", () => {
    const base: ListoneState = {
      budget: 500,
      flags: { A: "noi", B: "noi", C: "altri" },
      prices: { A: 10, B: 20, C: 999 },
    };
    expect(listoneSpent(base)).toBe(30);
    expect(listoneRemaining(base)).toBe(470);
  });

  it("serialize/deserialize round-trip v2", () => {
    const state: ListoneState = { budget: 400, flags: { A: "noi" }, prices: { A: 15 } };
    expect(deserializeListoneState(serializeListoneState(state))).toEqual(state);
  });

  it("deserialize rigetta formati non supportati", () => {
    expect(() => deserializeListoneState("{not json")).toThrow();
    expect(() => deserializeListoneState('{"version":9}')).toThrow(
      "formato di stato non supportato",
    );
  });

  it("deserialize scarta valori invalidi ma accetta il resto", () => {
    const state = deserializeListoneState(
      JSON.stringify({
        version: 2,
        budget: 500,
        flags: { A: "noi", B: "boh", C: 3 },
        prices: { A: 10, D: -5, E: "x" },
      }),
    );
    expect(state.budget).toBe(500);
    expect(state.flags).toEqual({ A: "noi" });
    expect(state.prices).toEqual({ A: 10 });
  });
});

describe("mergedStatus", () => {
  it("la sessione vince sul file Excel", () => {
    const state: ListoneState = { budget: 500, flags: { Dimarco: "altri" }, prices: {} };
    expect(mergedStatus(row({ presoNoi: true }), state)).toBe("altri");
  });

  it("senza flag di sessione usa il file", () => {
    const empty: ListoneState = { budget: 500, flags: {}, prices: {} };
    expect(mergedStatus(row({ presoNoi: true }), empty)).toBe("noi");
    expect(mergedStatus(row({ presoAltri: true }), empty)).toBe("altri");
    expect(mergedStatus(row(), empty)).toBe("");
  });

  it("il libero esplicito (\"\") vince sul file", () => {
    const freed: ListoneState = { budget: 500, flags: { Dimarco: "" }, prices: {} };
    expect(mergedStatus(row({ presoNoi: true }), freed)).toBe("");
  });
});
