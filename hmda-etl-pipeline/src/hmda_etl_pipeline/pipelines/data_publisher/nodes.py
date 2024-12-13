"""
Processing related to publication of public and regulator datasets. These 
include the LAR, LAR loan limit, MLAR, Panel, and TS files (including public, 
regulator, yearly, and quarterly versions). 
"""

import logging
from functools import reduce
from operator import concat
from typing import Callable, Dict, List, Tuple

import pandas as pd

from .checks import *
from .lar_to_mlar_conversion_functions import (
    convert_age,
    convert_debt_to_income_ratio,
    convert_multifamily_affordable_units,
    convert_property_value,
    convert_total_units,
    is_age_greater_than_62,
    round_to_midpoint,
)

logger = logging.getLogger(__name__)


def create_lar_flat_file(
    data_partitions: Dict[str, Callable], columns_to_retain: List[str]
) -> Tuple[pd.DataFrame, int]:
    """Concatenates the raw LAR parquet data into a single dataframe.
    Only those columns listed under the given columns list found in
    data_publisher.yml are retained. The other columns are not included
    within the published LAR dataset.

    Returns both the concatenated dataframe and the number of rows to
    facilitate row count validation between LAR and MLAR flat files.

    Args:
        data_partitions (Dict[str, Callable]): data partitions generated
            from Kedro reading the parquet partitions of raw LAR data.
        columns_to_retain (List[str]): The list of columns that should
            be retained. Needs to be flattened in the case of LAR loan limit,
            which is [List[List[str]]].

    Returns:
        Tuple[pd.DataFrame, int]: A tuple containing a single dataframe
            representing the LAR dataset (ready for publication), and
            the number of rows in the dataset.
    """

    partition_holder = []

    # Flatten the list of columns to retain if needed
    if type(columns_to_retain[0]) is list:
        columns_to_retain = reduce(concat, columns_to_retain)

    # data_loader is a callable which triggers the .load() method
    # on the underlying data.
    logger.info(f"Number of LAR partitions: {len(data_partitions)}")
    for data_loader in data_partitions.values():
        partition_holder.append(data_loader().loc[:, columns_to_retain])

    concatenated = pd.concat(partition_holder, ignore_index=True)

    logger.info(f"Shape of LAR flat file: {concatenated.shape}")

    return concatenated


def create_mlar_flat_file(
    data_partitions: Dict[str, Callable]
) -> Tuple[pd.DataFrame, int]:
    """Concatenates the raw MLAR parquet data into a single dataframe.
    Only those columns listed under the given columns list found in
    data_publisher.yml are retained. The other columns are not included
    within the published MLAR dataset.

    The `income` field is modified to handle blanks consistently with
    legacy MLAR. All other fields are using blank strings, but this
    field uses `NA` for some reason.

    Returns both the concatenated dataframe and the number of rows to
    facilitate row count validation between LAR and MLAR flat files.

    Args:
        data_partitions (Dict[str, Callable]): data partitions generated
            from Kedro reading the parquet partitions of raw MLAR data.

    Returns:
        Tuple[pd.DataFrame, pd.DataFrame, int]: A tuple containing dataframes
            representing the MLAR dataset (ready for publication) to be
            saved in the public and archive public paths and the number
            of rows in the dataset.
    """

    partition_holder = []

    # data_loader is a callable which triggers the .load() method
    # on the underlying data.
    for partition_name, data_loader in data_partitions.items():
        partition_holder.append(data_loader())
        logger.info(f"Loaded {partition_name} with shape {partition_holder[-1].shape}.")

    flat_mlar = pd.concat(partition_holder, ignore_index=True)

    flat_mlar["income"] = flat_mlar.income.astype(str).replace("<NA>", "NA")

    logger.info(f"Shape of MLAR flat file: {flat_mlar.shape}")

    # Return flat_mlar twice so it can be saved in public and public archive paths
    return flat_mlar, flat_mlar


def analyze_mlar_flat_file(
    mlar_df: pd.DataFrame, params: Dict, year: int = 0
) -> pd.DataFrame:
    mlar_df["Analysis"] = ""
    check_config = params["checks"]
    for col in check_config.keys():
        for check in check_config[col]:
            globals()[check](mlar_df, params, year, col)
    return mlar_df


