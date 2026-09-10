"""Sensor platform for the RTE France integration."""

import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import RTEDataUpdateCoordinator
from .endpoints import RTESensorDefinition

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

    sensors: list[RTEFranceSensor] = []
    for coordinator in coordinators.values():
        for sensor_definition in coordinator.endpoint.sensors:
            sensors.append(RTEFranceSensor(coordinator, sensor_definition))

    async_add_entities(sensors)


class RTEFranceSensor(CoordinatorEntity, SensorEntity):
    """Sensor exposing a value parsed from an RTE Data API endpoint."""

    _attr_has_entity_name = True
    _attr_device_info = DeviceInfo(
        identifiers={(DOMAIN, "rte_france")},
        name="RTE France",
        manufacturer="RTE",
    )

    def __init__(
        self,
        coordinator: RTEDataUpdateCoordinator,
        sensor_definition: RTESensorDefinition,
    ) -> None:
        """Initialize the sensor.

        :param coordinator: Coordinator providing the endpoint data.
        :type coordinator: RTEDataUpdateCoordinator
        :param sensor_definition: Sensor definition with description and parser.
        :type sensor_definition: RTESensorDefinition
        """
        super().__init__(coordinator)
        self.sensor_definition = sensor_definition
        self.entity_description = sensor_definition.description
        self._attr_unique_id = (
            f"{DOMAIN}_{coordinator.endpoint.key}_{sensor_definition.description.key}"
        )

    @property
    def available(self) -> bool:
        """Return True if the coordinator has data."""
        return super().available and bool(self.coordinator.data)

    @property
    def native_value(self) -> float | str | None:
        """Return the parsed scalar value from the RTE response."""
        return self.sensor_definition.parser(self.coordinator.data)
