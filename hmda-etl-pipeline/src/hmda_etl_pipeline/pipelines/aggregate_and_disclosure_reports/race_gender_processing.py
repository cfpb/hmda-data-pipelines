from typing import List
import functools
import pandas as pd
from typing import Dict

races = [
    "Asian",
    "Native Hawaiian or Other Pacific Islander",
    "Free Form Text Only",
    "Race Not Available",
    "American Indian or Alaska Native",
    "Black or African American",
    "2 or more minority races",
    "White",
    "Joint",
]

genders = ["Sex Not Available", "Male", "Female", "Joint"]

ethnicities = [
    "Free Form Text Only",
    "Ethnicity Not Available",
    "Hispanic or Latino",
    "Not Hispanic or Latino",
    "Joint",
]


def include_zero_and_non_zero(
    disp_input: pd.DataFrame,
    title: str,
    all_unique_msa_md_tract: pd.DataFrame,
) -> pd.DataFrame:
    """Joins disposition data with non-zero data values with default disposition data.

    Args:
        disp_input (pd.DataFrame): The input DataFrame with non-zero data values.
        title (str): The disposition title.
        all_unique_msa_md_tract (pd.DataFrame): default disposition data for all 
            combinations of msa_md and tracts.
    Returns:
        A Dataframe with non-zero and default disposition data joined together.
    """

    # Perform outer join
    outer_join_df = all_unique_msa_md_tract.merge(
        disp_input,
        on=["msa_md"],
        how="outer",
        suffixes=("", "_right"),
        indicator=True,
    )

    # Discard the columns from right
    outer_join_df = outer_join_df[
        [c for c in outer_join_df.columns if not c.endswith("_right")]
    ]

    # Perform anti join to make left_anti
    left_anti = (
        outer_join_df[(outer_join_df["_merge"] == "left_only")]
        .drop("_merge", axis=1)
        .reset_index(drop=True)
    )

    # Set columns and combine
    left_anti["loan_amount"] = 0.0
    left_anti["count"] = 0
    left_anti = pd.concat([left_anti, disp_input])
    left_anti["title"] = title

    return left_anti


def create_default_data(msa_md: float, msa_md_name: str, title: str) -> List[Dict]:
    """Returns default data with title, race, sex, and ethicity data for a given msa.

    Args:
        msa_md (pd.DataFrame): The msa number
        msa_md_name (pd.DataFrame): The msa name
    Returns:
        A List of dictionaries containing all combinations of title, race, sex,
        and ethicity data for a given msa.
    """

    def fill(race: str, sex: str, ethnicity: str, title: str) -> Dict:
        return {
            "msa_md": msa_md,
            "msa_md_name": msa_md_name,
            "title": title,
            "loan_amount": 0,
            "count": 0,
            "race": race,
            "sex": sex,
            "ethnicity": ethnicity,
        }

    result = []
    for race in races:
        for gender in genders:
            for ethnicity in ethnicities:
                result.append(fill(race, gender, ethnicity, title))
    return result


def transformation_add_default_data(df: pd.DataFrame, title: str) -> pd.DataFrame:
    """Transforms the input DataFrame and adds default data to it.

    Args:
        df (pd.DataFrame): The input DataFrame containing disposition data.
        title (str): The title for the disposition.
    Returns:
        A DataFrame containing the input and default disposition data.
    """

    transformed_data_dict = {}
    msa_grouped_df = df.groupby(["msa_md", "msa_md_name"])
    for msa_group_name, msa_group in msa_grouped_df:
        # Create default data
        default_data = create_default_data(msa_group_name[0], msa_group_name[1], title)

        # Convert default data to a dictionary
        default_data_dict = {
            (
                key["race"],
                key["sex"],
                key["ethnicity"],
                key["title"],
            ): key
            for key in default_data
        }

        # Convert msa_group to a dict with tuple keys
        msa_group_dict = msa_group.to_dict("records")
        msa_group_dict = {
            (
                key["race"],
                key["sex"],
                key["ethnicity"],
                key["title"],
            ): key
            for key in msa_group_dict
        }

        # Update msa_group_dict into default_data_dict
        default_data_dict.update(msa_group_dict)
        transformed_data_dict.update(default_data_dict)

    # Convert to DataFrame
    return pd.DataFrame.from_dict(transformed_data_dict, orient="index")


