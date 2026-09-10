"""Endpoint descriptors for the RTE France integration.

Each RTE Data API resource is declared once as an ``RTEEndpoint``. The rest of
integration (coordinators, sensors, options flow) consumes that registry,
so adding a new endpoint only requires a new descriptor and parser here.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntityDescription,
    SensorStateClass,
)

from .parsers import (
    _data_available,
    consolidated_consumption_last,
    consumption_last,
    cross_zonal_capacity_last,
    ecowatt_current_signal,
    exchange_schedule_net,
    generation_forecast_total,
    generation_installed_capacity_total,
    generation_total,
    losses_last,
    market_current_price,
    ntc_last,
    physical_flow_net,
    tempo_today_color,
)


def _api_format(dt: datetime) -> str:
    """Return an ISO 8601 datetime string suitable for the RTE API."""
    return dt.isoformat()


def _midnight(offset: timedelta = timedelta()) -> datetime:
    """Return a UTC midnight datetime with an optional offset."""
    today = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    return today + offset


def _day_range(now: datetime, past: int = 1, future: int = 1) -> dict[str, Any]:
    """Return a standard start_date/end_date pair spanning several days."""
    start = (now - timedelta(days=past)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    end = (now + timedelta(days=future)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    return {
        "start_date": _api_format(start),
        "end_date": _api_format(end),
    }


@dataclass(frozen=True)
class RTESensorDefinition:
    """Definition of a sensor exposed by an endpoint.

    :param description: Home Assistant entity description for the sensor.
    :type description: SensorEntityDescription
    :param parser: Callable that extracts the scalar state from the raw API
        response data. The returned value may be numeric or a string for
        categorical sensors.
    :type parser: Callable[[dict[str, Any]], float | str | None]
    """

    description: SensorEntityDescription
    parser: Callable[[dict[str, Any]], float | str | None]


@dataclass(frozen=True)
class RTEEndpoint:
    """Descriptor for a single RTE Data API resource.

    :param key: Unique internal identifier for this endpoint.
    :type key: str
    :param path: RTE Data API path after ``/open_api/``.
    :type path: str
    :param category: Logical group used in the UI and logs (market, production,
        consumption, exchange, etc.).
    :type category: str
    :param update_interval: Polling interval for this endpoint.
    :type update_interval: timedelta
    :param sensors: List of sensors to create from this endpoint's data.
    :type sensors: list[RTESensorDefinition]
    :param build_params: Optional callable that returns query parameters for
        the API request. Receives the current UTC datetime.
    :type build_params: Callable[[datetime], dict[str, Any] | None] | None
    """

    key: str
    path: str
    category: str
    update_interval: timedelta
    sensors: list[RTESensorDefinition]
    build_params: Callable[[datetime], dict[str, Any] | None] | None = None


ENDPOINTS: dict[str, RTEEndpoint] = {
    endpoint.key: endpoint
    for endpoint in [
        # Market
        RTEEndpoint(
            key="market",
            path="wholesale_market/v2/france_power_exchanges",
            category="market",
            update_interval=timedelta(minutes=15),
            build_params=lambda now: _day_range(now, past=1, future=1),
            sensors=[
                RTESensorDefinition(
                    description=SensorEntityDescription(
                        key="market_price",
                        name="Market Price",
                        native_unit_of_measurement="EUR/MWh",
                        state_class=SensorStateClass.MEASUREMENT,
                    ),
                    parser=market_current_price,
                ),
            ],
        ),
        RTEEndpoint(
            key="signal",
            path="signal/v2/signals",
            category="market",
            update_interval=timedelta(minutes=15),
            sensors=[
                RTESensorDefinition(
                    description=SensorEntityDescription(
                        key="signal",
                        name="Signal",
                        state_class=SensorStateClass.MEASUREMENT,
                    ),
                    parser=_data_available,
                ),
            ],
        ),
        RTEEndpoint(
            key="balancing_energy",
            path="balancing_energy/v5/balancing_energy",
            category="market",
            update_interval=timedelta(minutes=15),
            build_params=lambda now: _day_range(now, past=1, future=0),
            sensors=[
                RTESensorDefinition(
                    description=SensorEntityDescription(
                        key="balancing_energy",
                        name="Balancing Energy",
                        native_unit_of_measurement="EUR/MWh",
                        state_class=SensorStateClass.MEASUREMENT,
                    ),
                    parser=_data_available,
                ),
            ],
        ),
        RTEEndpoint(
            key="balancing_capacity",
            path="balancing_capacity/v5/balancing_capacity",
            category="market",
            update_interval=timedelta(minutes=15),
            sensors=[
                RTESensorDefinition(
                    description=SensorEntityDescription(
                        key="balancing_capacity",
                        name="Balancing Capacity",
                        state_class=SensorStateClass.MEASUREMENT,
                    ),
                    parser=_data_available,
                ),
            ],
        ),
        RTEEndpoint(
            key="bre_imbalance_reconstitution",
            path="bre_imbalance_reconstitution/v2/bre_imbalance_reconstitutions",
            category="market",
            update_interval=timedelta(minutes=15),
            build_params=lambda now: _day_range(now, past=1, future=0),
            sensors=[
                RTESensorDefinition(
                    description=SensorEntityDescription(
                        key="bre_imbalance_reconstitution",
                        name="BRE Imbalance Reconstitution",
                        state_class=SensorStateClass.MEASUREMENT,
                    ),
                    parser=_data_available,
                ),
            ],
        ),
        RTEEndpoint(
            key="balancing_imbalances_account",
            path="balancing_imbalances_account/v1/balancing_imbalances_accounts",
            category="market",
            update_interval=timedelta(minutes=15),
            build_params=lambda now: _day_range(now, past=1, future=0),
            sensors=[
                RTESensorDefinition(
                    description=SensorEntityDescription(
                        key="balancing_imbalances_account",
                        name="Balancing Imbalances Account",
                        state_class=SensorStateClass.MEASUREMENT,
                    ),
                    parser=_data_available,
                ),
            ],
        ),
        RTEEndpoint(
            key="bre_referential",
            path="bre_referential/v1/bre_referentials",
            category="market",
            update_interval=timedelta(hours=6),
            sensors=[
                RTESensorDefinition(
                    description=SensorEntityDescription(
                        key="bre_referential",
                        name="BRE Referential",
                        state_class=SensorStateClass.MEASUREMENT,
                    ),
                    parser=_data_available,
                ),
            ],
        ),
        RTEEndpoint(
            key="bre_temporal_reconciliation",
            path="bre_temporal_reconciliation/v1/bre_temporal_reconciliations",
            category="market",
            update_interval=timedelta(minutes=15),
            build_params=lambda now: _day_range(now, past=1, future=0),
            sensors=[
                RTESensorDefinition(
                    description=SensorEntityDescription(
                        key="bre_temporal_reconciliation",
                        name="BRE Temporal Reconciliation",
                        state_class=SensorStateClass.MEASUREMENT,
                    ),
                    parser=_data_available,
                ),
            ],
        ),
        RTEEndpoint(
            key="certified_capacities_registry",
            path="certified_capacities_registry/v1/certified_capacities",
            category="market",
            update_interval=timedelta(hours=6),
            sensors=[
                RTESensorDefinition(
                    description=SensorEntityDescription(
                        key="certified_capacities_registry",
                        name="Certified Capacities Registry",
                        state_class=SensorStateClass.MEASUREMENT,
                    ),
                    parser=_data_available,
                ),
            ],
        ),
        RTEEndpoint(
            key="certified_capacities_registry_v2",
            path="certified_capacities_registry/v2/certified_capacities",
            category="market",
            update_interval=timedelta(hours=6),
            sensors=[
                RTESensorDefinition(
                    description=SensorEntityDescription(
                        key="certified_capacities_registry_v2",
                        name="Certified Capacities Registry V2",
                        state_class=SensorStateClass.MEASUREMENT,
                    ),
                    parser=_data_available,
                ),
            ],
        ),
        RTEEndpoint(
            key="certification_obligation_parameter",
            path="certification_obligation_parameter/v1/certification_obligation_parameters",
            category="market",
            update_interval=timedelta(hours=6),
            sensors=[
                RTESensorDefinition(
                    description=SensorEntityDescription(
                        key="certification_obligation_parameter",
                        name="Certification Obligation Parameter",
                        state_class=SensorStateClass.MEASUREMENT,
                    ),
                    parser=_data_available,
                ),
            ],
        ),
        # Production
        RTEEndpoint(
            key="generation",
            path="actual_generation/v1/actual_generations_per_production_type",
            category="production",
            update_interval=timedelta(minutes=15),
            sensors=[
                RTESensorDefinition(
                    description=SensorEntityDescription(
                        key="generation_total",
                        name="Generation Total",
                        native_unit_of_measurement="MW",
                        state_class=SensorStateClass.MEASUREMENT,
                    ),
                    parser=generation_total,
                ),
            ],
        ),
        RTEEndpoint(
            key="generation_forecast",
            path="generation_forecast/v2/forecasts",
            category="production",
            update_interval=timedelta(minutes=15),
            build_params=lambda now: {
                "start_date": _api_format(_midnight()),
                "end_date": _api_format(_midnight(timedelta(days=1))),
            },
            sensors=[
                RTESensorDefinition(
                    description=SensorEntityDescription(
                        key="generation_forecast_total",
                        name="Generation Forecast Total",
                        native_unit_of_measurement="MW",
                        state_class=SensorStateClass.MEASUREMENT,
                    ),
                    parser=generation_forecast_total,
                ),
            ],
        ),
        RTEEndpoint(
            key="generation_installed_capacities",
            path="generation_installed_capacities/v1/installed_capacities",
            category="production",
            update_interval=timedelta(hours=6),
            sensors=[
                RTESensorDefinition(
                    description=SensorEntityDescription(
                        key="generation_installed_capacity_total",
                        name="Generation Installed Capacity Total",
                        native_unit_of_measurement="MW",
                        state_class=SensorStateClass.MEASUREMENT,
                    ),
                    parser=generation_installed_capacity_total,
                ),
            ],
        ),
        # Consumption
        RTEEndpoint(
            key="consumption",
            path="consumption/v1/short_term",
            category="consumption",
            update_interval=timedelta(minutes=15),
            build_params=lambda now: {
                "start_date": _api_format(_midnight(timedelta(days=-1))),
                "end_date": _api_format(_midnight()),
                "type": "REALISED",
            },
            sensors=[
                RTESensorDefinition(
                    description=SensorEntityDescription(
                        key="consumption",
                        name="Consumption",
                        native_unit_of_measurement="MW",
                        state_class=SensorStateClass.MEASUREMENT,
                    ),
                    parser=consumption_last,
                ),
            ],
        ),
        RTEEndpoint(
            key="consolidated_consumption",
            path="consolidated_consumption/v1/consolidated_consumptions",
            category="consumption",
            update_interval=timedelta(minutes=15),
            build_params=lambda now: _day_range(now, past=1, future=0),
            sensors=[
                RTESensorDefinition(
                    description=SensorEntityDescription(
                        key="consolidated_consumption",
                        name="Consolidated Consumption",
                        native_unit_of_measurement="MW",
                        state_class=SensorStateClass.MEASUREMENT,
                    ),
                    parser=consolidated_consumption_last,
                ),
            ],
        ),
        RTEEndpoint(
            key="ecowatt",
            path="ecowatt/v5/signals",
            category="consumption",
            update_interval=timedelta(minutes=15),
            sensors=[
                RTESensorDefinition(
                    description=SensorEntityDescription(
                        key="ecowatt_signal",
                        name="Ecowatt Signal",
                        device_class=SensorDeviceClass.ENUM,
                        options=["0", "1", "2", "3"],
                    ),
                    parser=ecowatt_current_signal,
                ),
            ],
        ),
        RTEEndpoint(
            key="tempo_like_supply_contract",
            path="tempo_like_supply_contract/v1/tempo_like_calendars",
            category="consumption",
            update_interval=timedelta(hours=1),
            sensors=[
                RTESensorDefinition(
                    description=SensorEntityDescription(
                        key="tempo_color",
                        name="Tempo Color",
                        device_class=SensorDeviceClass.ENUM,
                        options=["BLUE", "WHITE", "RED"],
                    ),
                    parser=tempo_today_color,
                ),
            ],
        ),
        # Exchanges
        RTEEndpoint(
            key="physical_flows",
            path="physical_flow/v1/physical_flows",
            category="exchange",
            update_interval=timedelta(minutes=15),
            sensors=[
                RTESensorDefinition(
                    description=SensorEntityDescription(
                        key="physical_flow_net",
                        name="Physical Flow Net",
                        native_unit_of_measurement="MW",
                        state_class=SensorStateClass.MEASUREMENT,
                    ),
                    parser=physical_flow_net,
                ),
            ],
        ),
        RTEEndpoint(
            key="ntc",
            path="ntc/v2/ntc",
            category="exchange",
            update_interval=timedelta(minutes=15),
            sensors=[
                RTESensorDefinition(
                    description=SensorEntityDescription(
                        key="ntc",
                        name="NTC",
                        native_unit_of_measurement="MW",
                        state_class=SensorStateClass.MEASUREMENT,
                    ),
                    parser=ntc_last,
                ),
            ],
        ),
        RTEEndpoint(
            key="cross_zonal_capacity",
            path="cross_zonal_capacity/v2/cross_zonal_capacities",
            category="exchange",
            update_interval=timedelta(minutes=15),
            sensors=[
                RTESensorDefinition(
                    description=SensorEntityDescription(
                        key="cross_zonal_capacity",
                        name="Cross Zonal Capacity",
                        native_unit_of_measurement="MW",
                        state_class=SensorStateClass.MEASUREMENT,
                    ),
                    parser=cross_zonal_capacity_last,
                ),
            ],
        ),
        RTEEndpoint(
            key="exchange_schedule",
            path="exchange_schedule/v2/exchange_schedules",
            category="exchange",
            update_interval=timedelta(minutes=15),
            sensors=[
                RTESensorDefinition(
                    description=SensorEntityDescription(
                        key="exchange_schedule_net",
                        name="Exchange Schedule Net",
                        native_unit_of_measurement="MW",
                        state_class=SensorStateClass.MEASUREMENT,
                    ),
                    parser=exchange_schedule_net,
                ),
            ],
        ),
        RTEEndpoint(
            key="losses",
            path="losses_public_transmission_system/v1/losses",
            category="exchange",
            update_interval=timedelta(minutes=15),
            sensors=[
                RTESensorDefinition(
                    description=SensorEntityDescription(
                        key="losses",
                        name="Losses",
                        native_unit_of_measurement="MW",
                        state_class=SensorStateClass.MEASUREMENT,
                    ),
                    parser=losses_last,
                ),
            ],
        ),
    ]
}


def get_endpoint(key: str) -> RTEEndpoint | None:
    """Return the endpoint descriptor for the given key, or None."""
    return ENDPOINTS.get(key)


def list_endpoints() -> list[RTEEndpoint]:
    """Return all registered endpoint descriptors."""
    return list(ENDPOINTS.values())


def list_endpoint_keys() -> list[str]:
    """Return all registered endpoint keys."""
    return list(ENDPOINTS.keys())
