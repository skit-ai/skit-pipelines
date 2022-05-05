from skit_pipelines.api.models import StorageOptions

def create_storage_path(storage_options: StorageOptions, path: str):
    if not storage_options or not path:
        return
    return f"{storage_options.type}://{storage_options.bucket}/{path}"
    