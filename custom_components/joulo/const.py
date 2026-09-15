"""Constants for the Joulo integration."""
from typing import Final

DOMAIN: Final = "joulo"

API_BASE_URL: Final = "https://api.joulo.nl/functions/v1/api"

CONF_API_TOKEN: Final = "api_token"

CONF_CHARGERS_SCAN_INTERVAL: Final = "chargers_scan_interval"
CONF_ENERGY_SCAN_INTERVAL: Final = "energy_scan_interval"
CONF_ERE_POSITION_SCAN_INTERVAL: Final = "ere_position_scan_interval"
CONF_SESSIONS_SCAN_INTERVAL: Final = "sessions_scan_interval"

# Default polling intervals (seconds), as recommended by Joulo's own Home
# Assistant guide (https://developer.joulo.nl/guides/home-assistant).
# Configurable per-entry via the options flow; these are just the defaults.
DEFAULT_CHARGERS_SCAN_INTERVAL: Final = 60
DEFAULT_ENERGY_SCAN_INTERVAL: Final = 3600
DEFAULT_ERE_POSITION_SCAN_INTERVAL: Final = 3600

# The sessions coordinator polls at this (configurable) cadence while at least
# one charger is actively charging, since that's the only time /sessions data
# for the in-progress session can change. It falls back to the fixed, slower
# SESSIONS_IDLE_SCAN_INTERVAL below while every charger is idle, to avoid
# needlessly polling an endpoint that won't have changed.
DEFAULT_SESSIONS_SCAN_INTERVAL: Final = 60
SESSIONS_IDLE_SCAN_INTERVAL: Final = 3600

# How many of the most recent account-wide sessions to fetch per poll. Sessions
# come back newest-first, so this only needs to comfortably cover "one latest
# session per charger" for the number of chargers a single account realistically has.
SESSIONS_POLL_LIMIT: Final = 50

MANUFACTURER: Final = "Joulo"
