import numpy as np
from pandas import DataFrame
from pathlib import Path
from os import PathLike

import logging

logger = logging.getLogger(__name__)


def convert_pxrd_ras_data_to_txt(
    file: str | PathLike[str],
    # target: str | PathLike[str] | None = None,
):

    # resolve the file to Path object
    # TODO: modify to support user-defined target position
    # TODO: add validation check
    filepath = Path(file)
    targetpath = filepath.with_suffix(".txt")

    _convert_pxrd_ras_data_to_txt(filepath, targetpath)

    # target examine
def _convert_pxrd_ras_data_to_txt(filepath: Path, targetpath: Path):
    DECODE = "cp932"
    logger.info(f"Reading data from {filepath}, decoding binary file with {DECODE}.")
    with open(filepath, "rb") as f1, open(targetpath, "w") as f2:
        for i, line in enumerate(f1):
            try:
                line = line.decode("cp932")
                f2.write(line)

            except UnicodeDecodeError:
                logger.warning(
                    f"Not able to decode line {i} with {DECODE}, skipping..."
                )
    logger.info(f'Binary ras file "{filepath}" have been converted to "{targetpath}".')

def read_pxrd_ras_data_to_df(file: str | PathLike[str]) -> DataFrame:
    """read xrd result data from .ras file.

    Args:
        file (str): the source .ras file

    Returns:
        DataFrame: returns the pandas.DataFrame of angle-intensity data.
            Column names are [ "2theta" , "Intensity" ].

    To access the data,
        ```python
        data = read_pxrd_ras_data_to_df(file)
        ```
    For example, for angles:
        ```python
        # angle 2 theta
        data["2theta"]
        # or
        data.iloc[:, 0]
        ```
    """
    filepath = Path(file)
    return _read_pxrd_ras_data_to_df(filepath)

def _read_pxrd_ras_data_to_df(filepath: Path) -> DataFrame:

    DECODE = "cp932"

    # resolve the file to Path object
    logger.info(f"Reading data from {filepath}, decoding binary file with {DECODE}.")
    with open(filepath, "rb") as f:
        ras_data = []

        # read data loop
        in_data_section = False
        for i, line in enumerate(f):
            try:
                line = line.decode(encoding=DECODE)
            except UnicodeDecodeError:
                logger.warning(
                    f"Not able to decode line {i} with encoding {DECODE}, skipping..."
                )
                continue

            # reads data if data_flag is on
            if in_data_section:
                if line.rstrip() == "*RAS_INT_END":
                    in_data_section = False
                    continue
                try:
                    # processing and splitting the line data
                    line_data = [float(x) for x in line.split()]
                    ras_data.append(line_data)
                    continue # no need to check other conditions
                except ValueError:
                    logger.warning(f"Unrecognized ras data at line {i}, \"{line.rstrip()}\", skipping...")
                    continue
            elif line.rstrip() == "*RAS_INT_START":
                in_data_section = True
                continue
            
            else: # other header conditions and metadata resolving. TODO
                pass

    # output as numpy array
    ras_data = np.array(ras_data, dtype=np.float64)
    # convert to DataFrame
    ras_data_df = DataFrame({"2theta": ras_data[:, 0], "Intensity": ras_data[:, 1]})

    logger.info("File reading done.")
    return ras_data_df

