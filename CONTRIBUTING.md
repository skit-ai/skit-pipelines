# Contributing

## Development

1. Clone the project
2. Create a conda/pyenv environment using python 3.9
3. Install git+https://github.com/skit-ai/eevee.git@1.3.0, `simpletransformers==0.63.6`, `kfp`, `scipy` separately until [this bug](https://github.com/skit-ai/skit-pipelines/issues/32) is resolved.
4. poetry install.
5. dvc pull
6. run `make secrets`.
7. run `source secrets/env.sh` this will setup the environment with secret variables.

You can test out components via pytest (recommended) or atleast build them interactively on ipython.

To develop locally, **always have an image built first** which will serve as `base image` to run the pipeline in this case. `make dev tag=<feature_x_tag>` would help you do this. It'll build an image and start the pipelines server. Now from next time onwards you can do just `make dev` and it'll automatically pick up last tagged image you had as `base image` and start the server. Whenever you'd again like to have a new image built and have the pipelines use that, run `make dev tag=<some_other_feature_tag>` and from there on new tag will be picked up. Here we are using a mono-image setup for pipelines.

Once server starts then one can test a pipeline by doing:
 ```bash
 task run_pipeline --pipeline-name=<your_pipeline_name> --params-file=<json_file_path_for_pipeline_params>
 ```
One can do `task run_pipeline -h` to know more.

### Workflow YAMLs 
Running `make pipes`  will build the pipeline yamls in the `build/` directory which can be used to upload for a new official pipeline release in Kubeflow.

## Component Anatomy

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
We maintain reusable functions in the `skit-pipelines.utils` or `skit-pipelines.components.*` packages. Any modification to these functions will require a new image build.

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


## Breaking changes

- Changing schema of pipelines or components.
- Server code changes: Things that modify the APIs, slack command parsing etc.
