import io

import numpy as np
from scipy.io import wavfile

SR = 44100            # samples per second
NOTE_DUR = 0.4        # seconds per year
BELL_DUR = 1.2        # seconds the bell rings out
# C major pentatonic (C D E G A) over 2 octaves, starting at C4 (MIDI 60)
PENTATONIC = [60 + octave * 12 + step for octave in range(2) for step in (0, 2, 4, 7, 9)]


def _midi_to_freq(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def _tone(freq, dur=NOTE_DUR, vol=0.4):
    """One soft note: a sine wave plus a quiet overtone, with a smooth start and fade."""
    t = np.linspace(0, dur, int(SR * dur), endpoint=False)
    wave = (np.sin(2 * np.pi * freq * t) + 0.3 * np.sin(2 * np.pi * 2 * freq * t)) / 1.3
    fade = int(0.01 * SR)
    env = np.ones_like(wave)
    env[:fade] = np.linspace(0, 1, fade)
    env[-fade:] = np.linspace(1, 0, fade)
    env *= np.exp(-1.5 * t)  # gentle decay, like a soft piano
    return vol * wave * env


def _bell(freq=1760, dur=BELL_DUR, vol=0.35):
    """A bell: a few metallic overtones that fade out."""
    t = np.linspace(0, dur, int(SR * dur), endpoint=False)
    partials = [(1.0, 0.6), (2.76, 0.3), (5.4, 0.15)]
    wave = sum(a * np.sin(2 * np.pi * freq * k * t) for k, a in partials)
    return vol * wave * np.exp(-3 * t)


def _to_wav_bytes(audio):
    peak = np.max(np.abs(audio)) if len(audio) else 0
    if peak > 0.95:
        audio = audio / peak * 0.95  # avoid distortion
    buf = io.BytesIO()
    wavfile.write(buf, SR, (audio * 32767).astype(np.int16))
    return buf.getvalue()


def value_to_note_index(values):
    """Lowest value -> lowest note, highest value -> highest note."""
    v = np.asarray(values, dtype=float)
    lo, hi = v.min(), v.max()
    if hi - lo == 0:
        return np.full(len(v), len(PENTATONIC) // 2)
    return np.round((v - lo) / (hi - lo) * (len(PENTATONIC) - 1)).astype(int)


def outside_band(values, trend_line=None, noise_sigma=None):
    """
    For each year: True if the value is outside the natural-variation band
    (more than 2 sigma from the start of the trend). These years are played louder.
    Returns None if there is no band to compare with.
    """
    if trend_line is None or not noise_sigma:
        return None
    base = float(trend_line[0])
    return [abs(float(v) - base) > 2 * noise_sigma for v in values]


def _year_ranges(years):
    """[2007, 2008, 2012, 2013, 2014] -> '2007 to 2008 and 2012 to 2014' (easy to read aloud)."""
    groups = []
    for y in sorted(years):
        if groups and y == groups[-1][1] + 1:
            groups[-1][1] = y
        else:
            groups.append([y, y])
    parts = [str(a) if a == b else f"{a} to {b}" for a, b in groups]
    if len(parts) == 1:
        return parts[0]
    return ", ".join(parts[:-1]) + " and " + parts[-1]


def _amount(value, unit=""):
    """0.93, 'C' -> '0.93 C above average', written out for screen readers."""
    unit_txt = f" {unit}" if unit and not unit[0].isdigit() else ""  # skip units like '0-1'
    digits = 2 if abs(value) >= 0.1 else 3
    if round(abs(value), digits) == 0:
        return "about average"
    side = "above" if value > 0 else "below"
    return f"{abs(value):.{digits}f}{unit_txt} {side} average"


def sonify(years, values, emergence_year=None, trend_line=None, noise_sigma=None):
    """
    Turn a yearly series into a short melody (WAV bytes).
    - one note per year, pitch follows the value (pentatonic, always pleasant)
    - notes outside the natural-variation band (more than 2 sigma from the start of the
      trend) are louder; notes inside it are softer
    - a bell rings on the emergence year
    """
    years = [int(y) for y in years]
    values = [float(v) for v in values]
    idx = value_to_note_index(values)
    outside = outside_band(values, trend_line, noise_sigma)
    note_len = int(SR * NOTE_DUR)

    notes = []
    for i, k in enumerate(idx):
        vol = 0.4
        if outside is not None:
            vol = 0.5 if outside[i] else 0.25
        notes.append(_tone(_midi_to_freq(PENTATONIC[k]), vol=vol))
    melody = np.concatenate(notes)

    bell = _bell()
    melody = np.concatenate([melody, np.zeros(len(bell))])  # room for the bell to ring out
    if emergence_year is not None and int(emergence_year) in years:
        start = years.index(int(emergence_year)) * note_len
        melody[start:start + len(bell)] += bell

    return _to_wav_bytes(melody)


def listening_guide(years, emergence_year=None, has_band=True):
    """Short 'how to listen' text, meant to be read BEFORE pressing play."""
    years = [int(y) for y in years]
    seconds = round(len(years) * NOTE_DUR + BELL_DUR)
    text = (f"How to listen: press play to hear one note for each year from {years[0]} to "
            f"{years[-1]}, about {seconds} seconds in total. Higher notes mean higher values.")
    if has_band:
        text += (" Soft notes are years inside normal year-to-year variation; "
                 "louder notes are years outside it.")
    if emergence_year is not None and int(emergence_year) in years:
        text += " A high bell rings in the year the change stood out."
    return text


def describe_sound(years, values, emergence_year=None, trend_line=None, noise_sigma=None,
                   unit=""):
    """A text description of the melody, for screen readers and anyone who can't listen."""
    years = [int(y) for y in years]
    values = [float(v) for v in values]
    idx = value_to_note_index(values)
    third = max(1, len(idx) // 3)
    start, end = idx[:third].mean(), idx[-third:].mean()
    if end - start > 1.5:
        shape = "The melody climbs from low notes to high notes, because the values rise over time."
    elif start - end > 1.5:
        shape = "The melody falls from high notes to low notes, because the values drop over time."
    else:
        shape = ("The melody moves up and down without a clear direction, because there is no "
                 "clear long-term change.")
    text = f"{len(years)} notes, one for each year from {years[0]} to {years[-1]}. {shape}"

    lo_i, hi_i = int(np.argmin(values)), int(np.argmax(values))
    if values[hi_i] > values[lo_i]:
        text += (f" The lowest note is {years[lo_i]} ({_amount(values[lo_i], unit)}) and the "
                 f"highest note is {years[hi_i]} ({_amount(values[hi_i], unit)}).")

    outside = outside_band(values, trend_line, noise_sigma)
    if outside is not None:
        loud_years = [y for y, o in zip(years, outside) if o]
        if not loud_years:
            text += (" All notes are soft, because every year stayed inside normal "
                     "year-to-year variation.")
        elif len(loud_years) == 1:
            text += (f" 1 of the {len(values)} notes is louder, because that year was outside "
                     f"normal year-to-year variation: {loud_years[0]}.")
        else:
            text += (f" {len(loud_years)} of the {len(values)} notes are louder, because those "
                     f"years were outside normal year-to-year variation: "
                     f"{_year_ranges(loud_years)}.")

    if emergence_year is not None and int(emergence_year) in years:
        text += (f" A bell rings in {emergence_year}, the year the change stood out from "
                 "normal year-to-year variation.")
    else:
        text += " No bell rings, because the change has not stood out from normal variation."
    return text
