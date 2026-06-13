# ALTK

**A**nalysis & **L**aboratory **T**ool**K**it, ALTK, is a personal Python toolkit
for daily laboratory data processing, calculation, and visualization.

The package is under active development. This README focuses on the currently
usable public modules and keeps experimental APIs explicitly marked.

## Features

- Read MPMS `.dat` files and calculate common magnetic quantities.
- Fit magnetic susceptibility with the Curie-Weiss law.
- Parse, balance, and calculate simple chemical reactions.
- Read Rigaku-style powder XRD `.ras` files.
- Plot furnace time-temperature programs.
- Align TIFF images and calculate dichroism-style difference images.

## Installation

ALTK is intended to be used as a local editable package. Clone the repository
and install it into your active Python environment:

```bash
cd <parent-directory>
git clone <repository-url>
cd <repository-directory>
pip install -e .
```

After installation, `altk` can be imported from any working directory that uses
the same Python environment:

```python
from altk.mpms import MpmsData
```

## Quick Start

### MPMS Data

```python
from altk.mpms import MpmsData, Sample

data = MpmsData.from_file("tests/data/sample_mpms_data_file.dat")
data.set_sample(Sample(mass=0.100, molar_mass=100.0))

temperature = data.T
field = data.H
moment = data.m
susceptibility = data.chi
molar_susceptibility = data.chi_mol
```

### Curie-Weiss Fit

```python
from altk.mpms import curie_weiss_fit

result = curie_weiss_fit(
    temperature=data.T,
    susceptibility=data.chi,
    t_min=150.0,
    t_max=300.0,
)

print(result.curie_constant)
print(result.weiss_temperature)
print(result.r_squared)
```

### Chemical Calculation

```python
from altk.chemcalc import Constraint, Reaction

reaction = Reaction.from_string("V2O5 + V2O3 -> VO2").balance()
result = reaction.calculate(
    [
        Constraint("V2O5", "<=", 10.0, "g"),
        Constraint("V2O3", "<=", 5.0, "g"),
    ]
)

print(reaction)
print(result)
```

### PXRD Data

```python
from altk.pxrd import read_pxrd_ras_data_to_df

df = read_pxrd_ras_data_to_df("tests/data/sample_pxrd_ras_data_file.ras")

angle = df["2theta"]
intensity = df["Intensity"]
```

### Furnace Program Plot

```python
import matplotlib.pyplot as plt

from altk.furnace import plot_furnace_program, read_program_data

sequence = read_program_data("tests/data/furnace/sample_furnace_program.csv")

fig = plt.figure()
plot_furnace_program(fig, [sequence], zoom_areas=[(0, 10)])
plt.show()
```

### Image Difference

```python
from altk.dichroism import calc_difference, find_offset, read_tif, slice_intersection

im1 = read_tif("image_1.tif")
im2 = read_tif("image_2.tif")

offset = find_offset(im1, im2)
im1_overlap, im2_overlap = slice_intersection(im1, im2, offset)
diff = calc_difference(im1_overlap, im2_overlap, mode="relative")
```

## Module Overview

### `altk.mpms`

MPMS data utilities.

Main APIs:

- `MpmsData`: structured MPMS data container.
- `Sample`: sample mass, molar mass, and formula container.
- `read_mpms_data_to_df`: read MPMS `.dat` data into a `pandas.DataFrame`.
- `calc_dM_dT`: calculate the first derivative of moment against temperature.
- `curie_weiss_fit`: fit susceptibility with the Curie-Weiss law.

Common aliases on `MpmsData`:

- `T`: temperature.
- `H`: magnetic field.
- `m`: measured long moment.
- `M`: mass-normalized magnetisation.
- `M_mol`: molar magnetisation.
- `chi`: susceptibility.
- `chi_mol`: molar susceptibility.

### `altk.chemcalc`

Chemical formula, reaction balancing, and reaction-quantity calculation.

Main APIs:

- `Species`: formula object with parsed composition and molar mass.
- `Reaction`: reaction parser and balancer.
- `Constraint`: reactant amount or mass constraint.
- `calculate_reaction`: calculate limiting reactants, used amounts, remaining
  reactants, and product quantities.

Current calculation support is intentionally narrow: reactant constraints with
`<=` in `g` or `mol` are supported. Product constraints and exact `=`
constraints are not implemented yet.

### `altk.pxrd`

Powder XRD data readers.

Main APIs:

- `read_pxrd_ras_data_to_df`: read angle-intensity data from `.ras` files.
- `convert_pxrd_ras_data_to_txt`: convert `.ras` files to text with CP932
  decoding.

### `altk.furnace`

Furnace-program reading and plotting.

Main APIs:

- `read_program_data`: read a CSV file with `time` and `temperature` columns.
- `plot_furnace_program`: draw one or more time-temperature sequences with
  optional zoom regions and interval annotations.

### `altk.dichroism`

TIFF image utilities for alignment and difference calculation.

Main APIs:

- `read_tif`: load a TIFF image.
- `find_offset`: estimate integer-pixel offset by cross-correlation.
- `slice_intersection`: crop the overlapping aligned region.
- `find_max_intensity_crop_box`: find the strongest fixed-size image window.
- `calc_difference`: calculate absolute or relative difference images.

### `altk.workflows`

Workflow modules compose lower-level utilities into opinionated analysis
procedures. These APIs are experimental and may change more frequently than the
core modules listed above.

## Development

The project targets Python 3.12 or newer.

For development, this repository uses `uv` to reproduce the local environment
and run tests:

```bash
uv sync
uv run pytest
```

Development notes and design history are kept in `DEVLOG.md`.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.