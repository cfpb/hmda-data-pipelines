"""
Generates data publisher dataset files. These include the LAR, LAR loan limit,
MLAR, Panel, and TS files (including public, regulator, yearly, and quarterly
versions).

Also generate a reduced LAR file to be used for aggregate and disclosure reports. 
"""

import functools as ft

from kedro.pipeline import Pipeline, node, pipeline

from .nodes import (
    convert_lar_to_modified_lar_data,
    create_mlar_flat_file,
    create_lar_flat_file,
    analyze_mlar_flat_file,
    create_institutions_flat_file,
    create_regulator_ts_flat_file,
    create_public_ts_flat_file,
)

# this will be supplied to create_pipeline below
nodes = []


def withkwargs(func, **kwargs):
    wrapper = ft.partial(func, **kwargs)
    ft.update_wrapper(wrapper, func)
    return wrapper


for year in (2019, 2020, 2021, 2022, 2023):
    nodes += [
        # Create regulator LAR flat file
        node(
            create_lar_flat_file,
            inputs=[f"lar_raw_parquets_{year}", "params:regulator_lar_columns"],
            outputs=f"regulator_lar_flat_file_{year}",
            tags=f"{year}_Filing_Season",
            name=f"generate_reg_lar_flat_file_for_{year}",
        ),
        # Create LAR loan limit flat file
        node(
            create_lar_flat_file,
            inputs=[f"lar_raw_parquets_{year}", "params:lar_loan_limit_columns"],
            outputs=f"lar_loan_limit_flat_file_{year}",
            tags=f"{year}_Filing_Season",
            name=f"generate_lar_loan_limit_flat_file_for_{year}",
        ),
        # Convert LAR data to public modified LAR data
        node(
            convert_lar_to_modified_lar_data,
            inputs=[
                f"lar_raw_parquets_{year}",
                "params:public_mlar_legacy_column_names_map_list",
            ],
            outputs=f"public_modified_lar_raw_parquets_{year}",
            tags=f"{year}_Filing_Season",
            name=f"generate_public_modified_lar_for_{year}",
        ),
        # Convert LAR data to combined modified LAR data
        node(
            convert_lar_to_modified_lar_data,
            inputs=[
                f"lar_raw_parquets_{year}",
                "params:combined_mlar_legacy_column_names_map_list",
            ],
            outputs=f"combined_modified_lar_raw_parquets_{year}",
            tags=f"{year}_Filing_Season",
            name=f"generate_combined_modified_lar_for_{year}",
        ),
        # Create public modified LAR flat file
        node(
            create_mlar_flat_file,
            inputs=[f"public_modified_lar_raw_parquets_{year}"],
            outputs=[
                f"public_modified_lar_flat_file_{year}",
                f"archive_public_modified_lar_flat_file_{year}",
            ],
            tags=f"{year}_Filing_Season",
            name=f"generate_public_modified_lar_flat_file_for_{year}",
        ),
        # Create combined modified LAR flat file and header file
        node(
            create_mlar_flat_file,
            inputs=[f"combined_modified_lar_raw_parquets_{year}"],
            outputs=[
                f"combined_modified_lar_noheader_flat_file_{year}",
                f"combined_modified_lar_header_flat_file_{year}",
            ],
            tags=f"{year}_Filing_Season",
            name=f"generate_combined_modified_lar_flat_file_for_{year}",
        ),
        # Analyze modified LAR flat file
        node(
            withkwargs(analyze_mlar_flat_file, year=year),
            inputs=[f"public_modified_lar_flat_file_{year}", "parameters"],
            outputs=f"analyzed_mlar_flat_file_{year}",
            tags=f"{year}_Filing_Season",
            name=f"generate_analyzed_mlar_flat_file_for_{year}",
        ),
        # Create panel flat file
        node(
            create_institutions_flat_file,
            inputs=[
                f"institutions_raw_parquet_{year}",
                f"institutions_email_domains_raw_parquet_{year}",
                f"ts_raw_parquet_{year}",
                "params:institutions_columns",
            ],
            outputs=f"institutions_flat_file_{year}",
            tags=f"{year}_Filing_Season",
            name=f"generate_institutions_flat_file_for_{year}",
        ),
        # Create reduced LAR flat file used for aggregate and disclosure reports
        node(
            create_lar_flat_file,
            inputs=[
                f"lar_raw_parquets_{year}",
                "params:reduced_lar_columns",
            ],
            outputs=f"reduced_lar_reports_parquet_{year}",
            tags=f"{year}_Filing_Season",
            name=f"generate_reduced_lar_reports_for_{year}",
        ),
        # Create regulator transmittal sheet flat file
        node(
            create_regulator_ts_flat_file,
            inputs=[f"ts_raw_parquet_{year}", "params:regulator_ts_columns"],
            outputs=f"regulator_ts_flat_file_{year}",
            tags=f"{year}_Filing_Season",
            name=f"generate_regulator_ts_flat_file_for_{year}",
        ),
        # Create public transmittal sheet flat file
        node(
            create_public_ts_flat_file,
            inputs=[
                f"ts_raw_parquet_{year}",
                "params:public_ts_legacy_column_names_map_list",
            ],
            outputs=[
                f"public_ts_flat_file_{year}",
                f"archive_public_ts_flat_file_{year}",
            ],
            tags=f"{year}_Filing_Season",
            name=f"generate_public_ts_flat_file_for_{year}",
        ),
    ]

    for quarter in ("q1", "q2", "q3"):
        nodes += [
            # Create LAR quarterly flat file
            node(
                create_lar_flat_file,
                inputs=[
                    f"lar_raw_parquets_{year}_{quarter}",
                    "params:regulator_lar_columns",
                ],
                outputs=f"regulator_lar_flat_file_{year}_{quarter}",
                tags=[f"{year}_Filing_Season", f"{year}_{quarter}_Filing_Season"],
                name=f"generate_reg_lar_flat_file_for_{year}_{quarter}",
            ),
            # Create regulator transmittal sheet quarterly flat file
            node(
                create_regulator_ts_flat_file,
                inputs=[
                    f"ts_raw_parquet_{year}_{quarter}",
                    "params:regulator_ts_columns",
                ],
                outputs=f"regulator_ts_flat_file_{year}_{quarter}",
                tags=[f"{year}_Filing_Season", f"{year}_{quarter}_Filing_Season"],
                name=f"generate_regulator_ts_flat_file_for_{year}_{quarter}",
            ),
        ]


def create_pipeline(**kwargs) -> Pipeline:
    return pipeline(nodes, tags="data_publisher")
