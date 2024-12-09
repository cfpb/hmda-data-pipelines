from typing import List
import pandas as pd
from .constants import NA_LIST


def prepare(df: pd.DataFrame) -> pd.DataFrame:
    """Removes rows from a DataFrame if the msa_md or tract columns have NA values.

    Args:
        df (pd.DataFrame): The input DataFrame to be filtered.
    Returns:
        A Dataframe with NA values for msa_md and tract data filtered out.
    """

    # Filter out NA values
    filtered_df = df[
        (df["msa_md"] != "0")
        & (~df["tract"].isin(NA_LIST))
    ]

    return filtered_df


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
        on=["tract", "msa_md"],
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

    # Set columns
    left_anti["loan_amount"] = 0.0
    left_anti["count"] = 0

    # Combine
    left_anti = pd.concat([left_anti, disp_input])
    left_anti["disposition_name"] = disposition_name
    left_anti["title"] = title

    return left_anti


def disposition_a(
    input: pd.DataFrame,
    title: str,
    actions_taken: List[int],
    all_unique_msa_md_tract: pd.DataFrame,
) -> pd.DataFrame:
    """Creates disposition A for the disposition name "FHA, FSA/RHS & VA (A)".

    Args:
        input (pd.DataFrame): The input DataFrame used to create the disposition data.
        title (str): The title for the disposition.
        actions_taken (List[int]): A list of actions_taken values to be kept in the
            disposition data.
        all_unique_msa_md_tract (pd.DataFrame): A DataFrame grouped by tract, msa_md,
            and msa_md_name.
    Returns:
        A DataFrame for disposition A containing data for the disposition name
            "FHA, FSA/RHS & VA (A)".
    """

    disp_a = prepare(input)

    disp_a = disp_a[disp_a["action_taken_type"].isin(actions_taken)]
    disp_a = disp_a[disp_a["total_units"].isin([1, 2, 3, 4])]
    disp_a = disp_a[disp_a["loan_purpose"] == 1]
    disp_a = disp_a[disp_a["loan_type"].isin([2, 3, 4])]

    disp_a = add_count_and_loan_amount_sum_columns(disp_a)

    return include_zero_and_non_zero(
        disp_a, title, "FHA, FSA/RHS & VA (A)", all_unique_msa_md_tract
    )


def disposition_b(
    input: pd.DataFrame,
    title: str,
    actions_taken: List[int],
    all_unique_msa_md_tract: pd.DataFrame,
) -> pd.DataFrame:
    """Creates disposition B for the disposition name "Conventional (B)".

    Args:
        input (pd.DataFrame): The input DataFrame used to create the disposition data.
        title (str): The title for the disposition.
        actions_taken (List[int]): A list of actions_taken values to be kept in the
            disposition data.
        all_unique_msa_md_tract (pd.DataFrame): A DataFrame grouped by tract, msa_md,
            and msa_md_name.
    Returns:
        A DataFrame for disposition B containing data for the disposition name
            "Conventional (B)".
    """

    disp_b = prepare(input)

    disp_b = disp_b[disp_b["action_taken_type"].isin(actions_taken)]
    disp_b = disp_b[disp_b["total_units"].isin([1, 2, 3, 4])]
    disp_b = disp_b[disp_b["loan_purpose"] == 1]
    disp_b = disp_b[disp_b["loan_type"] == 1]

    disp_b = add_count_and_loan_amount_sum_columns(disp_b)

    return include_zero_and_non_zero(
        disp_b, title, "Conventional (B)", all_unique_msa_md_tract
    )


def disposition_c(
    input: pd.DataFrame,
    title: str,
    actions_taken: List[int],
    all_unique_msa_md_tract: pd.DataFrame,
) -> pd.DataFrame:
    """Creates disposition C for the disposition name "Refinancings (C)".

    Args:
        input (pd.DataFrame): The input DataFrame used to create the disposition data.
        title (str): The title for the disposition.
        actions_taken (List[int]): A list of actions_taken values to be kept in the
            disposition data.
        all_unique_msa_md_tract (pd.DataFrame): A DataFrame grouped by tract, msa_md,
            and msa_md_name.
    Returns:
        A DataFrame for disposition C containing data for the disposition name
            "Refinancings (C)".
    """

    disp_c = prepare(input)

    disp_c = disp_c[disp_c["action_taken_type"].isin(actions_taken)]
    disp_c = disp_c[disp_c["total_units"].isin([1, 2, 3, 4])]
    disp_c = disp_c[disp_c["loan_purpose"].isin([31, 32])]

    disp_c = add_count_and_loan_amount_sum_columns(disp_c)

    return include_zero_and_non_zero(
        disp_c, title, "Refinancings (C)", all_unique_msa_md_tract
    )