def disposition(
    input: pd.DataFrame,
    title: str,
    actions_taken: List[int],
    all_unique_combinations: pd.DataFrame,
) -> pd.DataFrame:
    """Creates disposition data for the income bracket "LESS THAN 50% OF MSA/MD MEDIAN".

    Args:
        input (pd.DataFrame): The input DataFrame used to create the disposition data.
        title (str): The title for the disposition.
        actions_taken (List[int]): A list of actions_taken values to be kept in the 
            disposition data.
        all_unique_combinations (pd.DataFrame): A DataFrame grouped by msa_md, 
            msa_md_name, race, sex, and ethnicity.
    Returns:
        A DataFrame for disposition A containing data for the income bracket 
            "LESS THAN 50% OF MSA/MD MEDIAN".
    """

    disp = input[input["action_taken_type"].isin(actions_taken)]

    grouped_disposition_df = disp.groupby(
        ["msa_md", "msa_md_name", "race", "sex", "ethnicity"], as_index=False
    )
    disp = grouped_disposition_df.agg(
        loan_amount=("loan_amount", "sum"), count=("loan_amount", "count")
    )

    return include_zero_and_non_zero(disp, title, all_unique_combinations)


def output_collection_table_3_and_4(
    aggregate_report_df: pd.DataFrame,
) -> pd.DataFrame:
    """Creates pre-processed disposition data for aggregate reports 3 and 4.

    Args:
        aggregate_report_df (pd.DataFrame): The input DataFrame.
    Returns:
        A DataFrame for disposition data for aggregate reports 3 and 4.
    """
    
    actions_taken = {
        "Loans Originated - (A)": [1],
        "Applications Approved but not Accepted - (B)": [2],
        "Applications Denied by Financial Institution - (C)": [3],
        "Applications Withdrawn by Applicant - (D)": [4],
        "File Closed for Incompleteness - (E)": [5],
        "Purchased Loans - (F)": [6],
    }
    
    all_unique_combinations = aggregate_report_df[
        ["msa_md", "msa_md_name", "race", "sex", "ethnicity"]
    ].drop_duplicates()

    output_table_3_and_4_list = []
    for description in actions_taken.keys():
        output_table_3_and_4_list.append(
            transformation_add_default_data(
                disposition(
                    aggregate_report_df,
                    description,
                    actions_taken[description],
                    all_unique_combinations,
                ),
                description,
            )
        )

    return pd.concat(output_table_3_and_4_list)


def build_sorted_ethnicity(
    ethnicity_name: str, dispositions: list, gender: list
) -> Dict:
    """Adds the field ethnicityNameForSorting to the ethnicity disposition dictionary.
    Args:
        ethnicity_name (str): The enthincity name for the disposition.
        dispositions (list): A list of disposition data.
        gender (list): A list disposition data for all the genders.
    Returns:
        A dictionary of disposition data containing a new field ethnicityNameForSorting.
    """

    if ethnicity_name == "Hispanic or Latino":
        ethnicity_name_for_sorting = "(A)"
    elif ethnicity_name == "Not Hispanic or Latino":
        ethnicity_name_for_sorting = "(B)"
    elif ethnicity_name == "Joint":
        ethnicity_name_for_sorting = "(C)"
    elif ethnicity_name == "Free Form Text Only":
        ethnicity_name_for_sorting = "(D)"
    else:
        ethnicity_name_for_sorting = "(E)"

    return {
        "ethnicityName": ethnicity_name,
        "dispositions": dispositions,
        "gender": gender,
        "ethnicityNameForSorting": ethnicity_name_for_sorting,
    }


def build_sorted_gender(gender: str, dispositions: list) -> Dict:
    """Adds the field genderForSorting to the gender disposition dictionary.
    Args:
        gender (str): The gender name for the disposition.
        dispositions (list): A list of disposition data.
    Returns:
        A dictionary of disposition data containing a new field genderForSorting.
    """

    gender_for_sorting = ""
    if gender == "Male":
        gender_for_sorting = "(A)"
    elif gender == "Female":
        gender_for_sorting = "(B)"
    elif gender == "Joint":
        gender_for_sorting = "(C)"
    else:
        gender_for_sorting = "(D)"

    return {
        "gender": gender,
        "dispositions": dispositions,
        "genderForSorting": gender_for_sorting,
    }


def build_sorted_race(race: str, dispositions: list, gender: list) -> Dict:
    """Adds the field raceForSorting to the race disposition dictionary.
    Args:
        race (str): The race name for the disposition.
        dispositions (list): A list of disposition data.
        gender (list): A list disposition data for all the genders
    Returns:
        A dictionary of disposition data containing a new field raceForSorting.
    """

    if race == "American Indian or Alaska Native":
        race_for_sorting = "(A)"
    elif race == "Asian":
        race_for_sorting = "(B)"
    elif race == "Black or African American":
        race_for_sorting = "(C)"
    elif race == "Native Hawaiian or Other Pacific Islander":
        race_for_sorting = "(D)"
    elif race == "White":
        race_for_sorting = "(E)"
    elif race == "2 or more minority races":
        race_for_sorting = "(F)"
    elif race == "Joint":
        race_for_sorting = "(H)"
    elif race == "Free Form Text Only":
        race_for_sorting = "(I)"
    else:
        race_for_sorting = "(J)"

    return {
        "race": race,
        "dispositions": dispositions,
        "gender": gender,
        "raceForSorting": race_for_sorting,
    }
