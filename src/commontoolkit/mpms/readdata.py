import pandas as pd

import logging

logger = logging.getLogger(__name__)

def readdata(file: str):
    """Read .dat datafile from mpms.

    Args:
        file (str): _description_

    Returns:
        _type_: _description_
    """    
    try:
        logger.info(f"Reading from {file}.")
        df = pd.read_csv(file)
    except FileNotFoundError:
        logger.exception(f"Failed to read {file}")
        raise
    logger.info(f"{file} read.")
    return df
