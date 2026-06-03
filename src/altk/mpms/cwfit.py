import numpy as np
import pandas as pd
from pandas import Series


def curie_weiss_fit(T_seq: Series, chi_seq: Series, low_cut: float):
    T = T_seq.to_numpy(dtype=np.float64)
    chi = chi_seq.to_numpy(dtype=np.float64)
