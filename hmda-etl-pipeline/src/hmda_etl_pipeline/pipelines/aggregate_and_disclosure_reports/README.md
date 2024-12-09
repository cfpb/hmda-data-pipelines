# Pipeline aggregate_and_disclosure_reports

## Overview

The purpose of this pipeline is to consume reduced LAR data, institution data, and a state/county code mapping, which is then used to create aggregate and disclosure reports. 

The state/county mapping file is generated in the ingest_data_from_pg pipeline. The reduced LAR flat file and the institution file are generated in the data_publisher pipeline. These files only need to be created once for each year. 

## Pipeline inputs

reduced_lar_for_disclosure_reports_flat_file_{year}
institutions_flat_file_{year}
state_county_mapping_{year}

## Pipeline outputs

aggregate_reports_{year}
disclosure_reports_{year}
