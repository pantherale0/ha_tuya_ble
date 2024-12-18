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
    DEVICE_DEF_MANUFACTURER
)

@dataclass
class TuyaBLEProductInfo:
    """Store a product info."""
    name: str
    manufacturer: str = DEVICE_DEF_MANUFACTURER
    datapoints: dict[Platform, dict[str, int]] = {}
    entity_description: EntityDescription

@dataclass
class TuyaBLECategoryInfo:
    products: dict[str, TuyaBLEProductInfo]
    info: TuyaBLEProductInfo | None = None

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
                    entity_description=EntityDescription(
                        key="ble_blind_controller"
                    ),
                    datapoints={
                        "cover_state_dp_id": {
                            Platform.COVER: {
                                "state": 1,
                                "position_set": 2,
                                "current_position": 3,
                                "supported_features": (
                                    CoverEntityFeature.OPEN|CoverEntityFeature.CLOSE|
                                    CoverEntityFeature.SET_POSITION
                                )
                            },
                            Platform.SENSOR: {
                                "battery_level": 13,
                            },
                            None: {
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
                    }
                )
            ),
            **dict.fromkeys(
                [
                    "kcy0xpi"
                ],
                TuyaBLEProductInfo(
                    name="Curtain Controller",
                    entity_description=EntityDescription(
                        key="ble_curtain_controller"
                    ),
                    datapoints={
                        Platform.COVER: {
                            "state": 7,
                            "current_position": 3,
                            "position_set": 2,
                            "supported_features": (
                                CoverEntityFeature.OPEN|CoverEntityFeature.CLOSE|
                                CoverEntityFeature.SET_POSITION
                            )
                        },
                        Platform.SENSOR: {
                            "battery_level": 13,
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
