"""Genera le guide asta (moduli e ruoli) in xlsx, csv e md dentro `output/`.

Uso: python tools/generate_guide.py [--budget N] [--output DIR]

Legge la cache `data/` e lo stato asta (`data/asta.json`): il pool è
costituito dai giocatori rimasti, il budget è quello residuo (o `--budget`).
Nessuna rete.
"""

from __future__ import annotations

import argparse
import csv
import logging
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from openpyxl import Workbook
from openpyxl.utils import get_column_letter

from entities import GROUP_LABELS, ROLE_GROUP, Role, RoleGroup, attach_stats
from fetch_fixtures import read_league_context, read_remaining_calendar
from fetch_quotazioni import read_players
from fetch_stats import read_season_stats
from guide import greedy_cover, optimize_roster_coverage, top_candidates
from projection import LeagueContext, project
from state import load_state, spent_budget, taken_urls
from utility import (
    MODULE_POSITIONS,
    MODULES,
    TeamCalendar,
    formation_positions,
    opponent_outlook,
    player_roles,
    remaining_weeks,
    team_strengths_from_players,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class GuideContext:
    """Contesto condiviso per proiezioni e copertura."""

    league: LeagueContext
    calendars: Mapping[str, TeamCalendar]
    strengths: Mapping[str, float]


def _role_code(player) -> str:
    """Codici ruolo compatti (es. "E/W")."""
    return "/".join(role.value.upper() for role in player_roles(player))


def _easy_weeks(player, ctx: GuideContext) -> tuple[int, ...]:
    """Le giornate rimanenti con partita facile per il giocatore."""
    return tuple(
        opp.matchweek
        for opp in opponent_outlook(player, ctx.league, ctx.calendars, ctx.strengths)
        if opp.easy is True
    )


def _fmt_weeks(weeks: Sequence[int]) -> str:
    return ", ".join(str(week) for week in weeks) if weeks else "—"


def _load_data(budget: int | None) -> tuple[list, GuideContext, list, int]:
    """Cache + stato: (players, context, remaining, budget)."""
    players = attach_stats(read_players(), read_season_stats())
    ctx = GuideContext(
        league=read_league_context(),
        calendars=read_remaining_calendar(),
        strengths=team_strengths_from_players(players),
    )
    state = load_state()
    taken = taken_urls(state)
    remaining = [player for player in players if player.url not in taken]
    remaining_budget = state.budget - spent_budget(state) if budget is None else budget
    return players, ctx, remaining, remaining_budget


def _module_guide(
    module: str,
    remaining: Sequence,
    ctx: GuideContext,
    budget: int,
) -> dict:
    """Rosa per copertura + XI dal template del modulo."""
    squad = optimize_roster_coverage(
        remaining, ctx.league, ctx.calendars, ctx.strengths, budget=budget
    )
    weeks = remaining_weeks(ctx.league, ctx.calendars)
    if squad.status != "Optimal":
        return {
            "module": module,
            "status": squad.status,
            "xi": (),
            "bench": (),
            "cost": 0,
            "points": 0.0,
            "covered": (),
            "uncovered": weeks,
            "weeks": weeks,
        }
    xi_lines = formation_positions(module, squad.selected)
    xi = [slot.player for line in xi_lines for slot in line.positions if slot.player]
    bench = [player for player in squad.selected if player not in xi]
    return {
        "module": module,
        "status": squad.status,
        "xi": xi,
        "bench": bench,
        "cost": squad.total_cost,
        "points": squad.total_points,
        "covered": squad.covered_weeks,
        "uncovered": tuple(week for week in weeks if week not in squad.covered_weeks),
        "weeks": weeks,
    }


def _role_guide(
    module: str,
    remaining: Sequence,
    ctx: GuideContext,
) -> list[dict]:
    """Per gruppo del modulo: candidati per posizione + greedy."""
    template = MODULE_POSITIONS[module]
    groups: list[dict] = []
    for group, role_names in zip(
        (RoleGroup.P, RoleGroup.D, RoleGroup.C, RoleGroup.A), template, strict=True
    ):
        group_players = [player for player in remaining if ROLE_GROUP[player.role] is group]
        positions = [
            {
                "role": Role(role_name),
                "candidates": top_candidates(
                    [p for p in group_players if Role(role_name) in player_roles(p)],
                    ctx.league,
                    ctx.calendars,
                    ctx.strengths,
                ),
            }
            for role_name in role_names
        ]
        greedy = greedy_cover(
            group_players, ctx.league, ctx.calendars, ctx.strengths, limit=len(role_names)
        )
        groups.append({"group": group, "positions": positions, "greedy": greedy})
    return groups


def _player_row(player, ctx: GuideContext) -> list[object]:
    """Riga tabellare comune: nome, squadra, qi, punti, giornate facili."""
    return [
        player.name,
        player.team_name,
        player.quote.qi,
        round(project(player, ctx.league).total_points, 1),
        _fmt_weeks(_easy_weeks(player, ctx)),
    ]


def _write_xlsx_moduli(guides: list[dict], ctx: GuideContext, path: Path) -> None:
    wb = Workbook()
    ws = wb.active
    ws.title = "Confronto"
    ws.append(["Modulo", "Stato", "Costo", "Giornate coperte", "Su", "Punti", "Scoperte"])
    for guide in guides:
        ws.append(
            [
                guide["module"],
                guide["status"],
                guide["cost"],
                len(guide["covered"]),
                len(guide["weeks"]),
                round(guide["points"], 1),
                _fmt_weeks(guide["uncovered"]),
            ]
        )
    for guide in guides:
        ws = wb.create_sheet(guide["module"])
        ws.append(
            [
                f"Modulo {guide['module']} — costo {guide['cost']} — coperto "
                f"{len(guide['covered'])}/{len(guide['weeks'])} — punti "
                f"{guide['points']:.1f}"
            ]
        )
        ws.append(["Linea", "Ruolo", "Nome", "Squadra", "QI", "Punti", "Giornate facili"])
        for line in formation_positions(guide["module"], guide["xi"]):
            for slot in line.positions:
                if slot.player is None:
                    continue
                ws.append(
                    [
                        GROUP_LABELS[line.group],
                        slot.role.value.upper(),
                        *_player_row(slot.player, ctx),
                    ]
                )
        if guide["bench"]:
            ws.append([])
            ws.append(["Panchina", "Ruolo", "Nome", "Squadra", "QI", "Punti", "Giornate facili"])
            for player in guide["bench"]:
                ws.append(["Panchina", _role_code(player), *_player_row(player, ctx)])
        ws.append([])
        ws.append(["Giornate scoperte:", _fmt_weeks(guide["uncovered"])])
    _autofit_workbook(wb)
    wb.save(path)


def _write_csv_moduli(guides: list[dict], ctx: GuideContext, path: Path) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "modulo",
                "tipo",
                "linea",
                "ruolo",
                "nome",
                "squadra",
                "qi",
                "punti",
                "giornate_facili",
            ]
        )
        for guide in guides:
            for line in formation_positions(guide["module"], guide["xi"]):
                for slot in line.positions:
                    if slot.player is None:
                        continue
                    writer.writerow(
                        [
                            guide["module"],
                            "titolare",
                            GROUP_LABELS[line.group],
                            slot.role.value.upper(),
                            *_player_row(slot.player, ctx),
                        ]
                    )
            for player in guide["bench"]:
                writer.writerow(
                    [guide["module"], "panchina", "", _role_code(player), *_player_row(player, ctx)]
                )


