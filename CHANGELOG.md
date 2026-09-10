# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Initial release of the RTE France custom integration.
- OAuth2 client-credentials authentication for the RTE Data API.
- Generic `fetch_data` service to query any RTE Data API endpoint.
- Sensors for Market, Production, Generation Forecast, Consumption and Exchanges categories.
- French UI translation (`translations/fr.json`).
- hassfest validation workflow.
- Brand assets (`icon.png` / `logo.png`) for HACS under `custom_components/rte_france/brand/`.
- HACS validation workflow and `hacs.json`.
- MIT `LICENSE` file.
- `FUNDING.yaml` file.
- `integration_type` set to `service` in `manifest.json`.
- GitHub Actions release workflows that update `CHANGELOG.md` and `manifest.json` on release (manual or automatic).
- Security scanning workflows with Gitleaks and Kingfisher.
- Kingfisher pre-commit hook.
- Renovate configuration.

### Changed

- Updated `requires-python` to `>=3.14.2` and CI Python version to 3.14.
- HACS validation workflow now ignores repository topics and brand checks until the repository settings are updated.
- Upgraded `gitleaks-action` to v3 and `actions/checkout` to v6 in the security workflow.
- Improved `README.md` with HACS badge, installation instructions, supported sensors table and service documentation.

### Fixed

- `async_setup_entry` now creates one `RTEDataUpdateCoordinator` per API category, matching the coordinator constructor signature and fixing setup errors.
- `services.py` now uses `SupportsResponse.ONLY` from `homeassistant.core`, fixing an `ImportError` that prevented the config flow from loading.
- `api.py` now uses the correct RTE Data API versions and query parameters (`wholesale_market/v2`, `generation_forecast/v2/forecasts`, `type=REALISED` for consumption, realistic date ranges) and exposes `authenticate()` to validate credentials without fetching data during setup.
- `async_setup_entry` now probes each API category during setup and only creates sensors for the endpoints the RTE application is allowed to access, preventing a single `403 Forbidden` from failing the whole integration.
- The API probe now catches `ConfigEntryNotReady` (raised by `DataUpdateCoordinator.first_refresh`) for each endpoint instead of `UpdateFailed`.
