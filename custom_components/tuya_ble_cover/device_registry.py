"""Store device registry for all cover devices."""

from dataclasses import dataclass

from homeassistant.components.cover import (
    CoverEntityFeature
)
from homeassistant.const import Platform
from homeassistant.helpers.entity import (
    EntityDescription
)

from .tuya_ble import TuyaBLEDevice
from .const import (
    DEVICE_DEF_MANUFACTURER,
    SENSOR_BATTERY_LEVEL_ENTITY
)

class TuyaBLEProductInfo:
    """Store a product info."""

    name: str
    manufacturer: str = DEVICE_DEF_MANUFACTURER
    datapoints: dict[Platform, dict[str, int] | list[dict[str, int]]] = {}
    entity_description: EntityDescription

    def __init__(self, name, manufacturer, datapoints, entity_description):
        self.name = name
        self.manufacturer = manufacturer
        self.datapoints = datapoints
        self.entity_description = entity_description

class TuyaBLECategoryInfo:

    products: dict[str, TuyaBLEProductInfo]

    def __init__(self, products):
        self.products = products

devices_database: dict[str, TuyaBLECategoryInfo] = {
    "cl": TuyaBLECategoryInfo(
        products={
            **dict.fromkeys(
                [
                    "4pbr8eig",
                    "qqdxfdht"
                ],
                TuyaBLEProductInfo(
                    name="Blind Controller",
                    manufacturer="Tuya",
                    entity_description=EntityDescription(
                        key="ble_blind_controller"
                    ),
                    datapoints={
                        Platform.COVER: {
                            "position_set": 2,
                            "current_position": 3,
                            "supported_features": (
                                CoverEntityFeature.OPEN|CoverEntityFeature.CLOSE|
                                CoverEntityFeature.SET_POSITION|CoverEntityFeature.STOP
                            ),
                            "use_state_set": False
                        },
                        Platform.SENSOR: [
                            {
                                "state": 13,
                                "entity_config_key": SENSOR_BATTERY_LEVEL_ENTITY
                            }
                        ],
                        None: {
                            "state": 1, # does not work on this controller
                            "unknown_1": 5,
                            "unknown_2": 103,
                            "unknown_3": 104,
                            "opening_mode": 4,
                            "work_state": 7,
                            "motor_direction": 101,
                            "set_upper_limit": 102,
                            "factory_reset": 107,
                        }
                    }
                )
            ),
            **dict.fromkeys(
                [
                    "kcy0xpi"
                ],
                TuyaBLEProductInfo(
                    name="Curtain Controller",
                    manufacturer="Tuya",
                    entity_description=EntityDescription(
                        key="ble_curtain_controller"
                    ),
                    datapoints={
                        Platform.COVER: {
                            "state": 1,
                            "current_position": 3,
                            "position_set": 2,
                            "supported_features": (
                                CoverEntityFeature.OPEN|CoverEntityFeature.CLOSE|
                                CoverEntityFeature.SET_POSITION|CoverEntityFeature.STOP
                            ),
                            "use_state_set": True
                        },
                        Platform.SENSOR: [
                            {
                                "state": 13,
                                "entity_config_key": SENSOR_BATTERY_LEVEL_ENTITY
                            }
                        ],
                        None: {
                            "work_state": 7,
                            "fault": 12,
                            "timer": 22,
                            "end_default": 101,
                            "learning": 102,
                            "temp_current": 103,
                            "light_current": 104,
                            "temp_set": 105,
                            "light_set": 106,
                            "reset": 107,
                            "pair": 108,
                            "check": 109
                        }
                    }
                )
            )
        }
    )
}

def get_mapping_by_device(device: TuyaBLEDevice) -> TuyaBLEProductInfo:
    """Return mapping for platform."""
    category = devices_database.get(device.category)
    if category is not None and category.products is not None:
        product_mapping = category.products.get(device.product_id)
        if product_mapping:
            return product_mapping
        return {}