def _write_md_moduli(guides: list[dict], ctx: GuideContext, path: Path) -> None:
    lines = ["# Guide moduli — rosa completa per copertura giornate facili", ""]
    lines.append("| Modulo | Stato | Costo | Coperto | Punti | Giornate scoperte |")
    lines.append("|---|---|---|---|---|---|")
    for guide in guides:
        lines.append(
            f"| {guide['module']} | {guide['status']} | {guide['cost']} | "
            f"{len(guide['covered'])}/{len(guide['weeks'])} | {guide['points']:.1f} | "
            f"{_fmt_weeks(guide['uncovered'])} |"
        )
    for guide in guides:
        lines.append("")
        lines.append(f"## Modulo {guide['module']}")
        lines.append(
            f"Costo {guide['cost']} — coperto {len(guide['covered'])}/"
            f"{len(guide['weeks'])} — punti {guide['points']:.1f}"
        )
        lines.append("")
        lines.append("| Linea | Ruolo | Nome | Squadra | QI | Punti | Giornate facili |")
        lines.append("|---|---|---|---|---|---|---|")
        for line in formation_positions(guide["module"], guide["xi"]):
            for slot in line.positions:
                if slot.player is None:
                    continue
                lines.append(
                    f"| {GROUP_LABELS[line.group]} | {slot.role.value.upper()} | "
                    + " | ".join(str(value) for value in _player_row(slot.player, ctx))
                    + " |"
                )
        if guide["bench"]:
            lines.append("")
            lines.append("### Panchina")
            lines.append("| Ruolo | Nome | Squadra | QI | Punti | Giornate facili |")
            lines.append("|---|---|---|---|---|---|")
            for player in guide["bench"]:
                lines.append(
                    f"| {_role_code(player)} | "
                    + " | ".join(str(value) for value in _player_row(player, ctx))
                    + " |"
                )
        lines.append("")
        lines.append(f"Giornate scoperte: {_fmt_weeks(guide['uncovered'])}")
    path.write_text("\n".join(lines), encoding="utf-8")


