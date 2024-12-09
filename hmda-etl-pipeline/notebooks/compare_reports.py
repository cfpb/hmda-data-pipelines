import json
import os
import pandas as pd
import s3fs

YEAR = 2022  # os.environ["YEAR"]

kedro_reports_path = f"cfpb-hmda-export/dev/kedro-etl-pipeline/{YEAR}/reports/disclosure/disclosure_reports/"
old_reports_path = f"cfpb-hmda-public/prod/reports/disclosure/{YEAR}/"
lei_list_file_name = (
    f"cfpb-hmda-export/dev/kedro-etl-pipeline/{YEAR}/reports/disclosure/lei_list.csv"
)

fs = s3fs.S3FileSystem()

lei_list = pd.read_csv(fs.open(lei_list_file_name, "rb"), names=["lei"])["lei"].tolist()

print(f"Comparing files for {len(lei_list)} leis")


# Helper for ordering the JSON fields
def ordered(obj):
    if isinstance(obj, dict):
        return sorted((k, ordered(v)) for k, v in obj.items())
    if isinstance(obj, list):
        return sorted(ordered(x) for x in obj)
    else:
        return obj


# Compare files one lei at a time
for lei in lei_list:
    kedro_files = fs.find(path=kedro_reports_path, prefix=lei)
    old_files = fs.find(path=old_reports_path, prefix=lei)

    # Filter to get only json files
    kedro_files = list(filter(lambda x: "json" in x, kedro_files))
    old_files = list(filter(lambda x: "json" in x, old_files))

    # Check if there is the same number of kedro files and old files
    if len(kedro_files) != len(old_files):
        print(
            f"The number of kedro disclosure report files ({len(kedro_files)}) for lei {lei} does not equal the number of disclosure reports expected ({len(old_files)})"
        )
        continue
    print(f"Number of report files ({len(kedro_files)}) for lei {lei} look correct")

    lei_msa_count = len(kedro_files)
    bad_files = 0

    for k_file in kedro_files:
        # Check if MSA/file is in both kedro and old reports
        msa_file_name = k_file.split(f"{lei}/", 1)[1]
        old_file = f"{old_reports_path}{lei}/{msa_file_name}"

        # Skip examining files if the file counts are not the same
        if old_file not in old_files:
            print(
                f"lei/msa file {lei}/{msa_file_name} in kedro reports, but not old reports"
            )
            continue

        # Compare the files
        with fs.open(k_file, "rb") as k_f, fs.open(old_file, "rb") as old_f:
            kedro_disclosure_dict = json.load(k_f)
            old_disclosure_dict = json.load(old_f)

            # Exclude the report date from the comparison
            kedro_disclosure_dict.pop("reportDate")
            old_disclosure_dict.pop("reportDate")

            ordered_kedro_report = ordered(kedro_disclosure_dict)
            ordered_old_report = ordered(old_disclosure_dict)

            if ordered_kedro_report != ordered_old_report:
                print(f"lei/msa file {lei}/{msa_file_name} is DIFFERENT")
                bad_files = bad_files + 1

                # Save the ordered files locally to compare manually
                # msa_file_name = msa_file_name.replace("/", "-")
                # with open(f'{lei}-{msa_file_name}-kedro.json', 'w') as k_diff_file:
                #     k_diff_file.write(json.dumps(ordered_kedro_report))
                # with open(f'{lei}-{msa_file_name}-old.json', 'w') as old_diff_file:
                #     old_diff_file.write(json.dumps(ordered_old_report))
                #
                # Exit for loop once files are saved
                # continue
            # else:
            #     print(f"lei/msa file {lei}/{msa_file_name} in kedro MATCHES old file")

    good_files = lei_msa_count - bad_files

    if good_files == lei_msa_count:
        print(f"For lei {lei}, all files are correct")
    else:
        print(f"For lei {lei}, {good_files}/{lei_msa_count} files are correct")
