"""Response parsers for the RTE France integration."""

import logging
from datetime import datetime
from typing import Any

import homeassistant.util.dt as dt_util

_LOGGER = logging.getLogger(__name__)


def _parse_iso(value: str | None) -> datetime | None:
    """Parse an ISO 8601 timestamp string.

    :param value: ISO 8601 timestamp, or None.
    :type value: str | None
    :return: Parsed datetime, or None if the input is missing/invalid.
    :rtype: datetime | None
    """
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


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
        for item in sorted(values, key=lambda x: x.get("start_date", ""))
        if item.get("start_date")
        and "value" in item
        and (parsed := _parse_iso(item["start_date"]))
        and parsed <= now
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
            if "price" not in item:
                continue
            start = _parse_iso(item.get("start_date"))
            end = _parse_iso(item.get("end_date"))
            if start and end and start <= now < end:
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
        if "value" not in item or not item.get("start_date"):
            continue
        start = item["start_date"]
        totals[start] = totals.get(start, 0.0) + float(item["value"])

    sorted_totals = sorted(totals.items(), key=lambda x: x[0])
    now = dt_util.now()
    for start, value in reversed(sorted_totals):
        if (parsed := _parse_iso(start)) and parsed <= now:
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

    borders = data.get("physical_flows", [])
    if not borders:
        return None

    net: dict[str, float] = {}
    now = dt_util.now()
    for border in borders:
        sender = (border.get("sender_country_name") or "").upper()
        receiver = (border.get("receiver_country_name") or "").upper()
        if "FRANCE" in receiver:
            sign = 1.0  # import into France
        elif "FRANCE" in sender:
            sign = -1.0  # export from France
        else:
            continue

        for item in border.get("values", []):
            start = item.get("start_date")
            if not start or "value" not in item:
                continue
            parsed = _parse_iso(start)
            if not parsed or parsed > now:
                continue
            try:
                net[start] = net.get(start, 0.0) + sign * float(item["value"])
            except ValueError, TypeError:
                continue

    if not net:
        return None
    return round(sorted(net.items())[-1][1], 2)


def _last_numeric_value(
    data: dict[str, Any],
    root_key: str,
    value_key: str = "value",
) -> float | None:
    """Return the last numeric value from a flat list of intervals.

    :param data: Parsed API response.
    :type data: dict[str, Any]
    :param root_key: Top-level key containing the list of intervals.
    :type root_key: str
    :param value_key: Key containing the numeric value.
    :type value_key: str
    :return: Last numeric value in the past, or None.
    :rtype: float | None
    """
    if not data:
        return None

    now = dt_util.now()
    candidates: list[tuple[datetime, float]] = []
    for item in data.get(root_key, []):
        start = _parse_iso(item.get("start_date"))
        if not start or start > now or value_key not in item:
            continue
        try:
            candidates.append((start, float(item[value_key])))
        except ValueError, TypeError:
            continue

    if not candidates:
        return None
    return round(sorted(candidates)[-1][1], 2)


def _sum_last_numeric_values(
    data: dict[str, Any],
    root_key: str,
    value_key: str = "value",
) -> float | None:
    """Sum numeric values by interval and return the last completed total.

    :param data: Parsed API response.
    :type data: dict[str, Any]
    :param root_key: Top-level key containing the list of intervals.
    :type root_key: str
    :param value_key: Key containing the numeric value.
    :type value_key: str
    :return: Last summed value in the past, or None.
    :rtype: float | None
    """
    if not data:
        return None

    now = dt_util.now()
    totals: dict[str, float] = {}
    for item in data.get(root_key, []):
        start = item.get("start_date")
        if not start or value_key not in item:
            continue
        parsed = _parse_iso(start)
        if not parsed or parsed > now:
            continue
        try:
            totals[start] = totals.get(start, 0.0) + float(item[value_key])
        except ValueError, TypeError:
            continue

    if not totals:
        return None
    return round(sorted(totals.items())[-1][1], 2)


