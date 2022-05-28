from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from skit_pipelines.api.models.requests import StorageOptions

def create_storage_path(storage_options: 'StorageOptions', path: str):
    if not storage_options or not path:
        return
    return f"{storage_options.type}://{storage_options.bucket}/{path}"
