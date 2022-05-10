# Changelog

## 0.1.39

- [x] update: skit-calls==0.2.12
- [x] update: remove recurrent from fetch-n-tag pipeline and start_date, end_date logic moved to skit-calls instead.

## 0.1.38

- [x] update: skit-calls==0.2.11
- [x] update: skit-labels==0.3.20
- [x] fix: save labelencoder pickle while running the train xlmr pipeline.

## 0.1.32

- [x] update: remove dvc link for pipelines.
- [x] add: makefile downloads secrets from skit-calls.

## 0.1.26

- [x] feat: APIs for pipelines.
- [x] add: secrets via dvc.

## 0.1.25

- [x] add: pipeline to fetch and tag a dataset.
- [x] fix: support legacy dataframes missing utterance columns.

## 0.1.24

- [x] update: XLMR intent classifier training pipeline pushes models to s3.

## 0.1.23

- [x] update: trained models upload to s3.

## 0.1.22

- [x] add: Conda and Cuda within base docker image.

## 0.1.21

- [x] add: Cuda installation within Dockerfile.
- [x] fix: Intent classifier training component.

## 0.1.20

- [x] fix: intent classifier featurizer fixed to apply row-wise transformation.
- [x] fix: hacky solution for https://github.com/ThilinaRajapakse/simpletransformers/issues/1386

## 0.1.19

- [x] update: kfp installed within container.

## 0.1.18

- [x] update: components isolated from helper functions.

## 0.1.17

- [x] add: component to create utterance column `utterances`.
- [x] add: component to create true intent column `intent_y`.
- [x] add: component to add state and utterances as features for intent classifer (xlmr).
- [x] update: model training pipeline with train set only.

## 0.1.16

- [x] add: torch = "^1.11.0" for cuda 10.2

## 0.1.15

- [x] add: preprocessing module for specialized components.

## 0.1.14

- [x] update: skit-labels 0.3.17 with higher tolerance for utterance structures.

## 0.1.13

- [x] update: skit-labels skit-calls for serialized json fields.

## 0.1.12

- [x] update: skit-labels 0.3.13, values for db creds resolved.

## 0.1.11

- [x] add: placeholder component to train xlmr intent classifier.

## 0.1.10

- [x] add: component that fetches tagged datasets.
- [x] add: kubeflow pipeline utilizing the above component.

## 0.1.9

- [x] update: skit-calls 0.2.3

## 0.1.8

- [x] fix: Slack notification component -- Slack token constant.

## 0.1.7

- [x] fix: Slack notification component -- Slack token constant.

## 0.1.6

- [x] update: link slack component with fetch data pipeline.

## 0.1.5

- [x] feat: slack integration.

## 0.1.4

- [x] update: skit-pipelines is available within docker image.

## 0.1.3

- [x] update: build pipeline yamls via `make`.

## 0.1.2

- [x] refactor: modularize project.

## 0.1.1

- [x] add: boto3 for s3 upload/download.

## 0.1.0

- [x] add: calls dataset component.
- [x] add: Upload to s3 component.
- [x] add: Calls dataset pipeline.
- [x] add: workflow to automate docker image creation on tag push.
