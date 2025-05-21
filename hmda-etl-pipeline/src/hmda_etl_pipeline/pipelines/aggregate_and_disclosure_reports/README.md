# Pipeline aggregate_and_disclosure_reports

## Overview

The purpose of this pipeline is to consume reduced LAR data, institution data, and a state/county code mapping, which is then used to create aggregate and disclosure reports. 

The state/county mapping file is generated in the ingest_data_from_pg pipeline. The reduced LAR flat file and the institution file are generated in the data_publisher pipeline. These files only need to be created once for each year. 

The state_county_mapping_{year} input relies on the output of the get_state_county_code_mapping function in the ingest_data_from_pg pipeline node, taking a dataframe generated from the cbsa_county_name.csv file. These files are irregularly updated and published by the US Census Bureau [here](https://www.census.gov/geographies/reference-files/time-series/demo/metro-micro/delineation-files.html), and when Census updates the file we must also update the file we use in our pipeline. The current file is dated July 2023. It should be downloaded, converted to .CSV format, and stripped of table names and meta information kept in the header and footer before being placed in the appropriate folders to run as part of the Kedro pipeline. 

## Pipeline inputs

reduced_lar_for_disclosure_reports_flat_file_{year}
institutions_flat_file_{year}
state_county_mapping_{year}

## Pipeline outputs

aggregate_reports_{year}
disclosure_reports_{year}
