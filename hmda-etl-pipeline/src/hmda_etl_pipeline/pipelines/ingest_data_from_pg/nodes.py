"""
Performs basic count integrity checks on LAR, TS, and Panel datasets 
from Postgres. This validation will run prior to further processing. 

Additionally, functions exist to facilitate writing LAR, TS, and Panel
data to parquet files. TS and Panel are written to individual parquet 
files whereas LAR is partitioned due to data volume. Modified LAR is 
handled within the `data_publisher` pipeline.
"""

import logging
import os
from typing import Callable, Dict

import numpy as np
import pandas as pd
from pandas.io.parsers import TextFileReader

logger = logging.getLogger(__name__)


def validate_counts(
    lar_counts_by_lei: pd.DataFrame, ts: pd.DataFrame, institutions: pd.DataFrame
) -> bool:
    """Performs basic count integrity checks on LAR, TS, and Panel
    datasets from Postgres. The record count in LAR must align with
    the total_lines field within TS for the corresponding LEI, and each
    LEI in LAR must exist within the Institutions table for the
    corresponding year.

    Args:
        lar_counts_by_lei (pd.DataFrame): Table containing lei and row
            counts within the given LAR YYYY table.
        ts (pd.DataFrame): Copy of the TS table from Postgres for the
            corresponding year.
        institutions (pd.DataFrame): Copy of the Institutions table from
            Postgres for the corresponding year.

    Raises:
        RuntimeError: If either check fails. LAR and TS row counts are
            checked first and then Panel is checked for presence of
            each LEI in the LAR table. Check 2 will not run if check
            1 fails.

    Returns:
        bool: This will be supplied to the function that writes the raw
            LAR data to CSV files. Passing this boolean as an input
            ensures Kedro will perform validation on the data prior to
            running further processing on the data.
    """

    # join lar_counts_by_lei and the "total_lines" column in ts
    # this new table will have columns lei, count, and total_lines
    joined = pd.merge(lar_counts_by_lei, ts, on="lei", how="outer")

    # Get all rows that have different counts and convert to a list of dicts
    all_differences = joined[joined["count"] != joined["total_lines"]]

    # Throw an error if there are any differences
    if not all_differences.empty:

        # Convert differences to a list of dicts
        differences = all_differences[["lei", "submission_id", "total_lines", "count"]]
        differences.rename(
            columns={"total_lines": "count_from_ts", "count": "count_from_lar"},
            inplace=True,
        )
        differences_list_of_dicts = differences.to_dict("records")

        # Create error message
        msg = "Some of the LEIs has different counts of records in Transmittal Sheet table and in LAR table."
        for row in differences_list_of_dicts:
            msg += f"\n" + str(row)

        raise RuntimeError(msg)

    # now verify that each lei in the lar table has a corresonding
    # entry in institutions (Panel)
    leis_in_lar = lar_counts_by_lei.lei.values
    leis_in_institutions = institutions.lei.values

    # here setdiff1d finds all records in leis_in_lar that are not in
    # leis_in_institutions. This must be empty
    missing_leis = np.setdiff1d(leis_in_lar, leis_in_institutions)
    if missing_leis.size != 0:
        raise RuntimeError(
            f"LEIs not found in Panel. Number missing: {missing_leis.size}"
        )

    logger.info("Preliminary count validation successful.")
    return True


########################################################################################
# These values are referenced and updated by the LAR processing
# functions below and are used to provide logging messages.

# this value is updated with each call to _process_lar_partition and
# facilitates logging processing status.
partition_counter = 1

# this value is set by process_lar_partitions and is used to track the
# total number of partitions requiring processing
n_partitions_to_process = None
########################################################################################


