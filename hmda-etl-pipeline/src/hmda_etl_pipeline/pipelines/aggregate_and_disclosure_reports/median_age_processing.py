from typing import Dict, List
import functools
import pandas as pd


def include_zero_and_non_zero(
    disp_input: pd.DataFrame,
    title: str,
    disposition_name: str,
    all_unique_msa_md_tract: pd.DataFrame,
) -> pd.DataFrame:
    """Joins disposition data with non-zero data values with default disposition data.

    Args:
        disp_input (pd.DataFrame): The input DataFrame with non-zero data values.
        title (str): The disposition title.
        disposition_name (str): The disposition name.
        all_unique_msa_md_tract (pd.DataFrame): default disposition data for all
            combinations of msa_md and tracts.
    Returns:
        A Dataframe with non-zero and default disposition data joined together.
    """

    # Perform outer join
    outer_join_df = all_unique_msa_md_tract.merge(
        disp_input,
        on=["median_age_calculated", "msa_md"],
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
    left_anti["disposition_name"] = disposition_name
    left_anti["title"] = title

    return left_anti


def disposition_a(
    disp_a: pd.DataFrame,
    title: str,
    actions_taken: List[int],
    all_unique_msa_md_tract: pd.DataFrame,
) -> pd.DataFrame:
    """Creates disposition A for the disposition name "FHA, FSA/RHS & VA (A)".

    Args:
        disp_a (pd.DataFrame): The input DataFrame used to create the disposition data.
        title (str): The title for the disposition.
        actions_taken (List[int]): A list of actions_taken values to be kept in the
            disposition data.
        all_unique_msa_md_tract (pd.DataFrame): A DataFrame grouped by msa_md,
            msa_md_name, and median_age_calculated.
    Returns:
        A DataFrame for disposition A containing data for the disposition name
            "FHA, FSA/RHS & VA (A)".
    """

    disp_a = disp_a[disp_a["action_taken_type"].isin(actions_taken)]
    disp_a = disp_a[disp_a["total_units"].isin([1, 2, 3, 4])]
    disp_a = disp_a[disp_a["loan_purpose"] == 1]
    disp_a = disp_a[disp_a["loan_type"].isin([2, 3, 4])]

    disp_a = add_count_and_loan_amount_sum_columns(disp_a)

    return include_zero_and_non_zero(
        disp_a, title, "FHA, FSA/RHS & VA (A)", all_unique_msa_md_tract
    )


def disposition_b(
    disp_b: pd.DataFrame,
    title: str,
    actions_taken: List[int],
    all_unique_msa_md_tract: pd.DataFrame,
) -> pd.DataFrame:
    """Creates disposition B for the disposition name "Conventional (B)".

    Args:
        disp_b (pd.DataFrame): The input DataFrame used to create the disposition data.
        title (str): The title for the disposition.
        actions_taken (List[int]): A list of actions_taken values to be kept in the
            disposition data.
        all_unique_msa_md_tract (pd.DataFrame): A DataFrame grouped by msa_md,
            msa_md_name, and median_age_calculated.
    Returns:
        A DataFrame for disposition B containing data for the disposition name
            "Conventional (B)".
    """

    disp_b = disp_b[disp_b["action_taken_type"].isin(actions_taken)]
    disp_b = disp_b[disp_b["total_units"].isin([1, 2, 3, 4])]
    disp_b = disp_b[disp_b["loan_purpose"] == 1]
    disp_b = disp_b[disp_b["loan_type"] == 1]

    disp_b = add_count_and_loan_amount_sum_columns(disp_b)

    return include_zero_and_non_zero(
        disp_b, title, "Conventional (B)", all_unique_msa_md_tract
    )


def disposition_c(
    disp_c: pd.DataFrame,
    title: str,
    actions_taken: List[int],
    all_unique_msa_md_tract: pd.DataFrame,
) -> pd.DataFrame:
    """Creates disposition C for the disposition name "Refinancings (C)".

    Args:
        disp_c (pd.DataFrame): The input DataFrame used to create the disposition data.
        title (str): The title for the disposition.
        actions_taken (List[int]): A list of actions_taken values to be kept in the
            disposition data.
        all_unique_msa_md_tract (pd.DataFrame): A DataFrame grouped by msa_md,
            msa_md_name, and median_age_calculated.
    Returns:
        A DataFrame for disposition C containing data for the disposition name
            "Refinancings (C)".
    """

    disp_c = disp_c[disp_c["action_taken_type"].isin(actions_taken)]
    disp_c = disp_c[disp_c["total_units"].isin([1, 2, 3, 4])]
    disp_c = disp_c[disp_c["loan_purpose"].isin([31, 32])]

    disp_c = add_count_and_loan_amount_sum_columns(disp_c)

    return include_zero_and_non_zero(
        disp_c, title, "Refinancings (C)", all_unique_msa_md_tract
    )


def disposition_d(
    disp_d: pd.DataFrame,
    title: str,
    actions_taken: List[int],
    all_unique_msa_md_tract: pd.DataFrame,
) -> pd.DataFrame:
    """Creates disposition D for the disposition name "Home Improvement Loans (D)".

    Args:
        disp_d (pd.DataFrame): The input DataFrame used to create the disposition data.
        title (str): The title for the disposition.
        actions_taken (List[int]): A list of actions_taken values to be kept in the
            disposition data.
        all_unique_msa_md_tract (pd.DataFrame): A DataFrame grouped by msa_md,
            msa_md_name, and median_age_calculated.
    Returns:
        A DataFrame for disposition D containing data for the disposition name
            "Home Improvement Loans (D)".
    """

    disp_d = disp_d[disp_d["action_taken_type"].isin(actions_taken)]
    disp_d = disp_d[disp_d["total_units"].isin([1, 2, 3, 4])]
    disp_d = disp_d[disp_d["loan_purpose"] == 2]

    disp_d = add_count_and_loan_amount_sum_columns(disp_d)

    return include_zero_and_non_zero(
        disp_d, title, "Home Improvement Loans (D)", all_unique_msa_md_tract
    )


def disposition_e(
    disp_e: pd.DataFrame,
    title: str,
    actions_taken: List[int],
    all_unique_msa_md_tract: pd.DataFrame,
) -> pd.DataFrame:
    """Creates disposition E for the disposition name "Loans on Dwellings For 5 or More Families (E)".

    Args:
        disp_e (pd.DataFrame): The input DataFrame used to create the disposition data.
        title (str): The title for the disposition.
        actions_taken (List[int]): A list of actions_taken values to be kept in the
            disposition data.
        all_unique_msa_md_tract (pd.DataFrame): A DataFrame grouped by msa_md,
            msa_md_name, and median_age_calculated.
    Returns:
        A DataFrame for disposition E containing data for the disposition name
            "Loans on Dwellings For 5 or More Families (E)".
    """

    disp_e = disp_e[disp_e["action_taken_type"].isin(actions_taken)]
    disp_e = disp_e[~disp_e["total_units"].isin([1, 2, 3, 4])]

    disp_e = add_count_and_loan_amount_sum_columns(disp_e)

    return include_zero_and_non_zero(
        disp_e,
        title,
        "Loans on Dwellings For 5 or More Families (E)",
        all_unique_msa_md_tract,
    )


def disposition_f(
    disp_f: pd.DataFrame,
    title: str,
    actions_taken: List[int],
    all_unique_msa_md_tract: pd.DataFrame,
) -> pd.DataFrame:
    """Creates disposition F for the disposition name "Nonoccupant Loans from Columns A, B, C ,& D (F)".

    Args:
        disp_f (pd.DataFrame): The input DataFrame used to create the disposition data.
        title (str): The title for the disposition.
        actions_taken (List[int]): A list of actions_taken values to be kept in the
            disposition data.
        all_unique_msa_md_tract (pd.DataFrame): A DataFrame grouped by msa_md,
            msa_md_name, and median_age_calculated.
    Returns:
        A DataFrame for disposition F containing data for the disposition name
            "Nonoccupant Loans from Columns A, B, C ,& D (F)".
    """

    disp_f = disp_f[disp_f["action_taken_type"].isin(actions_taken)]
    disp_f = disp_f[disp_f["total_units"].isin([1, 2, 3, 4])]
    disp_f = disp_f[disp_f["loan_purpose"].isin([1, 2, 31, 32])]
    disp_f = disp_f[disp_f["loan_type"].isin([1, 2, 3, 4])]
    disp_f = disp_f[disp_f["occupancy_type"].isin([2, 3])]

    disp_f = add_count_and_loan_amount_sum_columns(disp_f)

    return include_zero_and_non_zero(
        disp_f,
        title,
        "Nonoccupant Loans from Columns A, B, C ,& D (F)",
        all_unique_msa_md_tract,
    )


def disposition_g(
    disp_g: pd.DataFrame,
    title: str,
    actions_taken: List[int],
    all_unique_msa_md_tract: pd.DataFrame,
) -> pd.DataFrame:
    """Creates disposition G for the disposition name "Loans On Manufactured Home Dwellings From Columns A, B, C & D (G)".

    Args:
        disp_g (pd.DataFrame): The input DataFrame used to create the disposition data.
        title (str): The title for the disposition.
        actions_taken (List[int]): A list of actions_taken values to be kept in the
            disposition data.
        all_unique_msa_md_tract (pd.DataFrame): A DataFrame grouped by msa_md,
            msa_md_name, and median_age_calculated.
    Returns:
        A DataFrame for disposition G containing data for the disposition name
            "Loans On Manufactured Home Dwellings From Columns A, B, C & D (G)".
    """

    disp_g = disp_g[disp_g["action_taken_type"].isin(actions_taken)]
    disp_g = disp_g[disp_g["total_units"].isin([1, 2, 3, 4])]
    disp_g = disp_g[disp_g["loan_purpose"].isin([1, 2, 31, 32])]
    disp_g = disp_g[disp_g["loan_type"].isin([1, 2, 3, 4])]
    disp_g = disp_g[disp_g["construction_method"] == 2]

    disp_g = add_count_and_loan_amount_sum_columns(disp_g)

    return include_zero_and_non_zero(
        disp_g,
        title,
        "Loans On Manufactured Home Dwellings From Columns A, B, C & D (G)",
        all_unique_msa_md_tract,
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
        ["msa_md", "msa_md_name", "median_age_calculated"], as_index=False
    )
    aggregated_df = grouped_disposition_df.agg(
        loan_amount=("loan_amount", "sum"), count=("loan_amount", "count")
    )
    return aggregated_df


def transformation_add_default_data(df: pd.DataFrame) -> pd.DataFrame:
    """Transforms the input DataFrame and adds default data to it.

    Args:
        df (pd.DataFrame): The input DataFrame containing disposition data.
    Returns:
        A DataFrame containing the input and default disposition data.
    """

    transformed_data_dict = {}
    msa_grouped_df = df.groupby(["msa_md", "msa_md_name"])
    for msa_group_name, msa_group in msa_grouped_df:

        # Create default data
        default_data = create_default_data(
            msa_group_name[0],
            msa_group_name[1],
            msa_group.iloc[0]["disposition_name"],
            msa_group.iloc[0]["title"],
        )

        # Convert default data to a dictionary
        default_data_dict = {
            (
                key["median_age_calculated"],
                key["title"],
                key["disposition_name"],
            ): key
            for key in default_data
        }

        # Convert msa_group to a dict with tuple keys
        msa_group_dict = msa_group.to_dict("records")
        msa_group_dict = {
            (
                key["median_age_calculated"],
                key["title"],
                key["disposition_name"],
            ): key
            for key in msa_group_dict
        }

        # Update msa_group_dict into default_data_dict
        default_data_dict.update(msa_group_dict)
        transformed_data_dict.update(default_data_dict)

    # Convert to DataFrame
    return pd.DataFrame.from_dict(transformed_data_dict, orient="index")


def create_default_data(
    msa: str, msa_name: str, disposition_name: str, title: str
) -> List[Dict]:
    """Create a list of default dispositions for each age range.

    Args:
        msa_md (str): The msa_md for the disposition.
        msa_md_name (str): The msa_md name for the disposition.
        dispositio_name (str): The name of the disposition.
        title (str): The title of the disposition.
    Returns:
        A list of dictionaries containing the default dispositions for each age range.
    """

    age_ranges = [
        "Age Unknown",
        "1969 or Earlier",
        "1970 - 1979",
        "1980 - 1989",
        "1990 - 1999",
        "2000 - 2010",
        "2011 - Present",
    ]
    default_data = {
        "msa_md": msa,
        "msa_md_name": msa_name,
        "disposition_name": disposition_name,
        "title": title,
        "loan_amount": 0,
        "count": 0,
    }
    default_data_list = []
    for age_range in age_ranges:
        data_with_age_range = default_data.copy()
        data_with_age_range["median_age_calculated"] = age_range
        default_data_list.append(data_with_age_range)

    return default_data_list


def median_age_output_collection_table(
    aggregate_report_9_df: pd.DataFrame,
) -> pd.DataFrame:
    """Creates pre-processed disposition data for aggregate report 9.

    Args:
        aggregate_report_9_df (pd.DataFrame): The input DataFrame.
    Returns:
        A DataFrame for disposition data for aggregate report 9.
    """

    actions_taken = {
        "Loans Originated": [1],
        "Applications Approved but not Accepted": [2],
        "Applications Denied by Financial Institution": [3],
        "File Closed for Incompleteness": [5],
        "Applications Withdrawn by Applicant": [4],
        "Applications Received": [1, 2, 3, 4, 5],
    }

    output_a_table_list = []
    output_b_table_list = []
    output_c_table_list = []
    output_d_table_list = []
    output_e_table_list = []
    output_f_table_list = []
    output_g_table_list = []

    all_unique_msa_md_tract = aggregate_report_9_df[
        ["msa_md", "msa_md_name", "median_age_calculated"]
    ].drop_duplicates()

    for description in actions_taken.keys():

        output_a_table_list.append(
            transformation_add_default_data(
                disposition_a(
                    aggregate_report_9_df,
                    description,
                    actions_taken[description],
                    all_unique_msa_md_tract,
                )
            )
        )

        output_b_table_list.append(
            transformation_add_default_data(
                disposition_b(
                    aggregate_report_9_df,
                    description,
                    actions_taken[description],
                    all_unique_msa_md_tract,
                )
            )
        )

        output_c_table_list.append(
            transformation_add_default_data(
                disposition_c(
                    aggregate_report_9_df,
                    description,
                    actions_taken[description],
                    all_unique_msa_md_tract,
                )
            )
        )

        output_d_table_list.append(
            transformation_add_default_data(
                disposition_d(
                    aggregate_report_9_df,
                    description,
                    actions_taken[description],
                    all_unique_msa_md_tract,
                )
            )
        )

        output_e_table_list.append(
            transformation_add_default_data(
                disposition_e(
                    aggregate_report_9_df,
                    description,
                    actions_taken[description],
                    all_unique_msa_md_tract,
                )
            )
        )
        output_f_table_list.append(
            transformation_add_default_data(
                disposition_f(
                    aggregate_report_9_df,
                    description,
                    actions_taken[description],
                    all_unique_msa_md_tract,
                )
            )
        )
        output_g_table_list.append(
            transformation_add_default_data(
                disposition_g(
                    aggregate_report_9_df,
                    description,
                    actions_taken[description],
                    all_unique_msa_md_tract,
                )
            )
        )

    output_a_table = pd.concat(output_a_table_list)
    output_b_table = pd.concat(output_b_table_list)
    output_c_table = pd.concat(output_c_table_list)
    output_d_table = pd.concat(output_d_table_list)
    output_e_table = pd.concat(output_e_table_list)
    output_f_table = pd.concat(output_f_table_list)
    output_g_table = pd.concat(output_g_table_list)

    return pd.concat(
        [
            output_a_table,
            output_b_table,
            output_c_table,
            output_d_table,
            output_e_table,
            output_f_table,
            output_g_table,
        ]
    )


def build_sorted_median_age(median_age, loan_categories):
    """Adds the field ageForSorting to the median ages disposition dictionary.

    Args:
        median_age (str): The median age range of homes.
        loan_categories (list): A list of disposition data.
    Returns:
        A dictionary of disposition data containing a new field ageForSorting.
    """

    if median_age == "2011 - Present":
        age_for_sorting = "(A)"
    elif median_age == "2000 - 2010":
        age_for_sorting = "(B)"
    elif median_age == "1990 - 1999":
        age_for_sorting = "(C)"
    elif median_age == "1980 - 1989":
        age_for_sorting = "(D)"
    elif median_age == "1970 - 1979":
        age_for_sorting = "(E)"
    elif median_age == "1969 or Earlier":
        age_for_sorting = "(F)"
    else:
        age_for_sorting = "(G)"

    return {
        "medianAge": median_age,
        "loanCategories": loan_categories,
        "ageForSorting": age_for_sorting,
    }
