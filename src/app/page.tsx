"use client";

import { useMemo, useState } from "react";

import listoneData from "@/data/listone.json";
import { StateExport } from "@/components/listone/state-export";
import { ListoneTable, type ListoneRowView } from "@/components/listone/listone-table";
import { Toolbar, type GroupFilter } from "@/components/listone/toolbar";
import { SectionNav } from "@/components/section-nav";
import { listoneRemaining, useListone } from "@/lib/listone-state";
import type { ListoneRow, PlayerStatus } from "@/lib/types";
import { GROUP_BY_ROLE, mergedStatus } from "@/lib/types";

interface ListonePayload {
  version: number;
  players: ListoneRow[];
}

const LISTONE = listoneData as ListonePayload;

const APP_VERSION = "0.1.0";

export default function ListonePage() {
  const listone = useListone((store) => store.state);
  const toggle = useListone((store) => store.toggle);
  const setBudget = useListone((store) => store.setBudget);

  const [query, setQuery] = useState("");
  const [team, setTeam] = useState("Tutte");
  const [group, setGroup] = useState<GroupFilter>("Tutti");
  const [price, setPrice] = useState(0);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [message, setMessage] = useState<{ text: string; kind: "error" | "ok" } | null>(null);

  const teams = useMemo(
    () => Array.from(new Set(LISTONE.players.map((player) => player.teamName))).sort(),
    [],
  );

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return LISTONE.players.filter((player) => {
      if (q && !player.name.toLowerCase().includes(q)) {
        return false;
      }
      if (team !== "Tutte" && player.teamName !== team) {
        return false;
      }
      if (group !== "Tutti" && !player.roles.some((role) => GROUP_BY_ROLE[role] === group)) {
        return false;
      }
      return true;
    });
  }, [query, team, group]);

  const rows: ListoneRowView[] = useMemo(
    () =>
      filtered.map((player) => ({
        player,
        status: mergedStatus(player, listone),
        price:
          listone.flags[player.name] === "noi" ? (listone.prices[player.name] ?? null) : null,
      })),
    [filtered, listone],
  );

  const remaining = useMemo(() => listoneRemaining(listone), [listone]);

  function handleToggle(name: string) {
    setMessage(null);
    setSelected((current) => {
      const next = new Set(current);
      if (next.has(name)) {
        next.delete(name);
      } else {
        next.add(name);
      }
      return next;
    });
  }

  function handleToggleAll(checked: boolean) {
    setMessage(null);
    setSelected(checked ? new Set(rows.map((row) => row.player.name)) : new Set());
  }

  function clearSelection() {
    setMessage(null);
    setSelected(new Set());
  }

  function handleMark(owner: PlayerStatus) {
    const error = toggle([...selected], owner, price);
    if (error) {
      setMessage({ text: error, kind: "error" });
    } else {
      setPrice(0);
      setMessage(null);
    }
  }

  return (
    <div className="mx-auto flex min-h-dvh max-w-[1600px] flex-col gap-3 p-3 sm:p-5">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-lg">Mega Listone</h1>
          <p className="text-xs text-muted-foreground">FantaOptimizer · v{APP_VERSION}</p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <SectionNav current="/" />
          <StateExport onMessage={(text, kind) => setMessage({ text, kind })} />
        </div>
      </header>

      <Toolbar
        query={query}
        onQueryChange={setQuery}
        teams={teams}
        team={team}
        onTeamChange={setTeam}
        group={group}
        onGroupChange={setGroup}
        totalShown={filtered.length}
        total={LISTONE.players.length}
        remaining={remaining}
        budget={listone.budget}
        onBudgetChange={setBudget}
        price={price}
        onPriceChange={setPrice}
        selectedCount={selected.size}
        onMark={handleMark}
        onClearSelection={clearSelection}
        message={message}
      />

      <ListoneTable
        rows={rows}
        selected={selected}
        onToggle={handleToggle}
        onToggleAll={handleToggleAll}
      />

      <footer className="text-center text-[11px] text-muted-foreground/60">
        Verde = preso da noi · rosso = preso da altri · premi di nuovo lo stesso pulsante per
        liberare un giocatore.
      </footer>
    </div>
  );
}