def _process_lar_partition(
    lar_df: pd.DataFrame,
    dtypes: Dict[str, str],
) -> pd.DataFrame:
    """Performs type conversion on the raw Postgres LAR data to optimal
    Pandas nullable datatypes. By default, Pandas will treat integer
    columns will nulls as float64 whereas a nullable type such as Int8
    may be more optimal. These data types are loaded from
    conf/parameters/ingest_data_from_pg.yaml.

    In addition to type conversion, column name typos are fixed and
    application_date and action_taken_date are cast to date objects.

    Args:
        lar_df (pd.DataFrame): Chunk of lar data from Postgres
        dtypes (Dict[str, str]): Mapping of column names to dtype

    Returns:
        pd.DataFrame: A typed dataframe containing raw LAR data.
    """

    global partition_counter
    logger.info(
        f"processing LAR partition {partition_counter}/{n_partitions_to_process}"
    )
    partition_counter += 1

    # perform type conversion on the columns
    # NA and blank strings in numerical columns are converted to Nulls
    # prior to casting. This does not impact columns that are kept as
    # strings (street, city, state, etc.).
    for column, dtype in dtypes.items():
        logger.debug(f"Converting column {column} to datatype {dtype}.")

        if dtype == "str":
            lar_df[column] = lar_df[column].astype(str)
        else:
            lar_df[column] = (
                lar_df[column]
                .replace(to_replace=["", "NA", "nA", "Na", "na"], value=np.nan)
                .astype(dtype)
            )

    # there are multiple columns that have typos
    typos_to_fix = {
        "debt_to_incode": "debt_to_income",
        "baloon_payment": "balloon_payment",
        "insert_only_payment": "interest_only_payment",
        "lan_property_interest": "land_property_interest",
        "total_uits": "total_units",
    }

    lar_df = lar_df.rename(columns=typos_to_fix)

    # cast the date columns to datetimes. Invalid dates are cast
    # to NaT values
    lar_df["application_date"] = pd.to_datetime(
        lar_df.application_date, format="%Y%m%d", errors="coerce"
    )

    lar_df["action_taken_date"] = pd.to_datetime(
        lar_df.action_taken_date, format="%Y%m%d", errors="coerce"
    )

    return lar_df


def process_lar_partitions(
    pg_lar_data: TextFileReader,
    lar_row_counts_by_lei: pd.DataFrame,
    column_dtypes: Dict[str, str],
    count_verification_passed: bool,
) -> Dict[str, Callable[[], pd.DataFrame]]:
    """Facilitates the partitioning of Postgres LAR data to typed
    parquet files. This function defers processing of LAR partitions to
    the function _process_lar_partition.

    The pg_lar_data generator contains an unknown number of elements. In
    order to calculate the number of partitions, the first partition is
    loaded and the number of partitions is calculated at run time. This
    is done by calculating the total number of rows in the given LAR
    table via lar_row_counts_by_lei, and then dividing by the number of
    rows within the first partition. The output dictionary has this
    number of keys (rounded up to the next integer).

    The input count_verification_passed is not used within this
    function. It exists because it is supplied by the count verification
    pipeline which ensures the row counts within lar, ts, and panel all
    look good. Passing the input to this pipeline is the only way to
    ensure Kedro runs these pipelines in the appropriate order. Do not
    remove due to linting failure.

    Args:
        pg_lar_data (TextFileReader): Raw, chunked lar data from
            production Postgres. This iterable loads data lazily via
            repeated calls to next().
        lar_row_counts_by_lei (pd.DataFrame): A dataframe specifying the
            number of LAR records associated with each LEI. This serves
            double duty. Here we use it to calculate the number of rows
            within the given LAR table. It also serves the purpose of
            initial validation on LAR and TS data counts.
        column_dtypes (Dict[str,str]): This is a mapping of column name
            to Pandas datatypes. This is supplied by Kedro and is read
            from the data in parameters.ingest_data_from_pg.yaml.
        count_verification_passed (bool): This will take the value
            of True and is supplied by the initial_validation pipeline.
            It is supplied as an input to this method to ensure Kedro
            runs the count validation prior to data processing.

    Returns:
        Dict[str, Callable[[], pd.DataFrame]]: A mapping of partition
            names of the form lar_{partition_index} to lambda functions
            calling for the processing of the next data partition. Kedro
            refers to this as lazy loading.
    """

    # this function sets this global value. Used to facilitate logging
    # in a deferred execution context.
    global n_partitions_to_process

    # Total row count computed from LAR count per LEI
    n_rows = lar_row_counts_by_lei["count"].sum()

    # Determine the number of rows per partition, and total number of
    # partitions using the first sample of data. Using round() resulted
    # in unpredictable behavior because it rounds to the nearest int.
    # A fractional partition is an additional partition. Round up!
    partition_0 = next(pg_lar_data)
    n_partitions_to_process = np.ceil(n_rows / partition_0.shape[0]).astype(int)

    partition_holder = {
        "lar_0": lambda: _process_lar_partition(
            lar_df=partition_0, dtypes=column_dtypes
        )
    }

    if n_partitions_to_process == 1:
        # this should only occur at the very beginning of filing season
        logger.warning("Only a single LAR partition is being processed")
        return partition_holder
    else:
        for partition_index in range(1, n_partitions_to_process):
            partition_holder[f"lar_{partition_index}"] = lambda: _process_lar_partition(
                lar_df=next(pg_lar_data),
                dtypes=column_dtypes,
            )

        return partition_holder


