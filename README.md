# RTE France

[![hassfest](https://github.com/gounick/ha_rte_france/actions/workflows/hassfest.yaml/badge.svg?branch=main)](https://github.com/gounick/ha_rte_france/actions/workflows/hassfest.yaml)
[![HACS](https://github.com/gounick/ha_rte_france/actions/workflows/hacs.yml/badge.svg?branch=main)](https://github.com/gounick/ha_rte_france/actions/workflows/hacs.yml)
[![Tests](https://github.com/gounick/ha_rte_france/actions/workflows/tests.yml/badge.svg?branch=main)](https://github.com/gounick/ha_rte_france/actions/workflows/tests.yml)
[![Security](https://github.com/gounick/ha_rte_france/actions/workflows/security.yml/badge.svg?branch=main)](https://github.com/gounick/ha_rte_france/actions/workflows/security.yml)
[![Release checks](https://github.com/gounick/ha_rte_france/actions/workflows/release.yml/badge.svg?branch=main)](https://github.com/gounick/ha_rte_france/actions/workflows/release.yml)
[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
![Version](https://img.shields.io/github/v/release/gounick/ha_rte_france?style=plastic)

Home Assistant custom integration for RTE France public electricity market data.

It connects to the official [RTE Data API](https://data.rte-france.com) and exposes
sensors for several categories: Market, Production, Consumption and Exchanges.

> [!NOTE]
> This integration is not affiliated with RTE. It is an independent project that
> uses the public RTE Data API. RTE is a trademark of RTE Réseau de transport
> d'électricité.

## Requirements

- A free RTE Data API account.
- An RTE application subscribed to the APIs you want to use.
- The generated `Client ID` and `Client Secret` for that application.

## Installation

### HACS (recommended)

1. Ensure that [HACS](https://hacs.xyz) is installed.
2. Add this repository as a custom repository in HACS.
3. Install **RTE France**.

   [![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=gounick&repository=ha_rte_france&category=integration)

4. Add **RTE France** to Home Assistant:

   [![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start?domain=rte_france)

### Manual

1. Copy the `custom_components/rte_france` folder into your Home Assistant
   `custom_components/` directory.
2. Restart Home Assistant.
3. Add **RTE France** to Home Assistant:

   [![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start?domain=rte_france)

## Configuration

During setup, enter your RTE Data API `Client ID` and `Client Secret`, then select
the endpoints you want to enable. Only endpoints subscribed to by your RTE
application will work; the integration skips the others automatically.

You can change the enabled endpoints later from the integration options.

### Obtaining credentials

1. Create an account at [data.rte-france.com](https://data.rte-france.com).
2. Subscribe to the APIs you want to use.
3. Create an application to retrieve your `Client ID` and `Client Secret`.

## Supported endpoints

| Category    | RTE API endpoint                                                                | Exposed sensor                            |
| ----------- | ------------------------------------------------------------------------------- | ----------------------------------------- |
| Market      | `wholesale_market/v2/france_power_exchanges`                                    | Market Price (EUR/MWh)                    |
| Market      | `signal/v2/signals`                                                             | Signal                                    |
| Market      | `balancing_energy/v5/balancing_energy`                                            | Balancing Energy (EUR/MWh)                |
| Market      | `balancing_capacity/v5/balancing_capacity`                                        | Balancing Capacity                        |
| Market      | `bre_imbalance_reconstitution/v2/bre_imbalance_reconstitutions`                 | BRE Imbalance Reconstitution              |
| Market      | `balancing_imbalances_account/v1/balancing_imbalances_accounts`                 | Balancing Imbalances Account              |
| Market      | `bre_referential/v1/bre_referentials`                                             | BRE Referential                           |
| Market      | `bre_temporal_reconciliation/v1/bre_temporal_reconciliations`                   | BRE Temporal Reconciliation             |
| Market      | `certified_capacities_registry/v1/certified_capacities`                         | Certified Capacities Registry             |
| Market      | `certified_capacities_registry/v2/certified_capacities`                         | Certified Capacities Registry V2          |
| Market      | `certification_obligation_parameter/v1/certification_obligation_parameters`     | Certification Obligation Parameter        |
| Production  | `actual_generation/v1/actual_generations_per_production_type`                 | Generation Total (MW)                     |
| Production  | `generation_forecast/v2/forecasts`                                              | Generation Forecast Total (MW)            |
| Production  | `generation_installed_capacities/v1/installed_capacities`                       | Generation Installed Capacity (MW)        |
| Consumption | `consumption/v1/short_term`                                                     | Consumption (MW)                          |
| Consumption | `consolidated_consumption/v1/consolidated_consumptions`                         | Consolidated Consumption (MW)             |
| Consumption | `ecowatt/v5/signals`                                                            | Ecowatt Signal (0-3)                      |
| Consumption | `tempo_like_supply_contract/v1/tempo_like_calendars`                             | Tempo Color (BLUE/WHITE/RED)              |
| Exchanges   | `physical_flow/v1/physical_flows`                                               | Physical Flow Net (MW)                    |
| Exchanges   | `ntc/v2/ntc`                                                                    | NTC (MW)                                  |
| Exchanges   | `cross_zonal_capacity/v2/cross_zonal_capacities`                                | Cross Zonal Capacity (MW)                 |
| Exchanges   | `exchange_schedule/v2/exchange_schedules`                                       | Exchange Schedule Net (MW)                |
| Exchanges   | `losses_public_transmission_system/v1/losses`                                     | Losses (MW)                               |

Endpoints marked as available in the table may still return a `403` error if your
RTE application is not subscribed to them.

## Service reference

### `rte_france.fetch_data`

Query any RTE Data API endpoint on demand and return the raw JSON response.

| Field    | Description                                                                            |
| -------- | -------------------------------------------------------------------------------------- |
| endpoint | RTE endpoint path after `/open_api/`, e.g. `wholesale_market/v2/france_power_exchanges`. |
| params   | Optional query parameters.                                                             |

Use `response_variable` in automations or scripts to access the returned data.

## How to debug an endpoint

The repository includes a standalone debug script at `scripts/probe_rte.py`.
It authenticates against the RTE Data API and prints the status code plus the
first part of the response for every registered endpoint.

### Run the debug script

```bash
RTE_CLIENT_ID=<your_client_id> \
  RTE_CLIENT_SECRET=<your_client_secret> \
  uv run python scripts/probe_rte.py
```

The credentials are read from environment variables only; they are never logged
or stored by the script.

### What to look for

- `200` with data: the endpoint is accessible and the parser can be verified
  against the returned JSON.
- `200` with an empty list or object: the endpoint works but there is no data
  right now; the sensor may show as `unavailable` until data is published.
- `403`: your RTE application is not subscribed to this API.
- `404`: the endpoint path or version may be incorrect.

### Add or fix a parser

1. Run the debug script and locate the endpoint response.
2. Open `custom_components/rte_france/parsers.py`.
3. Add or update the parser for that endpoint so it extracts the scalar value
   you want to expose as a sensor.
4. Run the checks:
   ```bash
   uvx ruff check custom_components/rte_france
   uvx pre-commit run --all-files
   ```

## Known limitations

- **Endpoint subscription is mandatory.** RTE returns `403` for any endpoint
  your application is not subscribed to. The integration skips those
  gracefully, but no sensor will be created.
- **Market parsers are placeholders.** Several Market endpoints (`signal`,
  `balancing_energy`, `balancing_capacity`, BRE endpoints, Certified Capacities,
  etc.) currently use a minimal parser that only reports whether data was
  returned. Real scalar parsers will be added once their JSON structure is
  observed from a subscribed application.
- **Ecowatt rate limit.** The Ecowatt API allows one call every 15 minutes. The
  integration already polls at that interval, but running the debug script in a
  tight loop may temporarily hit the quota.
- **French balancing mechanism prices.** The PRE/PRE+ balancing mechanism
  prices are not part of the public Wholesale Market API and are therefore not
  supported.
- **Credentials safety.** API credentials are stored in the Home Assistant
  config entry and are never logged by the integration.
