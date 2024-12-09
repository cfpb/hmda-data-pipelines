# HMDA ETL Pipeline V2

The purpose of this data pipeline is to consolidate the various HMDA data processes currently in existence with a single codebase. Version 1 of the ETL Pipeline consumed flat files from S3 which were produced by the __Data Publisher__ pipeline, processed said flat files, and wrote them to S3. From here, these files were accessible by Dask and Athena for analysis. See the [README file](https://github.cfpb.gov/HMDA-Operations/analytics_environment) from the original repo for additional details. This pipeline reads directly form Postgres. 

## Version 1 vs. Version 2

The two major differences between version 1 of the pipeline and this version are:
- Raw data is consumed from production Postgres rather than from downstream flat files. 
- This codebase leverages [Kedro](https://docs.kedro.org/en/stable/introduction/index.html) to enhance readability, testability, and maintainability of the code. 

Additionally, version 2 handles disclosure and aggregation report generation, which was not handled by version 1 of the pipeline. It also handles both quarterly and annual dataset generation, as well as metrics for internal use, such as dataset row count and validations.

This version contains several pipelines:
- Ingestion
  - The `ingest_data_from_pg` pipeline produces parquet files of the raw data stored within Postgres.
- Data Publisher
  - The `data_publisher` pipeline uses the raw parquet files created by the `ingest_data_from_pg` pipeline to generate flat files for regulator and public datasets like LAR, Modified LAR, Transmittal Sheet, Panel (institutions), etc.
- Aggregate and Disclosure reports
  - The `aggregate_and_disclosure_reports` uses some of the datasets created by the `data_publsiher` pipeline to generate aggregate and disclosure report files.

## Prerequisite: Learn the Basics of Kedro

This codebase will be a heck of a lot easier to make sense of once you work through the [official Kedro tutorial](https://docs.kedro.org/en/stable/tutorial/spaceflights_tutorial.html).

## Python Environment Setup

You'll need a Python 3.9 or 3.10 environment to run the code. Python 3.11+ is not ready for production use. I recommend installing `conda` and utilizing a virtual environment. Download Anaconda [here](https://www.anaconda.com/download) and make sure `conda` is available on your `PATH`. Once the virtual environment is created, use Pip to install the requirements file by running `pip install -r hmda-etl-pipeline/src/requirements.txt` from the root of the repository. 

The last thing you'll need is a credentials file that Kedro will use to connect to the various data backends. Create a file called `credentials.yaml` within `hmda-etl-pipeline/conf/base`. Message Johnathon or David for the file contents. This file is ignored by git. Do not rename the file or add the file to git. 

### Local Deployment

Running locally is trivial. Once you've set up your Python environment and installed the needed modules, simply run `kedro run --tags "YYYY_Filing_Season"` from within the `hmda-etl-pipeline` directory. This will run the entire pipeline for the supplied year. Valid `YYYY` values include 2019 through 2023. 

If you receive an error indicating that credentials cannot be located, make sure you have created a `credentials.yaml` file within the `conf/base/` directory. It will take approximately __2 hours__ to run the entire pipeline beginning to end for the LAR or MLAR datasets. The longest part is consuming and processing the LAR data from Postgres. Other data publisher datasets should take 20 minutes or less to run.

Kedro Viz can be launched by running `kedro viz` from the `hmda-etl-pipeline`. Accessing http://localhost:4141 will open the web interface where you can explore the pipeline graphically. 


#### Create local secrets

- Base Credentails (`hmda-etl-pipeline/conf/base/credentials.yaml`)
```
production_pg_readonly:
  con: "postgresql+psycopg2://dbuser1:passsword1@example1.us-east-1.rds.amazonaws.com/hmda" 
s3-bucket-1:
  client_kwargs:
    aws_access_key_id: EXMPLE1
    aws_secret_access_key: EXAMPLEKEY1
```
Note: If DB password has special characters it must be [encoded](https://stackoverflow.com/questions/23353623/how-to-handle-special-characters-in-the-password-of-a-postgresql-url-connection)
- Dev Credentails (`hmda-etl-pipeline/conf/dev/credentials.yaml`)
```
dev_pg_readonly:
  con: "postgresql+psycopg2://dbuser1:passsword1@example1.us-east-1.rds.amazonaws.com/hmda" 
```
- Dev Env configuration (`hmda-etl-pipeline/conf/dev/globals.yaml`)
```
regulator_path_prefix: s3://s3-bucket-1/dev/kedro-etl-pipeline/regulator
archive_public_path_prefix: s3://s3-bucket-1/dev/kedro-etl-pipeline/archive-public
public_path_prefix: s3://s3-bucket-1/dev/kedro-etl-pipeline/public
reports_path_prefix: s3://s3-bucket-1/dev/kedro-etl-pipeline/reports
credentials: s3-bucket-1
mm_url: mattermost-hook-url
```
Note: `mm_url` can also be set as in the params list in the kedro run command
- Kedro viz `requires` AWS credentials as environment [variables](https://docs.kedro.org/projects/kedro-viz/en/stable/publish_and_share_kedro_viz_on_aws.html#set-credentials)

## Kedro Environments

You'll notice that there are several folders under `hmda-etl-pipeline/conf/`. These correspond to different environments. I suggest giving the [Kedro Configuration docs](https://docs.kedro.org/en/0.18.5/kedro_project_setup/configuration.html) a read. The `base` environment is always loaded by Kedro. The other environments defined underneath `conf` can be used to change the default behaviors of `base`. 

At present, `dev` and `local` are used to change where Kedro stores data and where the raw Postgres data is loaded from. This is still in flux and will likely change once we move towards production. 
- When running in the local env, files will be saved locally, and no Mattermost notifications will be made.
- When running in dev env on a local machine (not in the kubernetes cluster), no mattermost notifications will be made unless the kedro run parameter `mm_url` is set with the correct mattermost webhook url
- When running in the dev env, files will be saved in S3 buckets, and some Mattermost notifications will be made unless the kedro run parameter `--params=post_to_mm=False` is used.
- More verbose mattermost notifications can be turned on when `--params=post_to_mm_verbose=False` is used.

#### Local run with python virtual environment on Mac
- Running a kedro command without the `to-outputs` tag is not recommended. The kedro pipelines handle many different datasets, which require too much time and memory to be reasonably run at once.
- See the [kubernetes README](https://github.cfpb.gov/HMDA-Operations/kedro-etl-pipeline/blob/main/kubernetes/README.md) for example kedro run commands

```
python --version
Python 3.11.5 (Do not use unsupport python versions)

$HOME/homebrew/bin/python3.10 --version
Python 3.10.9

$HOME/homebrew/bin/python3.10 -m venv kedro1
source kedro1/bin/activate
(kedro1) $ export PYTHONWARNINGS="ignore::UserWarning"
(kedro1) $ pip install --upgrade pip
(kedro1) $ pip install --no-cache -r hmda-etl-pipeline/src/requirements.txt
(kedro1) $ kedro info
 _            _
| | _____  __| |_ __ ___
| |/ / _ \/ _` | '__/ _ \
|   <  __/ (_| | | | (_) |
|_|\_\___|\__,_|_|  \___/
v0.18.12

(kedro1) $ export CURRENT_YEAR="2023_Filing_Season"
(kedro1) $ export KEDRO_DEV="dev"
(kedro1) $ export AWS_ACCESS_KEY_ID=" "
(kedro1) $ export AWS_SECRET_ACCESS_KEY=" "
(kedro1) $ export AWS_DEFAULT_REGION="us-east-1"

(kedro1) $ cd /hmda-etl-pipeline/ && kedro run --tags="$CURRENT_YEAR" --env=$KEDRO_DEV --to-outputs="public_ts_flat_file_2023"

(kedro1)  $ deactivate
rm -rf kedro1
```

#### Running in VS Code
- Create a `launch.json` file in the `.vscode` folder
- Add common run configurations to quickly and easily run kedro commands
- This is also useful for small kedro reporting runs, such as generating disclosure reports for a list of lei or aggregate reports for a list of msa.
- Run kedro in the VS Code "Run and Debug" tab with the desired config selected


Example `.vscode/launch.json` file:
```
{
    // Use IntelliSense to learn about possible attributes.
    // Hover to view descriptions of existing attributes.
    // For more information, visit: https://go.microsoft.com/fwlink/?linkid=830387
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Kedro 2023 Filing Season - lei list disclosure reports",
            "type": "debugpy",
            "request": "launch",
            "console": "integratedTerminal",
            "cwd": "${workspaceFolder}/hmda-etl-pipeline",
            "module": "kedro",
            "args": [
                "run",
                "--pipeline",
                "aggregate_and_disclosure_reports",
                "--tags",
                "2023_Filing_Season",
                "--to-outputs",
                "disclosure_reports_2023",
                "--params",
                "use_lei_list=True",
                "--env",
                "dev"
            ],
            "env": {
                "SQLALCHEMY_SILENCE_UBER_WARNING": "1"
            }
            // Any other arguments should be passed as a comma-seperated-list
            // e.g "args": ["run", "--pipeline", "pipeline_name"]
        },
        {
            "name": "Kedro 2022 Filing Season - msa list aggregate reports",
            "type": "debugpy",
            "request": "launch",
            "console": "integratedTerminal",
            "cwd": "${workspaceFolder}/hmda-etl-pipeline",
            "module": "kedro",
            "args": [
                "run",
                "--pipeline",
                "aggregate_and_disclosure_reports",
                "--tags",
                "2022_Filing_Season",
                "--to-outputs",
                "aggregate_reports_2022",
                "--params",
                "use_lei_list=False,use_msa_list=True,skip_existing_reports=False'",
                "--env",
                "dev"
            ],
            "env": {
                "SQLALCHEMY_SILENCE_UBER_WARNING": "1"
            }
            // Any other arguments should be passed as a comma-seperated-list
            // e.g "args": ["run", "--pipeline", "pipeline_name"]
        },
        {
            "name": "Kedro 2023 Filing Season - Regulator TS quarter 1",
            "type": "debugpy",
            "request": "launch",
            "console": "integratedTerminal",
            "cwd": "${workspaceFolder}/hmda-etl-pipeline",
            "module": "kedro",
            "args": [
                "run",
                // "--pipeline",
                // "data_publisher",
                "--tags",
                "2023_Filing_Season",
                "--to-outputs",
                "regulator_ts_flat_file_2023_q1",
                "--params",
                "post_to_mm=False",
                "--env",
                "dev"
            ],
            "env": {
                "SQLALCHEMY_SILENCE_UBER_WARNING": "1"
            }
            // Any other arguments should be passed as a comma-seperated-list
            // e.g "args": ["run", "--pipeline", "pipeline_name"]
        },
        {
            "name": "Kedro 2023 Filing Season - institutions",
            "type": "debugpy",
            "request": "launch",
            "console": "integratedTerminal",
            "cwd": "${workspaceFolder}/hmda-etl-pipeline",
            "module": "kedro",
            "args": [
                "run",
                // "--pipeline",
                // "data_publisher",
                "--tags",
                "2023_Filing_Season",
                "--to-outputs",
                "institutions_flat_file_2023",
                "--params",
                "post_to_mm=False",
                "--env",
                "dev"
            ],
            "env": {
                "SQLALCHEMY_SILENCE_UBER_WARNING": "1"
            }
            // Any other arguments should be passed as a comma-seperated-list
            // e.g "args": ["run", "--pipeline", "pipeline_name"]
        },
    ]
}
```

### Docker Deployment
Note: kedro versions in [`pyproject.toml`](hmda-etl-pipeline/pyproject.toml)and [`requirements.txt`](hmda-etl-pipeline/src/requirements.txt) must match  
- Update/Uncomment ENV variables
```
# ENV CURRENT_YEAR="2023_Filing_Season"
# ENV KEDRO_DEV="dev"
# ENV AWS_ACCESS_KEY_ID=" "
# ENV AWS_SECRET_ACCESS_KEY=" "
# ENV AWS_DEFAULT_REGION="us-east-1"
## CMD cd /hmda-etl-pipeline/ && /bin/bash && kedro run --tags="$CURRENT_YEAR" --env=$KEDRO_DEV --to-outputs="public_ts_flat_file_2023"
```
```
docker build -t local-kedro  .
```
#### Docker run
Note: cfpb-export-bucket service account does NOT work
```
docker run -it -v /Users/joshib/workdir/kedro-baseline/dockerfile-creds-master:/tmp/kedro  local-kedro /bin/bash

kedro_docker@883bb32e517f:/$ cd /tmp/kedro
cp hmda-etl-pipeline_conf_base_credentials.yaml /hmda-etl-pipeline/conf/base/credentials.yaml 
cp hmda-etl-pipeline_conf_dev_credentials.yaml /hmda-etl-pipeline/conf/dev/credentials.yaml
cp hmda-etl-pipeline_conf_dev_globals.yaml /hmda-etl-pipeline/conf/dev/globals.yaml

export SQLALCHEMY_SILENCE_UBER_WARNING="1"

export AWS_SECRET_ACCESS_KEY=" "
export AWS_ACCESS_KEY_ID=" "
export AWS_DEFAULT_REGION="us-east-1"

cd /hmda-etl-pipeline/ 

kedro run --tags="2023_Filing_Season" --env=dev --to-outputs="public_ts_flat_file_2023"
```

### Kubernetes Deployment
See [kubernetes README](https://github.cfpb.gov/HMDA-Operations/kedro-etl-pipeline/blob/main/kubernetes/README.md)

- The kubernetes kedro job configs are used for generating data publisher datasets on a schedule.
- It is also recommended to use these job configs instead of local runs when generating the larger datasets like LAR, MLAR, and the aggregate and disclosure reports, as these can take a long time to complete and require more memory to run than the other datasets.