# Joulo for Home Assistant

A [HACS](https://hacs.xyz/) custom integration for [Joulo](https://joulo.nl) — pulls charger
status, active charging sessions, and lifetime energy/ERE statistics from the
[Joulo API](https://developer.joulo.nl/) into Home Assistant.

## Entities

Per linked charger (one HA device each):

| Entity | Source | Poll interval |
|---|---|---|
| `sensor.<charger>_status` | `GET /chargers` | 60s |
| `binary_sensor.<charger>_charging` | `GET /chargers` | 60s |
| `sensor.<charger>_session_energy` | `GET /chargers` | 60s |
| `sensor.<charger>_meter_reading` (disabled by default) | `GET /chargers` | 60s |

Account-wide (one "Joulo account" device):

| Entity | Source | Poll interval |
|---|---|---|
| `sensor.joulo_total_energy` | `GET /energy` | 1h |
| `sensor.joulo_total_ere_credits` | `GET /energy` | 1h |
| `sensor.joulo_total_sessions` | `GET /energy` | 1h |
| `sensor.joulo_ere_paid` | `GET /ere-position` | 1h |
| `sensor.joulo_ere_payable` | `GET /ere-position` | 1h |
| `sensor.joulo_ere_reserved` | `GET /ere-position` | 1h |
| `sensor.joulo_ere_unsold_forecast` | `GET /ere-position` | 1h |
| `sensor.joulo_ere_unsold_future_forecast` | `GET /ere-position` | 1h |
| `sensor.joulo_ere_ytd_expected` | `GET /ere-position` | 1h |
| `sensor.joulo_ere_total_expected` | `GET /ere-position` | 1h |
| `sensor.joulo_ere_indicative_price` (diagnostic) | `GET /ere-position` | 1h |
| `sensor.joulo_ere_realized_avg_price` (diagnostic) | `GET /ere-position` | 1h |
| `sensor.joulo_ere_paid_price_per_ere` (diagnostic) | `GET /ere-position` | 1h |
| `sensor.joulo_ere_fee_pct` (diagnostic) | `GET /ere-position` | 1h |
| `sensor.joulo_ere_allocatable` (diagnostic) | `GET /ere-position` | 1h |
| `sensor.joulo_ere_forecast_confidence` (diagnostic) | `GET /ere-position` | 1h |
| `sensor.joulo_ere_forecast_history` (diagnostic) | `GET /ere-position` | 1h |

The `ere_indicative_price` sensor also carries the quarterly price breakdown
(`quarters`) from the API as an extra state attribute. All euro-denominated
`ere_*` figures other than `ere_paid` are Joulo's own forecasts/estimates and
can move up or down as market prices and allocations change.

New chargers added in the Joulo dashboard appear automatically on the next poll,
no reload required.

## Configuration

Both are available on an already-added entry from Settings → Devices & services → Joulo,
no need to remove and re-add:

- **⋮ → Reconfigure** — swap in a new personal API token (e.g. after rotating it in the
  Joulo dashboard) without recreating the entry or losing entity history.
- **⋮ → Configure** (options) — tune the poll interval (in seconds) for each of the three
  endpoints (chargers, energy, ERE position) independently. Changing a value reloads the
  entry immediately with the new intervals.

## Installation

### Via HACS

1. HACS → Integrations → ⋮ → Custom repositories → add this repo URL, category "Integration".
2. Install "Joulo", restart Home Assistant.
3. Settings → Devices & services → Add integration → "Joulo".
4. Paste a personal API token from the Joulo dashboard (Settings → API → Activate).

### Manual

Copy `custom_components/joulo` into your Home Assistant `config/custom_components/`
directory and restart.

## Development

This repo is set up to be opened in VS Code's Dev Containers using Docker Desktop —
it builds a container with a "fake" Home Assistant instance for testing the
integration live, following the same pattern as the official
[integration blueprint](https://github.com/ludeeus/integration_blueprint).

1. Install the [Dev Containers](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)
   VS Code extension (Docker Desktop must be running).
2. Open this folder in VS Code → "Reopen in Container" when prompted.
3. Wait for `scripts/setup` to finish installing Home Assistant + test deps.
4. Run the **"Run Home Assistant"** task (Terminal → Run Task…), or from a
   container terminal: `bash scripts/develop`.
5. Open http://localhost:8123, complete onboarding, then add the "Joulo"
   integration and enter a real API token to test against the live API.

`custom_components/joulo` is symlinked into `config/custom_components`, so
edits are picked up on restart — no rebuild needed. Home Assistant restarts
can be triggered from Developer Tools → YAML, or by re-running the task.

### Tests

```bash
pytest tests
```

### Lint

```bash
bash scripts/lint
```

