"""
Generate aggregate and disclosure reports. 
"""

from kedro.pipeline import Pipeline, node, pipeline

from .nodes import create_aggregate_reports, create_disclosure_reports

# this will be supplied to create_pipeline below
nodes = []

for year in (2019, 2020, 2021, 2022, 2023):
    nodes += [
        node(
            create_aggregate_reports,
            inputs=[
                f"params:report_{year}",
                f"institutions_flat_file_{year}",
                "params:institutions_columns",
                f"reduced_lar_reports_parquet_{year}",
                "params:reduced_lar_columns",
                f"state_county_mapping_{year}",
                f"params:aggregate_reports_path_for_year_{year}",
                f"params:use_lei_list",
                f"lei_list_aggregate_{year}",
                f"params:use_msa_list",
                f"msa_list_{year}",
                f"params:skip_existing_reports",
            ],
            outputs=f"aggregate_reports_{year}",
            tags=f"{year}_Filing_Season",
            name=f"generate_aggregate_reports_for_{year}",
        ),
        node(
            create_disclosure_reports,
            inputs=[
                f"params:report_{year}",
                f"institutions_flat_file_{year}",
                "params:institutions_columns",
                f"reduced_lar_reports_parquet_{year}",
                "params:reduced_lar_columns",
                f"state_county_mapping_{year}",
                f"params:disclosure_reports_path_for_year_{year}",
                f"params:use_lei_list",
                f"lei_list_disclosure_{year}",
                f"params:skip_existing_reports",
            ],
            outputs=f"disclosure_reports_{year}",
            tags=f"{year}_Filing_Season",
            name=f"generate_disclosure_reports_for_{year}",
        ),
    ]


def create_pipeline(**kwargs) -> Pipeline:
    return pipeline(nodes)
