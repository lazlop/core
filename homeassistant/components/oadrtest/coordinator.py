"""Sensor platform for CalFlexHub Prices integration."""
import pytz
from datetime import timedelta, datetime, timezone
import logging
from typing import Any
import aiohttp
import async_timeout
import asyncio
from isodate import parse_duration
import pandas as pd
import requests
from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CURRENCY_DOLLAR, UnitOfEnergy
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.event import async_track_time_interval
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
    ROTATE_PRICES,
    FORECAST_FROM_0
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
            # update_interval=timedelta
            update_interval=timedelta(seconds=ITER_INTERVAL),
        )
        hass.async_create_task(self._post_prices())
        async_track_time_interval(
            hass,
            self._post_prices, 
            timedelta(seconds=DEFAULT_SCAN_INTERVAL)
        )
        

    # self._always_try_the_vtn()
    
    # def _always_try_the_vtn(self):
    #     try:
    #         await hass.async_create_task(self._post_prices())
    #     except Exception as e:
    #         print("exception")
    #         self._always_try_the_vtn()

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

        try:
            # r = requests.get(self.url)
            # price_dict = r.json()
            # start_str = price_dict.get("intervalPeriod").get("start")

            price_dict = DEFAULT_SIGNAL

            if FORECAST_FROM_0:
                now = datetime.now().astimezone(pytz.timezone('US/Pacific'))
                now = now.replace(hour = 0)
                now = now.astimezone(pytz.utc)
            else:
                now = datetime.now(timezone.utc)
            
            start_str = now.strftime("%Y-%m-%dT%H:00:00+00:00")
            start_ts = pd.Timestamp(start_str)
            interval_prices = self._simplify_price_dict(price_dict)
            df = pd.DataFrame(interval_prices)
            df["end_time"] = start_ts + df.duration.cumsum()
            hourly_df = df.set_index("end_time").resample("60min").bfill().reset_index()
            hourly_df["start_time"] = (
                hourly_df["end_time"] - hourly_df["end_time"].diff()
            )
            hourly_df = hourly_df.drop(index=0)
            self.forecast_prices = hourly_df.set_index("start_time").to_dict(
                orient="index"
            )
            if ROTATE_PRICES:
                self.current_price = hourly_df.iloc[0]["price"]
            else:
                self.current_price = hourly_df.iloc[self.get_hour()]["price"]

            fake_time = start_ts + timedelta(hours=self.get_hour())

            return {
                "current_price": self.current_price,
                "forecast_prices": self.forecast_prices,
                "fake_time": fake_time.strftime("%Y-%m-%dT%H:00:00+00:00"),
            }

        except requests.RequestException as err:
            _LOGGER.error("Error fetching data: %s", err)
            raise

    def _simplify_price_dict(self, price_dict):
        """Simplify the price dictionary from the API response."""
        simple_prices = []
        prices = price_dict.get("intervals")
        if ROTATE_PRICES:
            # rearrange prices based on time
            new_start_hour = self.get_hour()
            # Extract pricing data from the event
            prices = prices[new_start_hour:] + prices[:new_start_hour]

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

    def get_hour(self):
        now = datetime.now()
        sec = (now - self.start_time).seconds
        return sec // ITER_INTERVAL % 24

    async def _post_prices(self, now = None):
        """post prices to openadr vtn."""
        # just getting static price while developing, will switch this to be backup
        # try:
        #     r = requests.get(self.url)
        #     price_dict = r.json()

        await _create_program()
        print('creating_pringram')
        # except requests.RequestException as err:
        #     price_dict = DEFAULT_SIGNAL
        price_dict = DEFAULT_SIGNAL
        # Just using default signal right now
        price_dict["programID"] = "0"
        await _delete_all_events()
        await _create_pricing_event(price_dict, 0)
        print('price_posted')
        # while True:
        #     await _delete_all_events()
        #     await _create_pricing_event(price_dict, 0)
        #     await asyncio.sleep(DEFAULT_SCAN_INTERVAL)
        #     print('price_posted')
