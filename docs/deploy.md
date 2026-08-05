# Deploy su Streamlit Community Cloud

Guida completa per pubblicare FantaOptimizer su Streamlit Community Cloud e
per testarla in locale senza deploy.

---

## 1. Prerequisiti

- Il repository GitHub con l'app già pushato
  (`github.com/VittorioGiordano1998/FantaAnalysis`, branch `main`).
- Un account Streamlit gratuito: vai su <https://share.streamlit.io> e accedi
  con Google, GitHub o email (nessuna carta richiesta).

---

## 2. Primo deploy (circa 5 minuti)

1. Apri <https://share.streamlit.io> e accedi.
2. Clicca **"Create app"** → **"From existing repo"**.
3. Compila i tre campi:
   - **Repository:** `VittorioGiordano1998/FantaAnalysis`
   - **Branch:** `main`
   - **Main file path:** `main.py`
4. Apri **"Advanced settings"**:
   - **Python version:** `3.12`
   - Secrets: nessuno (l'app non usa credenziali).
5. Clicca **"Deploy"** e attendi la build (2-5 minuti: Streamlit installa
   `requirements.txt`).
6. Alla prima apertura dell'app:
   - clicca **"Aggiorna dati"** nella home: popola la cache
     (quotazioni ~10 s, statistiche ~10 s, calendario ~60 s — 38 giornate
     con rate-limit rispettato);
   - crea o importa lo stato asta dalla **sidebar → "Importa stato"**.
7. Apri l'URL dell'app dal telefono: `https://<nome-app>.streamlit.app`.

Da quel momento l'app è usabile durante l'asta come da progetto.

---

## 3. Uso quotidiano e manutenzione

| Cosa | Come |
|------|------|
| Aggiornare i dati | Pulsante **"Aggiorna dati"** (unica via di invalidazione delle cache). |
| Stato asta dopo uno sleep/restart | Su Cloud il disco è **effimero**: esporta lo stato dalla sidebar prima di chiudere (**Esporta stato** → file `asta.json`) e reimportalo alla riapertura. |
| Aggiornamenti del codice | Ogni `git push` su `main` ricompila l'app in automatico. |
| App addormentata | Il piano gratuito sospende l'app dopo inattività: basta riaprire l'URL (riattivazione in ~30-60 s). |
| Cache persa dopo lo sleep | Semplicemente ripremere **"Aggiorna dati"** (le cache sono rigenerabili). |

---

## 4. Testare senza deploy (locale)

L'app si verifica completamente in locale, senza pubblicare nulla:

```powershell
# 1. dipendenze (una volta)
python -m pip install -r requirements.txt

# 2. avvio dell'app
python -m streamlit run main.py
# → apri http://localhost:8501

# 3. dal telefono (stessa rete WiFi del PC)
python -m streamlit run main.py --server.address 0.0.0.0
# → apri dal telefono: http://<IP-del-PC>:8501
```

**Verifica automatica (nessuna rete):**

```powershell
python -m pytest          # 72 test: unit + e2e con fixture reali
```

La suite non tocca mai il web: gli scraper sono testati contro fixture
registrate e il test end-to-end simula un'asta completa (prima presa →
rosa finale).

**Smoke test delle pagine Streamlit** (script veloce da eseguire con il
Python del progetto):

```python
from streamlit.testing.v1 import AppTest

for script in ["main.py", "pages/RosaOttimale.py", "pages/Analisi.py"]:
    at = AppTest.from_file(script).run()
    assert not at.exception, f"{script} ha lanciato un'eccezione"
    print(script, "OK")
```

Questo esegue davvero le pagine (widget inclusi) e fallisce se una pagina
va in errore — lo stesso check che si fa a mano con
`streamlit run main.py`.

---

## 5. Troubleshooting

| Problema | Causa probabile | Soluzione |
|----------|-----------------|-----------|
| Primo caricamento molto lento | Cold start + scraping on demand | Attendere; poi usare **"Aggiorna dati"**. |
| Dati "azzerati" dopo un po' | Disco effimero del piano gratuito | **"Aggiorna dati"** rigenera le cache. |
| Stato asta sparito | Stato salvato solo sul disco effimero | Usare **Esporta stato/Importa stato** (percorso ufficiale). |
| Build fallita su Cloud | Dipendenza o sintassi | Guarda i log in Cloud (tab "Logs"); in locale `python -m pytest` + `python -m streamlit run main.py`. |
| Scraper rotto (pagina fonte cambiata) | Selettori/URL cambiati sul sito | Aggiornare i selettori nei moduli `fetch_*`; i test su fixture mostrano subito cosa si è rotto; aggiornare le fixture con nuove pagine reali. |
| App non raggiungibile dal telefono | Rete diversa o firewall | Stessa rete WiFi del PC; usare `--server.address 0.0.0.0`. |

---

## 6. Note

- Il deploy su Streamlit Cloud non richiede configurazioni nel repo:
  l'entrypoint è auto-rilevato (`main.py`), `data/` e `output/` sono
  gitignored e rigenerabili, nessun segreto è versionato.
- I limiti del piano gratuito (sleep, disco effimero) sono gestiti dal
  design dell'app (ADR-0004: stato via export/import bytes).
- Item aperti registrati: **KI-1** (minuti giocati non esposti dalla fonte)
  e **DG-1** (migrazione PuLP 4.0) — non bloccano il deploy.
