#!/bin/bash

set -ex

date
cp /tmp/kedro-base-credentials/credentials.yaml  /hmda-etl-pipeline/conf/base/credentials.yaml
cp /tmp/kedro-dev-credentials/credentials.yaml /hmda-etl-pipeline/conf/dev/credentials.yaml
cp /tmp/kedro-dev-env-configmap/globals.yml  /hmda-etl-pipeline/conf/dev/globals.yml
mkdir -p /hmda-etl-pipeline/logs && touch /hmda-etl-pipeline/logs/info.log

