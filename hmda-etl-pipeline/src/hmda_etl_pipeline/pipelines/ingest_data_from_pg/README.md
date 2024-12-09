# Pipeline ingest_data_from_pg

## Overview

The purpose of this pipeline is to consume LAR, TS, and Panel data from production Postgres and create parquet analogs of each table. LAR data is written as a partitioned dataset and consumed from Postgres in chunks of 100k rows, while TS and Institutions (Panel) are small enough that they can be consumed and processed in a single partition/file. 

Prior to consuming LAR data, some count validation occurs. It is checked that each LEI in LAR has a corresponding entry in Panel and TS, and that the number of records present within LAR for a given LEI correspond with the `total_lines` field within TS for the given LEI. If this check fails, a runtime error is raised and processed halts. 

## Running this Pipeline

**Note that this pipeline takes approximately 60 to 90 minutes to run.** Reading the LAR data from production Postgres is a time consuming process. Luckily, it only needs to be done once and subsequent pipelines can leverage the parquet files stored on disk. The pipeline can be run in its entirety for a given filing season by running the following command. Substitute `YYYY` below for 2018 through 2023. 

```bash
kedro run --pipeline=ingest_data_from_pg --tags="YYYY Filing Season"
```

If you see the error `Error: No such command 'run'.` you'll need to make sure you're in the correct directory. The run command should be executed from the root of the kedro project. This directory is `/path/to/repo/hmda-etl-pipeline`. 