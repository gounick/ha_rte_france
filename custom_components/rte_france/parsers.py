"""Response parsers for the RTE France integration."""

import logging
from datetime import datetime
from typing import Any

import homeassistant.util.dt as dt_util

_LOGGER = logging.getLogger(__name__)


def _parse_iso(value: str) -> datetime:
    """Parse an ISO 8601 timestamp string.

    :param value: ISO 8601 timestamp.
    :type value: str
    :return: Parsed datetime.
    :rtype: datetime
    """
    return datetime.fromisoformat(value)


def _last_value(values: list[dict[str, Any]]) -> float | None:
    """Return the chronologically last numeric value from a list of intervals.

    :param values: List of interval dictionaries containing
        ``start_date`` and ``value``.
    :type values: list[dict[str, Any]]
    :return: Last numeric value, or None if no interval is in the past.
    :rtype: float | None
    """
    now = dt_util.now()
    candidates = [
        float(item["value"])
        for item in sorted(values, key=lambda x: x["start_date"])
        if _parse_iso(item["start_date"]) <= now
    ]
    return candidates[-1] if candidates else None


def market_current_price(data: dict[str, Any]) -> float | None:
    """Return the current spot market price from a RTE response.

    :param data: Parsed ``france_power_exchanges`` response.
    :type data: dict[str, Any]
    :return: Current price in EUR/MWh, or None.
    :rtype: float | None
    """
    if not data:
        return None

    now = dt_util.now()
    for exchange in data.get("france_power_exchanges", []):
        for item in exchange.get("values", []):
            start = _parse_iso(item["start_date"])
            end = _parse_iso(item["end_date"])
            if start <= now < end:
                return round(float(item["price"]), 2)
    return None


def generation_total(data: dict[str, Any]) -> float | None:
    """Return the most recent total actual generation.

    :param data: Parsed ``actual_generations_per_production_type`` response.
    :type data: dict[str, Any]
    :return: Total generation in MW, or None.
    :rtype: float | None
    """
    if not data:
        return None

    all_values: list[dict[str, Any]] = []
    for series in data.get("actual_generations_per_production_type", []):
        all_values.extend(series.get("values", []))

    if not all_values:
        return None

    # Group values by start_date and sum production types for the same interval.
    totals: dict[str, float] = {}
    for item in all_values:
        start = item["start_date"]
        totals[start] = totals.get(start, 0.0) + float(item["value"])

    sorted_totals = sorted(totals.items(), key=lambda x: x[0])
    now = dt_util.now()
    for start, value in reversed(sorted_totals):
        if _parse_iso(start) <= now:
            return round(value, 2)
    return None


def generation_forecast_total(data: dict[str, Any]) -> float | None:
    """Return the most recent total generation forecast.

    :param data: Parsed ``generation_forecasts`` response.
    :type data: dict[str, Any]
    :return: Total forecast generation in MW, or None.
    :rtype: float | None
    """
    if not data:
        return None

    all_values: list[dict[str, Any]] = []
    for series in data.get("generation_forecasts", []):
        all_values.extend(series.get("values", []))

    return _last_value(all_values)


def consumption_last(data: dict[str, Any]) -> float | None:
    """Return the most recent consumption value.

    :param data: Parsed ``short_term`` consumption response.
    :type data: dict[str, Any]
    :return: Consumption in MW, or None.
    :rtype: float | None
    """
    if not data:
        return None

    values = data.get("short_term", [])
    if not values:
        values = data.get("consumption", [])
    return _last_value(values)


def physical_flow_net(data: dict[str, Any]) -> float | None:
    """Return the most recent net physical cross-border flow.

    Positive values mean France is a net importer.

    :param data: Parsed ``physical_flows`` response.
    :type data: dict[str, Any]
    :return: Net flow in MW, or None.
    :rtype: float | None
    """
    if not data:
        return None

    values = data.get("physical_flows", [])
    if not values:
        return None

    # Sum flows by interval; a negative value means export.
    net: dict[str, float] = {}
    for item in values:
        start = item["start_date"]
        net[start] = net.get(start, 0.0) + float(item["value"])

    sorted_net = sorted(net.items(), key=lambda x: x[0])
    now = dt_util.now()
    for start, value in reversed(sorted_net):
        if _parse_iso(start) <= now:
            return round(value, 2)
    return None
