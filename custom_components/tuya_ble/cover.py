"""The Tuya BLE integration."""
from __future__ import annotations

from dataclasses import dataclass

import logging
from typing import Callable

from homeassistant.components.cover import (
    CoverEntityDescription,
    CoverEntityFeature,
    CoverEntity,
    STATE_CLOSED,
    STATE_OPEN,
    ATTR_POSITION
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.const import STATE_UNKNOWN
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN
from .devices import TuyaBLEData, TuyaBLEEntity, TuyaBLEProductInfo
from .tuya_ble import TuyaBLEDataPoint, TuyaBLEDataPointType, TuyaBLEDevice

_LOGGER = logging.getLogger(__name__)

TUYA_COVER_STATE_MAP = {
    0: STATE_OPEN,
    2: STATE_CLOSED
}

@dataclass
class TuyaBLECoverMapping:
    description: CoverEntityDescription

    cover_state_dp_id: int = 0
    cover_position_dp_id: int = 0
    cover_opening_mode_dp_id: int = 0
    cover_work_state_dp_id: int = 0
    cover_battery_dp_id: int = 0
    cover_motor_direction_dp_id: int = 0
    cover_set_upper_limit_dp_id: int = 0
    cover_factory_reset_dp_id: int = 0
    cover_position_set_dp: int = 0


@dataclass
class TuyaBLECategoryCoverMapping:
    products: dict[str, list[TuyaBLECoverMapping]] | None = None
    mapping: list[TuyaBLECoverMapping] | None = None


mapping: dict[str, TuyaBLECategoryCoverMapping] = {
    "cl": TuyaBLECategoryCoverMapping(
        products={
            **dict.fromkeys(
                [
                "4pbr8eig",
                ],  # BLE Blind Controller
                [
                # Blind Controller
                # - [X] 1   - State (0=open, 1=stop, 2=close)
                # - [X] 3   - Position (RAW)
                # - [ ] 4   - Opening Mode
                # - [ ] 5   - UNKNOWN?
                # - [ ] 7   - Work State (0=stdby, 1=success, 2=learning)
                # - [ ] 13  - Battery
                # - [ ] 101 - Direction
                # - [ ] 102 - Upper Limit
                # - [ ] 103 - UNKNOWN? DT_BOOL
                # - [ ] 104 - UNKNOWN? DT_BOOL
                # - [ ] 105 - UNKNOWN? DT_VALUE
                # - [ ] 107 - Reset
                TuyaBLECoverMapping(
                    description=CoverEntityDescription(
                        key="ble_blind_controller",
                    ),
                    cover_state_dp_id=1,
                    cover_position_set_dp=2,
                    cover_position_dp_id=3,
                    cover_opening_mode_dp_id=4,
                    cover_work_state_dp_id=7,
                    cover_battery_dp_id=13,
                    cover_motor_direction_dp_id=101,
                    cover_set_upper_limit_dp_id=102,
                    cover_factory_reset_dp_id=107
                    ),
                ],
            ),
        },
    ),
}


def get_mapping_by_device(device: TuyaBLEDevice) -> list[TuyaBLECategoryCoverMapping]:
    category = mapping.get(device.category)
    if category is not None and category.products is not None:
        product_mapping = category.products.get(device.product_id)
        if product_mapping is not None:
            return product_mapping
        if category.mapping is not None:
            return category.mapping
        else:
            return []
    else:
        return []


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
        mapping: TuyaBLECoverMapping,
    ) -> None:
        super().__init__(hass, coordinator, device, product, mapping.description)
        self._mapping = mapping

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        _LOGGER.debug("Updated data for %s: %s", self._device.name, self._device.datapoints)
        if self._mapping.cover_state_dp_id != 0:
            datapoint = self._device.datapoints[self._mapping.cover_state_dp_id]
            if datapoint:
                if datapoint.value == 0:
                    self._attr_is_opening = True
                if datapoint.value == 1:
                    self._attr_is_opening = False
                    self._attr_is_closing = False
                if datapoint.value == 2:
                    self._attr_is_closing = True

        if self._mapping.cover_position_dp_id != 0:
            datapoint = self._device.datapoints[self._mapping.cover_position_dp_id]
            if datapoint:
                self._attr_current_cover_position = 100 - int(datapoint.value) # reverse position
                if self._attr_current_cover_position == 0:
                    self._attr_is_closed = True
                if self._attr_current_cover_position == 100:
                    self._attr_is_closed = False

        self.async_write_ha_state()

    async def async_open_cover(self, **kwargs) -> None:
        """Open a cover."""
        _LOGGER.debug("Call to open cover %s", self._device.name)
        if self._mapping.cover_position_set_dp != 0:
            datapoint = self._device.datapoints.get_or_create(
                self._mapping.cover_position_set_dp,
                TuyaBLEDataPointType.DT_VALUE,
                100,
            )
            if datapoint:
                self._hass.create_task(datapoint.set_value(100))

    async def async_close_cover(self, **kwargs) -> None:
        """Set new target temperature."""
        _LOGGER.debug("Call to close cover %s", self._device.name)
        if self._mapping.cover_position_set_dp != 0:
            datapoint = self._device.datapoints.get_or_create(
                self._mapping.cover_position_set_dp,
                TuyaBLEDataPointType.DT_VALUE,
                0,
            )
            if datapoint:
                self._hass.create_task(datapoint.set_value(0))

    async def async_set_cover_position(self, **kwargs: logging.Any) -> None:
        """Set cover position"""
        position = 100 - kwargs[ATTR_POSITION]
        if self._mapping.cover_position_set_dp != 0:
            datapoint = self._device.datapoints.get_or_create(
                self._mapping.cover_position_set_dp,
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
    entities: list[TuyaBLECover] = []
    for mapping in mappings:
        entities.append(
            TuyaBLECover(
                hass,
                data.coordinator,
                data.device,
                data.product,
                mapping,
            )
        )
    async_add_entities(entities)