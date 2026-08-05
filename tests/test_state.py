"""Test dello stato asta (ADR-0004): round-trip, import/export, mutazioni.

Nessun test tocca la rete o il filesystem reale (tmp_path).
"""

import pytest

from entities import Player, Quote, Role, RoleGroup, SeasonStats, TakenPick
from optimize import DEFAULT_BUDGET
from state import (
    STATE_FILE,
    add_taken,
    default_state,
    export_state,
    import_state,
    load_state,
    remove_taken,
    save_state,
    slots_remaining,
    spent_budget,
    taken_urls,
)


def _player(url: str, role: Role) -> Player:
    return Player(
        name=url,
        role=role,
        team_id="1",
        team_code="T",
        team_name="Team",
        quote=Quote(qi=10),
        url=url,
        stats=SeasonStats(),
    )


PLAYERS = [
    _player("u1", Role.PC),
    _player("u2", Role.POR),
    _player("u3", Role.DC),
    _player("u4", Role.E),
]


def test_default_state():
    state = default_state()
    assert state.budget == DEFAULT_BUDGET
    assert state.own_team == "Io"
    assert state.taken == ()


def test_save_load_round_trip(tmp_path):
    state = add_taken(default_state(), TakenPick("u1", "Io", 35))
    path = tmp_path / STATE_FILE.name
    save_state(state, path)
    assert load_state(path) == state


def test_load_missing_file_returns_default(tmp_path):
    assert load_state(tmp_path / "assente.json") == default_state()


def test_export_import_round_trip():
    state = add_taken(default_state(), TakenPick("u1", "Io", 35))
    state = add_taken(state, TakenPick("u2", "Squadra B", None))
    assert import_state(export_state(state)) == state


def test_import_state_malformed_raises():
    with pytest.raises(ValueError):
        import_state(b"not json")
    with pytest.raises(ValueError):
        import_state(b'{"version": 99, "budget": 500, "own_team": "Io", "taken": []}')
    with pytest.raises(ValueError):
        import_state(b'{"version": 1, "budget": 500, "own_team": "Io", "taken": "x"}')
    with pytest.raises(ValueError):
        import_state(b'{"version": 1, "budget": 0, "own_team": "Io", "taken": []}')
    with pytest.raises(ValueError):
        import_state(b'{"version": 1, "budget": 500, "own_team": "Io", "taken": [[1]]}')


def test_add_taken_and_duplicate_raises():
    state = default_state()
    state = add_taken(state, TakenPick("u1", "Io", 35))
    assert state.taken[0].player_url == "u1"
    with pytest.raises(ValueError):
        add_taken(state, TakenPick("u1", "Squadra B", None))


def test_remove_taken():
    state = add_taken(default_state(), TakenPick("u1", "Io", 35))
    state = add_taken(state, TakenPick("u2", "Io", 20))
    state = remove_taken(state, "u1")
    assert [p.player_url for p in state.taken] == ["u2"]
    assert remove_taken(state, "sconosciuto") == state


def test_taken_urls_and_spent_budget():
    state = default_state()
    state = add_taken(state, TakenPick("u1", "Io", 35))
    state = add_taken(state, TakenPick("u2", "Squadra B", None))
    state = add_taken(state, TakenPick("u3", "Io", None))
    assert taken_urls(state) == frozenset({"u1", "u2", "u3"})
    assert spent_budget(state) == 35


def test_slots_remaining():
    state = default_state()
    remaining = slots_remaining(state, PLAYERS)
    assert remaining == {RoleGroup.P: 2, RoleGroup.D: 8, RoleGroup.C: 8, RoleGroup.A: 7}
    state = add_taken(state, TakenPick("u1", "Io", 35))
    state = add_taken(state, TakenPick("u3", "Io", 10))
    remaining = slots_remaining(state, PLAYERS)
    assert remaining[RoleGroup.A] == 6
    assert remaining[RoleGroup.D] == 7
    assert remaining[RoleGroup.P] == 2


def test_slots_remaining_ignores_other_teams_and_unknown():
    state = default_state()
    state = add_taken(state, TakenPick("u2", "Squadra B", None))
    state = add_taken(state, TakenPick("url-sconosciuta", "Io", 5))
    remaining = slots_remaining(state, PLAYERS)
    assert remaining[RoleGroup.P] == 2
