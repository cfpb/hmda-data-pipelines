## Kedro Pipeline is deployed as Kubernetes Job 

### Create k8 secrets from local files
```
cd hmda-etl-pipeline/conf/dev/      
kubectl create secret generic kedro-dev-credentials --from-file=credentials.yaml

cd hmda-etl-pipeline/conf/base/
kubectl create secret generic kedro-base-credentials --from-file=credentials.yaml

cd hmda-etl-pipeline/conf/dev/
kubectl create secret generic kedro-dev-env-config --from-file=globals.yaml
```

### NodeGroups
- Kedro requires a dedicated nodegrop with large instance for initial `data-publisher` and all disclosure reports runs
- Each disclosure reports `run` takes approximately 9 hours
- Delete the node on job completion to save cost
- Currently we only have one large and one regular nodegroup configuration, corresponding job taints/toleration is not year specific, hence reports for different years cannot be run in parallel 

<!-- memory node is used instead of 4x.large
###### m4.4xlarge
```
aws eks create-nodegroup \
--cluster-name awsdevhmda3 \
--nodegroup-name awsdevhmda3kedro-4x \
--scaling-config minSize=1,maxSize=1,desiredSize=1 \
--subnets subnet-04c8252aa9627efb1  \
--instance-types m5.4xlarge \
--remote-access ec2SshKey=CFPB_Default,sourceSecurityGroups=sg-0e94c2387fa0adc74 \
--node-role arn:aws:iam::626560329871:role/hmda-eks-role \
--labels node-group=kedro \
--taints key=node-group,value=kedro,effect=NO_SCHEDULE
```
-->

##### Memory [Node](https://aws.amazon.com/ec2/instance-types/r6a/) (r7g.4xlarge, vCPUs	16, Memory 128G)
- Create Node
```
aws eks create-nodegroup \
--cluster-name awsdevhmda3 \
--nodegroup-name awsdevhmda3kedro-large \
--scaling-config minSize=0,maxSize=1,desiredSize=0 \
--subnets subnet-04c8252aa9627efb1  \
--instance-types r6a.4xlarge \
--remote-access ec2SshKey=CFPB_Default,sourceSecurityGroups=sg-0e94c2387fa0adc74 \
--node-role arn:aws:iam::626560329871:role/hmda-eks-role \
--labels node-group=kedro-large \
--taints key=node-group,value=kedro-large,effect=NO_SCHEDULE
```
- Scale to zero
```
aws eks update-nodegroup-config \
--cluster-name awsdevhmda3 \
--nodegroup-name awsdevhmda3kedro-large \
--scaling-config minSize=0,maxSize=1,desiredSize=0
```
- Scale to one
```
aws eks update-nodegroup-config \
--cluster-name awsdevhmda3 \
--nodegroup-name awsdevhmda3kedro-large  \
--scaling-config minSize=1,maxSize=1,desiredSize=1
```
- Status
```
kubectl get nodes -l "eks.amazonaws.com/nodegroup=awsdevhmda3kedro-large" -w
```
> **_Note:_** Run pod after node is in Ready state

##### Regular [Node](https://aws.amazon.com/ec2/instance-types/m5/) (m5.2xlarge, vCPU	8, Memory 32G) is used for a running a `list of LEIs`
- Create Node
```
aws eks create-nodegroup \
--cluster-name awsdevhmda3 \
--nodegroup-name awsdevhmda3kedro-regular \
--scaling-config minSize=0,maxSize=1,desiredSize=0 \
--subnets subnet-04c8252aa9627efb1  \
--instance-types m5.2xlarge \
--remote-access ec2SshKey=CFPB_Default,sourceSecurityGroups=sg-0e94c2387fa0adc74 \
--node-role arn:aws:iam::626560329871:role/hmda-eks-role \
--labels node-group=kedro-regular \
--taints key=node-group,value=kedro-regular,effect=NO_SCHEDULE
```
- Scale to zero
```
aws eks update-nodegroup-config \
--cluster-name awsdevhmda3 \
--nodegroup-name awsdevhmda3kedro-regular \
--scaling-config minSize=0,maxSize=1,desiredSize=0
```
- Scale to one
```
aws eks update-nodegroup-config \
--cluster-name awsdevhmda3 \
--nodegroup-name awsdevhmda3kedro-regular  \
--scaling-config minSize=1,maxSize=1,desiredSize=1
```
- Status
```
kubectl get nodes -l "eks.amazonaws.com/nodegroup=awsdevhmda3kedro-regular" -w
```
> **_Note:_** Run pod after node is in Ready state


