from typing import Dict, List
import pandas as pd
from .constants import NA_LIST

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

ethnicities = [
    "Free Form Text Only",
    "Ethnicity Not Available",
    "Hispanic or Latino",
    "Not Hispanic or Latino",
    "Joint",
]


def prepare(df: pd.DataFrame) -> pd.DataFrame:
    """Removes rows from a DataFrame if the race or ethnicity columns have NA values.

    Args:
        df (pd.DataFrame): The input DataFrame to be filtered.
    Returns:
        A Dataframe with NA values for race and ethnicity data filtered out.
    """

    # Filter out NA values
    filtered_df = df[(~df["race"].isin(NA_LIST)) & (~df["ethnicity"].isin(NA_LIST))]

    return filtered_df


def include_zero_and_non_zero(
    disp_input: pd.DataFrame,
    title: str,
    income_bracket: str,
    all_unique_combinations: pd.DataFrame,
) -> pd.DataFrame:
    """Joins disposition data with non-zero data values with default disposition data.

    Args:
        disp_input (pd.DataFrame): The input DataFrame with non-zero data values.
        title (str): The disposition title.
        income_bracket (str): The income bracket of the disposition.
        all_unique_combinations (pd.DataFrame): default disposition data for all
            combinations of msa_md, msa_md_name, race, and ethnicity.
    Returns:
        A Dataframe with non-zero and default disposition data joined together.
    """

    # Perform outer join
    outer_join_df = all_unique_combinations.merge(
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
    left_anti["income_bracket"] = income_bracket
    left_anti["title"] = title

    return left_anti


def create_default_data(
    msa_md: str, msa_md_name: str, income_bracket: str, title: str
) -> List[Dict]:
    """Create a list of default dispositions for each race and ethnicity.

    Args:
        msa_md (str): The msa_md for the disposition.
        msa_md_name (str): The msa_md name for the disposition.
        income_bracket (str): The income bracket of the disposition.
        title (str): The title of the disposition.
    Returns:
        A list of dictionaries containing the default dispositions for each race and ethnicity.
    """

    def fill(race: str, ethnicity: str):
        return {
            "msa_md": msa_md,
            "msa_md_name": msa_md_name,
            "income_bracket": income_bracket,
            "title": title,
            "loan_amount": 0,
            "count": 0,
            "race": race,
            "ethnicity": ethnicity,
        }

    result = []
    for race in races:
        for ethnicity in ethnicities:
            result.append(fill(race, ethnicity))
    return result


def transformation_add_default_data(df: pd.DataFrame) -> pd.DataFrame:
    """Transforms the input DataFrame and adds default data to it.

    Args:
        df (pd.DataFrame): The input DataFrame containing disposition data.
    Returns:
        A DataFrame containing the input and default disposition data.
    """

    transformed_data_dict = {}
    msa_grouped_df = df.groupby(["msa_md", "msa_md_name", "income_bracket", "title"])
    for msa_group_name, msa_group in msa_grouped_df:

        # Create default data
        default_data = create_default_data(
            msa_group_name[0], msa_group_name[1], msa_group_name[2], msa_group_name[3]
        )

        # Convert default data to a dictionary
        default_data_dict = {
            (
                key["race"],
                key["ethnicity"],
            ): key
            for key in default_data
        }

        # Convert msa_group to a dict with tuple keys
        msa_group_dict = msa_group.to_dict("records")
        msa_group_dict = {
            (
                key["race"],
                key["ethnicity"],
            ): key
            for key in msa_group_dict
        }

        # Update msa_group_dict into default_data_dict
        default_data_dict.update(msa_group_dict)
        transformed_data_dict.update(default_data_dict)

    # Convert to DataFrame
    return pd.DataFrame.from_dict(transformed_data_dict, orient="index")


def disposition_a(
    input: pd.DataFrame,
    title: str,
    actions_taken: List[int],
    all_unique_combinations: pd.DataFrame,
) -> pd.DataFrame:
    """Creates disposition A for the income bracket "LESS THAN 50% OF MSA/MD MEDIAN".

    Args:
        input (pd.DataFrame): The input DataFrame used to create the disposition data.
        title (str): The title for the disposition.
        actions_taken (List[int]): A list of actions_taken values to be kept in the
            disposition data.
        all_unique_combinations (pd.DataFrame): A DataFrame grouped by msa_md,
            msa_md_name, race, and ethnicity.
    Returns:
        A DataFrame for disposition A containing data for the income bracket
            "LESS THAN 50% OF MSA/MD MEDIAN".
    """

    disp_a = prepare(input)

    disp_a = disp_a[disp_a["action_taken_type"].isin(actions_taken)]
    disp_a = disp_a[disp_a["percent_median_msa_income"] == "<50%"]

    disp_a = add_count_and_loan_amount_sum_columns(disp_a)

    return include_zero_and_non_zero(
        disp_a, title, "LESS THAN 50% OF MSA/MD MEDIAN", all_unique_combinations
    )


def disposition_b(
    input: pd.DataFrame,
    title: str,
    actions_taken: List[int],
    all_unique_combinations: pd.DataFrame,
) -> pd.DataFrame:
    """Creates disposition B for the income bracket "50-79% OF MSA/MD MEDIAN".

    Args:
        input (pd.DataFrame): The input DataFrame used to create the disposition data.
        title (str): The title for the disposition.
        actions_taken (List[int]): A list of actions_taken values to be kept in the
            disposition data.
        all_unique_combinations (pd.DataFrame): A DataFrame grouped by msa_md,
            msa_md_name, race, and ethnicity.
    Returns:
        A DataFrame for disposition B containing data for the income bracket
            "50-79% OF MSA/MD MEDIAN".
    """

    disp_b = prepare(input)

    disp_b = disp_b[disp_b["action_taken_type"].isin(actions_taken)]
    disp_b = disp_b[disp_b["percent_median_msa_income"] == "50-79%"]

    disp_b = add_count_and_loan_amount_sum_columns(disp_b)

    return include_zero_and_non_zero(
        disp_b, title, "50-79% OF MSA/MD MEDIAN", all_unique_combinations
    )


def disposition_c(
    input: pd.DataFrame,
    title: str,
    actions_taken: List[int],
    all_unique_combinations: pd.DataFrame,
) -> pd.DataFrame:
    """Creates disposition C for the income bracket "80-99% OF MSA/MD MEDIAN".

    Args:
        input (pd.DataFrame): The input DataFrame used to create the disposition data.
        title (str): The title for the disposition.
        actions_taken (List[int]): A list of actions_taken values to be kept in the
            disposition data.
        all_unique_combinations (pd.DataFrame): A DataFrame grouped by msa_md,
            msa_md_name, race, and ethnicity.
    Returns:
        A DataFrame for disposition C containing data for the income bracket
            "80-99% OF MSA/MD MEDIAN".
    """

    disp_c = prepare(input)

    disp_c = disp_c[disp_c["action_taken_type"].isin(actions_taken)]
    disp_c = disp_c[disp_c["percent_median_msa_income"] == "80-99%"]

    disp_c = add_count_and_loan_amount_sum_columns(disp_c)

    return include_zero_and_non_zero(
        disp_c, title, "80-99% OF MSA/MD MEDIAN", all_unique_combinations
    )


def disposition_d(
    input: pd.DataFrame,
    title: str,
    actions_taken: List[int],
    all_unique_combinations: pd.DataFrame,
) -> pd.DataFrame:
    """Creates disposition D for the income bracket "100-119% OF MSA/MD MEDIAN".

    Args:
        input (pd.DataFrame): The input DataFrame used to create the disposition data.
        title (str): The title for the disposition.
        actions_taken (List[int]): A list of actions_taken values to be kept in the
            disposition data.
        all_unique_combinations (pd.DataFrame): A DataFrame grouped by msa_md,
            msa_md_name, race, and ethnicity.
    Returns:
        A DataFrame for disposition D containing data for the income bracket
            "100-119% OF MSA/MD MEDIAN".
    """

    disp_d = prepare(input)

    disp_d = disp_d[disp_d["action_taken_type"].isin(actions_taken)]
    disp_d = disp_d[disp_d["percent_median_msa_income"] == "100-119%"]

    disp_d = add_count_and_loan_amount_sum_columns(disp_d)

    return include_zero_and_non_zero(
        disp_d, title, "100-119% OF MSA/MD MEDIAN", all_unique_combinations
    )


def disposition_e(
    input: pd.DataFrame,
    title: str,
    actions_taken: List[int],
    all_unique_combinations: pd.DataFrame,
) -> pd.DataFrame:
    """Creates disposition E for the income bracket "120% OR MORE OF MSA/MD MEDIAN".

    Args:
        input (pd.DataFrame): The input DataFrame used to create the disposition data.
        title (str): The title for the disposition.
        actions_taken (List[int]): A list of actions_taken values to be kept in the
            disposition data.
        all_unique_combinations (pd.DataFrame): A DataFrame grouped by msa_md,
            msa_md_name, race, and ethnicity.
    Returns:
        A DataFrame for disposition E containing data for the income bracket
            "120% OR MORE OF MSA/MD MEDIAN".
    """

    disp_e = prepare(input)

    disp_e = disp_e[disp_e["action_taken_type"].isin(actions_taken)]
    disp_e = disp_e[disp_e["percent_median_msa_income"] == ">120%"]

    disp_e = add_count_and_loan_amount_sum_columns(disp_e)

    return include_zero_and_non_zero(
        disp_e,
        title,
        "120% OR MORE OF MSA/MD MEDIAN",
        all_unique_combinations,
    )


def add_count_and_loan_amount_sum_columns(
    disposition_df: pd.DataFrame,
) -> pd.DataFrame:
    """Calculates the loan_amount sum and count for each disposition section.

    Args:
        disposition_df (pd.DataFrame): The input DataFrame.
    Returns:
        An aggregated DataFrame where the loan_amount column is the sum of the
            loan_amount values for each disposition section and the count column
            is the count of lar rows in each disposition section.
    """

    grouped_disposition_df = disposition_df.groupby(
        ["msa_md", "msa_md_name", "race", "ethnicity"], as_index=False
    )
    aggregated_df = grouped_disposition_df.agg(
        loan_amount=("loan_amount", "sum"), count=("loan_amount", "count")
    )
    return aggregated_df


def output_collection_table_income(
    aggregate_report_df: pd.DataFrame,
) -> pd.DataFrame:
    """Creates pre-processed disposition data for aggregate report 5.

    Args:
        aggregate_report_df (pd.DataFrame): The input DataFrame.
    Returns:
        A DataFrame for disposition data for aggregate report 5.
    """

    # Note that the sorting letters are different for this table compared to other reports.
    actions_taken_table_1 = {
        "Applications Received - (A)": [1, 2, 3, 4, 5],
        "Loans Originated - (B)": [1],
        "Applications Approved but not Accepted - (C)": [2],
        "Applications Denied by Financial Institution - (D)": [3],
        "Applications Withdrawn by Applicant - (E)": [4],
        "File Closed for Incompleteness - (F)": [5],
        "Purchased Loans - (G)": [6],
    }

    output_a_table_list = []
    output_b_table_list = []
    output_c_table_list = []
    output_d_table_list = []
    output_e_table_list = []

    all_unique_combinations = aggregate_report_df[
        ["msa_md", "msa_md_name", "race", "ethnicity"]
    ].drop_duplicates()

    for description in actions_taken_table_1.keys():

        output_a_table_list.append(
            transformation_add_default_data(
                disposition_a(
                    aggregate_report_df,
                    description,
                    actions_taken_table_1[description],
                    all_unique_combinations,
                )
            )
        )

        output_b_table_list.append(
            transformation_add_default_data(
                disposition_b(
                    aggregate_report_df,
                    description,
                    actions_taken_table_1[description],
                    all_unique_combinations,
                )
            )
        )

        output_c_table_list.append(
            transformation_add_default_data(
                disposition_c(
                    aggregate_report_df,
                    description,
                    actions_taken_table_1[description],
                    all_unique_combinations,
                )
            )
        )

        output_d_table_list.append(
            transformation_add_default_data(
                disposition_d(
                    aggregate_report_df,
                    description,
                    actions_taken_table_1[description],
                    all_unique_combinations,
                )
            )
        )

        output_e_table_list.append(
            transformation_add_default_data(
                disposition_e(
                    aggregate_report_df,
                    description,
                    actions_taken_table_1[description],
                    all_unique_combinations,
                )
            )
        )

    output_a_table = pd.concat(output_a_table_list)
    output_b_table = pd.concat(output_b_table_list)
    output_c_table = pd.concat(output_c_table_list)
    output_d_table = pd.concat(output_d_table_list)
    output_e_table = pd.concat(output_e_table_list)

    return pd.concat(
        [
            output_a_table,
            output_b_table,
            output_c_table,
            output_d_table,
            output_e_table,
        ]
    )


def build_sorted_applicant_income(
    applicant_income: str, borrower_characteristics: Dict
) -> Dict:
    """Adds the field applicantIncomeSorting to the income disposition dictionary.
    Args:
        applicant_income (str): The income bracket for the disposition.
        borrower_characteristics (Dict): A dictionary of disposition data.
    Returns:
        A dictionary of disposition data containing a new field applicantIncomeSorting.
    """
    if applicant_income == "LESS THAN 50% OF MSA/MD MEDIAN":
        applicant_income_sorting = "(A)"
    elif applicant_income == "50-79% OF MSA/MD MEDIAN":
        applicant_income_sorting = "(B)"
    elif applicant_income == "80-99% OF MSA/MD MEDIAN":
        applicant_income_sorting = "(C)"
    elif applicant_income == "100-119% OF MSA/MD MEDIAN":
        applicant_income_sorting = "(D)"
    else:
        applicant_income_sorting = "(E)"

    return {
        "applicantIncome": applicant_income,
        "borrowerCharacteristics": borrower_characteristics,
        "applicantIncomeSorting": applicant_income_sorting,
    }


def build_sorted_income_ethnicity(
    ethnicity_name: str, dispositions: list, name: str = "Name"
) -> Dict:
    """Adds the field ethnicityNameForSorting to the ethnicity disposition dictionary.
    Args:
        ethnicity_name (str): The enthincity name for the disposition.
        dispositions (list): A list of disposition data.
        name (str): Part of the field name for the sorting field in the disposition.
            The default value is "Name", which is used in report 4. An empty string
            is used in report 5.

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
        f"ethnicity{name}ForSorting": ethnicity_name_for_sorting,
    }


def build_sorted_income_race(race: str, dispositions: list) -> Dict:
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
        "raceForSorting": race_for_sorting,
    }
