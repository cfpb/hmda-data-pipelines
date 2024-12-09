import logging
from datetime import datetime
import pandas as pd
from typing import Dict

from .income_race_ethnicity_processing import (
    build_sorted_applicant_income,
    build_sorted_income_ethnicity,
    build_sorted_income_race,
)
from .median_age_processing import build_sorted_median_age
from .state_county_mapping import create_state_and_county_tract
from .race_gender_processing import (
    build_sorted_gender,
    build_sorted_race,
    build_sorted_ethnicity,
)

logger = logging.getLogger(__name__)


def create_aggregate_report_1(
    report_year: str, msa_group: pd.DataFrame, state_county_mapping_df: pd.DataFrame
) -> pd.DataFrame:
    """Returns aggregate report table 1 for a dataframe group for a single msa.

    Args:
        report_year (str): Report year for generating the aggregate reports.
        msa_group (pd.DataFrame): A dataframe group for a single msa.
        state_county_mapping_df (pd.DataFrame): State and county code lookup map.
    Returns:
        A single row dataframe created from a dictionary that represents the
        aggregate table 1 report.
    """

    # Reduce to one line to get static data
    one_line_report = msa_group.iloc[0]

    msa_md = one_line_report["msa_md"]
    logger.info(f"Creating aggregate report table 1 for {msa_md}")

    tracts = []
    grouped_tract_df = msa_group.groupby("tract")
    for tract_name, tract_group in grouped_tract_df:
        dispositions = []
        grouped_disposition_df = tract_group.groupby("title", sort=False)
        for title_name, title_group in grouped_disposition_df:
            list_info = []
            grouped_dispostion_name_title_df = title_group.groupby(
                "disposition_name", sort=False
            )
            for disposition_name, disposition_group in grouped_dispostion_name_title_df:
                list_info.append(
                    {
                        "dispositionName": disposition_name,
                        "count": disposition_group["count"].iloc[0],
                        "value": disposition_group["loan_amount"].iloc[0],
                    }
                )
            dispositions.append(
                {
                    "title": title_name.split("-")[0].strip(),
                    "values": list_info,
                    "titleForSorting": title_name,
                }
            )
        tract = create_state_and_county_tract(tract_name, state_county_mapping_df)
        tracts.append({"tract": tract, "dispositions": dispositions})

    report_date = datetime.now().strftime("%m/%d/%Y %I:%M %p")

    # Create report 1
    report_1 = {
        "table": "1",
        "type": "Aggregate",
        "description": "Disposition of loan applications, by location of property and type of loan",
        "year": report_year,
        "reportDate": report_date,
        "msa": get_msa(msa_md, one_line_report["msa_md_name"]),
        "tracts": tracts,
    }

    report_1_df = pd.DataFrame.from_dict(report_1, orient="index")

    return report_1_df


def create_aggregate_report_2(
    report_year: str, msa_group: pd.DataFrame, state_county_mapping_df: pd.DataFrame
) -> pd.DataFrame:
    """Returns aggregate report table 2 for a DataFrame group for a single msa.

    Args:
        report_year (str): Report year for generating the aggregate reports.
        msa_group (pd.DataFrame): A dataframe group for a single msa.
        state_county_mapping_df (pd.DataFrame): State and county code lookup map.
    Returns:
        A single row dataframe created from a dictionary that represents the
        aggregate table 2 report.
    """

    # Reduce to one line to get static data
    one_line_report = msa_group.iloc[0]

    msa_md = one_line_report["msa_md"]
    logger.info(f"Creating aggregate report table 2 for {msa_md}")

    tracts = []
    grouped_tract_df = msa_group.groupby("tract")
    for tract_name, tract_group in grouped_tract_df:
        dispositions_values = []
        grouped_disposition_df = tract_group.groupby("title", sort=False)
        for title_name, title_group in grouped_disposition_df:
            grouped_dispostion_name_title_df = title_group.groupby(
                "disposition_name", sort=False
            )
            for disposition_name, disposition_group in grouped_dispostion_name_title_df:
                dispositions_values.append(
                    {
                        "dispositionName": disposition_name,
                        "count": disposition_group["count"].iloc[0],
                        "value": disposition_group["loan_amount"].iloc[0],
                    }
                )
        tract = create_state_and_county_tract(tract_name, state_county_mapping_df)
        tracts.append({"tract": tract, "values": dispositions_values})

    report_date = datetime.now().strftime("%m/%d/%Y %I:%M %p")

    # Create report 2
    report_2 = {
        "table": "2",
        "type": "Aggregate",
        "description": "Loans purchased, by location of property and type of loan",
        "year": report_year,
        "reportDate": report_date,
        "msa": get_msa(msa_md, one_line_report["msa_md_name"]),
        "tracts": tracts,
    }

    report_2_df = pd.DataFrame.from_dict(report_2, orient="index")

    return report_2_df


