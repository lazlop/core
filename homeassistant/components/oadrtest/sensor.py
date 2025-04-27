"""Sensor platform for CalFlexHub Prices integration."""

from datetime import timedelta
import logging
from typing import Any

import aiohttp
import async_timeout
from isodate import parse_duration
import pandas as pd

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_SCAN_INTERVAL, CURRENCY_DOLLAR, UnitOfEnergy
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    """Set up the CalFlexHub Prices sensor from a config entry."""
    scan_interval = config_entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

    coordinator = CFHPricesDataUpdateCoordinator(hass, scan_interval=scan_interval)

    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()

    # Store the coordinator in hass.data for service access
    hass.data[DOMAIN][config_entry.entry_id] = coordinator

    async_add_entities([CFHPricesSensor(coordinator, rate_type)], True)


class CFHPricesDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching CFH Prices data."""

    def __init__(self, hass: HomeAssistant, rate_type: str, scan_interval: int):
        """Initialize the data update coordinator."""
        self.rate_type = rate_type
        self.url = f"{URL_BASE}{rate_type}/OpenADR3"
        self.hass = hass
        self.current_prices = None
        self.forecast_prices = None

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{rate_type}",
            update_interval=timedelta(seconds=scan_interval),
        )

    async def _async_update_data(self):
        """Fetch data from API endpoint."""
        try:
            async with async_timeout.timeout(30):
                return await self.hass.async_add_executor_job(self._fetch_prices)
        except TimeoutError as err:
            raise UpdateFailed(f"Timeout communicating with API: {err}") from err
        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err
        except Exception as err:
            raise UpdateFailed(f"Error parsing data: {err}") from err

    def _fetch_prices(self):
        """Fetch price data from the API."""
        import requests

        try:
            response = requests.get(self.url)
            response.raise_for_status()
            price_dict = response.json()

            # Process the price data
            start_str = price_dict.get("intervalPeriod").get("start")
            start_ts = pd.Timestamp(start_str)
            interval_prices = self._simplify_price_dict(price_dict)

            df = pd.DataFrame(interval_prices)
            df["end_time"] = start_ts + df.duration.cumsum()
            hourly_df = df.set_index("end_time").resample("60T").bfill().reset_index()
            hourly_df["start_time"] = hourly_df["end_time"] - pd.Timedelta(hours=1)
            hourly_df = hourly_df.drop(index=0)

            # Set the current price and forecast prices
            now = pd.Timestamp.now()
            current_price_row = hourly_df[
                (hourly_df["start_time"] <= now) & (hourly_df["end_time"] > now)
            ]

            if not current_price_row.empty:
                self.current_price = current_price_row.iloc[0]["price"]
            else:
                self.current_price = None

            # Create forecast data
            self.forecast_prices = hourly_df.set_index("start_time").to_dict(
                orient="index"
            )

            return {
                "current_price": self.current_price,
                "forecast_prices": self.forecast_prices,
            }

        except requests.RequestException as err:
            _LOGGER.error("Error fetching data: %s", err)
            raise

    def _simplify_price_dict(self, price_dict):
        """Simplify the price dictionary from the API response."""
        simple_prices = []
        prices = price_dict.get("intervals")
        duration = price_dict.get("intervalPeriod").get("duration")
        simple_prices.append({"duration": pd.Timedelta(0)})

        for i in prices:
            if "payloads" in i and i["payloads"][0]["type"] == "PRICE":
                if i.get("intervalPeriod"):
                    payload_duration = i.get("intervalPeriod").get("duration")
                    timedelta_duration = parse_duration(payload_duration)
                else:
                    timedelta_duration = parse_duration(duration)
                simple_prices.append(
                    {
                        "duration": timedelta_duration,
                        "price": i.get("payloads", [])[0]["values"][0],
                    }
                )
        return simple_prices


class CFHPricesSensor(CoordinatorEntity, SensorEntity):
    """Representation of a CFH Prices sensor."""

    def __init__(self, coordinator: CFHPricesDataUpdateCoordinator, rate_type: str):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._rate_type = rate_type
        self._attr_name = f"CFH Price {rate_type}"
        self._attr_unique_id = f"cfh_price_{rate_type}"
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
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        if not self.coordinator.data:
            return {}

        forecast_prices = self.coordinator.data.get("forecast_prices", {})
        forecast_data = []

        for timestamp, data in forecast_prices.items():
            forecast_data.append(
                {
                    "start_time": timestamp.isoformat(),
                    "end_time": data.get("end_time").isoformat(),
                    "price": data.get("price"),
                }
            )

        return {
            "rate_type": self._rate_type,
            "forecast": forecast_data,
        }
