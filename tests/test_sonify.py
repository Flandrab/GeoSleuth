import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.sonify import (NOTE_DUR, SR, _year_ranges, describe_sound, listening_guide,
                        outside_band, sonify, value_to_note_index)


def test_wav_header_and_length():
    years = list(range(2001, 2025))
    values = [0.1 * i for i in range(24)]
    wav = sonify(years, values)
    assert wav[:4] == b"RIFF"
    assert len(wav) > 2 * SR * NOTE_DUR * len(years)  # 16-bit samples, at least one note per year


def test_rising_values_give_rising_notes():
    idx = value_to_note_index([0, 1, 2, 3, 4])
    assert list(idx) == sorted(idx)
    assert idx[0] == 0 and idx[-1] == 9


def test_flat_values_do_not_crash():
    wav = sonify([2001, 2002, 2003], [1.0, 1.0, 1.0])
    assert wav[:4] == b"RIFF"
    text = describe_sound([2001, 2002, 2003], [1.0, 1.0, 1.0])
    assert "3 notes" in text


def test_description_mentions_bell_and_direction():
    years = list(range(2001, 2025))
    text = describe_sound(years, list(range(24)), emergence_year=2014)
    assert "climbs" in text
    assert "2014" in text


def test_description_counts_and_names_loud_years():
    years = [2001, 2002, 2003, 2004]
    values = [0.0, 0.1, 0.5, 1.0]
    trend = [0.0, 0.0, 0.0, 0.0]
    text = describe_sound(years, values, trend_line=trend, noise_sigma=0.1)
    assert "2 of the 4 notes are louder" in text
    assert "2003 to 2004" in text
    quiet = describe_sound(years, [0.0, 0.0, 0.1, 0.0], trend_line=trend, noise_sigma=0.1)
    assert "All notes are soft" in quiet
    one = describe_sound(years, [0.0, 0.0, 0.0, 1.0], trend_line=trend, noise_sigma=0.1)
    assert "1 of the 4 notes is louder, because that year was" in one


def test_description_gives_lowest_and_highest_values():
    text = describe_sound([2001, 2002, 2003], [-0.5, 0.2, 1.25], unit="°C")
    assert "lowest note is 2001 (0.50 °C below average)" in text
    assert "highest note is 2003 (1.25 °C above average)" in text
    assert "No bell rings" in text


def test_outside_band_matches_loud_rule():
    assert outside_band([0.0, 0.3], [0.0, 0.0], 0.1) == [False, True]
    assert outside_band([0.0, 0.3]) is None


def test_year_ranges_read_naturally():
    assert _year_ranges([2007, 2008, 2012, 2013, 2014, 2020]) == "2007 to 2008, 2012 to 2014 and 2020"
    assert _year_ranges([2010]) == "2010"


def test_listening_guide():
    years = list(range(2001, 2025))
    guide = listening_guide(years, emergence_year=2014)
    assert "2001 to 2024" in guide
    assert "bell" in guide
    assert "bell" not in listening_guide(years, emergence_year=None)
