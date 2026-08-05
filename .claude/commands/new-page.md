---
description: Scaffold a Streamlit page + sidebar entry
argument-hint: <Name>
---

# /new-page <Name>

Scaffold a new Streamlit page: a module under `pages/`, its title via `st.set_page_config`, and
the sidebar entry in `main.py`. Follows the layer rules in `docs/agents/RULES.md`
(`ui → logic ← data`).

## Usage

```
/new-page Analisi
```

## Output

1. `pages/<Name>.py` — Streamlit page module: `st.set_page_config(page_title="<Name>")`, section
   headers, and calls to `logic`/`data` functions. No network I/O inline: scraping goes through
   the cached `fetch_*` functions.
2. Sidebar entry in `main.py` (`st.sidebar.page_link` or `st.navigation`, matching the existing
   pattern).

## Conventions

- File name: `PascalCase` matching the page title (`pages/Analisi.py`).
- UI text in Italian; never inline raw data URLs or selectors.
- The page reads data only through `fetch_*`/`state.py` functions (cache-first), never with
  `requests`/`bs4` directly.
- Add docstrings and type hints to public functions.
- Follow the task-first workflow: create the task with `/new-task` before executing non-trivial
  work.
