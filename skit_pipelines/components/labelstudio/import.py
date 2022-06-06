import kfp


def upload_tasks(
    project_id: int,
    urls: str,
):
    import requests
    import json
    from skit_pipelines import constants as pipeline_constants

    urls = json.loads(urls)
    res = requests.post(
        url=f"{pipeline_constants.LABELSTUDIO_SVC}/api/projects/{project_id}/import",
        headers={"Authorization": f"Token {pipeline_constants.LABELSTUDIO_TOKEN}"},
        json=urls
    )
    if res.status_code != 200:
        raise Exception(res.text)
    return res.json()["task_count"]
