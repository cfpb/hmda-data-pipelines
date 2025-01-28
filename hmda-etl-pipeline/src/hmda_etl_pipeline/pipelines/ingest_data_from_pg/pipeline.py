"""
Performs basic record count validation on LAR, TS, and Panel prior to
continuing with parquet file creation. This pipeline will riase a 
runtime error if the count validation step fails, thereby halting the 
entire pipeline. 

LAR is written as a partitioned dataset while TS and Institutions are 
written as single files. The paths where these files are persisted are
specified within the data_paths.yaml files in conf/dev and conf/local. 
"""

from kedro.pipeline import Pipeline, node, pipeline

from .nodes import (
    persist_institutions_email_domains_table,
    persist_institutions_table,
    persist_ts_table,
    process_lar_partitions,
    validate_counts,
    get_state_county_code_mapping,
)

# this will be supplied to create_pipeline below
nodes = []

for year in (2019, 2020, 2021, 2022, 2023, 2024):
    nodes += [
        # perform count validation
        node(
            validate_counts,
            inputs={
                "lar_counts_by_lei": f"pg_lar_counts_by_lei_{year}",
                "ts": f"pg_ts_{year}",
                "institutions": f"pg_institutions_{year}",
            },
            outputs=f"count_verification_passed_{year}",
            tags=[f"{year}_Filing_Season", f"{year}_Annual_Filing_Season"],
            name=f"validate_counts_for_{year}",
        ),
        # write LAR partitions from postgres to parquet files
        node(
            process_lar_partitions,
            inputs={
                "pg_lar_data": f"pg_lar_{year}",
                "column_dtypes": "params:pg_lar_dtypes",
                "count_verification_passed": f"count_verification_passed_{year}",
            },
            outputs=f"lar_raw_parquets_{year}",
            tags=[f"{year}_Filing_Season", f"{year}_Annual_Filing_Season"],
            name=f"write_raw_lar_partitions_to_parquet_files_{year}",
        ),
        # write email domains table to parquet file
        node(
            persist_institutions_email_domains_table,
            inputs=[
                f"pg_institutions_email_domains_{year}",
                "params:pg_institutions_email_domains_dtypes",
            ],
            outputs=f"institutions_email_domains_raw_parquet_{year}",
            tags=[f"{year}_Filing_Season", f"{year}_Annual_Filing_Season"],
            name=f"write_institutions_email_domains_table_to_parquet_file_{year}",
        ),
        # write institutions table to parquet file
        node(
            persist_institutions_table,
            inputs=[
                f"pg_institutions_{year}",
                "params:pg_institutions_dtypes",
                f"count_verification_passed_{year}",
            ],
            outputs=f"institutions_raw_parquet_{year}",
            tags=[f"{year}_Filing_Season", f"{year}_Annual_Filing_Season"],
            name=f"write_institutions_table_to_parquet_file_{year}",
        ),
        # write transmittal sheet table to parquet file
        node(
            persist_ts_table,
            inputs=[
                f"pg_ts_{year}",
                "params:pg_ts_dtypes",
                f"count_verification_passed_{year}",
            ],
            outputs=f"ts_raw_parquet_{year}",
            tags=[f"{year}_Filing_Season", f"{year}_Annual_Filing_Season"],
            name=f"write_ts_table_to_parquet_file_{year}",
        ),
        node(
            get_state_county_code_mapping,
            inputs=[f"pg_cbsa_county_name_{year}", "params:pg_state_county_dtypes"],
            outputs=f"state_county_mapping_{year}",
            tags=[f"{year}_Filing_Season", f"{year}_Annual_Filing_Season"],
            name=f"generate_state_county_mapping_for_reports_for_{year}",
        ),
    ]
    
    for quarter in ("q1", "q2", "q3"):
        nodes += [
            # perform count validation for quarter
            node(
                validate_counts,
                inputs={
                    "lar_counts_by_lei": f"pg_lar_counts_by_lei_{year}_{quarter}",
                    "ts": f"pg_ts_{year}_{quarter}",
                    "institutions": f"pg_institutions_{year}",
                },
                outputs=f"count_verification_passed_{year}_{quarter}",
                tags=[f"{year}_Filing_Season", f"{year}_{quarter}_Filing_Season"],
                name=f"validate_counts_for_{year}_{quarter}",
            ),
            # write LAR quarterly partitions from postgres to parquet files
            node(
                process_lar_partitions,
                inputs={
                    "pg_lar_data": f"pg_lar_{year}_{quarter}",
                    "column_dtypes": "params:pg_lar_dtypes",
                    "count_verification_passed": f"count_verification_passed_{year}_{quarter}",
                },
                outputs=f"lar_raw_parquets_{year}_{quarter}",
                tags=[f"{year}_Filing_Season", f"{year}_{quarter}_Filing_Season"],
                name=f"write_raw_lar_partitions_to_parquet_files_{year}_{quarter}",
            ),
            # write transmittal sheet quarterly table to parquet file
            node(
                persist_ts_table,
                inputs=[
                    f"pg_ts_{year}_{quarter}",
                    "params:pg_ts_dtypes",
                    f"count_verification_passed_{year}_{quarter}",
                ],
                outputs=f"ts_raw_parquet_{year}_{quarter}",
                tags=[f"{year}_Filing_Season", f"{year}_{quarter}_Filing_Season"],
                name=f"write_ts_table_to_parquet_file_{year}_{quarter}",
            ),
        ]


def create_pipeline(**kwargs) -> Pipeline:
    return pipeline(nodes)
