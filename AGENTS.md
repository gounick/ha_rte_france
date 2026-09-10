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
4. If you need to add or change an API endpoint, read the endpoint and parser sections below first.

---

## Code Style

- Keep functions short and focused (ideally under 20–30 lines).
- Use explicit, descriptive names.
- No dead code, no commented-out blocks, no trailing whitespace.
- Write Sphinx-format docstrings (`:param name:`, `:type name:`, `:return:`, `:rtype:`).
- Never log secrets or credentials.
- Always use Python 3 exception syntax: `except (ValueError, TypeError):`, not `except ValueError, TypeError:`.

---

## Project Architecture

```
custom_components/rte_france/
├── __init__.py       # HA lifecycle (setup/unload), service registration
├── manifest.json     # Integration metadata
├── const.py          # Constants and config keys
├── config_flow.py    # UI configuration flow
├── options_flow.py   # Options flow for enabling/disabling endpoints
├── api.py            # RTE Data REST + OAuth2 client
├── endpoints.py      # Endpoint registry: paths, params, sensors, parsers
├── parsers.py        # Response parsing helpers per API category
├── coordinator.py    # Generic DataUpdateCoordinator driven by endpoints
├── sensor.py         # Sensor platform generated from endpoint descriptors
├── services.py       # HA service handlers
├── services.yaml     # Service definitions
└── translations/     # UI translations

scripts/
└── probe_rte.py      # Debug script to inspect live API responses
```

- `RTEDataAPI` owns all HTTP calls and OAuth2 token management.
- `endpoints.py` declares every RTE Data API resource once. Each endpoint knows
  its path, default query parameters, refresh interval, and sensor definitions.
- `parsers.py` extracts usable scalar values from the heterogeneous RTE responses.
- `RTEDataUpdateCoordinator` refreshes one configured endpoint.
- `sensor.py` creates sensors from coordinator data and must not call the API directly.
- `services.py` exposes the `fetch_data` service for on-demand API queries.
- `scripts/probe_rte.py` can be used with live credentials to inspect endpoint
  responses and design or verify parsers.

---

## Adding or Changing an Endpoint

1. Inspect the live response with the debug script:
   ```bash
   RTE_CLIENT_ID=<id> RTE_CLIENT_SECRET=<secret> uv run python scripts/probe_rte.py
   ```
2. If the response contains a scalar value you want to expose, add a parser in
   `parsers.py` that returns `float | str | None`.
3. Register the endpoint in `endpoints.py` by adding an `RTEEndpoint` entry.
   Link it to the parser through one or more `RTESensorDefinition` entries.
4. Prefer reusing existing parser helpers (`_last_numeric_value`,
   `_sum_nested_values`, `_sum_last_numeric_values`) before writing a new one.
5. Update `README.md` (supported endpoints table) and `CHANGELOG.md`.
6. Run the checks from the Testing & Quality section.

### When an endpoint is not subscribed

If the RTE application is not subscribed to an endpoint, the API returns `403`.
Do not remove the endpoint declaration. Instead:
- keep the endpoint in `endpoints.py`;
- use `_data_available` as a safe placeholder parser if the response structure is
  unknown;
- document the limitation in `README.md` under **Known limitations**.

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
□ If I added or changed an endpoint, did I update endpoints.py and verify the parser?
```

If the answer to any of these questions is **no**, revise before submitting.
