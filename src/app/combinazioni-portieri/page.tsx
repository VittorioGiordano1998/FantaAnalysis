import type { Metadata } from "next";

import { CombinazioniView } from "@/components/combinazioni/combinazioni-view";
import { SectionNav } from "@/components/section-nav";

export const metadata: Metadata = {
  title: "Combinazioni Portieri — FantaOptimizer",
  description: "Combinazioni portieri per squadra con valutazione /100",
};

const APP_VERSION = "0.1.0";

export default function CombinazioniPortieriPage() {
  return (
    <div className="mx-auto flex min-h-dvh max-w-[1600px] flex-col gap-3 p-3 sm:p-5">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-lg">Combinazioni Portieri</h1>
          <p className="text-xs text-muted-foreground">FantaOptimizer · v{APP_VERSION}</p>
        </div>
        <SectionNav current="/combinazioni-portieri" />
      </header>

      <CombinazioniView />

      <footer className="text-center text-[11px] text-muted-foreground/60">
        Cerca la squadra per filtrare le combinazioni portieri della giornata.
      </footer>
    </div>
  );
}
