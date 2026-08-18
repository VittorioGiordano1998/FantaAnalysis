"use client";

import { useRef } from "react";
import { Download, Upload } from "lucide-react";

import { useListone } from "@/lib/listone-state";

/**
 * Export/import dello stato del listone (local-first: trasferisce lo stato
 * tra device via file JSON, come l'export/import dello Streamlit).
 */
export function StateExport({
  onMessage,
}: {
  onMessage: (text: string, kind: "error" | "ok") => void;
}) {
  const inputRef = useRef<HTMLInputElement>(null);
  const exportJson = useListone((store) => store.exportJson);
  const importFromJson = useListone((store) => store.importFromJson);

  function handleExport() {
    const blob = new Blob([exportJson()], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "listone-stato.json";
    link.click();
    URL.revokeObjectURL(url);
  }

  function handleImportFile() {
    const file = inputRef.current?.files?.[0];
    if (!file) {
      return;
    }
    void file
      .text()
      .then((text) => {
        const error = importFromJson(text);
        if (error) {
          onMessage(error, "error");
        } else {
          onMessage("Stato importato: prese, prezzi e budget aggiornati.", "ok");
        }
        if (inputRef.current) {
          inputRef.current.value = "";
        }
      })
      .catch(() => onMessage("File non leggibile.", "error"));
  }

  return (
    <div className="flex shrink-0 items-center gap-1.5">
      <input
        ref={inputRef}
        type="file"
        accept="application/json"
        className="hidden"
        onChange={handleImportFile}
        data-testid="import-state-input"
      />
      <button
        type="button"
        onClick={() => inputRef.current?.click()}
        className="inline-flex h-8 items-center gap-1.5 rounded-full border border-border/70 bg-muted/40 px-3 text-xs font-medium text-muted-foreground transition-colors hover:bg-muted/70 hover:text-foreground"
      >
        <Upload className="size-3.5" />
        <span className="hidden sm:inline">Importa</span>
      </button>
      <button
        type="button"
        onClick={handleExport}
        className="inline-flex h-8 items-center gap-1.5 rounded-full border border-border/70 bg-muted/40 px-3 text-xs font-medium text-muted-foreground transition-colors hover:bg-muted/70 hover:text-foreground"
      >
        <Download className="size-3.5" />
        <span className="hidden sm:inline">Esporta</span>
      </button>
    </div>
  );
}
