import type { Metadata } from "next";
import Link from "next/link";

import { FormationView } from "@/components/formazioni/formation-view";

export const metadata: Metadata = {
  title: "Probabili Formazioni — FantaOptimizer",
  description: "Probabili formazioni delle 20 squadre di Serie A",
};

const APP_VERSION = "0.1.0";

export default function FormazioniPage() {
  return (
    <div className="mx-auto flex min-h-dvh max-w-[1600px] flex-col gap-3 p-3 sm:p-5">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-lg">Probabili Formazioni</h1>
          <p className="text-xs text-muted-foreground">FantaOptimizer · v{APP_VERSION}</p>
        </div>
        <Link
          href="/"
          className="inline-flex h-8 items-center gap-1.5 rounded-full border border-border/70 bg-muted/40 px-3 text-xs font-medium text-muted-foreground transition-colors hover:bg-muted/70 hover:text-foreground"
        >
          Mega Listone
        </Link>
      </header>

      <FormationView />

      <footer className="text-center text-[11px] text-muted-foreground/60">
        Seleziona la squadra per vedere la probabile formazione della giornata.
      </footer>
    </div>
  );
}