def persist_ts_table(
    ts_df: pd.DataFrame,
    column_dtypes: Dict[str, str],
    count_verification_passed: bool,
) -> pd.DataFrame:
    """Type and persist transmittal sheet dataframe to Parquet analog.
    The sign_date field is converted to a datetime object rather than a
    unix timestamp.

    The input count_verification_passed is not used within this
    function. It exists because it is supplied by the count verification
    pipeline which ensures the row counts within lar, ts, and panel all
    look good. Passing the input to this pipeline is the only way to
    ensure Kedro runs these pipelines in the appropriate order. Do not
    remove due to linting failure.

    Args:
        ts_df (pd.DataFrame): A dataframe resulting from reading
            transmittalsheetYYYY table in production Postgres.
        column_dtypes (Dict[str,str]): This is a mapping of column name
            to Pandas datatypes. This is supplied by Kedro and is read
            from the data in parameters.ingest_data_from_pg.yaml.
        count_verification_passed (bool): This will take the value
            of True and is supplied by the initial_validation pipeline.
            It is supplied as an input to this method to ensure Kedro
            runs the count validation prior to data processing.


    Returns:
        pd.DataFrame: Typed version of ts_df.
    """

    ts_df = ts_df.astype(column_dtypes)

    ts_df["sign_date"] = pd.to_datetime(ts_df.sign_date, unit="ms")

    return ts_df


def persist_institutions_email_domains_table(
    email_domains_df: pd.DataFrame,
    column_dtypes: Dict[str, str],
) -> pd.DataFrame:
    """Type and persist email domains dataframe to parquet analog.

    Args:
        email_domains_df (pd.DataFrame): A dataframe resulting from
            reading institutions_emails_2018 table in production Postgres.
        column_dtypes (Dict[str, str]): This is a mapping of column name
            to Pandas datatypes. This is supplied by Kedro and is read
            from the data in parameters.ingest_data_from_pg.yaml.

    Returns:
        pd.DataFrame: Typed version of email_domains_df.
    """

    typed_email_table = email_domains_df.astype(column_dtypes)

    return typed_email_table


def persist_institutions_table(
    institutions_df: pd.DataFrame,
    column_dtypes: Dict[str, str],
    count_verification_passed: bool,
) -> pd.DataFrame:
    """Type and persist institutions dataframe to parquet analog.

    The input count_verification_passed is not used within this
    function. It exists because it is supplied by the count verification
    pipeline which ensures the row counts within lar, ts, and panel all
    look good. Passing the input to this pipeline is the only way to
    ensure Kedro runs these pipelines in the appropriate order. Do not
    remove due to linting failure.

    Args:
        institutions_df (pd.DataFrame): A dataframe resulting from
            reading institutionsYYY table in production Postgres.
        column_dtypes (Dict[str, str]): This is a mapping of column name
            to Pandas datatypes. This is supplied by Kedro and is read
            from the data in parameters.ingest_data_from_pg.yaml.
        count_verification_passed (bool): This will take the value
            of True and is supplied by the initial_validation pipeline.
            It is supplied as an input to this method to ensure Kedro
            runs the count validation prior to data processing.

    Returns:
        pd.DataFrame: Typed version of institutions_df.
    """

    return institutions_df.astype(column_dtypes)


def get_state_county_code_mapping(
    state_county_df: pd.DataFrame, column_dtypes: Dict[str, str]
) -> pd.DataFrame:
    """Returns a dataframe that can be used to map state and county codes
    to state and county names.

    Args:
        cbsa_county_name_df (pd.DataFrame): Dataframe containing data from
        the state and coutny csv file

    Returns:
        pd.DataFrame: A single dataframe that can be used to map state and
        county codes to state and county names.
    """

    # Rename columns
    state_county_df = state_county_df.rename(
        columns={
            "County/County Equivalent": "county_name",
            "State Name": "state_name",
            "FIPS State Code": "state_code",
            "FIPS County Code": "county_code",
        }
    )

    # Select relevant columns to retain
    columns_list = ["county_name", "state_name", "state_code", "county_code"]
    state_county_df = (
        state_county_df.groupby(columns_list, as_index=False)
        .nth(0)
        .loc[:, columns_list]
    )

    # Make codes into ints
    state_county_df = state_county_df.astype(column_dtypes)

    return state_county_df
