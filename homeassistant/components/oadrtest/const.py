"""Constants for the oadrtest integration."""

# MODES
ROTATE_PRICES = False
FORECAST_FROM_0 = True
AS_PST = False
VTN_URL = "http://localhost:8080/openadr3/3.0.1"
# DOMAIN = "sensor"
DOMAIN = "oadrtest"
DEFAULT_NAME = "oadrtest"
ITER_INTERVAL = 5
DEFAULT_SCAN_INTERVAL = ITER_INTERVAL * 24
DEFAULT_URL = "https://api.olivineinc.com/i/lbnl/v1/prices/cfh/SpringHDP/OpenADR3"
OPENADR_VTN = ""

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

DEFAULT_SIGNAL = {
    "createdDateTime": "2025-05-09T21:43:50.4925054+00:00",
    "objectType": "EVENT",
    "eventName": "SpringHDP",
    "programID": "0",
    "id": "0",
    "payloadDescriptors": [{"payloadType": "PRICE", "units": "KWH", "currency": "USD"}],
    "intervalPeriod": {"start": "2025-05-09T21:00:00+00:00", "duration": "PT1H"},
    "intervals": [
        {"id": 0, "payloads": [{"type": "PRICE", "values": [0.0255]}]},
        {"id": 1, "payloads": [{"type": "PRICE", "values": [0.0632]}]},
        {"id": 2, "payloads": [{"type": "PRICE", "values": [0.0957]}]},
        {"id": 3, "payloads": [{"type": "PRICE", "values": [0.2358]}]},
        {"id": 4, "payloads": [{"type": "PRICE", "values": [0.4931]}]},
        {"id": 5, "payloads": [{"type": "PRICE", "values": [0.6618]}]},
        {"id": 6, "payloads": [{"type": "PRICE", "values": [0.5364]}]},
        {"id": 7, "payloads": [{"type": "PRICE", "values": [0.4116]}]},
        {"id": 8, "payloads": [{"type": "PRICE", "values": [0.2905]}]},
        {"id": 9, "payloads": [{"type": "PRICE", "values": [0.2209]}]},
        {"id": 10, "payloads": [{"type": "PRICE", "values": [0.1714]}]},
        {"id": 11, "payloads": [{"type": "PRICE", "values": [0.144]}]},
        {"id": 12, "payloads": [{"type": "PRICE", "values": [0.1385]}]},
        {"id": 13, "payloads": [{"type": "PRICE", "values": [0.1518]}]},
        {"id": 14, "payloads": [{"type": "PRICE", "values": [0.1829]}]},
        {"id": 15, "payloads": [{"type": "PRICE", "values": [0.2713]}]},
        {"id": 16, "payloads": [{"type": "PRICE", "values": [0.4659]}]},
        {"id": 17, "payloads": [{"type": "PRICE", "values": [0.5328]}]},
        {"id": 18, "payloads": [{"type": "PRICE", "values": [0.28]}]},
        {"id": 19, "payloads": [{"type": "PRICE", "values": [0.1158]}]},
        {"id": 20, "payloads": [{"type": "PRICE", "values": [0.0398]}]},
        {"id": 21, "payloads": [{"type": "PRICE", "values": [0.0196]}]},
        {"id": 22, "payloads": [{"type": "PRICE", "values": [0.011]}]},
        {"id": 23, "payloads": [{"type": "PRICE", "values": [0.0188]}]},
    ],
}
