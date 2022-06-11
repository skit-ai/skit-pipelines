# Changelog

## 0.1.100 [pre-release]

- [x] fix: slack parser handles urls in code blocks.
- [x] update: add slack thread id, channel and user id automatically.
- [x] update: slack notification component expects code_blocks instead of s3_path.
- [x] update: slack notifications can go to threads directly.

## 0.1.99

- [x] fix: auth-token type.

## 0.1.98

- [x] fix: training pre-proc handles utterances from these columns as well: alternatives, data.

## 0.1.97

- [x] update: dockerfile uses python 3.8 and cuda 10.2.
- [x] fix: labelstudio download.
- [x] update: compatible with python 3.8.

## 0.1.96

- [x] update: normalize.comma_sep_str can be used for comma separated numbers and strings.

## 0.1.95

- [x] fix: TypeError: Object of type JSONDecodeError is not JSON serializable on dataset uploads.
- [x] fix: invalid literal for int() with base 10: '' on dataset uploads

## 0.1.94

- [x] update: skit-labels unpacks tagged dataset.
- [x] fix: 'AttributeError: 'NoneType' object has no attribute 'get' on fetching calls with failed predictions.
- [x] fix: compatibility between skit-labels, skit-calls, skit-auth, kfp, etc.
- [x] add: s3 url support for tag calls pipeline.

## 0.1.93

- [x] fix: Slack hyperlink markup removed.

## 0.1.92

- [x] add: Labelstudio integration.

## 0.1.91

- [x] update: fetch_calls_n_upload_tog_and_sheet and fetch_calls_n_push_to_sheets pipelines refactor

## 0.1.90

- [x] update: replace org-id with reference in s3 upload component.

## 0.1.89

- [x] fix: storage options.

## 0.1.88

- [x] fix: slack token const.
- [x] refactor: unused types.

## 0.1.87

- [x] fix: db host name.
- [x] update: default arguments fixed.

## 0.1.86

- [x] docs: Better examples, easier to copy paste commands.
- [x] add: slack notifications to all components.

## 0.1.85

- [x] fix: slack urls.
- [x] add: slack notifications to all components.

## 0.1.84

- [x] add: slack signing secret.

## 0.1.83

- [x] docs: Pipeline and payload docs added.
- [x] update: slackbot command parser responds with stacktrace.

## 0.1.82

- [x] fix: No module named 'skit_pipelines' caused by installing before copy source in dockerfile.
- [x] refactor: makefile for building pipelines is leaner.

## 0.1.80

- [x] add: slack-bot integration. Invoke pipelines via slackbot.
- [x] refactor: Automatic generation of pydantic models using kfp signature.

## 0.1.79

- [x] add: intent evaluation pipeline.
- [x] add: crr evaluation pipeline.
- [x] add: slack-bot integration.

## 0.1.62
- [x] update: remove helper function for upload2sheet
- [x] update: sheet duplication and row logic while pushing calls to google sheet

## 0.1.53
- [x] update: move helper functions of upload2sheet into a folder

## 0.1.52
- [x] update: skit-calls==0.2.15

## 0.1.48
- [x] update: skit-calls==0.2.14

## 0.1.45
- [x] fix: to make Docker file and github actions yaml to use google secrets

## 0.1.44
- [x] update: component to push CSV to a google sheet. Load google secrets from a Github secrets
- [x] update: Docker file and github actions yaml to use google secrets
## 0.1.43
- [x] add: component to push CSV to a google sheet.
- [x] add: pipeline to fetch calls and push to google sheet.

## 0.1.42

- [x] update: XLMR training supports lr parameter.

## 0.1.41

- [x] update: skit-calls==0.2.13

## 0.1.40

- [x] update: skit-labels==0.3.21
- [x] update: ping users on slack channels.

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
