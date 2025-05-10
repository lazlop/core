"""Sensor platform for CalFlexHub Prices integration."""

from datetime import timedelta, datetime
import logging
from typing import Any

import aiohttp
import async_timeout
from isodate import parse_duration
import pandas as pd
import requests
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
from .const import (
    DOMAIN,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_URL,
    DEFAULT_SIGNAL,
    ITER_INTERVAL,
)
from .vtn_comms import _create_pricing_event, _create_program, _delete_all_events
import threading

_LOGGER = logging.getLogger(__name__)


class CFHPricesDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching CFH Prices data."""

    def __init__(self, hass: HomeAssistant, scan_interval: int):
        """Initialize the data update coordinator."""
        self.url = DEFAULT_URL
        self.hass = hass
        self.current_prices = None
        self.forecast_prices = None
        self.start_time = datetime.now()

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}-{scan_interval}",
            update_interval=timedelta(seconds=scan_interval),
        )
        # _create_program()
        # thread = threading.Thread(target=_post_prices_with_threading, daemon=True)
        # thread.start()

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

    def _fetch_prices(self, current_time):
        """Fetch price data from the API."""
        # just getting static price while developing, will switch this to be backup
        # try:
        #     r = requests.get(self.url)
        #     price_dict = r.json()

        # except requests.RequestException as err:
        #     price_dict = DEFAULT_SIGNAL
        price_dict = DEFAULT_SIGNAL
        # Just using default signal right now

        sped_up_hour = self.get_hour()
        intervals = price_dict["intervals"]
        updated_intervals = intervals[sped_up_hour:] + intervals[:sped_up_hour]
        price_dict["intervals"] = updated_intervals

        event_prices = []
        for interval in price_dict.get("intervals", []):
            for payload in interval.get("payloads", []):
                if payload.get("type") == "PRICE" and payload.get("values"):
                    event_prices.append(payload["values"][0])

        return {
            "current_price": event_prices[0],
            "forecast_prices": event_prices,
        }

    def get_hour(self):
        now = datetime.now()
        sec = (now - self.start_time).seconds
        return sec // ITER_INTERVAL % 24

    def _post_prices(self):
        """post prices to openadr vtn."""
        # just getting static price while developing, will switch this to be backup
        # try:
        #     r = requests.get(self.url)
        #     price_dict = r.json()

        # except requests.RequestException as err:
        #     price_dict = DEFAULT_SIGNAL
        price_dict = DEFAULT_SIGNAL
        # Just using default signal right now
        price_dict["programID"] = "0"
        _delete_all_events()
        _create_pricing_event(price_dict, 0)
