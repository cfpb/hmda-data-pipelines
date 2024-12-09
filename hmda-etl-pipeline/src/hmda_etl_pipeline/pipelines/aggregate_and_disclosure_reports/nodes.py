"""
Processing related to disclosure reports
"""

import s3fs
import logging
from typing import List

import pandas as pd

from .aggregate_report_table_processing import (
    create_aggregate_report_1,
    create_aggregate_report_2,
    create_aggregate_report_3,
    create_aggregate_report_4,
    create_aggregate_report_5,
    create_aggregate_report_9,
    create_aggregate_report_i,
)
from .constants import NA_LIST
from .disclosure_report_table_processing import (
    create_disclosure_report_1,
    create_disclosure_report_2,
)
from .income_race_ethnicity_processing import output_collection_table_income
from .median_age_processing import median_age_output_collection_table
from .race_gender_processing import output_collection_table_3_and_4
from .reports_base_processing import (
    output_collection_table_1,
    output_collection_table_2,
)
from ..data_publisher.lar_to_mlar_conversion_functions import (
    income_categorization,
    median_age_calculated,
    round_to_midpoint,
)


logger = logging.getLogger(__name__)


def create_aggregate_reports(
    report_year: int,
    institutions_df: pd.DataFrame,
    institutions_columns: List[str],
    reduced_lar_df: pd.DataFrame,
    reduced_lar_columns: List[str],
    state_county_mapping_df: pd.DataFrame,
    aggregate_reports_path: str,
    use_lei_list: bool,
    exclude_lei_list_df: pd.DataFrame,
    use_msa_list: bool,
    msa_list_df: pd.DataFrame,
    skip_existing_reports: bool,
) -> pd.DataFrame:
    """Returns aggregate report tables in a partion holder so they
        can be saved into individual files.

    Args:
        report_year (int): Report year for generating the aggregate reports
        institutions_df (pd.DataFrame): Institutions data.
        institutions_columns (List[str]): The list of institution column names.
        reduced_lar_df (pd.DataFrame): Chunk of reduced lar data
            used to create aggregate reports.
        reduced_lar_columns (List[str]): The list of reduced lar column names.
        state_county_mapping_df (pd.DataFrame): State and county code lookup map.
        aggregate_reports_path (str): Path to save aggregate report files.
        use_lei_list (bool): If true, exclude a list of lei, otherwise run
            aggregate reports for all lei.
        lei_list_df (pd.DataFrame): The list of lei to run aggregate reports on.
        use_msa_list (bool): If true, run only on a list of msa, otherwise run
            aggregate reports for all msa.
        msa_list_df (pd.DataFrame): The list of msa to run aggregate reports on.
        skip_existing_reports (bool): If true, skip msa that already have reports generated.
            Note that this is not used if use_msa_list is True.

    Returns:
        A partion holder for aggregate tables for each msa_md for
        each lei.
    """

    # Set names on columns
    institutions_df.columns = institutions_columns
    reduced_lar_df.columns = reduced_lar_columns

    # Make msa_md a string
    reduced_lar_df["msa_md"] = reduced_lar_df["msa_md"].astype(str)

    # Merge institution and reduced lar tables
    aggregate_report_df = reduced_lar_df.merge(institutions_df, on="lei", how="left")

    if use_lei_list:
        # Generate aggregate reports excluding lei in lei_list
        lei_list = exclude_lei_list_df["lei"].tolist()
        logger.info(f"Generating aggregate reports excluding {lei_list}")
        aggregate_report_df = aggregate_report_df[
            ~aggregate_report_df["lei"].isin(lei_list)
        ]
    if use_msa_list:
        # Generate aggregate reports only for msa in msa_list
        msa_list_df["msa_md"] = msa_list_df["msa_md"].astype(str)
        msa_list = msa_list_df["msa_md"].tolist()
        logger.info(f"Generating aggregate reports for {msa_list}")
        aggregate_report_df = aggregate_report_df[
            aggregate_report_df["msa_md"].isin(msa_list)
        ]
    elif skip_existing_reports:
        logger.info(f"Checking S3 for existing aggregate report MSA folders to skip")
        # Remove msa that already have aggregate reports
        fs = s3fs.S3FileSystem()

        # Get all unique msa
        unique_msa = aggregate_report_df["msa_md"].unique()
        filtered_msa = filter(
            lambda x: reports_exist(x, aggregate_reports_path, fs), unique_msa
        )
        aggregate_report_df = aggregate_report_df[
            ~aggregate_report_df["msa_md"].isin(filtered_msa)
        ]

        # Count remaining msa now that some may have been skipped
        msa_count = len(aggregate_report_df["msa_md"].unique())

        if msa_count == 0:
            logger.info(f"Aggregate reports have already been generated for all MSA.")
        else:
            logger.info(f"Generating aggregate reports for remaining {msa_count} MSA")
    else:
        # Count all msa
        msa_count = len(aggregate_report_df["msa_md"].unique())
        logger.info(f"Generating aggregate reports for all {msa_count} MSA")

    # Rename columns
    aggregate_report_df = aggregate_report_df.rename(
        columns={
            "activity_year": "year",
            "respondent_name": "institution_name",
            "race_categorization": "race",
            "ethnicity_categorization": "ethnicity",
            "sex_categorization": "sex",
            "ffiec_msa_md_median_family_income": "ffiec_med_fam_income",
        }
    )

    # Filter the year
    aggregate_report_df = aggregate_report_df[
        aggregate_report_df["year"] == report_year
    ]

    # Fix loan amount to be the rounded mlar value instead of exact lar value
    aggregate_report_df["loan_amount"] = (
        aggregate_report_df["loan_amount"].apply(round_to_midpoint).astype(float)
    )

    # Get median_age_calculated
    aggregate_report_df["median_age_calculated"] = aggregate_report_df.apply(
        lambda x: median_age_calculated(
            x["year"], x["tract_median_age_of_housing_units"]
        ),
        axis=1,
    )

    # Get percent_median_msa_income
    aggregate_report_df["ffiec_med_fam_income"] = aggregate_report_df[
        "ffiec_med_fam_income"
    ].astype(int)
    aggregate_report_df["percent_median_msa_income"] = aggregate_report_df.apply(
        lambda x: income_categorization(x["income"], x["ffiec_med_fam_income"]),
        axis=1,
    )

    # Filter out NA values
    aggregate_report_df = aggregate_report_df[
        (aggregate_report_df["msa_md"] != "0")
        & (~aggregate_report_df["tract"].isin(NA_LIST))
    ]

    # Do pre-processing for each table and create reports
    report_year_str = str(report_year)
    reports_partition_holder = {}
    grouped_msa_df = aggregate_report_df.groupby("msa_md", as_index=False)
    for name, group in grouped_msa_df:
        logger.info(f"Processing data for reports for MSA {name}")

        # Create aggregate report table 1
        processed_table_1_df = output_collection_table_1(group)
        reports_partition_holder[f"{name}/1"] = (
            lambda input_df=processed_table_1_df: create_aggregate_report_1(
                report_year_str, input_df, state_county_mapping_df
            )
        )

        # Create aggregate report table 2
        processed_table_2_df = output_collection_table_2(group)
        reports_partition_holder[f"{name}/2"] = (
            lambda input_df=processed_table_2_df: create_aggregate_report_2(
                report_year_str, input_df, state_county_mapping_df
            )
        )

        # Create aggregate report table 3 and 4
        processed_table_3_and_4_df = output_collection_table_3_and_4(group)
        reports_partition_holder[f"{name}/3"] = (
            lambda input_df=processed_table_3_and_4_df: create_aggregate_report_3(
                report_year_str, input_df
            )
        )
        reports_partition_holder[f"{name}/4"] = (
            lambda input_df=processed_table_3_and_4_df: create_aggregate_report_4(
                report_year_str, input_df
            )
        )

        # Create aggregate report table 5
        processed_table_5_df = output_collection_table_income(group)
        reports_partition_holder[f"{name}/5"] = (
            lambda input_df=processed_table_5_df: create_aggregate_report_5(
                report_year_str, input_df
            )
        )

        # Create aggregate report table 9
        processed_table_9_df = median_age_output_collection_table(group)
        reports_partition_holder[f"{name}/9"] = (
            lambda input_df=processed_table_9_df: create_aggregate_report_9(
                report_year_str, input_df
            )
        )

        # Create aggregate report table i
        # Note there is no preprocessing required for table i
        reports_partition_holder[f"{name}/i"] = (
            lambda input_df=group: create_aggregate_report_i(report_year_str, input_df)
        )

    return reports_partition_holder