def _write_xlsx_ruoli(
    role_guides: list[list[dict]],
    modules: list[str],
    weeks: tuple[int, ...],
    ctx: GuideContext,
    path: Path,
) -> None:
    wb = Workbook()
    ws = wb.active
    ws.title = "Confronto"
    ws.append(["Modulo", "Gruppo", "Ruoli", "Scelti (greedy)", "Giornate coperte", "Costo"])
    for module, groups in zip(modules, role_guides, strict=True):
        for group in groups:
            greedy = group["greedy"]
            ws.append(
                [
                    module,
                    GROUP_LABELS[group["group"]],
                    "/".join(pos["role"].value.upper() for pos in group["positions"]),
                    len(greedy),
                    len(greedy[-1].covered_weeks) if greedy else 0,
                    greedy[-1].cost if greedy else 0,
                ]
            )
    for module, groups in zip(modules, role_guides, strict=True):
        ws = wb.create_sheet(module)
        for group in groups:
            ws.append([])
            ws.append([GROUP_LABELS[group["group"]]])
            ws.append(["Posizione", "Rango", "Nome", "Squadra", "QI", "Punti", "Giornate facili"])
            for pos in group["positions"]:
                for rank, player in enumerate(pos["candidates"], start=1):
                    ws.append([pos["role"].value.upper(), rank, *_player_row(player, ctx)])
            ws.append([])
            ws.append(["Scelti (greedy)", "Aggiunte", "Coperte cumulative", "Costo"])
            for pick in group["greedy"]:
                ws.append(
                    [
                        pick.player.name,
                        len(pick.added_weeks),
                        len(pick.covered_weeks),
                        pick.cost,
                    ]
                )
            ws.append([])
            ws.append(["Matrice copertura (X = partita facile)"] + [str(w) for w in weeks])
            for pick in group["greedy"]:
                easy = set(_easy_weeks(pick.player, ctx))
                ws.append([pick.player.name] + ["X" if w in easy else "" for w in weeks])
    _autofit_workbook(wb)
    wb.save(path)


def _write_csv_ruoli(
    role_guides: list[list[dict]],
    modules: list[str],
    ctx: GuideContext,
    path: Path,
) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "modulo",
                "gruppo",
                "ruolo",
                "tipo",
                "rango",
                "nome",
                "squadra",
                "qi",
                "punti",
                "giornate_facili",
                "coperte",
                "costo",
            ]
        )
        for module, groups in zip(modules, role_guides, strict=True):
            for group in groups:
                for pos in group["positions"]:
                    for rank, player in enumerate(pos["candidates"], start=1):
                        writer.writerow(
                            [
                                module,
                                GROUP_LABELS[group["group"]],
                                pos["role"].value.upper(),
                                "candidato",
                                rank,
                                *_player_row(player, ctx),
                                "",
                                "",
                            ]
                        )
                for pick in group["greedy"]:
                    writer.writerow(
                        [
                            module,
                            GROUP_LABELS[group["group"]],
                            _role_code(pick.player),
                            "scelto",
                            "",
                            *_player_row(pick.player, ctx),
                            len(pick.covered_weeks),
                            pick.cost,
                        ]
                    )


