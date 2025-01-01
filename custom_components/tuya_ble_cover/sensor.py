"""The Tuya BLE integration."""
from __future__ import annotations
import logging
from homeassistant.components.sensor import (
    SensorEntity
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.const import Platform
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from .const import (
    DOMAIN,
)
from .devices import TuyaBLEData, TuyaBLEEntity, TuyaBLEProductInfo
from .device_registry import get_mapping_by_device
from .tuya_ble import TuyaBLEDataPointType, TuyaBLEDevice

from .sensor_entity_registry import TuyaBLESensorEntityDescription, TUYA_SENSOR_CONFIG

_LOGGER = logging.getLogger(__name__)
_PLATFORM = Platform.SENSOR

class TuyaBLESensor(TuyaBLEEntity, SensorEntity):
    """Representation of a Tuya BLE sensor."""
    def __init__(
        self,
        hass: HomeAssistant,
        coordinator: DataUpdateCoordinator,
        device: TuyaBLEDevice,
        product: TuyaBLEProductInfo,
        description: TuyaBLESensorEntityDescription,
        base_config: dict
    ) -> None:
        super().__init__(hass, coordinator, device, product)
        self.entity_description = description
        self._base_config = base_config

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if self.entity_description.value_fn is not None:
            self.entity_description.value_fn(self)
        else:
            datapoint = self._device.datapoints[self._base_config["state"]]
            if datapoint:
                if datapoint.type == TuyaBLEDataPointType.DT_ENUM:
                    if self.entity_description.options is not None:
                        if datapoint.value >= 0 and datapoint.value < len(
                            self.entity_description.options
                        ):
                            self._attr_native_value = self.entity_description.options[
                                datapoint.value
                            ]
                        else:
                            self._attr_native_value = datapoint.value
                    if self.entity_description.icons is not None:
                        if datapoint.value >= 0 and datapoint.value < len(
                            self.entity_description.icons
                        ):
                            self._attr_icon = self.entity_description.icons[datapoint.value]
                elif datapoint.type == TuyaBLEDataPointType.DT_VALUE:
                    self._attr_native_value = (
                        datapoint.value / self.entity_description.coefficient
                    )
                else:
                    self._attr_native_value = datapoint.value
        self.async_write_ha_state()

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return super().available


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Tuya BLE sensors."""
    data: TuyaBLEData = hass.data[DOMAIN][entry.entry_id]
    mappings = get_mapping_by_device(data.device)
    entities: list[TuyaBLESensor] = []
    datapoints = mappings.datapoints.get(_PLATFORM)
    if datapoints is None:
        return
    if isinstance(datapoints, dict):
        entities.append(
            TuyaBLESensor(
                hass,
                data.coordinator,
                data.device,
                data.product,
                TUYA_SENSOR_CONFIG.get(datapoints["entity_config_key"]),
                datapoints
            )
        )
    if isinstance(datapoints, list):
        for datapoint in datapoints:
            entities.append(
                TuyaBLESensor(
                    hass,
                    data.coordinator,
                    data.device,
                    data.product,
                    TUYA_SENSOR_CONFIG.get(datapoint["entity_config_key"]),
                    datapoint
                )
            )
    async_add_entities(entities)
