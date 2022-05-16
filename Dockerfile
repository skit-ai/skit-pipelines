FROM gpuci/miniconda-cuda:11.3-devel-ubuntu20.04

RUN apt-key adv --fetch-keys https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2004/x86_64/3bf863cc.pub \
    && apt-get -y update \
    && apt-get install -y wget gcc libpq-dev

RUN conda install python=3.10 -y\ 
    && conda install pip\
    && conda init bash

WORKDIR /home/kfp

RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -
RUN sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list'
RUN apt-get -y update\
    && apt-get -y install google-chrome-stable

# install chromedriver
RUN apt-get install -yqq unzip
RUN wget -O /tmp/chromedriver.zip http://chromedriver.storage.googleapis.com/`curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE`/chromedriver_linux64.zip
RUN unzip /tmp/chromedriver.zip chromedriver -d /usr/local/bin/\
    && rm /tmp/chromedriver.zip\
    rm -rf /var/lib/apt/lists/*

# set display port to avoid crash
ENV DISPLAY=:99

RUN pip install poetry simpletransformers==0.63.6 kfp==1.8.11
RUN poetry config virtualenvs.create false

COPY . .
RUN poetry install --no-dev

ARG BASE_IMAGE

ARG DB_HOST
ARG DB_PORT
ARG DB_NAME
ARG DB_PASSWORD
ARG DB_USER

ARG GOOGLE_SHEETS_CREDENTIALS

ARG CDN_RECORDINGS_BASE_PATH
ARG BUCKET

ARG SLACK_TOKEN
ARG DEFAULT_SLACK_CHANNEL

ARG SKIT_API_GATEWAY_URL
ARG SKIT_API_GATEWAY_EMAIL
ARG SKIT_API_GATEWAY_PASSWORD
ARG TOG_TASK_URL

ARG KUBEFLOW_GATEWAY_ENDPOINT
ARG KF_USERNAME
ARG KF_PASSWORD
ARG KAFKA_INSTANCE

ENV BASE_IMAGE=$BASE_IMAGE

ENV DB_HOST=$DB_HOST
ENV DB_PORT=$DB_PORT
ENV DB_PASSWORD=$DB_PASSWORD
ENV DB_NAME=$DB_NAME
ENV DB_USER=$DB_USER

ENV RANDOM_CALL_DATA_QUERY=secrets/random_calls_data.sql
ENV RANDOM_CALL_ID_QUERY=secrets/random_call_ids.sql
ENV CALL_IDS_FROM_UUIDS_QUERY=secrets/call_ids_from_uuids.sql

ENV GOOGLE_SHEETS_CREDENTIALS=$GOOGLE_SHEETS_CREDENTIALS

ENV CDN_RECORDINGS_BASE_PATH=$CDN_RECORDINGS_BASE_PATH
ENV BUCKET=$BUCKET

ENV SLACK_TOKEN=$SLACK_TOKEN
ENV DEFAULT_SLACK_CHANNEL=$DEFAULT_SLACK_CHANNEL

ENV SKIT_API_GATEWAY_URL=$SKIT_API_GATEWAY_URL
ENV SKIT_API_GATEWAY_EMAIL=$SKIT_API_GATEWAY_EMAIL
ENV SKIT_API_GATEWAY_PASSWORD=$SKIT_API_GATEWAY_PASSWORD
ENV TOG_TASK_URL=$TOG_TASK_URL

ENV KUBEFLOW_GATEWAY_ENDPOINT=$KUBEFLOW_GATEWAY_ENDPOINT
ENV KF_USERNAME=$KF_USERNAME
ENV KF_PASSWORD=$KF_PASSWORD

ENV KAFKA_INSTANCE=$KAFKA_INSTANCE

CMD ["/bin/sh", "-ec", "while :; do echo '.'; sleep 5 ; done"]
