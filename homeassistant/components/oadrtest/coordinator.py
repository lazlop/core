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
from homeassistant.const import CURRENCY_DOLLAR, UnitOfEnergy
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)
from .const import DOMAIN, DEFAULT_SCAN_INTERVAL, DEFAULT_URL

_LOGGER = logging.getLogger(__name__)


class CFHPricesDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching CFH Prices data."""

    def __init__(self, hass: HomeAssistant, scan_interval: int):
        """Initialize the data update coordinator."""
        self.url = DEFAULT_URL
        self.hass = hass
        self.current_prices = None
        self.forecast_prices = None

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}-{scan_interval}",
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
            r = requests.get(self.url)
            price_dict = r.json()
            start_str = price_dict.get("intervalPeriod").get("start")
            start_ts = pd.Timestamp(start_str)
            interval_prices = self._simplify_price_dict(price_dict)
            df = pd.DataFrame(interval_prices)
            df["end_time"] = start_ts + df.duration.cumsum()
            hourly_df = df.set_index("end_time").resample("60T").bfill().reset_index()
            hourly_df["start_time"] = (
                hourly_df["end_time"] - hourly_df["end_time"].diff()
            )
            hourly_df = hourly_df.drop(index=0)
            self.forecast_prices = hourly_df.set_index("start_time")
            self.current_price = self.forecast_prices.iloc[0]["price"]

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
