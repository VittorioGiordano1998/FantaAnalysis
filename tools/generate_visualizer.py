"""Genera `output/visualizzatore.html`: formazioni con titolari e riserve.

Uso: python -m tools.generate_visualizer [--budget N] [--output DIR]
      [--alternative K]

Riusa la logica di `guide.py` (k_best_rosters) e i dati della cache
`data/`; produce un file HTML autonomo (nessun server) con la formazione
disegnata per ogni modulo/alternativa: titolari nel campo, riserve sotto.
"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

from entities import GROUP_LABELS, RoleGroup
from guide import k_best_rosters
from projection import project
from tools.generate_guide import GuideContext, _easy_weeks, _load_data, _role_code
from utility import (
    MODULE_POSITIONS,
    MODULES,
    formation_positions,
    remaining_weeks,
)

logger = logging.getLogger(__name__)

_LINE_ORDER = (RoleGroup.P, RoleGroup.D, RoleGroup.C, RoleGroup.A)

_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>FantaOptimizer — Formazioni titolari e riserve</title>
<style>
  body { font-family: system-ui, sans-serif; margin: 16px; background: #f4f6f8; color: #1c2530; }
  h1 { font-size: 20px; }
  header { display: flex; gap: 12px; align-items: center; flex-wrap: wrap; }
  select { padding: 8px; font-size: 16px; border-radius: 8px; border: 1px solid #cbd5e1;
           background: #fff; }
  .summary { margin: 12px 0; font-size: 15px; }
  .uncovered { color: #b91c1c; }
  .field { background: linear-gradient(#e9f2e9, #dcefe0); border: 1px solid #bcd9c0;
           border-radius: 14px; padding: 12px; margin-bottom: 14px; }
  .line { display: flex; justify-content: center; gap: 8px; margin: 8px 0; flex-wrap: wrap; }
  .line-label { text-align: center; font-weight: 600; color: #475569; font-size: 13px;
                margin-top: 12px; }
  .slot { width: 118px; min-height: 74px; border-radius: 10px; padding: 6px; text-align: center; }
  .slot.tit { background: #dcfce7; border: 2px solid #16a34a; }
  .slot.res { background: #fee2e2; border: 2px dashed #dc2626; }
  .slot .nome { font-weight: 700; font-size: 13px; }
  .slot .info { font-size: 11px; color: #334155; }
  .bench h3 { margin-top: 6px; }
  .bench-grid { display: flex; gap: 8px; flex-wrap: wrap; }
  .bench-card { background: #fff; border: 1px solid #e2e8f0; border-radius: 10px; padding: 8px;
                width: 160px; font-size: 12px; }
</style>
</head>
<body>
<header>
  <h1>Formazioni con titolari e riserve</h1>
  <select id="modulo"></select>
  <select id="alt"></select>
</header>
<div id="summary" class="summary"></div>
<div id="field" class="field"></div>
<div id="bench" class="bench"></div>
<script>
const DATA = __DATA__;
const moduleSel = document.getElementById('modulo');
const altSel = document.getElementById('alt');
DATA.modules.forEach((m, i) => {
  const o = document.createElement('option');
  o.value = i;
  o.textContent = m.name;
  moduleSel.appendChild(o);
});
function slotEl(s, filled) {
  const d = document.createElement('div');
  d.className = 'slot ' + (filled ? 'tit' : 'res');
  if (filled) {
    const facili = s.facili.length ? s.facili.join(', ') : '—';
    d.innerHTML = '<div class="nome">' + s.nome + '</div>'
      + '<div class="info">' + s.squadra + ' &middot; ' + s.codici
      + '<br>QI ' + s.qi + ' &middot; ' + s.punti + ' pt'
      + '<br>facili: ' + facili + '</div>';
  } else {
    d.innerHTML = '<div class="nome">&mdash;</div><div class="info">' + (s.ruolo || '') + '</div>';
  }
  return d;
}
function render() {
  const m = DATA.modules[moduleSel.value];
  altSel.innerHTML = '';
  m.alternatives.forEach((a, i) => {
    const o = document.createElement('option');
    o.value = i;
    o.textContent = 'Alternativa ' + (i + 1);
    altSel.appendChild(o);
  });
  show();
}
function show() {
  const m = DATA.modules[moduleSel.value];
  const a = m.alternatives[altSel.value];
  const summary = document.getElementById('summary');
  summary.innerHTML = 'Costo <b>' + a.cost + '</b> &middot; coperto <b>'
    + a.covered + '/' + a.total + '</b> &middot; punti <b>' + a.points + '</b>'
    + (a.uncovered.length
      ? ' &middot; <span class="uncovered">giornate scoperte: ' + a.uncovered.join(', ') + '</span>'
      : '');
  const field = document.getElementById('field');
  field.innerHTML = '';
  m.lines.forEach((label, li) => {
    const lab = document.createElement('div');
    lab.className = 'line-label';
    lab.textContent = label;
    const row = document.createElement('div');
    row.className = 'line';
    const slots = a.xi.filter(x => x.linea === label);
    slots.forEach(s => row.appendChild(slotEl(s, true)));
    const count = m.counts[li];
    for (let i = slots.length; i < count; i++) {
      row.appendChild(slotEl({ ruolo: '', nome: '—' }, false));
    }
    field.appendChild(lab);
    field.appendChild(row);
  });
  const bench = document.getElementById('bench');
  bench.innerHTML = '';
  if (a.bench.length) {
    const h = document.createElement('h3');
    h.textContent = 'Riserve (' + a.bench.length + ')';
    const grid = document.createElement('div');
    grid.className = 'bench-grid';
    a.bench.forEach(b => {
      const c = document.createElement('div');
      c.className = 'bench-card';
      const facili = b.facili.length ? b.facili.join(', ') : '—';
      c.innerHTML = '<b>' + b.nome + '</b> ' + b.squadra
        + '<br>' + b.codici + ' &middot; QI ' + b.qi + ' &middot; ' + b.punti + ' pt'
        + '<br><small>facili: ' + facili + '</small>';
      grid.appendChild(c);
    });
    bench.appendChild(h);
    bench.appendChild(grid);
  }
}
moduleSel.onchange = render;
altSel.onchange = show;
render();
</script>
</body>
</html>
"""