def disposition_d(
    input: pd.DataFrame,
    title: str,
    actions_taken: List[int],
    all_unique_msa_md_tract: pd.DataFrame,
) -> pd.DataFrame:
    """Creates disposition D for the disposition name "Home Improvement Loans (D)".

    Args:
        input (pd.DataFrame): The input DataFrame used to create the disposition data.
        title (str): The title for the disposition.
        actions_taken (List[int]): A list of actions_taken values to be kept in the
            disposition data.
        all_unique_msa_md_tract (pd.DataFrame): A DataFrame grouped by tract, msa_md,
            and msa_md_name.
    Returns:
        A DataFrame for disposition D containing data for the disposition name
            "Home Improvement Loans (D)".
    """

    disp_d = prepare(input)
    disp_d = disp_d[disp_d["action_taken_type"].isin(actions_taken)]
    disp_d = disp_d[disp_d["total_units"].isin([1, 2, 3, 4])]
    disp_d = disp_d[disp_d["loan_purpose"] == 2]

    disp_d = add_count_and_loan_amount_sum_columns(disp_d)

    return include_zero_and_non_zero(
        disp_d, title, "Home Improvement Loans (D)", all_unique_msa_md_tract
    )


def disposition_e(
    input: pd.DataFrame,
    title: str,
    actions_taken: List[int],
    all_unique_msa_md_tract: pd.DataFrame,
) -> pd.DataFrame:
    """Creates disposition E for the disposition name "Loans on Dwellings For 5 or More Families (E)".

    Args:
        input (pd.DataFrame): The input DataFrame used to create the disposition data.
        title (str): The title for the disposition.
        actions_taken (List[int]): A list of actions_taken values to be kept in the
            disposition data.
        all_unique_msa_md_tract (pd.DataFrame): A DataFrame grouped by tract, msa_md,
            and msa_md_name.
    Returns:
        A DataFrame for disposition E containing data for the disposition name
            "Loans on Dwellings For 5 or More Families (E)".
    """

    disp_e = prepare(input)
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
    input: pd.DataFrame,
    title: str,
    actions_taken: List[int],
    all_unique_msa_md_tract: pd.DataFrame,
) -> pd.DataFrame:
    """Creates disposition F for the disposition name "Nonoccupant Loans from Columns A, B, C ,& D (F)".

    Args:
        input (pd.DataFrame): The input DataFrame used to create the disposition data.
        title (str): The title for the disposition.
        actions_taken (List[int]): A list of actions_taken values to be kept in the
            disposition data.
        all_unique_msa_md_tract (pd.DataFrame): A DataFrame grouped by tract, msa_md,
            and msa_md_name.
    Returns:
        A DataFrame for disposition F containing data for the disposition name
            "Nonoccupant Loans from Columns A, B, C ,& D (F)".
    """

    disp_f = prepare(input)
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
    input: pd.DataFrame,
    title: str,
    actions_taken: List[int],
    all_unique_msa_md_tract: pd.DataFrame,
) -> pd.DataFrame:
    """Creates disposition G for the disposition name "Loans On Manufactured Home Dwellings From Columns A, B, C & D (G)".

    Args:
        input (pd.DataFrame): The input DataFrame used to create the disposition data.
        title (str): The title for the disposition.
        actions_taken (List[int]): A list of actions_taken values to be kept in the
            disposition data.
        all_unique_msa_md_tract (pd.DataFrame): A DataFrame grouped by tract, msa_md,
            and msa_md_name.
    Returns:
        A DataFrame for disposition G containing data for the disposition name
           "Loans On Manufactured Home Dwellings From Columns A, B, C & D (G)".
    """

    disp_g = prepare(input)
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
        ["tract", "msa_md", "msa_md_name", "year"], as_index=False
    )
    aggregated_df = grouped_disposition_df.agg(
        loan_amount=("loan_amount", "sum"), count=("loan_amount", "count")
    )
    return aggregated_df


