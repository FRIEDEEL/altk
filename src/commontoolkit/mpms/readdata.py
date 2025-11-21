from typing import NoReturn
import pandas as pd
from pandas import DataFrame

import logging

logger = logging.getLogger(__name__)

class StartPositionNotFound(BaseException):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)

def readdata(file: str) -> DataFrame:
    """Read .dat datafile from mpms.

    Args:
        file (str): the data file

    Returns:
        pd.DataFrame: Pandas Dataframe with data.

    Raises:
        FileNotFoundError: File of the given file path is not found.
        StartPositionNotFound: Data start line does not exist in this file
    """

    try:
        logger.info(f"Reading from \"{file}\".")
        with open(file, "r") as f:
            for i, line in enumerate(f):
                if line.strip() == "[Data]":
                    data_start = i + 1
                    break
            else:
                raise StartPositionNotFound("Data start position \"[Data]\" not found.")
        df = pd.read_csv(file, skiprows=data_start)
    except FileNotFoundError:
        logger.exception(f"Failed to read \"{file}\"")
        raise
    except StartPositionNotFound:
        logger.exception(f"Start position not found in \"{file}\"")
        raise
    logger.info(f"File \"{file}\" read.")
    return df
