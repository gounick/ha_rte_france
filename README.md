# RTE France

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

## Supported data

| Category   | RTE API endpoint                                    | Exposed sensor                         |
| ---------- | --------------------------------------------------- | -------------------------------------- |
| Market     | `wholesale_market/v3/france_power_exchanges`        | Market Price (EUR/MWh)                 |
| Production | `actual_generation/v1/actual_generations_per_production_type` | Generation Total (MW)          |
| Production | `generation_forecast/v1/generation_forecasts`       | Generation Forecast Total (MW)         |
| Consumption| `consumption/v1/short_term`                         | Consumption (MW)                      |
| Exchanges  | `physical_flow/v1/physical_flows`                   | Physical Flow Net (MW)                 |

The integration also exposes a `rte_france.fetch_data` service that can call
any RTE Data API endpoint and return the raw JSON response.

## Requirements

- A free RTE Data API account.
- An RTE application subscribed to the APIs you want to use (Wholesale Market,
  Actual Generation, Generation Forecast, Consumption, Physical Flows).
- The generated `Client ID` and `Client Secret`.

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

During setup, enter your RTE Data API `Client ID` and `Client Secret`.

### Obtaining credentials

1. Create an account at [data.rte-france.com](https://data.rte-france.com).
2. Subscribe to the APIs you want to use.
3. Create an application to retrieve your `Client ID` and `Client Secret`.

## Service

### `rte_france.fetch_data`

Query any RTE Data API endpoint on demand.

| Field    | Description                                                         |
| -------- | ------------------------------------------------------------------- |
| endpoint | RTE endpoint path after `/open_api/`, e.g. `wholesale_market/v3/france_power_exchanges`. |
| params   | Optional query parameters.                                          |

Use `response_variable` in automations or scripts to access the returned data.

## Sensors

The integration creates one device **RTE France** with the following sensors:

- **Market Price** — current spot market price (EUR/MWh).
- **Average / Lowest / Highest Price** — daily statistics (EUR/MWh).
- **Generation Total** — latest actual generation (MW).
- **Generation Forecast Total** — latest generation forecast (MW).
- **Consumption** — latest short-term consumption forecast (MW).
- **Physical Flow Net** — latest net cross-border flow (MW). Positive means
  France is a net importer.

## Notes

- This integration uses the public RTE Data API.
- The French balancing mechanism prices (PRE/PRE+) are **not** part of the
  public Wholesale Market API and are therefore not supported.
- API credentials are stored in the config entry and are never logged.
