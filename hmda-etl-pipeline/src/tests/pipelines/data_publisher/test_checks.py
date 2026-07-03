"""
Verify the high/low value checks handle non-numeric keyword cells
(for example "Exempt") without raising a TypeError.
"""

import pandas as pd

from hmda_etl_pipeline.pipelines.data_publisher.checks import (
    check_high_values,
    check_low_values,
)


def make_mlar_df():
    """A small MLAR frame whose origination_charges column mixes numeric
    strings with the "Exempt" keyword, as happens on real HMDA data.
    """
    df = pd.DataFrame(
        {
            "lei": ["a", "b", "c"],
            "origination_charges": ["100", "Exempt", "9999"],
        }
    )
    df["Analysis"] = ""
    return df


PARAMS = {"check_vars": {"default": {"high_value": 9000, "low_value": 10}}}


def test_check_high_values_skips_keyword_cells():
    df = make_mlar_df()
    check_high_values(df, PARAMS, 2023, "origination_charges")
    # Only the 9999 row is a high outlier; "Exempt" and "100" stay untouched.
    assert list(df["Analysis"]) == ["", "", "002H"]


def test_check_low_values_skips_keyword_cells():
    df = make_mlar_df()
    check_low_values(df, PARAMS, 2023, "origination_charges")
    # Nothing is below the low threshold of 10, and "Exempt" is ignored.
    assert list(df["Analysis"]) == ["", "", ""]
