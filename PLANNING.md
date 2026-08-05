# FantaOptimizer — Piano di sviluppo

Web app per il fantacalcio **Serie A 2026/27** — Asta 500M, regolamento **Mantra**, listone ufficiale Fantacalcio.it.

---

## 1. Obiettivo

App web (Streamlit) usabile anche dal telefono durante l'asta, che:

- tiene traccia dei giocatori presi (tuoi e degli altri) e dello stato dell'asta;
- ricalcola in tempo reale la **rosa ottimale** tra i giocatori rimasti, con budget e slot per ruolo residui;
- suggerisce per ogni giocatore rimasto **quanto offrire al massimo** all'asta;
- offre analisi: statistiche, proiezioni punti, calendario facile/difficile, rapporto qualità/prezzo;
- esporta report Excel.

## 2. Funzionalità

| # | Funzione | Dettaglio |
|---|----------|-----------|
| 1 | Stato asta live | Giocatori presi (tua squadra / altre squadre), budget speso/residuo, slot rimasti per ruolo (P, DC, DD, DS, E, M, CC, W, T, PC). A ogni modifica → ricalcolo automatico. |
| 2 | Chi prendere ora | Ottimizzazione PuLP sui soli giocatori rimasti, con vincoli dinamici: budget residuo + slot mancanti. Rosa finale 25 (2P-8D-8C-7A). |
| 3 | Limite di spesa per giocatore | Prezzo massimo consigliato = valore punti attesi − costo opportunità (quanto serve per coprire i ruoli mancanti). |
| 4 | Analisi giocatori | Proiezioni punti per ruolo (stats stagione + FVM + rigori + gol subiti), calendario facile/difficile (5 giornate), top qualità/prezzo. |
| 5 | Persistenza stato | File JSON locale + esporta/importa stato da telefono (Streamlit Cloud non ha disco persistente). |
| 6 | Aggiornamento dati | Pulsante "Aggiorna dati" (cache settimanale CSV). |
| 7 | Export Excel | Rosa ottimale, giocatori rimasti, classifica per ruolo, calendario, qualità/prezzo. |

## 3. Fonti dati (gratuite)

| Fonte | Dato | Stato |
|-------|------|-------|
| `fantacalcio.it/quotazioni-fantacalcio` | QI (prezzo iniziale), QA (aggiornata), FVM, squadra, ruolo Mantra | ✅ verificata |
| Fantacalcio.it — pagina statistiche | Gol, assist, minuti, cartellini, rigori per giocatore | ⚠️ URL da individuare |
| Fantacalcio.it — calendario Serie A | Partite e giornate | ⚠️ da individuare |
| Understat (`understat.com/league/Serie_A`) | xG / xA giocatori e squadre (cross-check proiezioni) | ✅ verificata |

Scraping con `requests` + `BeautifulSoup`, cache locale in CSV.

## 4. Architettura

```
Desktop/fantacalcio/
├── PLANNING.md            # questo file
├── main.py                # UI Streamlit (sidebar stato asta + pagine)
├── fetch_quotazioni.py    # scraping quotazioni fantacalcio.it
├── fetch_stats.py         # scraping statistiche giocatori
├── fetch_fixtures.py      # scraping calendario + classifica
├── projection.py          # punti attesi per ruolo Mantra
├── optimize.py            # ottimizzatore PuLP + limite spesa
├── state.py               # stato asta (JSON + import/export)
├── requirements.txt
├── data/                  # cache CSV + stato asta
└── output/                # report Excel
```

## 5. Modello di proiezione punti

- Punti fanta attesi per ruolo (regolamento Mantra standard):
  - portieri/difensori: gol subiti, clean sheet, gol, assist, cartellini, rigori parati;
  - centrocampisti: gol (bonus), assist, cartellini, rigori;
  - attaccanti: gol, assist, rigori, cartellini.
- Base: statistiche stagione in corso + FVM (Fantacalcio.it) + minuti giocati.
- Aggiustamento calendario: forza avversarie (classifica/xG) applicata alle prossime 5 giornate.

## 6. Ottimizzazione (PuLP)

- **Obiettivo**: massimizzare punti attesi totali della rosa.
- **Vincoli**:
  - budget totale 500M (modificabile);
  - rosa 25 giocatori: 2 portieri, 8 difensori, 8 centrocampisti, 7 attaccanti (configurabile);
  - solo giocatori rimasti all'asta;
  - prezzo = QI (opzione QA).
- **Limite spesa**: ricalcolo marginale per ogni candidato → prezzo massimo consigliato.

## 7. Deploy

1. Repo GitHub con il progetto.
2. Streamlit Community Cloud (gratis) → link apribile dal telefono.
3. Locale: `streamlit run main.py` dopo `pip install -r requirements.txt`.

## 8. Dipendenze

`streamlit`, `pandas`, `openpyxl`, `pulp`, `requests`, `beautifulsoup4`, `plotly`

## 9. Assunzioni (modificabili dall'app)

- Asta 500M; rosa 25: 2P-8D-8C-7A; prezzo asta = QI.
- Proiezione: stats in corso + FVM, aggiustata su 5 giornate.
- Regolamento Mantra standard (nessun ribasso obbligatorio: eventuali regole lega da configurare).

## 10. Passi di implementazione

1. Scraper quotazioni → CSV cache → verifica dati.
2. Scraper statistiche giocatori + calendario.
3. Modello proiezioni punti per ruolo.
4. Ottimizzatore PuLP dinamico + limite di spesa.
5. UI Streamlit con stato asta interattivo.
6. Export Excel.
7. Deploy GitHub + Streamlit Cloud.
8. Test end-to-end con dati reali.