def _write_md_ruoli(
    role_guides: list[list[dict]],
    modules: list[str],
    weeks: tuple[int, ...],
    ctx: GuideContext,
    path: Path,
) -> None:
    lines = ["# Guide ruoli — combinazioni per ruolo (moduli Mantra)", ""]
    for module, groups in zip(modules, role_guides, strict=True):
        lines.append(f"## Modulo {module}")
        for group in groups:
            lines.append("")
            lines.append(f"### {GROUP_LABELS[group['group']]}")
            lines.append("| Posizione | Rango | Nome | Squadra | QI | Punti | Giornate facili |")
            lines.append("|---|---|---|---|---|---|---|")
            for pos in group["positions"]:
                for rank, player in enumerate(pos["candidates"], start=1):
                    lines.append(
                        f"| {pos['role'].value.upper()} | {rank} | "
                        + " | ".join(str(value) for value in _player_row(player, ctx))
                        + " |"
                    )
            lines.append("")
            lines.append("**Scelti (greedy):**")
            for pick in group["greedy"]:
                lines.append(
                    f"- {pick.player.name}: +{len(pick.added_weeks)} giornate, "
                    f"{len(pick.covered_weeks)} coperte cumulative, {pick.cost} crediti"
                )
            lines.append("")
            lines.append("Matrice copertura (X = partita facile):")
            lines.append("| Giocatore | " + " | ".join(str(w) for w in weeks) + " |")
            lines.append("|" + "---|" * (len(weeks) + 1))
            for pick in group["greedy"]:
                easy = set(_easy_weeks(pick.player, ctx))
                lines.append(
                    "| "
                    + pick.player.name
                    + " | "
                    + " | ".join("X" if w in easy else "" for w in weeks)
                    + " |"
                )
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def _autofit_workbook(wb: Workbook, max_width: int = 40) -> None:
    for ws in wb.worksheets:
        for column in ws.columns:
            letter = get_column_letter(column[0].column)
            width = max(len(str(cell.value or "")) for cell in column)
            ws.column_dimensions[letter].width = min(width + 2, max_width)


def main() -> None:
    parser = argparse.ArgumentParser(description="Genera le guide asta in output/")
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
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    args.output.mkdir(parents=True, exist_ok=True)

    _, ctx, remaining, budget = _load_data(args.budget)
    logger.info("Pool: %d giocatori rimasti — budget: %d crediti", len(remaining), budget)
    weeks = remaining_weeks(ctx.league, ctx.calendars)

    modules = list(MODULES)
    guides = [_module_guide(module, remaining, ctx, budget) for module in modules]
    role_guides = [_role_guide(module, remaining, ctx) for module in modules]

    _write_xlsx_moduli(guides, ctx, args.output / "guide_moduli.xlsx")
    _write_csv_moduli(guides, ctx, args.output / "guide_moduli.csv")
    _write_md_moduli(guides, ctx, args.output / "guide_moduli.md")
    _write_xlsx_ruoli(role_guides, modules, weeks, ctx, args.output / "guide_ruoli.xlsx")
    _write_csv_ruoli(role_guides, modules, ctx, args.output / "guide_ruoli.csv")
    _write_md_ruoli(role_guides, modules, weeks, ctx, args.output / "guide_ruoli.md")
    for name in (
        "guide_moduli.xlsx",
        "guide_moduli.csv",
        "guide_moduli.md",
        "guide_ruoli.xlsx",
        "guide_ruoli.csv",
        "guide_ruoli.md",
    ):
        logger.info("Generato: %s", args.output / name)


if __name__ == "__main__":
    main()
