"""Constants for the oadrtest integration."""

# DOMAIN = "sensor"
DOMAIN = "oadrtest"
DEFAULT_NAME = "oadrtest"
DEFAULT_SCAN_INTERVAL = 3600
DEFAULT_URL = "https://api.olivineinc.com/i/lbnl/v1/prices/cfh/SummerHDP_MD/OpenADR3"

# Available rate types
RATE_TYPES = [
    "SummerHDP",
    "SummerLD-TOU",
    "SummerMildHDP",
    "SummerHDPg",
    "FallHDP",
    "FallHDPg",
    "WinterHDP",
    "WinterHDPg",
    "SpringHDP",
    "SpringHDPg",
    "SummerHDP_MD",
    "FallHDP_MD",
    "WinterHDP_MD",
    "SpringHDP_MD",
]