def create_aggregate_report_3(
    report_year: str, msa_group: pd.DataFrame
) -> pd.DataFrame:
    """Returns aggregate report table 3 for a dataframe group for a single msa.

    Args:
        report_year (str): Report year for generating the aggregate reports
        msa_group (pd.DataFrame): A dataframe group for a single msa.
    Returns:
        A single row dataframe created from a dictionary that represents the
        aggregate table 3 report.
    """
    
    # Reduce to one line to get static data
    one_line_report = msa_group.iloc[0]

    msa_md = one_line_report["msa_md"]
    logger.info(f"Creating aggregate report table 3 for {msa_md}")

    # Group by race
    total_grouping = []
    grouped_race_df = msa_group.groupby("race")
    for race, race_group in grouped_race_df:
        dispositions_by_race = []
        disposition_by_race_gender = []

        # Group by title
        grouped_race_title_df = race_group.groupby("title", sort=False)
        for title, race_title_group in grouped_race_title_df:
            # Get dispositions for race and title
            dispositions_by_race.append(build_disposition(race_title_group, title))

        # Group by gender
        grouped_race_gender_df = race_group.groupby("sex", sort=False)
        for gender, race_gender_group in grouped_race_gender_df:
            disposition_by_race_gender_title = []

            # Group by title
            grouped_race_gender_title_df = race_gender_group.groupby(
                "title", sort=False
            )
            for title, race_gender_title_group in grouped_race_gender_title_df:
                # Get dispositions for race, gender, and title
                disposition_by_race_gender_title.append(
                    build_disposition(race_gender_title_group, title)
                )

            # Get dispositions with sorting field
            disposition_by_race_gender.append(
                build_sorted_gender(gender, disposition_by_race_gender_title)
            )

        # Sort the dispositions
        disposition_by_race_gender = sorted(
            disposition_by_race_gender, key=lambda d: d["genderForSorting"]
        )

        # Combine dispositions
        total_grouping.append(
            build_sorted_race(race, dispositions_by_race, disposition_by_race_gender)
        )

    # Sort the dispositions
    sorted_total_grouping = sorted(total_grouping, key=lambda d: d["raceForSorting"])

    report_date = datetime.now().strftime("%m/%d/%Y %I:%M %p")

    # Create report 3
    report_3 = {
        "table": "3",
        "type": "Aggregate",
        "description": "Disposition of loan applications, by race and sex of applicant",
        "year": report_year,
        "reportDate": report_date,
        "msa": get_msa(msa_md, one_line_report["msa_md_name"]),
        "races": sorted_total_grouping,
    }

    report_3_df = pd.DataFrame.from_dict(report_3, orient="index")

    return report_3_df


