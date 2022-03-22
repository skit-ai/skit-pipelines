# skit-pipelines

Reusable workflows for ml teams at skit.ai. Built using kubeflow components. The core focus of this project is to build as kubeflow components and pipelines. 
Take the following example workflow: 

1. Download a dataset.
2. Run some pre-processing.
3. Upload the dataset for future references.
4. Upload the dataset for annotation.
5. Download the dataset after annotation.
6. Split the dataset to test/train conditionally.
6. Train a model on the train set.
7. Evaluate the model on the test set.
8. Upload the model for future references.

We can make a single monolithic pipeline for all these tasks but it puts a great burden on the maintainer to add more pipelines this way.
Often we see the pre-processing steps become opaque as they are hard coupled in the data access tools. This makes it hard to apply the same
pre-processing steps to different datasets. Hence for the above example workflow we will have components that:

1. Connect to a source and downloads a dataset as a csv. (Restricting to csv for starters).
2. Run pre-processing steps on the dataset, it should be possible to re-order, pick and choose the steps as well.
3. Upload files to s3.
4. Upload files to annotation service.
5. Download files from annotation service ? If yes, this is not efficient as we already have [1] doing the same thing.
6. Train models on a dataset.
7. Evaluate models on a dataset.
8. Upload models to s3 ? **No** we already have [3] for this.

## Modules

Understand the directory strucuture.

```shell
.
├── build
│   └── fetch_calls_pipeline.yaml
├── ... (skipping other files)
├── skit_pipelines
│   ├── components
│   │   ├── fetch_calls.py
│   │   ├── __init__.py
│   │   └── upload2s3.py
│   ├── constants.py
│   ├── __init__.py
│   ├── pipelines
│   │   ├── fetch_calls_pipeline.py
│   │   └── __init__.py
│   └── utils
│       └── __init__.py
└── tests
```

- We have `components` module, each file corresponds to exactly one component.
- We have `pipelines` module, each file corresponds to exactly one pipeline.
- Reusable functions should go to `utils`.
- We have `constants.py` file that contains constants to prevent typos and assist with code completion.
- `build` houses our pipeline yamls. These will get more important in a later section.

It is necessary to understand the anatomy of a kubeflow [component](https://www.kubeflow.org/docs/components/pipelines/sdk/component-development/) and [pipeline](https://www.kubeflow.org/docs/components/pipelines/sdk/build-pipeline/) before contributing to this project.

## Making a new pipelines

Once a new pipeline and its pre-requisite components are ready.

1. Add an entry to the `CHANGELOG.md`.
2. Create a new tag with updated semver and push, our github actions take care of pushing the image to our private ECR.
3. Run `source env.sh` You may not have this if you aren't part of skit.ai.
4. Run `make`. This will lint the project and rebuild all the pipeline yamls.
5. Upload the yamls to [kubeflow ui](https://www.kubeflow.org/docs/components/pipelines/sdk/build-pipeline/#option-1-compile-and-then-upload-in-ui) or [use it via the sdk](https://www.kubeflow.org/docs/components/pipelines/sdk/build-pipeline/#option-2-run-the-pipeline-using-kubeflow-pipelines-sdk-client).

## Pre-requisites

- This project is based on `python 3.10`. You would require an environment setup for the same. Using [miniconda](https://docs.conda.io/en/latest/miniconda.html) is recommended.
- make [mac](https://formulae.brew.sh/formula/make)
- [poetry](https://python-poetry.org/docs/#installation)