def _process_modified_lar_partition(
    lar_df: pd.DataFrame,
    mlar_legacy_column_names_map_list: List[Dict[str, str]],
) -> pd.DataFrame:
    """Converts LAR data into MLAR data by dropping, renaming, and
    transforming several columns. This function is a bit bloated, but it
    is broken into numerous independent steps so it should be easy
    enough to follow.

    Args:
        lar_df (pd.DataFrame): Chunk of lar data from Postgres
        mlar_legacy_column_names_map_list (List[Dict[str,str]]): A list
            of mappings of MLAR column names used here and the legacy
            column names used by MLAR data created by the data publisher
            service.

    Returns:
        pd.DataFrame: A single processed partition of modified LAR.
    """

    mlar_df = lar_df.copy()

    # Add year column
    mlar_df.insert(0, "year", mlar_df["action_taken_date"].dt.year)

    # Convert ages to string age ranges
    mlar_df["age_greater_than_or_equal_62"] = mlar_df["age_applicant"].transform(
        is_age_greater_than_62
    )
    mlar_df["age_co_greater_than_or_equal_62"] = mlar_df["age_co_applicant"].transform(
        is_age_greater_than_62
    )
    mlar_df["age_applicant"] = mlar_df["age_applicant"].transform(convert_age)
    mlar_df["age_co_applicant"] = mlar_df["age_co_applicant"].transform(convert_age)

    # match data types present in the legacy modified LAR dataset
    # income is set to Int32 within the parquet file to allow this field
    # to be blank.
    mlar_df["income"] = mlar_df["income"].astype("Int32")

    # Adjust columns which exist in public MLAR but not combined MLAR
    if set(["credit_score_type_applicant", "credit_score_type_co_applicant"]).issubset(
        mlar_df.columns
    ):
        mlar_df["credit_score_type_applicant"] = mlar_df[
            "credit_score_type_applicant"
        ].astype(int)
        mlar_df["credit_score_type_co_applicant"] = mlar_df[
            "credit_score_type_co_applicant"
        ].astype(int)

    # no idea who came up with this name :)
    # this needs to run before the conversion of total_units.
    # later renamed to multifamily_affordable_units
    mlar_df["mf_affordable"] = mlar_df.apply(
        lambda x: convert_multifamily_affordable_units(
            x["mf_affordable"], x["total_units"]
        ),
        axis=1,
    )

    # Other conversions
    for column, transform in (
        ("loan_amount", round_to_midpoint),
        ("debt_to_income", convert_debt_to_income_ratio),
        ("property_value", convert_property_value),
        ("total_units", convert_total_units),
    ):
        mlar_df[column] = mlar_df[column].transform(transform)

    # Rename columns to match legacy MLAR data column names
    # This dictionary comprehension is flattening the list of column
    # name maps to a single level dictionary
    mlar_legacy_column_names_map = {
        k: v for d in mlar_legacy_column_names_map_list for k, v in d.items()
    }
    mlar_df.rename(columns=mlar_legacy_column_names_map, inplace=True)

    # Drop unneeded LAR columns from MLAR data
    # only retain those column listed within the name map. Each name map
    # pair is iterated over and only the value is retained. These values
    # are extracted from the raw list to ensure consistent ordering.
    columns_to_retain = [
        v for d in mlar_legacy_column_names_map_list for v in d.values()
    ]

    return mlar_df.loc[:, columns_to_retain]


def convert_lar_to_modified_lar_data(
    lar_partitions: Dict[str, Callable],
    mlar_legacy_column_names_map_list: List[Dict[str, str]],
) -> Dict[str, Callable[[], pd.DataFrame]]:
    """Create analog MLAR dataframes for each partition of LAR data.
    This is accomplished by iterating over each chunk of regulator LAR
    data and processing the partition via _process_modified_lar_partition.

    Args:
        lar_partitions (Dict[str, Callable]): LAR partitions generated
            from Kedro reading the parquet partitions of raw LAR.
        mlar_legacy_column_names_map_list (List[Dict[str,str]]): A list
            of mappings of MLAR column names used here and the legacy
            column names used by MLAR data created by the data publisher
            service.

    Returns:
        Dict[str, pd.DataFrame]: This is a dictionary mapping the name
            of the MLAR file partition a Pandas dataframe processed by
            _process_modified_lar_partition.
    """

    # useful for logging
    n_partitions = len(list(lar_partitions.keys()))

    # populated and returned
    partition_holder = {}

    # data_loader is a callable which triggers the .load() method
    # on the underlying data. Data is loaded and processed eagerly
    for partition_index, (lar_partition_name, data_loader) in enumerate(
        lar_partitions.items()
    ):
        logger.info(f"Processing MLAR partition {partition_index + 1}/{n_partitions}")

        # the keys are the names of the modified lar parquet files less
        # the suffix. Prefixing the lar partition with modified ensures
        # that modified_lar_N aligns with lar_N. Makes debugging easier
        partition_holder[f"modified_{lar_partition_name}"] = (
            _process_modified_lar_partition(
                data_loader(), mlar_legacy_column_names_map_list
            )
        )
    return partition_holder


