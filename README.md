# ALTK user guide

Arima-Lab ToolKit, or ALTK, gathers the common tools used in the lab.
Mostly integrates figure plotting and data processing for XRD, magnetisation, etc.

Actively updating.

## Usages
### Data loading
Basically, `altk` provides functions that load data into `pandas.DataFrame` and `numpy.ndarray`, no matter the type of data.

The loading function can be accessed using

## Design principles

## Sub-Modules

### `altk.pxrd`
Powder XRD data processing and making plots, running analysis(TODO).

### `altk.furnace`
The furnace part.

Aims to automatically make the time-temperature plot of furnace with input set of time - temperature pair list.

Still under development.

### `altk.mpms`
Reads MPMS magnetisation data and making plots for analysis.
