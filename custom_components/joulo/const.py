"""Constants for the Joulo integration."""
from typing import Final

DOMAIN: Final = "joulo"

API_BASE_URL: Final = "https://api.joulo.nl/functions/v1/api"

CONF_API_TOKEN: Final = "api_token"

CONF_CHARGERS_SCAN_INTERVAL: Final = "chargers_scan_interval"
CONF_ENERGY_SCAN_INTERVAL: Final = "energy_scan_interval"
CONF_ERE_POSITION_SCAN_INTERVAL: Final = "ere_position_scan_interval"

# Default polling intervals (seconds), as recommended by Joulo's own Home
# Assistant guide (https://developer.joulo.nl/guides/home-assistant).
# Configurable per-entry via the options flow; these are just the defaults.
DEFAULT_CHARGERS_SCAN_INTERVAL: Final = 60
DEFAULT_ENERGY_SCAN_INTERVAL: Final = 3600
DEFAULT_ERE_POSITION_SCAN_INTERVAL: Final = 3600

MANUFACTURER: Final = "Joulo"