### Docker Build for k8

Our kedro report generation jobs are based on the [Amazon Elastic Container Registry (Amazon ECR)](https://docs.aws.amazon.com/ecr). Set your environment as shown.

```
$ export AWS_ECR=626560329871.dkr.ecr.us-east-1.amazonaws.com
```

The [AWS CLI](https://aws.amazon.com/cli) is also required.

- Run ```aws configure``` and authenticate with your AWS **sandbox** credentials. If this is unclear, contact your manager.
- Log into AWS ECR as shown.
```
$ aws ecr get-login-password --profile default --region us-east-1 | docker login --username AWS --password-stdin $AWS_ECR
```
- Comment configuration and commands in Dockerfile used for local docker run. **_Note:_** `.dockerignore` removes the local credentials.
- Choose an image tag **{myimagetag}**.
- Build and push to AWS ECR as shown.
```
$ docker build --platform linux/amd64 -t $AWS_ECR/hmda/kedro-etl-pipeline:{myimagetag} .
$ docker push $AWS_ECR/hmda/kedro-etl-pipeline:{myimagetag}
```

## Kubernetes Data Publisher Jobs 
- Before running:
    - For the docker image listed in `kedro-data-publisher/values.yaml`, make sure the `hmda-ecr` repository is set correctly and that the tag is correct
    - Check that `runCronJobs=true` is set in `kedro-data-publisher/values.yaml`
- All job runs generate data for a single year (or year and quarter for quarterly datasets)
- Large datasets, such as LAR and MLAR, use the node group `kedro-large`, while other jobs use the node group `kedro-regular`

### Cron jobs
- Helm can also be used to upgrade all kedro data publisher cron jobs at once
- Example helm command to upgrade cron jobs
```
helm upgrade --install kedro-data-publisher ./kedro-data-publisher
```

### Jobs
- Helm can also be used to upgrade a single job.
- To do this, some variables in `kedro-data-publisher/values.yaml` must be set in the helm command:
    - `runJob=true`
        - Unless you want to also upgrade the cron jobs, also set `runCronJobs=false`
    - `jobName="regulator-lar"`
        - Used for the kubernetes job name
    - `nodeGroup="kedro-large"`
        - Default is `"kedro-regular"`
    - `output="regulator_lar_flat_file"`
        - The output dataset name as defined in the `data_publisher.yaml` catalog, not including the year/quarter
    - `year="2023"`
        - If the dataset is quarterly, include the quarter at the end with an underscore: `"2024_q1"`
    - `pipeline="data_publisher"`
        - Only run required nodes in the `data_publisher` pipeline to get the output dataset. This will skip the pipeline that reads raw data from postgres.
        - Default is "__default__", which will run all necessary pipelines to get the output dataset
    - `post_to_mm=False`
        - Turn off Mattermost notifications for node errors or when saving datasets.
        - Default is true.
        - Will not make posts when using the local environment.
    - `post_to_mm_verbose=true`
        - Turn on all Mattermost notifications when starting or completing nodes, saving datasets, etc. See hooks.py for all kedro hooks that trigger Mattermost notifications. 
        - Default is false.
        - Will not make posts when using the local environment.
    
    
- All these variables can be updated at once under a single `--set` flag
- Example helm command to upgrade single job
```
helm upgrade --install kedro-data-publisher ./kedro-data-publisher --set runJob=true,runCronJobs=false,jobName="panel",nodeGroup="kedro-regular",year="2023",output="institutions_flat_file"
```

## Kubernetes jobs 
- Before running:
  - Verify the [nightly restore script](https://github.cfpb.gov/HMDA-Operations/hmda-devops/blob/master/rds/restore/restore-instdb-script-rds-nightly.yaml) ran successfully and created the expected tables. Many or most pipelines depend on these tables.
  - Modify the **image** key in the job yaml file.
    - Replace `hmda-ecr` with the value of AWS_ECR.
    - Replace "latest_image" with {myimagetag} (as you chose above).
- All job runs generate data for a single year (or year and quarter for quarterly datasets)
- Make sure the k8 job has the correct kedro command for each step  
- Outputs and commands shown here are for YEAR `2023` 
- Large datasets, such as LAR and MLAR, use the node group `kedro-large`, while other jobs use the node group `kedro-regular`

### General Kedro runtime parameters:
There are several useful parameters that can be used when running kedro commands. Mulitple params can be used at once, for example: `--params=max_workers=6,post_to_mm=False`

- `max_workers=6`
    - The number of thread workers. Used with the kedro run tag `--runner=ThreadRunner`. This is included in all kedro job run configs since speeds up processing and reduce OOM errors when generating the larger datasets like LAR and MLAR. Currently set to `max_workers=6` in kedro job configs.
- `post_to_mm=False`
    - Turn off Mattermost notifications for node errors or when saving datasets.
    - Default is true.
    - Will not make posts when using the local environment.
- `post_to_mm_verbose=true`
    - Turn on all Mattermost notifications when starting or completing nodes, saving datasets, etc. See hooks.py for all kedro hooks that trigger Mattermost notifications. 
    - Default is false.
    - Will not make posts when using the local environment.

### Institutions (panel)
- Example Kedro run command to be used in `kedro-etl-pipeline-job-panel-2023.yaml`
```
kedro run --runner=ThreadRunner --params=max_workers=6 --tags="2023_Filing_Season" --env=dev  --to-outputs="institutions_flat_file_2023"
```
> **_Note:_**   Add `--pipeline="data_publisher"` to the command to skip reading from the institutions postgres table. This only works if the raw data has already been read and saved for the year.
- Apply kedro job for institutions (panel):
```
kubectl apply -f kedro-etl-pipeline-job-panel-2023.yaml
```
- Confirm that S3 contains the dated and latest panel file for that year. The exact S3 filepaths can be found in the job's logs, along with the number of rows in the dataset.
```
aws s3 ls  --human-readable s3://cfpb-hmda-export/dev/kedro-etl-pipeline/regulator/2023/institutions/02_data_publication/
2024-09-26 21:01:10    1.0 MiB 2024-09-26_2023_panel.txt
2024-09-26 21:01:08    1.0 MiB latest_2023_panel.txt
```

### LAR
- Example Kedro run command to be used in `kedro-etl-pipeline-job-regulator-lar-2023.yaml`
```
kedro run --runner=ThreadRunner --params=max_workers=6 --tags="2023_Filing_Season" --env=dev  --to-outputs="regulator_lar_flat_file_2023"
```
> **_Note:_**   Add `--pipeline="data_publisher"` to the command to skip reading from the LAR postgres table. This only works if the raw data has already been read and saved for the year.
- Apply kedro job for LAR:
```
kubectl apply -f kedro-etl-pipeline-job-regulator-lar-2023.yaml
```
- Confirm that S3 contains the dated LAR flat file for that year. The exact S3 filepath can be found in the job's logs, along with the number of rows in the dataset.
```
aws s3 ls  --human-readable s3://cfpb-hmda-export/dev/kedro-etl-pipeline/regulator/2023/lar/02_data_publication/
2024-03-15 10:41:01    5.3 GiB 2024-03-15-2023_lar.txt
2024-03-20 16:20:53    5.3 GiB 2024-03-20-2023_lar.txt
```
    
### Modified LAR
- Example Kedro run command to be used in `kedro-etl-pipeline-job-modified-lar-2023.yaml`
```
kedro run --runner=ThreadRunner --params=max_workers=6 --tags="2023_Filing_Season" --env=dev   --to-outputs="public_modified_lar_flat_file_2023"
```
> **_Note:_**   Add `--pipeline="data_publisher"` to the command to skip reading from the LAR postgres table. This only works if the raw data has already been read and saved for the year.
- Apply kedro job for modified LAR:
```
kubectl apply -f kedro-etl-pipeline-job-modified-lar-2023.yaml
```
- Confirm that S3 contains the modified LAR flat files (public and public archive) for that year. The exact S3 filepaths can be found in the job's logs, along with the number of rows in the dataset.
```
aws s3 ls  --human-readable s3://cfpb-hmda-export/dev/kedro-etl-pipeline/public/2023/modified_lar/02_data_publication/
2024-09-26 22:06:06    2.3 GiB 2023_lar.zip

aws s3 ls  --human-readable s3://cfpb-hmda-export/dev/kedro-etl-pipeline/archive-public/2023/modified_lar/02_data_publication/
2024-09-26 22:26:41    2.3 GiB 2023_lar_2024-09-26.zi
```

### Regulator Transmittal Sheet
- Example Kedro run command to be used in `kedro-etl-pipeline-job-regulator-ts-2023.yaml`
```
kedro run --runner=ThreadRunner --params=max_workers=6 --tags="2023_Filing_Season" --env=dev --to-outputs="regulator_ts_flat_file_2023"
```
> **_Note:_**   Add `--pipeline="data_publisher"` to the command to skip reading from the transmittal sheet postgres table. This only works if the raw data has already been read and saved for the year.
- Apply kedro job for transmittal sheet:
```
kubectl apply -f kedro-etl-pipeline-job-regulator-ts-2023.yaml
```
- Confirm that S3 contains the transmittal sheet flat file for that year. The exact S3 filepath can be found in the job's logs, along with the number of rows in the dataset.
```
aws s3 ls  --human-readable s3://cfpb-hmda-export/dev/kedro-etl-pipeline/regulator/2023/ts/02_data_publication/
2024-09-17 13:31:51    8.1 KiB 2024-09-17_quarter_1_2023_ts.txt
2024-09-19 19:42:33  931.7 KiB 2024-09-19-2023_ts.txt
2024-09-20 13:26:18  931.7 KiB 2024-09-20-2023_ts.txt
```

### Public Transmittal Sheet
- Example Kedro run command to be used in `kedro-etl-pipeline-job-public-ts-2023.yaml`
```
kedro run --tags="2023_Filing_Season" --env=dev --runner=ThreadRunner --params=max_workers=6 --to-outputs="public_ts_flat_file_2023"
```
> **_Note:_**   Add `--pipeline="data_publisher"` to the command to skip reading from the transmittal sheet postgres table. This only works if the raw data has already been read and saved for the year.
- Apply kedro job for transmittal sheet:
```
kubectl apply -f kedro-etl-pipeline-job-public-ts-2023.yaml
```
- Confirm that S3 contains the transmittal sheet flat files (public and public archive) for that year. The exact S3 filepaths can be found in the job's logs, along with the number of rows in the dataset.
```
aws s3 ls  --human-readable s3://cfpb-hmda-export/dev/kedro-etl-pipeline/public/2023/public_ts/02_data_publication/
2024-09-26 20:59:41  200.4 KiB 2023_ts.zip

aws s3 ls  --human-readable s3://cfpb-hmda-export/dev/kedro-etl-pipeline/archive-public/2023/public_ts/02_data_publication/
2024-09-26 20:59:49  200.5 KiB 2023_ts_2024-09-26.zip
```

### Aggregate and Disclosure Reports 
- See [aggregate and disclosure pipeline file](https://github.cfpb.gov/HMDA-Operations/kedro-etl-pipeline/blob/main/hmda-etl-pipeline/src/hmda_etl_pipeline/pipelines/aggregate_and_disclosure_reports/pipeline.py) for list of inputs and outputs.

#### Steps to prepare input data before running aggregate or disclosure reports
##### Step 1 a) Upload the lei_list.csv file (Do once per year)
- The csv file should contain only one LEI per line.
- Example file:
```
cat lei_list.csv 
549300M8WGW2D17CZD19
OX3PU53ZLPQKJ4700D47
```
- The file should be placed in s3://cfpb-hmda-export/dev/kedro-etl-pipeline/reports/2023/disclosure/ for disclosure reports or in s3://cfpb-hmda-export/dev/kedro-etl-pipeline/reports/2023/aggregate/ for aggregate reports
- Upload LEI list file to S3
```
aws s3 cp lei_list.csv s3://cfpb-hmda-export/dev/kedro-etl-pipeline/reports/disclosure/2023
```
- For disclosure reports, this file is used to run reports on a list of LEI.
- For aggregate reports, this file is used to exclude some LEI from the reports.

##### Step 1 b) Upload the msa_list.csv file (Do once per year)
- The csv file should contain only one MSA per line.
- Example file:
```
cat msa_list.csv 
16180
99999
```
- This file is only used for aggregate reports to run reports on a list of MSA.
- The file should be placed in s3://cfpb-hmda-export/dev/kedro-etl-pipeline/reports/aggregate/2023/.
- Upload MSA list file to S3
```
aws s3 cp msa_list.csv s3://cfpb-hmda-export/dev/kedro-etl-pipeline/reports/aggregate/2023/
```

##### Step 2) Generate state county mapping csv file (Run once per year)
- Example Kedro run command to be used in kedro-etl-pipeline-job-state-county-mapping-2023.yaml
```
kedro run --runner=ThreadRunner --params=max_workers=6 --tags="2023_Filing_Season" --env=dev  --to-outputs="state_county_mapping_2023"
```
- Apply kedro job for state county mapping:
```
kubectl apply -f kedro-etl-pipeline-job-state-county-mapping-2023.yaml
```
- Confirm that S3 contains the state county mapping csv file for that year. The exact S3 filepath can be found in the job's logs, along with the number of rows in the dataset.
```
aws s3 ls  --human-readable s3://cfpb-hmda-export/dev/kedro-etl-pipeline/reports/2023/state_county_mapping.csv
2024-05-10 14:28:10   57.1 KiB state_county_mapping.csv
```

##### Step 3) Generate reduced LAR input file (Run once per year)
- Example Kedro run command to be used in kedro-etl-pipeline-job-reduced-lar-2023.yaml
```
kedro run --runner=ThreadRunner --params=max_workers=6 --tags="2023_Filing_Season" --env=dev  --to-outputs="reduced_lar_for_disclosure_reports_flat_file_2023"
```
> **_Note:_**   Add `--pipeline="data_publisher"` to the command to skip reading from the LAR postgres table. This only works if the raw data has already been read and saved for the year.
- Apply kedro job for reduced LAR:
```
kubectl apply -f kedro-etl-pipeline-job-reduced-lar-2023.yaml
```
- Confirm that S3 contains the reduced LAR parquet file for that year. The exact S3 filepath can be found in the job's logs, along with the number of rows in the dataset.
```
aws s3 ls  --human-readable s3://cfpb-hmda-export/dev/kedro-etl-pipeline/reports/2023/reduced_lar.parquet
2024-05-01 18:52:19  307.0 MiB reduced_lar.parquet
```

##### Step 4) Generate institutions (panel) input file (Run once per year)*
- See institutions (panel) section above for more details
- Apply kedro job for institutions (panel) file:
```
kubectl apply -f kedro-etl-pipeline-job-panel-2023.yaml
```

#### Generate aggregate reports
- SQL query to get MSA count from the cbsa_county_name table
```
SELECT COUNT(*) FROM hmda_user.cbsa_county_name;
1899
```
- Example Kedro run command to be used in kedro-etl-pipeline-job-aggregate-2023.yaml
```
kedro run --runner=ThreadRunner --params=max_workers=6,use_lei_list=false --tags="2023_Filing_Season" --env=dev --pipeline="aggregate_and_disclosure_reports"
```
- Include `skip_existing_reports=False` in the params list to regenerate all reports, including ones that already exist in S3.
- Include `use_lei_list=True` in the params list to exclude the list of LEI found in lei_list.csv from the reports.
- Include `use_msa_list=True` in the params list to generate aggregate reports on the list of MSA in msa_list.csv.
    - The job config kedro-etl-pipeline-job-aggregate-msalist-2023.yaml uses this param.

- Apply kedro job for aggregate report files:
```
kubectl apply -f kedro-etl-pipeline-job-aggregate-2023.yaml
```
- S3 outputs MSA folder count processed
```
aws s3 ls  --human-readable s3://cfpb-hmda-export/dev/kedro-etl-pipeline/reports/2023/aggregate/aggregate_reports/ | wc -l
    1899
```
- Alternative command to run all pre steps and aggregate report in a single command (not used)
```
kedro run --runner=ThreadRunner --params=max_workers=6,use_lei_list=false --tags="2023_Filing_Season" --env=dev --to-outputs="aggregate_reports_2023"
```

#### Generate disclosure reports
- SQL query to get LEI count in the LAR table
```
SELECT COUNT(DISTINCT(lei)) FROM hmda_user.restore_nightly_loanapplicationregister2023;
4376
```
- Example Kedro run command to be used in kedro-etl-pipeline-job-disclosure-2023.yaml
```
kedro run --runner=ThreadRunner --params=max_workers=6,use_lei_list=false --tags="2023_Filing_Season" --env=dev --pipeline="aggregate_and_disclosure_reports"
```
- Include `skip_existing_reports=False` in the params list to regenerate all reports, including ones that already exist in S3.
    - The job config kedro-etl-pipeline-job-disclosure-leilist-2023.yaml uses this param. 
- Include `use_lei_list=True` in the params list to generate disclosure reports on the list of LEI in lei_list.csv. This is set in the job config kedro-etl-pipeline-job-disclosure-leilist-2023.yaml

- Apply kedro job for disclosure report files:
```
kubectl apply -f kedro-etl-pipeline-job-disclosure-2023.yaml
```
- S3 outputs LEI folder count processed
```
aws s3 ls  --human-readable s3://cfpb-hmda-export/dev/kedro-etl-pipeline/reports/disclosure/2023/disclosure_reports/ | wc -l
    4375
```
- Alternative command to run all pre steps and disclosure report in a single command (not used)
```
kedro run --runner=ThreadRunner --params=max_workers=6,use_lei_list=false --tags="2023_Filing_Season" --env=dev --to-outputs="disclosure_reports_2023"
```

##### Example disclosure report run
```
kubectl apply -f kedro-etl-pipeline-job-disclosure-2023.yaml
kubectl delete -f kedro-etl-pipeline-job-disclosure-2023.yaml

kubectl logs -f  $(kubectl get pods | grep kedro-etl-pipeline-job-disclosure-2023 | awk '{print $1}') 
[03/27/24 16:17:58] INFO     Creating disclosure report table 2 for nodes.py:210
                             ZXMJHJK466PBZTM5F379/99999                         
[03/27/24 16:18:03] INFO     Completed node:                thread_runner.py:138
                             generate_disclosure_reports_fo                     
                             r_2023                                             
                    INFO     Completed 1 out of 1 tasks     thread_runner.py:139
                    INFO     Pipeline execution completed          runner.py:105
                             successfully.
```
> **_Note:_** Reports job can be re-run and if folders for specific LEI exists in S3 buckets, they will ber skipped. If you find errors, re-run all the reports with the param `skip_existing_reports=False`, or re-run some reports by updating lei_list.csv and using the param `use_lei_list=True`.
```
                    INFO     Skipping reports for                   nodes.py:138
                             549300CMO3QHQGZ2Z096 because report                
                             files already exist                                
                    INFO     Generating diclosure reports for        nodes.py:60
                             remaining 1 lei 
```

#### Run reports using snapshot postgres tables
- Use job config kedro-etl-pipeline-job-reduced-lar-2023-snapshot.yaml.
    - Unlike the other reduced LAR job configs, this job config adds the configmap `kedro-dev-postgres-configmap.yaml` to the `volumeMounts` and `volume` sections and copies the configmap file in the `command` section.
- Make sure that that the congfigmap file `kedro-dev-postgres-configmap.yaml` uses the correct snapshot tables for `pg_lar_{{year}}`, `pg_lar_counts_by_lei_{{ year }}`, and `pg_institutions_{{ year }}` datasets. The rest of the content in the configmap should be the same as in the file [dev_postgres.yaml](https://github.cfpb.gov/HMDA-Operations/kedro-etl-pipeline/blob/main/hmda-etl-pipeline/conf/dev/catalogs/dev_postgres.yaml)
- Apply kedro job for the reduced lar snapshot dataset:
```
kubectl apply -f kedro-etl-pipeline-job-reduced-lar-2023-snapshot.yaml
```
- Apply kedro job for the institutions snapshot dataset:
```
kubectl apply -f kedro-etl-pipeline-job-panel-2023-snapshot.yaml
```
- Run the reports, making sure that `--pipeline="aggregate_and_disclosure_reports"` is included in the kedro run command to avoid re-generating the reduced LAR dataset again on non-snapshot data.

#### Additional commands to check generate files
- All files for year 2023
```
aws s3 ls --recursive --human-readable s3://cfpb-hmda-export/dev/kedro-etl-pipeline/reports/2023/ | grep -v "0 Bytes"
```
- All files generated on specific date
```
aws s3 ls --recursive --human-readable s3://cfpb-hmda-export/dev/kedro-etl-pipeline/reports/2023/ | grep -v "0 Bytes" | grep "2023-11-17"
```
- Disclosure Reports single LEI
```
aws s3 ls --recursive --human-readable s3://cfpb-hmda-export/dev/kedro-etl-pipeline/reports/2023/ | grep -v "0 Bytes" | grep -e 2024 | grep 549300FGXN1K3HLB1R50 | wc -l
```
