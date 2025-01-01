"""The Tuya BLE integration."""
from __future__ import annotations

import logging

from homeassistant.components.cover import (
    CoverEntityFeature,
    CoverEntity,
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
from .enum import TuyaCoverState

_LOGGER = logging.getLogger(__name__)
_PLATFORM = Platform.COVER

class TuyaBLECover(TuyaBLEEntity, CoverEntity):
    """Representation of a Tuya BLE Cover."""

    _attr_is_closed = False
    _attr_is_opening = False
    _attr_is_closing = False
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
        return self._product.datapoints[_PLATFORM].get("supported_features")

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        _LOGGER.debug("Updated data for %s: %s", self._device.name, self._device.datapoints.__dict__())
        cover_state_dp = self.get_tuya_datapoint("state", _PLATFORM)
        cover_position_dp = self.get_tuya_datapoint("current_position", _PLATFORM)
        if cover_state_dp:
            datapoint = self._device.datapoints[cover_state_dp]
            if datapoint:
                self._update_ha_state_for_cover(TuyaCoverState(datapoint.value))

        if cover_position_dp:
            datapoint = self._device.datapoints[cover_position_dp]
            if datapoint:
                self._attr_current_cover_position = 100 - int(datapoint.value) # reverse position
                if self._attr_current_cover_position == 0:
                    self._attr_is_closed = True
                    self._attr_is_closing = False
                if self._attr_current_cover_position == 100:
                    self._attr_is_closed = False
                    self._attr_is_opening = False

        self.async_write_ha_state()

    def _update_ha_state_for_cover(self, state: TuyaCoverState) -> None:
        """Update the state of the cover based on the current request or response from device."""
        self._attr_is_closing = False
        self._attr_is_opening = False
        self._attr_is_closed = False
        if self._attr_current_cover_position == 0:
            self._attr_is_closed = True
        if state == TuyaCoverState.OPEN and self._attr_current_cover_position != 100:
            self._attr_is_opening = True
        if state == TuyaCoverState.CLOSE and self._attr_current_cover_position != 0:
            self._attr_is_closing = True
        self.async_write_ha_state()

    async def _update_cover_state(self, state: TuyaCoverState) -> None:
        """Handler to change state from open, close and stop action."""
        cover_state_dp = self.get_tuya_datapoint("state", _PLATFORM)
        cover_position_dp = self.get_tuya_datapoint("current_position", _PLATFORM)
        if cover_state_dp != 0:
            datapoint = self._device.datapoints.get_or_create(
                cover_state_dp,
                TuyaBLEDataPointType.DT_VALUE,
                state.value
            )
            if datapoint:
                self._hass.create_task(datapoint.set_value(state.value))
                self._update_ha_state_for_cover(state)
                return

        if cover_position_dp != 0:
            new_pos = self._attr_current_cover_position # this will be overriden anyway, but fixes linting
            if state == TuyaCoverState.CLOSE:
                await self.async_set_cover_position(position=0)
                new_pos = 0
            if state == TuyaCoverState.OPEN:
                await self.async_set_cover_position(position=100)
                new_pos = 100
            if state == TuyaCoverState.STOP:
                return
            if self._attr_current_cover_position != new_pos:
                self._update_ha_state_for_cover(state)


    async def async_open_cover(self, **kwargs) -> None:
        """Open a cover."""
        await self._update_cover_state(TuyaCoverState.OPEN)

    async def async_stop_cover(self, **kwargs: logging.Any) -> None:
        """Stop a cover."""
        await self._update_cover_state(TuyaCoverState.STOP)

    async def async_close_cover(self, **kwargs) -> None:
        """Set new target temperature."""
        await self._update_cover_state(TuyaCoverState.CLOSE)

    async def async_set_cover_position(self, **kwargs: logging.Any) -> None:
        """Set cover position"""
        position = 100 - kwargs[ATTR_POSITION]
        if self.get_tuya_datapoint("position", _PLATFORM):
            datapoint = self._device.datapoints.get_or_create(
                self.get_tuya_datapoint("position", _PLATFORM),
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
    datapoints = mappings.datapoints.get(_PLATFORM)
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
