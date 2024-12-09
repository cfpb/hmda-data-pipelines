ARG BASE_IMAGE=python:3.9
FROM $BASE_IMAGE AS runtime-environment

# install project requirements
COPY /hmda-etl-pipeline/src/requirements.txt /tmp/requirements.txt
COPY /hmda-etl-pipeline/src/setup-job.sh /tmp/setup-job.sh
RUN pip install --upgrade pip 
RUN pip install --no-cache -r /tmp/requirements.txt && rm -f /tmp/requirements.txt
RUN apt-get update
RUN apt-get clean
RUN rm -rf /usr/local/lib/python3.9/site-packages/tornado/test/test.key

# add kedro user
ARG KEDRO_UID=999
ARG KEDRO_GID=0
RUN groupadd -f -g ${KEDRO_GID} kedro_group && \
useradd -m -d /home/kedro_docker/ -s /bin/bash -g ${KEDRO_GID} -u ${KEDRO_UID} kedro_docker

USER kedro_docker

FROM runtime-environment

# copy the whole project except what is in .dockerignore
ARG KEDRO_UID=999
ARG KEDRO_GID=0
COPY --chown=${KEDRO_UID}:${KEDRO_GID} . .

# ENV CURRENT_YEAR="2022 Filing Season"
# ENV KEDRO_DEV="dev"
# ENV AWS_ACCESS_KEY_ID=" "
# ENV AWS_SECRET_ACCESS_KEY=" "
# ENV AWS_DEFAULT_REGION="us-east-1"

## CMD cd /hmda-etl-pipeline/ && /bin/bash && kedro run --tags="$CURRENT_YEAR" --env=$KEDRO_DEV
