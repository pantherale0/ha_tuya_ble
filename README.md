# Home Assistant support for Tuya Cover BLE devices

## Overview

This integration supports Tuya Cover devices connected via BLE. (blind and curtain motors)

## Installation

Place the `custom_components` folder in your configuration directory (or add its contents to an existing `custom_components` folder). Alternatively install via [HACS](https://hacs.xyz/).

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=pantherale0&repository=ha_tuya_ble&category=integration)

## Usage

After adding to Home Assistant integration should discover all supported Bluetooth devices, or you can add discoverable devices manually.

The integration works locally, but connection to Tuya BLE device requires device ID and encryption key from Tuya IOT cloud. It could be obtained using the same credentials as in the previous official Tuya integration. To obtain the credentials, please refer to official Tuya integration [documentation](https://web.archive.org/web/20231228044831/https://www.home-assistant.io/integrations/tuya/) [[1]](https://github.com/home-assistant/home-assistant.io/blob/a4e6d4819f1db584cc66ba2082508d3978f83f7e/source/_integrations/tuya.markdown)

## Supported devices list

* Covers (category_id 'cl')
  + Moes Roller Blind Motor (product_id '4pbr8eig', 'qqdxfdht')
  * Curtain Motor (product_id 'kcy0xpi')

## Sources

_poc-tuya-ble-fingerbot by [@redphx](https://github.com/redphx/poc-tuya-ble-fingerbot)_

_ha_tuya_ble by [@PlusPlus-ua](https://github.com/PlusPlus-ua/ha_tuya_ble)_