def _player_slot(player, ctx: GuideContext) -> dict:
    """Slot giocatore: nome, squadra, codici, qi, punti, giornate facili."""
    return {
        "nome": player.name,
        "squadra": player.team_name,
        "codici": _role_code(player),
        "qi": player.quote.qi,
        "punti": round(project(player, ctx.league).total_points, 1),
        "facili": list(_easy_weeks(player, ctx)),
    }


def _build_data(ctx: GuideContext, remaining: list, budget: int, alternatives: int) -> dict:
    """Struttura JSON: per modulo → linee, conteggi, alternative (XI + riserve)."""
    weeks = remaining_weeks(ctx.league, ctx.calendars)
    modules: list[dict] = []
    for module in MODULES:
        alternative_list: list[dict] = []
        for squad in k_best_rosters(
            module,
            remaining,
            ctx.league,
            ctx.calendars,
            ctx.strengths,
            budget=budget,
            k=alternatives,
        ):
            xi_lines = formation_positions(module, squad.selected)
            xi = [
                {
                    "linea": GROUP_LABELS[line.group],
                    "ruolo": slot.role.value.upper(),
                    **_player_slot(slot.player, ctx),
                }
                for line in xi_lines
                for slot in line.positions
                if slot.player is not None
            ]
            xi_players = [
                slot.player for line in xi_lines for slot in line.positions if slot.player
            ]
            bench = [player for player in squad.selected if player not in xi_players]
            alternative_list.append(
                {
                    "cost": squad.total_cost,
                    "covered": len(squad.covered_weeks),
                    "total": len(weeks),
                    "points": round(squad.total_points, 1),
                    "uncovered": [w for w in weeks if w not in squad.covered_weeks],
                    "xi": xi,
                    "bench": [_player_slot(player, ctx) for player in bench],
                }
            )
        modules.append(
            {
                "name": module,
                "lines": [GROUP_LABELS[group] for group in _LINE_ORDER],
                "counts": [len(MODULE_POSITIONS[module][i]) for i in range(4)],
                "alternatives": alternative_list,
            }
        )
    return {"modules": modules}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Genera output/visualizzatore.html (formazioni titolari+riserve)"
    )
    parser.add_argument(
        "--budget",
        type=int,
        default=None,
        help="Budget da usare (default: residuo dello stato asta)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("output"),
        help="Directory di destinazione (default: output)",
    )
    parser.add_argument(
        "--alternative",
        type=int,
        default=10,
        help="Rose alternative per modulo (default: 10)",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    args.output.mkdir(parents=True, exist_ok=True)

    _, ctx, remaining, budget = _load_data(args.budget)
    logger.info(
        "Pool: %d giocatori rimasti — budget: %d crediti — alternative: %d",
        len(remaining),
        budget,
        args.alternative,
    )
    data = _build_data(ctx, remaining, budget, args.alternative)
    html = _HTML_TEMPLATE.replace("__DATA__", json.dumps(data, ensure_ascii=False))
    path = args.output / "visualizzatore.html"
    path.write_text(html, encoding="utf-8")
    logger.info("Generato: %s", path)


if __name__ == "__main__":
    main()
