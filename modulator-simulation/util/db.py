import numpy as np


def db(linear):
    return 10 * np.log10(linear)


def linear(db):
    return np.power(db / 10, 10)