def create_aggregate_report_4(
    report_year: str, msa_group: pd.DataFrame
) -> pd.DataFrame:
    """Returns aggregate report table 4 for a dataframe group for a single msa.

    Args:
        report_year (str): Report year for generating the aggregate reports
        msa_group (pd.DataFrame): A dataframe group for a single msa.
    Returns:
        A single row dataframe created from a dictionary that represents the
        aggregate table 4 report.
    """

    # Reduce to one line to get static data
    one_line_report = msa_group.iloc[0]

    msa_md = one_line_report["msa_md"]
    logger.info(f"Creating aggregate report table 4 for {msa_md}")

    # Group by ethnicity
    total_grouping = []
    grouped_ethnicity_df = msa_group.groupby("ethnicity")
    for ethnicity, ethnicity_group in grouped_ethnicity_df:
        dispositions_by_ethnicity = []
        disposition_by_ethnicity_gender = []

        # Group by title
        grouped_ethnicity_title_df = ethnicity_group.groupby("title", sort=False)
        for title, ethnicity_title_group in grouped_ethnicity_title_df:
            # Get dispositions for ethnicity and title
            dispositions_by_ethnicity.append(
                build_disposition(ethnicity_title_group, title)
            )

        # Group by gender
        grouped_ethnicity_gender_df = ethnicity_group.groupby("sex", sort=False)
        for gender, ethnicity_gender_group in grouped_ethnicity_gender_df:
            disposition_by_ethnicity_gender_title = []

            # Group by title
            grouped_ethnicity_gender_title_df = ethnicity_gender_group.groupby(
                "title", sort=False
            )

            for (
                title,
                ethnicity_gender_title_group,
            ) in grouped_ethnicity_gender_title_df:
                # Get dispositions for ethnicity, gender, and title
                disposition_by_ethnicity_gender_title.append(
                    build_disposition(ethnicity_gender_title_group, title)
                )

            # Get dispositions with sorting field
            disposition_by_ethnicity_gender.append(
                build_sorted_gender(gender, disposition_by_ethnicity_gender_title)
            )

        # Sort the dispositions
        disposition_by_ethnicity_gender = sorted(
            disposition_by_ethnicity_gender, key=lambda d: d["genderForSorting"]
        )

        # Combine dispositions
        total_grouping.append(
            build_sorted_ethnicity(
                ethnicity,
                dispositions_by_ethnicity,
                disposition_by_ethnicity_gender,
            )
        )

    # Sort the dispositions
    sorted_total_grouping = sorted(
        total_grouping, key=lambda d: d["ethnicityNameForSorting"]
    )

    report_date = datetime.now().strftime("%m/%d/%Y %I:%M %p")

    # Create report 4
    report_4 = {
        "table": "4",
        "type": "Aggregate",
        "description": "Disposition of loan applications, by ethnicity and sex of applicant",
        "year": report_year,
        "reportDate": report_date,
        "msa": get_msa(msa_md, one_line_report["msa_md_name"]),
        "ethnicities": sorted_total_grouping,
    }

    report_4_df = pd.DataFrame.from_dict(report_4, orient="index")

    return report_4_df


