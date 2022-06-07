# Contributing

## Development

1. Clone the project
2. Create a conda environment using python 3.10
3. Install git+https://github.com/skit-ai/eevee.git@1.2.1, `simpletransformers==0.63.6`, `kfp`, `scipy` separately until [this bug](https://github.com/skit-ai/skit-pipelines/issues/32) is resolved.
4. poetry install.
5. dvc pull
6. run `make secrets`.
7. run `source secrets/env.sh` this will setup the environment with secret variables.

To develop locally, just run `task serve`. This will host a fastapi server on your development environment.
You can test out components via pytest (recommended) or atleast build them interactively on ipython.

To deploy your pipeline on kubeflow, run `make pipes`. This will build the pipeline yamls in the `build/` directory.

### Component Anatomy

We use this project as a base image for all our pipelines. This helps us re-use a lot of code that we couldn't otherwise.
However to make use of this we will decide on conventions.

- Pipeline
- Component

#### Pipeline

A Kubeflow Pipeline is at the top level of the heirarchy since modifying and updating it **does not require an image build**.
Building an image takes anywhere from 20-30 minutes. Since pipeline code is a dsl, we actively avoid logic apart from connecting components.

#### Components

A Kubeflow Component is good a doing one thing really well. A component is a python function that gets deployed as a container on kubeflow.
Therefore you would see code like:

```python

def metadata2accuracy(metadata: str) -> float:
    import json

    eval_result = json.loads(metadata)
    return eval_result['accuracy']
```

The import statement is within the component because kubeflow while compiling, will take the function body as the source code for the container.
We maintain reusable functions in the `skit-pipelines.utls` or `skit-pipelines.components.*` packages. Any modification to these functions will require a new image build.

## Soft Release

1. Build a docker image locally.
2. Tag it with a name instead of semver, preferably a branch-name.
3. 

## Release

We use github actions to make releases. It helps us update our images over to aws ecr. If we are adding secrets, make sure they are added to the projects secrets page as well and then used in the dockerfile. This is necessary because we don't want the image to have provisions to read secrets.

To release, we update the:

1. Add docs for **atleast** pipelines as they are consumer facing and are also automatically generated as APIs.
2. Project version in `pyproject.toml`. We use semver.
3. Add an entry in the `CHANGELOG.md` to notify ourselves and other users about the updates.
4. Release a tag with the semver.
5. run `make docs` after releasing the tag.
6. The pipeline name on kubeflow should be exactly the same as the file name and function name of the pipeline. We can normalize kebab-cased-names to snake_cased_names.

**Do not** create tags for development and testing purposes.
