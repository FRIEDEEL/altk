# Changelog

This project uses lightweight changelog entries for tagged development snapshots.
The format is intentionally simple because the public API is still evolving.

## [0.3.0.dev1] - 2026-06-29

Development snapshot for the first SCMAG data API.

### Added

- Added `ScmagData` and `ScmagSample` for SCMAG measurement data.
- Added SCMAG raw quantity accessors for temperature, time, current, and charge.
- Added SCMAG sample geometry handling with SI-unit internal storage and a `from_um()` helper for microscope-scale inputs.
- Added derived SCMAG quantities:
  - polarization `P`
  - current density `J`
  - heating/cooling rate `beta = dT/dt`
  - `I_beta = I/beta`
  - `J_beta = J/beta`
- Added `with_beta_columns()` for materializing beta-related quantities into a new `ScmagData`.
- Added `interpolate_on_temperature()` for simple temperature-grid interpolation.
- Added quantity-based `align_on()` for aligning multiple `ScmagData` objects on a shared quantity grid.
- Added sanitized SCMAG sample data files for tests.
- Added `tests/scmag/` coverage for SCMAG data reading, sample validation, derived quantities, interpolation, and alignment.
- Added development notes for SCMAG quantity design principles in `DEVLOG.md`.

### Changed

- SCMAG quantity design now treats public access as quantity-oriented rather than dataframe-column-oriented.
- Derived quantities materialized by alignment now use distinct column names, avoiding ambiguity between raw quantities such as `I`/`Q` and derived quantities such as `J`/`P`.
- SCMAG sample geometry documentation now clarifies SI-unit internal storage.
- Interpolation and alignment design now favors resolving requested quantities through `ScmagData` properties.

### Notes

- The SCMAG API is still experimental and may change before `0.3.0`.
- `align_on()` is the preferred high-level API for aligning multiple datasets; direct interpolation remains available for simpler one-dataset cases.
- Some older workflow files are still experimental and are not considered stable API.

## [0.2.0] - 2026-06-13

Baseline release before the SCMAG data API work.

### Included

- MPMS data handling and Curie-Weiss fitting utilities.
- Chemistry calculation utilities.
- PXRD RAS data reading.
- Furnace program helpers.
- Dichroism and image-related utilities.