def create_aggregate_report_5(
    report_year: str, msa_group: pd.DataFrame
) -> pd.DataFrame:
    """Returns aggregate report table 5 for a dataframe group for a single msa.

    Args:
        report_year (str): Report year for generating the aggregate reports
        msa_group (pd.DataFrame): A dataframe group for a single msa.
    Returns:
        A single row dataframe created from a dictionary that represents the
        aggregate table 5 report.
    """

    # Reduce to one line to get static data
    one_line_report = msa_group.iloc[0]

    msa_md = one_line_report["msa_md"]
    logger.info(f"Creating aggregate report table 5 for {msa_md}")

    # Group by income bracket
    total_grouping = []
    grouped_income_bracket_df = msa_group.groupby("income_bracket")

    for income_bracket, income_bracket_group in grouped_income_bracket_df:
        # Group by race
        dispositions_by_race = []
        grouped_race_income_bracket_df = income_bracket_group.groupby("race")

        for race, race_group in grouped_race_income_bracket_df:
            # Group by title
            dispositions = []
            grouped_title_race_income_bracket_df = race_group.groupby("title")

            for title, title_group in grouped_title_race_income_bracket_df:
                # Get dispositions for title
                dispositions.append(build_disposition(title_group, title, "name"))

            # Sort the dispositions by the letter at the end of the nameForSorting field
            sorted_dispositions = sorted(
                dispositions, key=lambda d: d["nameForSorting"].split("-")[1].strip()
            )

            # Get sorted dispositions for race
            dispositions_by_race.append(
                build_sorted_income_race(race, sorted_dispositions)
            )

        # Sort the race dispositions by the letter at the end of the nameForSorting field
        sorted_dispositions_by_race = sorted(
            dispositions_by_race, key=lambda d: d["raceForSorting"]
        )

        borrower_race = {"characteristic": "Race", "races": sorted_dispositions_by_race}

        # Group by ethnicity
        dispositions_by_ethnicity = []
        grouped_ethnicity_income_bracket_df = income_bracket_group.groupby("ethnicity")

        for ethnicity, ethnicity_group in grouped_ethnicity_income_bracket_df:
            # Group by title
            dispositions = []
            grouped_title_ethnicity_income_bracket_df = ethnicity_group.groupby("title")

            for title, title_group in grouped_title_ethnicity_income_bracket_df:
                # Get dispositions for title
                dispositions.append(build_disposition(title_group, title, "name"))

            # Sort the dispositions by the letter at the end of the nameForSorting field
            sorted_dispositions = sorted(
                dispositions, key=lambda d: d["nameForSorting"].split("-")[1].strip()
            )

            # Get sorted dispositions for ethnicity
            dispositions_by_ethnicity.append(
                build_sorted_income_ethnicity(ethnicity, sorted_dispositions, "")
            )

        # Sort the ethnicity dispositions
        sorted_dispositions_by_ethnicity = sorted(
            dispositions_by_ethnicity, key=lambda d: d["ethnicityForSorting"]
        )

        borrower_ethnicity = {
            "characteristic": "Ethnicity",
            "ethnicities": sorted_dispositions_by_ethnicity,
        }

        # Combine dispositions
        borrower_characteristics = {
            "race": borrower_race,
            "ethnicity": borrower_ethnicity,
        }
        total_grouping.append(
            build_sorted_applicant_income(income_bracket, borrower_characteristics)
        )

    # Sort the dispositions
    sorted_total_grouping = sorted(
        total_grouping, key=lambda d: d["applicantIncomeSorting"]
    )

    report_date = datetime.now().strftime("%m/%d/%Y %I:%M %p")

    # Create report 5
    report_5 = {
        "table": "5",
        "type": "Aggregate",
        "description": "Disposition of applications by income, race, and ethnicity of applicant",
        "year": report_year,
        "reportDate": report_date,
        "msa": get_msa(msa_md, one_line_report["msa_md_name"]),
        "applicantIncomes": sorted_total_grouping,
    }

    report_5_df = pd.DataFrame.from_dict(report_5, orient="index")

    return report_5_df


