
import pandas as pd
from typing import Any, Callable, Dict, List


def add_markers(mlar_df: pd.DataFrame, col: str, test: Callable, m: str) -> None:
    colnum = f"{list(mlar_df.columns).index(col) + 1:03d}"
    mlar_df["Analysis"] += mlar_df.apply(lambda row: "" if not test(row, col)
                                         else m if colnum in row.Analysis else colnum+m, axis=1)
    

def get_var(params: Dict, col: str, v: str) -> Any:
    return params["check_vars"].get(col)[v] if params["check_vars"].get(col)\
        else params["check_vars"]["default"][v]


def check_invalidity(mlar_df: pd.DataFrame, params: Dict, year: int, col: str) -> None:
    col_valid_vals = params["valid_values"][col]
    check_valid_vals = col_valid_vals.get(year) if col_valid_vals.get(year)\
        else col_valid_vals.get("default")
    def invalid(row: pd.Series, col: str) -> bool: return row[col] not in check_valid_vals
    add_markers(mlar_df, col, invalid, "X")


def check_high_values(mlar_df: pd.DataFrame, params: Dict, year: int, col: str) -> None:
    def high_value(row: pd.Series, col: str) -> bool:
        return row[col] >= get_var(params, col, "high_value")
    add_markers(mlar_df, col, high_value, "H")


def check_low_values(mlar_df: pd.DataFrame, params: Dict, year: int, col: str) -> None:
    def low_value(row: pd.Series, col: str) -> bool:
        return row[col] <= get_var(params, col, "low_value")
    add_markers(mlar_df, col, low_value, "L")


def check_lender_nulls(mlar_df: pd.DataFrame, params: Dict, year: int, col: str) -> None:
    lender_null_pcts = 1 - mlar_df.groupby("lei")[col].count()/mlar_df.groupby("lei")["lei"].count()
    def lender_null(row: pd.Series, col: str) -> bool:
        return pd.isna(row[col]) and (lender_null_pcts[row["lei"]] >=
                                      get_var(params, col, "lender_null_factor"))
    add_markers(mlar_df, col, lender_null, "n")


def check_year_nulls(mlar_df: pd.DataFrame, params: Dict, year: int, col: str) -> None:
    year_null_pct = 1 - mlar_df[col].count() / mlar_df["lei"].count()
    def year_null(row: pd.Series, col: str) -> bool:
        return pd.isna(row[col]) and (year_null_pct >= get_var(params, col, "year_null_factor"))
    add_markers(mlar_df, col, year_null, "N")


def check_lender_outliers(mlar_df: pd.DataFrame, params: Dict, year: int, col: str) -> None:
    lender_vals = mlar_df.groupby("lei")[col]
    def lender_outlier(row: pd.Series, col: str) -> bool:
        return (abs(lender_vals.mean()[row["lei"]] - row[col]) >
                get_var(params, col, "lender_outlier_factor") * lender_vals.std()[row["lei"]])
    add_markers(mlar_df, col, lender_outlier, "o")


def check_year_outliers(mlar_df: pd.DataFrame, params: Dict, year: int, col: str) -> None:
    def year_outlier(row: pd.Series, col: str) -> bool:
        return (abs(mlar_df[col].mean() - row[col]) >
                get_var(params, col, "year_outlier_factor") * mlar_df[col].std())
    add_markers(mlar_df, col, year_outlier, "O")


def column_value_buckets(df: pd.DataFrame, col: str) -> pd.Series:
    val_range = df[col].max() - df[col].min() if df[col].max() - df[col].min() > 0 else 100
    return pd.Series((df[col] - df[col].min()) / (val_range / 100)).astype(int)


def repeater_buckets(buckets: pd.Series, params: Dict, col: str, repeat_factor: str) -> List:
    bucket_counts = dict(buckets.groupby(buckets).count())
    high_repeat_count = int(max(get_var(params, col, repeat_factor) * len(buckets), 2))
    return [b for b, c in bucket_counts.items() if c >= high_repeat_count]


def check_lender_repeaters(mlar_df: pd.DataFrame, params: Dict, year: int, col: str) -> None:
    lender_buckets, lender_repeater_buckets = {}, {}
    for lei in mlar_df["lei"].unique():
        lender_df = mlar_df[mlar_df["lei"] == lei]
        lender_buckets[lei] = column_value_buckets(lender_df, col)
        lender_repeater_buckets[lei] = repeater_buckets(lender_buckets[lei], params,
                                                        col, "lender_repeat_factor")
    def lender_repeater(row: pd.Series, col: str) -> bool:
        return lender_buckets[row.lei][row.name] in lender_repeater_buckets[row.lei]
    add_markers(mlar_df, col, lender_repeater, "r")


def check_year_repeaters(mlar_df: pd.DataFrame, params: Dict, year: int, col: str) -> None:
    year_buckets = column_value_buckets(mlar_df, col)
    year_repeater_buckets = repeater_buckets(year_buckets, params, col, "year_repeat_factor")
    def year_repeater(row: pd.Series, col: str) -> bool:
        return year_buckets[row.name] in year_repeater_buckets
    add_markers(mlar_df, col, year_repeater, "R")