def ecowatt_current_signal(data: dict[str, Any]) -> str | None:
    """Return the current Ecowatt signal for the current hour.

    Values are 0 (green + zero CO2), 1 (green), 2 (orange) or 3 (red).

    :param data: Parsed ``ecowatt`` signals response.
    :type data: dict[str, Any]
    :return: Current signal value, or None.
    :rtype: str | None
    """
    if not data:
        return None

    now = dt_util.now()
    for signal in data.get("signals", []):
        day_start = _parse_iso(signal.get("jour")) or _parse_iso(
            signal.get("start_date")
        )
        if not day_start or day_start.date() != now.date():
            continue
        for item in signal.get("values", []):
            start = _parse_iso(item.get("start_date"))
            end = _parse_iso(item.get("end_date"))
            if not start or not end or not (start <= now < end):
                continue
            hvalue = item.get("hvalue")
            if hvalue is not None:
                return str(hvalue)
    return None


def tempo_today_color(data: dict[str, Any]) -> str | None:
    """Return today's Tempo-like supply contract colour.

    The API returns either a single calendar object or a list of calendars.

    :param data: Parsed ``tempo_like_calendars`` response.
    :type data: dict[str, Any]
    :return: One of ``BLUE``, ``WHITE`` or ``RED``, or None.
    :rtype: str | None
    """
    if not data:
        return None

    now = dt_util.now()
    calendars = data.get("tempo_like_calendars", [])
    if isinstance(calendars, dict):
        calendars = [calendars]

    for calendar in calendars:
        values = calendar.get("values", [])
        if isinstance(values, dict):
            values = [values]
        for item in values:
            start = _parse_iso(item.get("start_date"))
            end = _parse_iso(item.get("end_date"))
            if start and end and start <= now < end:
                return item.get("value")
    return None


def _sum_nested_values(
    data: dict[str, Any],
    root_key: str,
    value_key: str = "value",
) -> float | None:
    """Sum numeric values nested under each item of the root list.

    Several RTE endpoints (NTC, cross-border flows, etc.) return a list of
    per-border series, each containing its own ``values`` list. This helper
    flattens those nested values and sums them by ``start_date``.

    :param data: Parsed API response.
    :type data: dict[str, Any]
    :param root_key: Top-level key containing the list of per-border items.
    :type root_key: str
    :param value_key: Key containing the numeric value inside each nested item.
    :type value_key: str
    :return: Last summed value in the past, or None.
    :rtype: float | None
    """
    if not data:
        return None

    now = dt_util.now()
    totals: dict[str, float] = {}
    for border in data.get(root_key, []):
        for item in border.get("values", []):
            start = item.get("start_date")
            if not start or value_key not in item:
                continue
            parsed = _parse_iso(start)
            if not parsed or parsed > now:
                continue
            try:
                totals[start] = totals.get(start, 0.0) + float(item[value_key])
            except ValueError, TypeError:
                continue

    if not totals:
        return None
    return round(sorted(totals.items())[-1][1], 2)


def _data_available(data: dict[str, Any]) -> int | None:
    """Return 1 when the API returned non-empty data, None otherwise.

    Used as a safe placeholder for endpoints whose response structure is not
    yet parsed into a meaningful scalar sensor.

    :param data: Parsed API response.
    :type data: dict[str, Any]
    :return: 1 if data is present, else None.
    :rtype: int | None
    """
    return 1 if data else None


def ntc_last(data: dict[str, Any]) -> float | None:
    """Return the most recent total NTC value in MW."""
    return _sum_nested_values(data, "ntc")


def cross_zonal_capacity_last(data: dict[str, Any]) -> float | None:
    """Return the most recent total cross zonal capacity value in MW."""
    return _sum_nested_values(data, "cross_zonal_capacities")


def exchange_schedule_net(data: dict[str, Any]) -> float | None:
    """Return the most recent net exchange schedule value in MW."""
    return _sum_nested_values(data, "exchange_schedules")


def losses_last(data: dict[str, Any]) -> float | None:
    """Return the most recent public transmission system losses in MW."""
    return _sum_nested_values(data, "losses")


def consolidated_consumption_last(data: dict[str, Any]) -> float | None:
    """Return the most recent consolidated consumption value in MW."""
    return _last_numeric_value(data, "consolidated_consumptions")


def generation_installed_capacity_total(data: dict[str, Any]) -> float | None:
    """Return the total installed generation capacity in MW.

    :param data: Parsed ``installed_capacities`` response.
    :type data: dict[str, Any]
    :return: Total installed capacity in MW, or None.
    :rtype: float | None
    """
    if not data:
        return None

    total = 0.0
    for item in data.get("installed_capacities", []):
        value = item.get("value")
        if value is None:
            continue
        try:
            total += float(value)
        except ValueError, TypeError:
            continue
    return round(total, 2) if total else None
