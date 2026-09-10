"""Sensor platform for the RTE France integration."""

import logging

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import RTEDataUpdateCoordinator
from .parsers import (
    consumption_last,
    generation_forecast_total,
    generation_total,
    market_current_price,
    physical_flow_net,
)

_LOGGER = logging.getLogger(__name__)


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
    entry_data = hass.data[DOMAIN][entry.entry_id]
    coordinators: dict[str, RTEDataUpdateCoordinator] = entry_data["coordinators"]

    category_sensors = {
        "market": RTEFranceMarketPriceSensor,
        "generation": RTEFranceGenerationSensor,
        "generation_forecast": RTEFranceGenerationForecastSensor,
        "consumption": RTEFranceConsumptionSensor,
        "physical_flows": RTEFrancePhysicalFlowSensor,
    }

    sensors = [
        category_sensors[category](coordinator)
        for category, coordinator in coordinators.items()
        if category in category_sensors
    ]

    async_add_entities(sensors)


class RTEFranceBaseSensor(CoordinatorEntity, SensorEntity):
    """Base sensor for RTE France data."""

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
    """Sensor for the current spot market price."""

    def __init__(self, coordinator: RTEDataUpdateCoordinator) -> None:
        """Initialize the market price sensor."""
        super().__init__(
            coordinator,
            SensorEntityDescription(
                key="market_price",
                name="Market Price",
                native_unit_of_measurement="EUR/MWh",
                state_class=SensorStateClass.MEASUREMENT,
            ),
        )

    @property
    def native_value(self) -> float | None:
        """Return the current market price in EUR/MWh."""
        return market_current_price(self.coordinator.data)


class RTEFranceGenerationSensor(RTEFranceBaseSensor):
    """Sensor for the most recent total generation."""

    def __init__(self, coordinator: RTEDataUpdateCoordinator) -> None:
        """Initialize the generation sensor."""
        super().__init__(
            coordinator,
            SensorEntityDescription(
                key="generation_total",
                name="Generation Total",
                native_unit_of_measurement="MW",
                state_class=SensorStateClass.MEASUREMENT,
            ),
        )

    @property
    def native_value(self) -> float | None:
        """Return the most recent total generation in MW."""
        return generation_total(self.coordinator.data)


class RTEFranceGenerationForecastSensor(RTEFranceBaseSensor):
    """Sensor for the most recent generation forecast."""

    def __init__(self, coordinator: RTEDataUpdateCoordinator) -> None:
        """Initialize the generation forecast sensor."""
        super().__init__(
            coordinator,
            SensorEntityDescription(
                key="generation_forecast_total",
                name="Generation Forecast Total",
                native_unit_of_measurement="MW",
                state_class=SensorStateClass.MEASUREMENT,
            ),
        )

    @property
    def native_value(self) -> float | None:
        """Return the most recent generation forecast in MW."""
        return generation_forecast_total(self.coordinator.data)


class RTEFranceConsumptionSensor(RTEFranceBaseSensor):
    """Sensor for the most recent consumption."""

    def __init__(self, coordinator: RTEDataUpdateCoordinator) -> None:
        """Initialize the consumption sensor."""
        super().__init__(
            coordinator,
            SensorEntityDescription(
                key="consumption",
                name="Consumption",
                native_unit_of_measurement="MW",
                state_class=SensorStateClass.MEASUREMENT,
            ),
        )

    @property
    def native_value(self) -> float | None:
        """Return the most recent consumption in MW."""
        return consumption_last(self.coordinator.data)


class RTEFrancePhysicalFlowSensor(RTEFranceBaseSensor):
    """Sensor for the most recent net physical cross-border flow."""

    def __init__(self, coordinator: RTEDataUpdateCoordinator) -> None:
        """Initialize the physical flow sensor."""
        super().__init__(
            coordinator,
            SensorEntityDescription(
                key="physical_flow_net",
                name="Physical Flow Net",
                native_unit_of_measurement="MW",
                state_class=SensorStateClass.MEASUREMENT,
            ),
        )

    @property
    def native_value(self) -> float | None:
        """Return the most recent net physical flow in MW."""
        return physical_flow_net(self.coordinator.data)
