FROM 536612919621.dkr.ecr.ap-south-1.amazonaws.com/vernacular-voice-services/ai/kubeflow/base-py:master

WORKDIR /home/kfp

RUN apt-get update \
    && apt-get install -y wget gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip install poetry
RUN poetry config virtualenvs.create false

COPY ./pyproject.toml ./pyproject.toml
COPY ./poetry.lock ./poetry.lock
RUN poetry install --no-dev

ARG BASE_IMAGE
ARG DB_HOST
ARG DB_PORT
ARG DB_PASSWORD
ARG DB_NAME
ARG DB_USER
ARG RANDOM_CALL_DATA_QUERY
ARG RANDOM_CALL_ID_QUERY
ARG CDN_RECORDINGS_BASE_PATH
ARG BUCKET
ARG DATA_UPLOAD_PATH

ENV BASE_IMAGE=$BASE_IMAGE
ENV DB_HOST=$DB_HOST
ENV DB_PORT=$DB_PORT
ENV DB_PASSWORD=$DB_PASSWORD
ENV DB_NAME=$DB_NAME
ENV DB_USER=$DB_USER
ENV RANDOM_CALL_DATA_QUERY=$RANDOM_CALL_DATA_QUERY
ENV RANDOM_CALL_ID_QUERY=$RANDOM_CALL_ID_QUERY
ENV CDN_RECORDINGS_BASE_PATH=$CDN_RECORDINGS_BASE_PATH
ENV BUCKET=$BUCKET
ENV DATA_UPLOAD_PATH=$DATA_UPLOAD_PATH

CMD ["/bin/sh", "-ec", "while :; do echo '.'; sleep 5 ; done"]
