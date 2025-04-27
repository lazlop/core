"""The oadrtest integration."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME, Platform
from homeassistant.core import HomeAssistant, ServiceCall
from .const import DOMAIN, DEFAULT_SCAN_INTERVAL
from .coordinator import CFHPricesDataUpdateCoordinator


# TODO List the platforms that you want to support.
# For your initial PR, limit it to 1 platform.
_PLATFORMS: list[Platform] = [Platform.SENSOR]

# _LOGGER = logging.getLogger(__name__)

# TODO Create ConfigEntry type alias with API object
# TODO Rename type alias and update all entry annotations
type OadrTestConfigEntry = ConfigEntry[CFH_Server_Data]


@dataclass
class CFH_Server_Data:
    """CFH Server Host."""

    name: str


# TODO Update entry annotation
async def async_setup_entry(hass: HomeAssistant, entry: OadrTestConfigEntry) -> bool:
    """Set up oadrtest from a config entry."""

    # TODO 1. Create API instance
    # TODO 2. Validate the API connection (and authentication)
    # TODO 3. Store an API object for your platforms to access
    # entry.runtime_data = MyAPI(...)
    host = entry.data[CONF_NAME]
    coordinator = CFHPricesDataUpdateCoordinator(
        hass, scan_interval=DEFAULT_SCAN_INTERVAL
    )
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, _PLATFORMS)

    return True


# TODO Update entry annotation
async def async_unload_entry(hass: HomeAssistant, entry: OadrTestConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, _PLATFORMS)