def create_institutions_flat_file(
    institutions_df: pd.DataFrame,
    email_domains_df: pd.DataFrame,
    ts_df: pd.DataFrame,
    columns_to_retain: List[str],
) -> pd.DataFrame:
    """Returns a subset of columns for regulator institutions data given
    institutions, email domain, and ts parquet data. Only those columns
    listed under the given columns list found in data_publisher.yml are
    retained.

    Args:
        institutions_df (pd.DataFrame): raw institutions data.
        email_domains_df (pd.DataFrame): raw institutions email domains data.
        ts_df (pd.DataFrame): raw TS data. Used to filter out leis from
            non-hmda filers and test banks.
        columns_to_retain (List[str]): The list of columns that should
            be retained.
    Returns:
        pd.DataFrame: A single dataframe representing the regulator
        institutions dataset.
    """

    # Clean up email domains into several rows of single unique email domains per lei
    email_domains_df = cleanup_email_domains_table(email_domains_df)

    # Filter institution leis using the TS file
    institutions_filtered_df = institutions_df[
        institutions_df["lei"].isin(ts_df["lei"].tolist())
    ]

    # Merge email domains and institution tables
    institutions_and_emails_df = institutions_filtered_df.merge(
        email_domains_df, on="lei", how="left"
    )

    # Drop unneeded columns from institutions data
    institutions_and_emails_df_subset = institutions_and_emails_df.loc[
        :, columns_to_retain
    ]

    logger.info(
        f"Shape of institutions file: {institutions_and_emails_df_subset.shape}"
    )

    return institutions_and_emails_df_subset


def cleanup_email_domains_table(email_domains_df: pd.DataFrame) -> pd.DataFrame:
    """Cleans up the email domains dataframe of duplicate data and
    consolidates all distinct email domains into a list

    Args:
        email_domains_df (pd.DataFrame): raw institutions email domains data.

    Returns:
        pd.DataFrame: The cleaned up dataframe of email domains per lei
    """

    # Drop unused id column. This is also needed to avoid duplicate email
    # domains because later we only want to keep distinct rows based on
    # email domains per lei and distinct ids don't matter.
    email_domains_df = email_domains_df.drop("id", axis=1)

    # Clean up extra whitesace and split into rows of distinct email domains per lei
    email_domains_df["email_domain"] = email_domains_df["email_domain"].apply(
        lambda x: x.replace(" ", "").split(",")
    )
    email_domains_distinct_df = email_domains_df.explode(
        "email_domain"
    ).drop_duplicates()

    # Combine into a list of email domains per lei
    email_domains_combined_df = email_domains_distinct_df.groupby(
        ["lei"], as_index=False
    ).agg(", ".join)

    return email_domains_combined_df


def create_regulator_ts_flat_file(
    ts_df: pd.DataFrame, columns_to_retain: List[str]
) -> pd.DataFrame:
    """Returns a subset of columns for regulator TS data given TS
    parquet data. Only those columns listed under the given columns list
    found in data_publisher.yml are retained.

    Args:
        ts_df (pd.DataFrame): raw TS data.
        columns_to_retain (List[str]): The list of columns that should
            be retained.

    Returns:
        pd.DataFrame: A single dataframe representing the regulator TS
        dataset.
    """

    ts_df_subset = ts_df.loc[:, columns_to_retain]

    # Adjust the format on the sign_date field to match legacy data
    ts_df_subset["sign_date"] = (
        ts_df_subset["sign_date"]
        .dt.strftime("%Y-%m-%dT%H:%M:%S.%f")  # Format with T separator
        .str[:-3]  # Remove nanoseconds
    )

    logger.info(f"Shape of TS file: {ts_df_subset.shape}")

    return ts_df_subset


def create_public_ts_flat_file(
    ts_df: pd.DataFrame,
    public_ts_legacy_column_names_map_list: List[Dict[str, str]],
) -> pd.DataFrame:
    """Returns a subset of columns for public TS data given TS parquet
    data. Only those columns listed under the given columns list found
    in data_publisher.yml are retained.

    Args:
        ts_df (pd.DataFrame): raw TS data.
        public_ts_legacy_column_names_map_list (List[Dict[str,str]]): A
            list of mappings of public TS column names used here and the
            legacy column names used by existing public TS data.

    Returns:
        Tuple[pd.DataFrame, pd.DataFrame]: A tuple containing dataframes
            representing the public TS dataset to be saved in the public
            and archive public paths.
    """

    # Rename columns to match legacy public TS column names
    # This dictionary comprehension is flattening the list of column
    # name maps to a single level dictionary
    ts_legacy_column_names_map = {
        k: v for d in public_ts_legacy_column_names_map_list for k, v in d.items()
    }
    ts_df.rename(columns=ts_legacy_column_names_map, inplace=True)

    # Drop unneeded columns from public TS data
    # only retain those column listed within the name map. Each name map
    # pair is iterated over and only the value is retained. These values
    # are extracted from the raw list to ensure consistent ordering.
    columns_to_retain = [
        v for d in public_ts_legacy_column_names_map_list for v in d.values()
    ]

    ts_df_subset = ts_df.loc[:, columns_to_retain]

    logger.info(f"Shape of public TS file: {ts_df_subset.shape}")

    return ts_df_subset, ts_df_subset
