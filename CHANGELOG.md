# Changelog

All notable changes to this integration are documented in this file.

## [1.2.0] - 2026-09-15

### Added

- New per-charger `estimated_euro` sensor: the ERE payout estimate for the
  charger's in-progress (or just-finished) charging session — not what you
  paid for the electricity.
  - `0` while idle (no session in progress).
  - While charging: Joulo's own `/sessions` only fills in a session's real
    `estimated_euro`/`ere_credits` once it ends, so until then this derives a
    live approximation instead — the charger's own most recent finished
    session gives an ERE-credits-per-kWh rate (from real API data, not a
    hardcoded conversion factor), applied to the live `kwh_so_far` from
    `GET /chargers` and priced using `GET /sessions`' current
    `estimate_basis` (`price_per_ere`, `effective_fee_pct`).
  - Once the session ends, switches straight to Joulo's own exact figure.
  - The `is_estimate` extra attribute says which case a given state came from.
- New "Sessions poll interval" option, tuning how often `GET /sessions` is
  polled while a charger is actively charging.

### Changed

- The new sessions polling only runs on that fast, configurable interval
  while at least one charger is actively charging; it falls back to a fixed
  1h cadence while every charger is idle (with an immediate refresh the
  moment a session starts), since `/sessions` can only change while a session
  is in progress.

## [1.1.1] - 2026-09-06

### Added

- New diagnostic sensor `ere_compliance_year`, exposing `/ere-position`'s
  `compliance_year` field. Every other `ere_*` sensor is scoped to whichever
  year the Joulo API defaults to (the current calendar year), so this makes
  it unambiguous which year's figures you're looking at — especially useful
  right at the New Year boundary.

## [1.1.0] - 2026-09-06

### Added

- New `/ere-position` sensors that were previously fetched but never mapped:
  - `ere_unsold_ytd_forecast` and `ere_unsold_ytd_ere` — the "still to sell,
    year to date" balance (euros and ERE credits).
  - `ere_pending_forecast` and `ere_pending_ere` — the "pending review" balance
    that Joulo hasn't yet allocated to a quarter.
- New "current quarter" sensors: `ere_current_quarter`,
  `ere_current_quarter_price_per_ere`, `ere_current_quarter_sold_ere`,
  `ere_current_quarter_unsold_ere`, `ere_current_quarter_realized`. These track
  whichever quarter the Joulo API marks as in-progress and roll over to the
  next quarter automatically — no reconfiguration needed. `ere_current_quarter_realized`
  also carries a `net_eur_by_status` (paid/payable/reserved) breakdown as an
  extra state attribute.

### Changed

- Renamed the `ere_unsold_forecast` sensor's display name from "(year to date)"
  to "(total)". The underlying value never changed — it was always the combined
  year-to-date + rest-of-year forecast — only the label was wrong. The
  entity ID and unique ID are untouched, so existing automations/dashboards
  keep working; only the friendly name shown in the UI changes.

## [1.0.2] - 2026-08-12

### Added

- Per-charger `active_tag_id` sensor exposing the RFID/TAG id of the active
  charging session, to identify the vehicle/driver behind a charge.

### Fixed

- `session_energy` now uses state class `total_increasing` instead of
  `measurement` — Home Assistant rejects `measurement` combined with
  device class `energy`, and `total_increasing` is the documented pattern for
  a value that only rises within a session and may reset to 0 when a new
  session starts.

## [1.0.1] - 2026-08-03

### Fixed

- HACS/hassfest validation failures.

## [1.0.0] - 2026-08-03

Initial release: charger status, active charging sessions, and lifetime
energy/ERE statistics pulled from the Joulo API.
