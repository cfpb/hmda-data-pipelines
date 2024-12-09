import logging
from datetime import datetime
from typing import Dict

import pandas as pd

from .state_county_mapping import (
    create_state_and_county_tract
)

logger = logging.getLogger(__name__)

def create_disclosure_report_1(
    report_year: str, lei_msa_group: pd.DataFrame, state_county_mapping_df: pd.DataFrame
) -> pd.DataFrame:
    """Returns disclosure report table 1 for a DataFrame group for a single
    lei/msa pair.

    Args:
        report_year (str): Report year for generating the disclosure reports.
        lei_msa_group (pd.DataFrame): A DataFrame group for a single lei/msa pair.
        state_county_mapping_df (pd.DataFrame): State and county code lookup map.
    Returns:
        A single row DataFrame created from a dictionary that represents the
        disclosure table 1 report.
    """
    
    # Reduce to one line to get static data
    one_line_report = lei_msa_group.iloc[0]

    lei = one_line_report["lei"]
    msa_md = one_line_report["msa_md"]
    logger.info(f"Creating disclosure report table 1 for {lei}/{msa_md}")

    tracts = []
    grouped_tract_df = lei_msa_group.groupby("tract")
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
        "lei": lei,
        "institutionName": one_line_report["institution_name"],
        "table": "1",
        "type": "Disclosure",
        "description": "Disposition of loan applications, by location of property and type of loan",
        "year": report_year,
        "reportDate": report_date,
        "msa": get_msa(msa_md, one_line_report["msa_md_name"]),
        "tracts": tracts,
    }

    report_1_df = pd.DataFrame.from_dict(report_1, orient="index")

    return report_1_df


def create_disclosure_report_2(
    report_year: str, lei_msa_group: pd.DataFrame, state_county_mapping_df: pd.DataFrame
) -> pd.DataFrame:
    """Returns disclosure report table 2 for a DataFrame group for a single
    lei/msa pair.

    Args:
        report_year (str): Report year for generating the disclosure reports.
        lei_msa_group (pd.DataFrame): A DataFrame group for a single lei/msa pair.
        state_county_mapping_df (pd.DataFrame): State and county code lookup map.
    Returns:
        A single row DataFrame created from a dictionary that represents the
        disclosure table 2 report.
    """
    
    # Reduce to one line to get static data
    one_line_report = lei_msa_group.iloc[0]

    lei = one_line_report["lei"]
    msa_md = one_line_report["msa_md"]
    logger.info(f"Creating disclosure report table 2 for {lei}/{msa_md}")

    tracts = []
    grouped_tract_df = lei_msa_group.groupby("tract")
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
        "lei": lei,
        "institutionName": one_line_report["institution_name"],
        "table": "2",
        "type": "Disclosure",
        "description": "Loans purchased, by location of property and type of loan",
        "year": report_year,
        "reportDate": report_date,
        "msa": get_msa(msa_md, one_line_report["msa_md_name"]),
        "tracts": tracts,
    }

    report_2_df = pd.DataFrame.from_dict(report_2, orient="index")

    return report_2_df

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