def create_disclosure_reports(
    report_year: int,
    institutions_df: pd.DataFrame,
    institutions_columns: List[str],
    reduced_lar_df: pd.DataFrame,
    reduced_lar_columns: List[str],
    state_county_mapping_df: pd.DataFrame,
    disclosure_reports_path: str,
    use_lei_list: bool,
    lei_list_df: pd.DataFrame,
    skip_existing_reports: bool,
) -> pd.DataFrame:
    """Returns disclosure report tables 1 and 2 in a partion holder so they
        can be saved into individual files.

    Args:
        report_year (int): Report year for generating the disclosure reports.
        institutions_df (pd.DataFrame): Institutions data.
        institutions_columns (List[str]): The list of institution column names.
        reduced_lar_df (pd.DataFrame): Chunk of reduced lar data
            used to create disclosure reports.
        reduced_lar_columns (List[str]): The list of reduced lar column names.
        state_county_mapping_df (pd.DataFrame): State and county code lookup map.
        disclosure_reports_path (str): Path to save disclosure report files.
        use_lei_list (bool): If true, run only on a list of lei, otherwise run
            disclosure reports for all lei.
        lei_list_df (pd.DataFrame): The list of lei to run disclosure reports on.
        skip_existing_reports (bool): If true, skip lei that already have reports generated.
            Note that this is not used if use_lei_list is True.

    Returns:
        A partion holder for disclosure tables 1 and 2 for each msa_md for
        each lei.
    """

    # Set names on columns
    institutions_df.columns = institutions_columns
    reduced_lar_df.columns = reduced_lar_columns

    if use_lei_list:
        # Generate disclosure reports only for lei in lei_list
        lei_list = lei_list_df["lei"].tolist()
        logger.info(f"Generating diclosure reports for {lei_list}")
        institutions_df = institutions_df[institutions_df["lei"].isin(lei_list)]
    elif skip_existing_reports:
        logger.info(f"Checking S3 for existing disclosure report LEI folders to skip")

        # Remove leis that already have disclosure reports
        fs = s3fs.S3FileSystem()
        mask = institutions_df["lei"].apply(
            lambda x: reports_exist(x, disclosure_reports_path, fs)
        )
        institutions_df = institutions_df[~mask]

        if len(institutions_df) == 0:
            logger.info(f"Disclosure reports have already been generated for all LEI.")
        else:
            logger.info(
                f"Generating diclosure reports for remaining {len(institutions_df)} LEI"
            )
    else:
        logger.info(f"Generating diclosure reports for all {len(institutions_df)} LEI")

    # Merge institution and reduced lar tables
    disclosure_report_df = reduced_lar_df.merge(institutions_df, on="lei", how="left")

    # Rename columns
    disclosure_report_df = disclosure_report_df.rename(
        columns={"activity_year": "year", "respondent_name": "institution_name"}
    )

    # Filter the year
    disclosure_report_df = disclosure_report_df[
        disclosure_report_df["year"] == report_year
    ]

    # Make msa_md a string
    disclosure_report_df["msa_md"] = disclosure_report_df["msa_md"].astype(str)

    # Fix loan amount to be the rounded mlar value instead of exact lar value
    disclosure_report_df["loan_amount"] = (
        disclosure_report_df["loan_amount"].apply(round_to_midpoint).astype(float)
    )

    # Do base processing for both tables
    logger.info(f"Preprocessing reduced LAR data for disclosure reports table 1")
    grouped_lei_df = disclosure_report_df.groupby(["lei", "institution_name"])
    processed_table_1_df = grouped_lei_df.apply(output_collection_table_1).reset_index()

    logger.info(f"Preprocessing reduced LAR data for disclosure reports table 2")
    processed_table_2_df = grouped_lei_df.apply(output_collection_table_2).reset_index()
    logger.info(f"Finished preprocessing reduced LAR data for disclosure reports")

    reports_partition_holder = {}
    report_year_str = str(report_year)

    # Group by lei and msa, then create report table 1
    grouped_table_1_disclosure_df = processed_table_1_df.groupby(
        ["lei", "msa_md"], as_index=False
    )
    for name, group in grouped_table_1_disclosure_df:
        # Create disclosure report 1
        reports_partition_holder[f"{name[0]}/{int(name[1])}/1"] = (
            lambda group=group: create_disclosure_report_1(
                report_year_str, group, state_county_mapping_df
            )
        )

    # Group by lei and msa, then create report table 2
    grouped_table_2_disclosure_df = processed_table_2_df.groupby(
        ["lei", "msa_md"], as_index=False
    )
    for name, group in grouped_table_2_disclosure_df:
        # Create disclosure report 2
        reports_partition_holder[f"{name[0]}/{int(name[1])}/2"] = (
            lambda group=group: create_disclosure_report_2(
                report_year_str, group, state_county_mapping_df
            )
        )

    return reports_partition_holder


def reports_exist(prefix: str, reports_path: str, fs: s3fs.S3FileSystem) -> bool:
    """Checks if any report files exist for a given prefix. The prefix will be
    lei for disclosure reports and msa for aggregate reports.

    Args:
        lei (str): The lei that might have disclosure report files.
        reports_path (str: Path to where the report files are stored.
        fs (S3FileSystem): the file system used to look for the report files.
    Returns:
        True if any report files exist for a given lei, otherwise false.
    """
    result = fs.find(path=reports_path, prefix=prefix)
    reports_exist = False
    if len(result) > 1:
        logger.info(f"Skipping reports for {prefix} because folder already exist")
        reports_exist = True
    return reports_exist
