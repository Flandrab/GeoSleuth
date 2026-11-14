import io

import numpy as np
from scipy.io import wavfile

SR = 44100


def sonify(years, values, emergence_year=None):
    """FAKE for now: returns 1 s of silence as WAV bytes."""
    buf = io.BytesIO()
    wavfile.write(buf, SR, np.zeros(SR, dtype=np.int16))
    return buf.getvalue()