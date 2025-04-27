"""Sensor platform for CalFlexHub Prices integration."""

from datetime import timedelta
import logging
from typing import Any

import aiohttp
import async_timeout
import pandas as pd

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CURRENCY_DOLLAR, UnitOfEnergy
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from .coordinator import CFHPricesDataUpdateCoordinator

from .const import DOMAIN, DEFAULT_SCAN_INTERVAL, DEFAULT_URL

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the CalFlexHub Prices sensor from a config entry."""
    scan_interval = DEFAULT_SCAN_INTERVAL
    coordinator = entry.runtime_data
    # coordinator = CFHPricesDataUpdateCoordinator(hass, scan_interval=scan_interval)

    # # Fetch initial data
    # await coordinator.async_config_entry_first_refresh()

    # Store the coordinator in hass.data for service access
    # TODO: Coordinator should be entry.runtime_data based like electricity maps

    async_add_entities([CFHPricesSensor(coordinator)], True)


class CFHPricesSensor(SensorEntity):
    """Representation of a CFH Prices sensor."""

    def __init__(self, coordinator: CFHPricesDataUpdateCoordinator):
        """Initialize the sensor."""
        self._coordinator = coordinator
        self.coordinator = coordinator
        self._attr_name = f"CFH Price"
        self._attr_unique_id = f"cfh_price"
        self._attr_device_class = "monetary"
        self._attr_native_unit_of_measurement = (
            f"{CURRENCY_DOLLAR}/{UnitOfEnergy.KILO_WATT_HOUR}"
        )
        self._attr_icon = "mdi:currency-usd"

    @property
    def native_value(self) -> float:
        """Return the current price."""
        if self.coordinator.data:
            return self.coordinator.data.get("current_price")
        return None

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        if self.coordinator.data.get("current_price"):
            return True
        return False

    async def async_added_to_hass(self) -> None:
        """Connect to dispatcher listening for entity data notifications."""
        self.async_on_remove(
            self._coordinator.async_add_listener(self.async_write_ha_state)
        )


    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        if not self.coordinator.data:
            return {}

        forecast_prices = self.coordinator.data.get("forecast_prices", {})
        # print(forecast_prices)
        forecast_data = []
        for timestamp, data in forecast_prices.items():
            forecast_data.append(
                {
                    "start_time": timestamp.isoformat(),
                    "end_time": data.get("end_time").isoformat(),
                    "price": data.get("price"),
                }
            )
        # print(forecast_data)

        return {
            "forecast": forecast_data,
        }
