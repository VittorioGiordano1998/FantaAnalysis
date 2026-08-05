# Delivery Gap: Migrazione a PuLP 4.0 (CBC esterno)

- **ID:** DG-1
- **Status:** Open
- **Release impact:** n/a — risk
- **Date opened:** 2026-08-05

## Description

`optimize.py` usa `pulp.PULP_CBC_CMD` (solver CBC incluso nel pacchetto
pulp): funziona con `pulp>=2.8` ma è deprecato e sarà rimosso in PuLP 4.0,
che richiede `pip install pulp[cbc]` (CBC installato separatamente) e
`COIN_CMD` (testato: non risolvibile oggi, `cbc.exe` assente dal PATH su
Windows e su CI).

Impatto: quando PuLP 4.0 uscirà, il solve della rosa si romperebbe senza
un cambio di dipendenza. Oggi il gap non blocca nulla (3.3.2 con CBC
bundled funziona, 54 test verdi, solve base 99 ms).

Fix direction: passare a `requirements.txt` `pulp[cbc]>=3.3` e usare
`COIN_CMD`, con verifica CI; oppure pinnare `pulp>=2.8,<4` finché il
bundled CBC non viene migrato.

## Notes

- Related: ADR-0003 (modello di ottimizzazione), M4-T1.
- Da risolvere quando PuLP 4.0 sarà stabile o prima di un deploy vincolante.
