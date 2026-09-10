"""Probe all declared RTE Data API endpoints and print their responses.

Usage:
    RTE_CLIENT_ID=<id> RTE_CLIENT_SECRET=<secret> uv run python scripts/probe_rte.py

The credentials are read from environment variables only; they are never logged
or stored.
"""

import asyncio
import base64
import json
import os
from datetime import UTC, datetime, timedelta

import aiohttp

OAUTH_URL = "https://digital.iservices.rte-france.com/oauth2/token"
BASE_URL = "https://digital.iservices.rte-france.com/open_api"

ENDPOINTS: list[tuple[str, str, dict[str, str] | None]] = [
    # Market
    ("market", "wholesale_market/v2/france_power_exchanges", None),
    ("signal", "signal/v2/signals", None),
    ("balancing_energy", "balancing_energy/v5/balancing_energy", None),
    ("balancing_capacity", "balancing_capacity/v5/balancing_capacity", None),
    (
        "bre_imbalance_reconstitution",
        "bre_imbalance_reconstitution/v2/bre_imbalance_reconstitutions",
        None,
    ),
    (
        "balancing_imbalances_account",
        "balancing_imbalances_account/v1/balancing_imbalances_accounts",
        None,
    ),
    ("bre_referential", "bre_referential/v1/bre_referentials", None),
    (
        "bre_temporal_reconciliation",
        "bre_temporal_reconciliation/v1/bre_temporal_reconciliations",
        None,
    ),
    (
        "certified_capacities_registry",
        "certified_capacities_registry/v1/certified_capacities",
        None,
    ),
    (
        "certified_capacities_registry_v2",
        "certified_capacities_registry/v2/certified_capacities",
        None,
    ),
    (
        "certification_obligation_parameter",
        "certification_obligation_parameter/v1/certification_obligation_parameters",
        None,
    ),
    # Production
    (
        "generation",
        "actual_generation/v1/actual_generations_per_production_type",
        None,
    ),
    ("generation_forecast", "generation_forecast/v2/forecasts", None),
    (
        "generation_installed_capacities",
        "generation_installed_capacities/v1/installed_capacities",
        None,
    ),
    # Consumption
    ("consumption", "consumption/v1/short_term", None),
    (
        "consolidated_consumption",
        "consolidated_consumption/v1/consolidated_consumptions",
        None,
    ),
    ("ecowatt", "ecowatt/v5/signals", None),
    (
        "tempo_like_supply_contract",
        "tempo_like_supply_contract/v1/tempo_like_calendars",
        None,
    ),
    # Exchanges
    ("physical_flows", "physical_flow/v1/physical_flows", None),
    ("ntc", "ntc/v2/ntc", None),
    (
        "cross_zonal_capacity",
        "cross_zonal_capacity/v2/cross_zonal_capacities",
        None,
    ),
    (
        "exchange_schedule",
        "exchange_schedule/v2/exchange_schedules",
        None,
    ),
    (
        "losses",
        "losses_public_transmission_system/v1/losses",
        None,
    ),
]


def _api_format(dt: datetime) -> str:
    return dt.isoformat()


def _default_params() -> dict[str, str]:
    now = datetime.now(UTC)
    start = (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    end = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    return {
        "start_date": _api_format(start),
        "end_date": _api_format(end),
    }


async def _get_token(
    session: aiohttp.ClientSession, client_id: str, client_secret: str
) -> str:
    credentials = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    async with session.post(
        OAUTH_URL,
        headers={"Authorization": f"Basic {credentials}"},
        data={"grant_type": "client_credentials"},
    ) as resp:
        resp.raise_for_status()
        data = await resp.json()
        return str(data["access_token"])


async def _probe(
    session: aiohttp.ClientSession,
    token: str,
    name: str,
    path: str,
    params: dict[str, str] | None,
) -> None:
    url = f"{BASE_URL}/{path}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    }
    query = params if params is not None else _default_params()
    print(f"=== {name}: {path} ===")
    try:
        async with session.get(
            url,
            headers=headers,
            params=query,
            timeout=aiohttp.ClientTimeout(total=30),
        ) as resp:
            print(f"Status: {resp.status}")
            try:
                data = await resp.json()
            except aiohttp.ContentTypeError:
                data = await resp.text()
            print(json.dumps(data, indent=2)[:3000])
    except aiohttp.ClientError as err:
        print(f"Request error: {err}")
    print()


async def main() -> None:
    client_id = os.environ["RTE_CLIENT_ID"]
    client_secret = os.environ["RTE_CLIENT_SECRET"]

    async with aiohttp.ClientSession() as session:
        token = await _get_token(session, client_id, client_secret)
        for name, path, params in ENDPOINTS:
            await _probe(session, token, name, path, params)
            await asyncio.sleep(0.5)


if __name__ == "__main__":
    asyncio.run(main())
