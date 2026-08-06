# Task: Visualizzatore HTML delle formazioni (titolari + riserve)

- **ID:** M8-T7
- **Status:** Done
- **Date opened:** 2026-08-06
- **Date done:** 2026-08-06
- **Severity:** Low
- **Area:** tools

## Problem

L'utente vuole vedere ogni formazione (rose alternative dei moduli) con
titolari e riserve dentro il campo, senza passare dal sito Streamlit.

## Proposed Solution

- `tools/generate_visualizer.py`: genera `output/visualizzatore.html`,
  file HTML autonomo (niente server) con:
  - dati incorporati (JSON) dalle rose alternative (`k_best_rosters`,
    stesso calcolo delle guide);
  - selettori Modulo e Alternativa;
  - campo disegnato: righe Portieri/Difensori/Centrocampisti/Attaccanti con
    i titolari (verde) e i posti vuoti (rosso tratteggiato con ruolo
    richiesto);
  - riepilogo (costo, coperto, punti, scoperte) e griglia "Riserve" con
    nome, squadra, ruoli, QI, punti, giornate facili.
- Riusa `guide.k_best_rosters` e gli helper di `tools.generate_guide`.

## Notes

- Nessuna modifica all'app; nessun ADR.

## Resolution

- `tools/generate_visualizer.py` (`python -m tools.generate_visualizer`
  [--budget N] [--output DIR] [--alternative K]): genera
  `output/visualizzatore.html`, file HTML autonomo (nessun server) con i
  dati incorporati in JSON.
- Il visualizzatore ha selettori Modulo e Alternativa; il campo disegna le
  righe Portieri/Difensori/Centrocampisti/Attaccanti con i titolari (verde:
  nome, squadra, ruoli, QI, punti, giornate facili) e i posti scoperti
  (rosso tratteggiato con il ruolo richiesto); riepilogo costo/coperto/
  punti/scoperte; griglia "Riserve" con nome, squadra, ruoli, QI, punti,
  giornate facili.
- Riusa `guide.k_best_rosters` e gli helper di `tools.generate_guide`.
- Verifica: `pytest` → 131/131; ruff puliti; generato con dati reali (4
  moduli, 10 alternative, XI + 16 riserve per alternativa, JSON valido,
  nessun placeholder residuo).
