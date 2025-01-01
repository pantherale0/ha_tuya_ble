"""Contains generic definitions for sensor entities."""

import collections

from homeassistant.const import (
    PERCENTAGE,
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    UnitOfTemperature
)
from homeassistant.components.sensor import (
    SensorEntityDescription,
    SensorStateClass,
    SensorDeviceClass
)
from homeassistant.helpers.entity import EntityCategory

from .const import SENSOR_BATTERY_LEVEL_ENTITY, SENSOR_TEMPERATURE_ENTITY, SENSOR_RSSI_ENTITY
from .devices import TuyaBLEEntity

class TuyaBLESensorEntityDescription(SensorEntityDescription):
    """Describe a Tuya BLE Sensor."""
    value_fn: collections.abc.Callable[[TuyaBLEEntity], str | int] = None
    name_fn: collections.abc.Callable[[TuyaBLEEntity], str] = None
    native_unit_of_measurement: collections.abc.Callable[[TuyaBLEEntity], str] = None
    options: dict = {}
    icons: dict = {}
    coefficient: int = 0

TUYA_SENSOR_CONFIG: dict[str, TuyaBLESensorEntityDescription] = {
    SENSOR_BATTERY_LEVEL_ENTITY: TuyaBLESensorEntityDescription(
        key=SENSOR_BATTERY_LEVEL_ENTITY,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        device_class=SensorDeviceClass.BATTERY
    ),
    SENSOR_TEMPERATURE_ENTITY: TuyaBLESensorEntityDescription(
        key=SENSOR_TEMPERATURE_ENTITY,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.TEMPERATURE
    ),
    SENSOR_RSSI_ENTITY: TuyaBLESensorEntityDescription(
        key=SENSOR_RSSI_ENTITY,
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda data: data._device.rssi
    )
}
