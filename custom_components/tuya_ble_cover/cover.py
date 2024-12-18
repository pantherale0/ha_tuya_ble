"""The Tuya BLE integration."""
from __future__ import annotations

from dataclasses import dataclass

import logging

from homeassistant.components.cover import (
    CoverEntityFeature,
    CoverEntity,
    STATE_CLOSED,
    STATE_OPEN,
    ATTR_POSITION
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN
from .devices import TuyaBLEData, TuyaBLEEntity, TuyaBLEProductInfo
from .device_registry import get_mapping_by_device
from .tuya_ble import TuyaBLEDataPointType, TuyaBLEDevice

_LOGGER = logging.getLogger(__name__)

TUYA_COVER_STATE_MAP = {
    0: STATE_OPEN,
    2: STATE_CLOSED
}

class TuyaBLECover(TuyaBLEEntity, CoverEntity):
    """Representation of a Tuya BLE Cover."""

    _attr_is_closed = False
    _attr_current_cover_position = 0

    def __init__(
        self,
        hass: HomeAssistant,
        coordinator: DataUpdateCoordinator,
        device: TuyaBLEDevice,
        product: TuyaBLEProductInfo,
    ) -> None:
        super().__init__(hass, coordinator, device, product)

    @property
    def supported_features(self) -> CoverEntityFeature:
        """Return the supported features of the device."""
        return self._product.datapoints[Platform.COVER].get("supported_features")

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        _LOGGER.debug("Updated data for %s: %s", self._device.name, self._device.datapoints)
        cover_state_dp = self.get_tuya_datapoint("state")
        cover_position_dp = self.get_tuya_datapoint("current_position")
        if cover_state_dp:
            datapoint = self._device.datapoints[cover_state_dp]
            if datapoint:
                if datapoint.value == 0:
                    self._attr_is_opening = True
                if datapoint.value == 1:
                    self._attr_is_opening = False
                    self._attr_is_closing = False
                if datapoint.value == 2:
                    self._attr_is_closing = True

        if cover_position_dp:
            datapoint = self._device.datapoints[cover_position_dp]
            if datapoint:
                self._attr_current_cover_position = 100 - int(datapoint.value) # reverse position
                if self._attr_current_cover_position == 0:
                    self._attr_is_closed = True
                if self._attr_current_cover_position == 100:
                    self._attr_is_closed = False

        self.async_write_ha_state()

    async def async_open_cover(self, **kwargs) -> None:
        """Open a cover."""
        await self.async_set_cover_position(position=100)
        # sometimes the device does not update DP 1 so force the current state
        if self._attr_current_cover_position != 100:
            self._attr_is_opening = True
            self.async_write_ha_state()

    async def async_stop_cover(self, **kwargs: logging.Any) -> None:
        """Stop a cover."""
        if self.get_tuya_datapoint("state"):
            datapoint = self._device.datapoints.get_or_create(
                self.get_tuya_datapoint("state"),
                TuyaBLEDataPointType.DT_VALUE,
                1,
            )
            if datapoint:
                self._hass.create_task(datapoint.set_value(1))

    async def async_close_cover(self, **kwargs) -> None:
        """Set new target temperature."""
        await self.async_set_cover_position(position=0)
        # sometimes the device does not update DP 1 so force the current state
        if self._attr_current_cover_position != 0:
            self._attr_is_closing = True
            self.async_write_ha_state()

    async def async_set_cover_position(self, **kwargs: logging.Any) -> None:
        """Set cover position"""
        position = 100 - kwargs[ATTR_POSITION]
        if self.get_tuya_datapoint("position"):
            datapoint = self._device.datapoints.get_or_create(
                self.get_tuya_datapoint("position"),
                TuyaBLEDataPointType.DT_VALUE,
                position
            )
            if datapoint:
                self._hass.create_task(datapoint.set_value(position))


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Tuya BLE sensors."""
    data: TuyaBLEData = hass.data[DOMAIN][entry.entry_id]
    mappings = get_mapping_by_device(data.device)
    datapoints = mappings.datapoints.get(Platform.COVER)
    entities: list[TuyaBLECover] = []
    if datapoints is None:
        return
    entities.append(
        TuyaBLECover(
            hass,
            data.coordinator,
            data.device,
            data.product,
        )
    )
    async_add_entities(entities)
