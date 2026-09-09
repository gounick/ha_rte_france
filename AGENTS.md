# AGENTS.md

This file provides guidance to compatible agentic tools when generating or reviewing code in this repository.

**Note:** This file is for AI assistant use only. For human developers, refer to the project's contribution guide.

---

## Important: Always Start Here

1. **Read this file first** — Do not work from memory or assumptions.
2. **Scan the existing codebase** — Identify utilities, helpers and patterns already available.
3. **Follow the principles below** — They are non-negotiable.
4. **Self-check before responding** — Use the checklist at the bottom of this file.

---

## Core Principles

### Use English Everywhere

- Always use English for code, comments, documentation, and user-facing messages.
- No French or other languages, except in the French translation file if one exists.

### DRY — Don't Repeat Yourself

- Never duplicate logic. Reuse or extend existing functions before writing new ones.
- Extract shared logic into helpers when the same pattern appears twice.

### KISS — Keep It Simple, Stupid

- Prefer the simplest readable solution.
- Avoid premature abstraction.

### Documentation & Changelog

- Update `README.md` when adding or changing features visible to users.
- Add an entry to `CHANGELOG.md` at the repository root for every user-facing or architectural change.

---

## Before Writing Any Code

1. Scan existing utilities under `custom_components/rte_france/`.
2. Check for similar patterns in other Home Assistant integrations in this repo.
3. Reuse before creating.

---

## Code Style

- Keep functions short and focused (ideally under 20–30 lines).
- Use explicit, descriptive names.
- No dead code, no commented-out blocks, no trailing whitespace.
- Write Sphinx-format docstrings (`:param name:`, `:type name:`, `:return:`, `:rtype:`).
- Never log secrets or credentials.

---

## Project Architecture

```
custom_components/rte_france/
├── __init__.py       # HA lifecycle (setup/unload), service registration
├── manifest.json     # Integration metadata
├── const.py          # Constants and config keys
├── config_flow.py    # UI configuration flow
├── api.py            # RTE Data REST + OAuth2 client
├── parsers.py        # Response parsing helpers per API category
├── coordinator.py    # Generic DataUpdateCoordinator
├── sensor.py         # Sensor platform
├── services.py       # HA service handlers
├── services.yaml     # Service definitions
└── translations/     # UI translations
```

- `RTEDataAPI` owns all HTTP calls and OAuth2 token management.
- `parsers.py` extracts usable scalar values from the heterogeneous RTE responses.
- `RTEDataUpdateCoordinator` refreshes each configured API category.
- `sensor.py` creates sensors from coordinator data and must not call the API directly.
- `services.py` exposes the `fetch_data` service for on-demand API queries.

---

## Testing & Quality

- Run `python3 -m py_compile <file>` for every changed Python file.
- If `prek` or `pre-commit` is configured, run the full check suite.
- Add or update tests when modifying logic or adding features.

### Development environment with uv

This project uses `uv` to manage the Python environment and dependencies.

```bash
# Sync dev dependencies (lint/test tools).
uv sync --extra test

# Run tests.
uv run pytest tests/ -v

# Run pre-commit hooks.
uvx pre-commit run --all-files

# Compile changed Python files for syntax checks.
uv run python3 -m py_compile <modified_files>
```

---

## Self-Check Before Submitting

```
□ Is there an existing function that already handles this logic?
□ Am I duplicating code that exists elsewhere in the project?
□ Is this the simplest solution that works?
□ Did I remove all unused code and trailing whitespace?
□ Are credentials or secrets never logged or hard-coded?
□ Have I updated README.md and CHANGELOG.md?
```

If the answer to any of these questions is **no**, revise before submitting.
