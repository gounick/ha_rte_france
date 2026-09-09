"""Sensor platform for the RTE France integration."""

import logging
from typing import Any

import homeassistant.util.dt as dt_util
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTR_DATA,
    ATTR_END_TIME,
    ATTR_PRICE_PER_KWH,
    ATTR_PRICE_PER_MWH,
    ATTR_START_TIME,
    DOMAIN,
)
from .coordinator import RTEDataUpdateCoordinator
from .models import PricePoint

_LOGGER = logging.getLogger(__name__)


def _current_price(points: list[PricePoint]) -> float | None:
    """Return the price valid at the current time.

    :param points: Sorted list of price points.
    :type points: list[PricePoint]
    :return: Current price per MWh, or None if no interval matches.
    :rtype: float | None
    """
    now = dt_util.now()
    for point in points:
        if point.start_time <= now < point.end_time:
            return point.price_per_mwh
    return None


def _today_points(points: list[PricePoint]) -> list[PricePoint]:
    """Return price intervals that start today in the local timezone.

    :param points: Sorted list of price points.
    :type points: list[PricePoint]
    :return: Today's price points.
    :rtype: list[PricePoint]
    """
    today = dt_util.now().date()
    return [
        point for point in points if dt_util.as_local(point.start_time).date() == today
    ]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up RTE France sensor entities.

    :param hass: Home Assistant instance.
    :type hass: HomeAssistant
    :param entry: Config entry being set up.
    :type entry: ConfigEntry
    :param async_add_entities: Entity registration callback.
    :type async_add_entities: AddEntitiesCallback
    """
    coordinator: RTEDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            RTEFranceMarketPriceSensor(coordinator),
            RTEFranceAveragePriceSensor(coordinator),
            RTEFranceLowestPriceSensor(coordinator),
            RTEFranceHighestPriceSensor(coordinator),
        ]
    )


class RTEFranceBaseSensor(CoordinatorEntity, SensorEntity):
    """Base sensor for RTE France market data."""

    _attr_has_entity_name = True
    _attr_device_info = DeviceInfo(
        identifiers={(DOMAIN, "rte_france")},
        name="RTE France",
        manufacturer="RTE",
    )

    def __init__(
        self,
        coordinator: RTEDataUpdateCoordinator,
        description: SensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{DOMAIN}_{description.key}"

    @property
    def available(self) -> bool:
        """Return True if the coordinator has data."""
        return super().available and bool(self.coordinator.data)


class RTEFranceMarketPriceSensor(RTEFranceBaseSensor):
    """Sensor for the current market price."""

    entity_description = SensorEntityDescription(
        key="market_price",
        name="Market Price",
        native_unit_of_measurement="EUR/MWh",
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.MONETARY,
    )

    @property
    def native_value(self) -> float | None:
        """Return the current market price in EUR/MWh."""
        if not self.coordinator.data:
            return None
        return _current_price(self.coordinator.data)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return today price data as attributes."""
        if not self.coordinator.data:
            return {}

        today = _today_points(self.coordinator.data)
        return {
            ATTR_DATA: [
                {
                    ATTR_START_TIME: dt_util.as_local(point.start_time).isoformat(),
                    ATTR_END_TIME: dt_util.as_local(point.end_time).isoformat(),
                    ATTR_PRICE_PER_MWH: point.price_per_mwh,
                    ATTR_PRICE_PER_KWH: point.price_per_kwh,
                }
                for point in today
            ]
        }


class RTEFranceAveragePriceSensor(RTEFranceBaseSensor):
    """Sensor for today's average market price."""

    entity_description = SensorEntityDescription(
        key="average_price",
        name="Average Price",
        native_unit_of_measurement="EUR/MWh",
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.MONETARY,
    )

    @property
    def native_value(self) -> float | None:
        """Return today's average market price in EUR/MWh."""
        if not self.coordinator.data:
            return None
        today = _today_points(self.coordinator.data)
        if not today:
            return None
        return round(sum(point.price_per_mwh for point in today) / len(today), 2)


class RTEFranceLowestPriceSensor(RTEFranceBaseSensor):
    """Sensor for today's lowest market price."""

    entity_description = SensorEntityDescription(
        key="lowest_price",
        name="Lowest Price",
        native_unit_of_measurement="EUR/MWh",
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.MONETARY,
    )

    @property
    def native_value(self) -> float | None:
        """Return today's lowest market price in EUR/MWh."""
        if not self.coordinator.data:
            return None
        today = _today_points(self.coordinator.data)
        if not today:
            return None
        return round(min(point.price_per_mwh for point in today), 2)


class RTEFranceHighestPriceSensor(RTEFranceBaseSensor):
    """Sensor for today's highest market price."""

    entity_description = SensorEntityDescription(
        key="highest_price",
        name="Highest Price",
        native_unit_of_measurement="EUR/MWh",
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.MONETARY,
    )

    @property
    def native_value(self) -> float | None:
        """Return today's highest market price in EUR/MWh."""
        if not self.coordinator.data:
            return None
        today = _today_points(self.coordinator.data)
        if not today:
            return None
        return round(max(point.price_per_mwh for point in today), 2)