def output_collection_table_1(report_1_df: pd.DataFrame) -> pd.DataFrame:
    """Creates pre-processed disposition data for aggregate or disclosure report 1.

    Args:
        report_1_df (pd.DataFrame): The input DataFrame.
    Returns:
        A DataFrame for disposition data for aggregate or dislosure report 1.
    """

    actions_taken_table_1 = {
        "Loans Originated - (A)": [1],
        "Applications Approved but not Accepted - (B)": [2],
        "Applications Denied by Financial Institution - (C)": [3],
        "Applications Withdrawn by Applicant - (D)": [4],
        "File Closed for Incompleteness - (E)": [5],
        "Applications Received - (F)": [1, 2, 3, 4, 5],
    }

    all_unique_msa_md_tract = report_1_df[
        ["tract", "msa_md", "msa_md_name"]
    ].drop_duplicates()

    output_a_table_1_list = []
    output_b_table_1_list = []
    output_c_table_1_list = []
    output_d_table_1_list = []
    output_e_table_1_list = []
    output_f_table_1_list = []
    output_g_table_1_list = []

    for description in actions_taken_table_1.keys():

        output_a_table_1_list.append(
            disposition_a(
                report_1_df,
                description,
                actions_taken_table_1[description],
                all_unique_msa_md_tract,
            )
        )

        output_b_table_1_list.append(
            disposition_b(
                report_1_df,
                description,
                actions_taken_table_1[description],
                all_unique_msa_md_tract,
            )
        )

        output_c_table_1_list.append(
            disposition_c(
                report_1_df,
                description,
                actions_taken_table_1[description],
                all_unique_msa_md_tract,
            )
        )

        output_d_table_1_list.append(
            disposition_d(
                report_1_df,
                description,
                actions_taken_table_1[description],
                all_unique_msa_md_tract,
            )
        )

        output_e_table_1_list.append(
            disposition_e(
                report_1_df,
                description,
                actions_taken_table_1[description],
                all_unique_msa_md_tract,
            )
        )
        output_f_table_1_list.append(
            disposition_f(
                report_1_df,
                description,
                actions_taken_table_1[description],
                all_unique_msa_md_tract,
            )
        )
        output_g_table_1_list.append(
            disposition_g(
                report_1_df,
                description,
                actions_taken_table_1[description],
                all_unique_msa_md_tract,
            )
        )

    output_a_table_1 = pd.concat(output_a_table_1_list)
    output_b_table_1 = pd.concat(output_b_table_1_list)
    output_c_table_1 = pd.concat(output_c_table_1_list)
    output_d_table_1 = pd.concat(output_d_table_1_list)
    output_e_table_1 = pd.concat(output_e_table_1_list)
    output_f_table_1 = pd.concat(output_f_table_1_list)
    output_g_table_1 = pd.concat(output_g_table_1_list)

    return pd.concat(
        [
            output_a_table_1,
            output_b_table_1,
            output_c_table_1,
            output_d_table_1,
            output_e_table_1,
            output_f_table_1,
            output_g_table_1,
        ]
    )


def output_collection_table_2(report_2_df: pd.DataFrame) -> pd.DataFrame:
    """Creates pre-processed disposition data for aggregate or disclosure report 2.

    Args:
        report_2_df (pd.DataFrame): The input DataFrame.
    Returns:
        A DataFrame for disposition data for aggregate or dislosure report 2.
    """

    description = "Purchased Loans"
    action_list = [6]

    all_unique_msa_md_tract = report_2_df[
        ["tract", "msa_md", "msa_md_name"]
    ].drop_duplicates()

    output_table_2_list = []

    output_table_2_list.append(
        disposition_a(
            report_2_df,
            description,
            action_list,
            all_unique_msa_md_tract,
        )
    )

    output_table_2_list.append(
        disposition_b(
            report_2_df,
            description,
            action_list,
            all_unique_msa_md_tract,
        )
    )

    output_table_2_list.append(
        disposition_c(
            report_2_df,
            description,
            action_list,
            all_unique_msa_md_tract,
        )
    )

    output_table_2_list.append(
        disposition_d(
            report_2_df,
            description,
            action_list,
            all_unique_msa_md_tract,
        )
    )

    output_table_2_list.append(
        disposition_e(
            report_2_df,
            description,
            action_list,
            all_unique_msa_md_tract,
        )
    )
    output_table_2_list.append(
        disposition_f(
            report_2_df,
            description,
            action_list,
            all_unique_msa_md_tract,
        )
    )
    output_table_2_list.append(
        disposition_g(
            report_2_df,
            description,
            action_list,
            all_unique_msa_md_tract,
        )
    )

    return pd.concat(output_table_2_list)