def create_aggregate_report_9(
    report_year: str, msa_group: pd.DataFrame
) -> pd.DataFrame:
    """Returns aggregate report table 9 for a dataframe group for a single msa.

    Args:
        report_year (str): Report year for generating the aggregate reports
        msa_group (pd.DataFrame): A dataframe group for a single msa.
    Returns:
        A single row dataframe created from a dictionary that represents the
        aggregate table 9 report.
    """

    # Reduce to one line to get static data
    one_line_report = msa_group.iloc[0]

    msa_md = one_line_report["msa_md"]
    logger.info(f"Creating aggregate report table 9 for {msa_md}")

    median_ages = []
    grouped_median_age_calc_df = msa_group.groupby("median_age_calculated")

    for median_age_calc_name, median_age_calc_group in grouped_median_age_calc_df:
        dispositions = []
        grouped_dispostion_name_df = median_age_calc_group.groupby(
            "disposition_name", sort=False
        )

        for disposition_name, disposition_group in grouped_dispostion_name_df:
            list_info = []
            grouped_dispostion_name_title_df = disposition_group.groupby(
                "title", sort=False
            )

            for title, disposition_title_group in grouped_dispostion_name_title_df:
                list_info.append(
                    {
                        "disposition": title,
                        "count": disposition_title_group["count"].iloc[0],
                        "value": disposition_title_group["loan_amount"].iloc[0],
                    }
                )
            dispositions.append(
                {
                    "loanCategory": disposition_name,
                    "dispositions": list_info,
                }
            )
        median_ages.append(build_sorted_median_age(median_age_calc_name, dispositions))

    # Sort the dispositions
    sorted_median_ages = sorted(median_ages, key=lambda d: d["ageForSorting"])

    report_date = datetime.now().strftime("%m/%d/%Y %I:%M %p")

    # Create report 9
    report_9 = {
        "table": "9",
        "type": "Aggregate",
        "description": "Disposition of loan applications, by median age of homes in census tract in which property is located and type of loan",
        "year": report_year,
        "reportDate": report_date,
        "msa": get_msa(msa_md, one_line_report["msa_md_name"]),
        "characteristic": "Census Tracts by Median Age of Homes",
        "medianAges": sorted_median_ages,
    }

    report_9_df = pd.DataFrame.from_dict(report_9, orient="index")

    return report_9_df


def create_aggregate_report_i(
    report_year: str, msa_group: pd.DataFrame
) -> pd.DataFrame:
    """Returns aggregate report table i for a dataframe group for a single msa.

    Args:
        report_year (str): Report year for generating the aggregate reports
        msa_group (pd.DataFrame): A dataframe group for a single msa.
    Returns:
        A single row dataframe created from a dictionary that represents the
        aggregate table i report.
    """

    # Reduce to one line to get static data
    one_line_report = msa_group.iloc[0]

    msa_md = one_line_report["msa_md"]
    logger.info(f"Creating aggregate report table i for {msa_md}")

    # Get list of institutions
    reported_institutions = msa_group["institution_name"].str.upper()
    reported_institutions_list = reported_institutions.drop_duplicates().to_list()

    report_date = datetime.now().strftime("%m/%d/%Y %I:%M %p")

    # Create report i
    report_i = {
        "table": "I",
        "type": "Aggregate",
        "description": f"List of financial institutions whose data make up the {report_year} MSA/MD aggregate report",
        "year": report_year,
        "reportDate": report_date,
        "msa": get_msa(msa_md, one_line_report["msa_md_name"]),
        "institutions": reported_institutions_list,
    }

    report_i_df = pd.DataFrame.from_dict(report_i, orient="index")

    return report_i_df


def build_disposition(input_df: pd.DataFrame, title: str, name: str = "disposition"):
    """Creates a dictionary of dispositon data used for aggregate reports 3, 4, and 5.

    Args:
        input_df (pd.DataFrame): The input DataFrame.
        title (str): The title for the disposition.
        name (str): The name to use for the disposition title and sorting fields
            in the disposition. The default value is "disposition", which is
            used in reports 3 and 4. The value "name" is used in report 5.
    Returns:
        A dictionary of the dispositon data used for aggregate reports 3, 4, and 5.
    """

    # Get sum of the counts
    count = input_df["count"].sum()

    # Get sum of loan_amount values
    value = input_df["loan_amount"].sum()

    # Get the disposition name without the sorting letter
    disposition = title.split("-")[0].strip()

    disposition_dict = {
        name: disposition,
        "count": count,
        "value": value,
        f"{name}ForSorting": title,
    }

    return disposition_dict


def get_msa(msa_md: str, msa_md_name: str) -> Dict:
    """Creates a dictionary of msa data used for aggregate reports.

    Args:
        msa_md (str): The msa code.
        msa_md_name (str): The name for the msa.
    Returns:
        A dictionary of the msa data used for aggregate reports.
    """
    
    # Fix msa name to be blank for msa 99999
    msa_md_name = "" if msa_md == 99999 else msa_md_name
    
    return {
        "id": msa_md,
        "name": msa_md_name,
        "state": "",
        "stateName": "",
    }