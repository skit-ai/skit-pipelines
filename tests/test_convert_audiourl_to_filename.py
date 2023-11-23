
from skit_pipelines.utils.helpers import convert_audiourl_to_filename

def test_audio_url_conversion():

    common_url_path = "/2023-08-08/O10686392138/"

    test_values = {
        "13325ba8-0182-4b71-b0d9-d0f04786989d.flac?AWSAccessKeyId=FAKEXZ4E7LFCTUFAKE&Signature=FakeSignB%2FMno%2BzZc5AzPlzCo%3D&Expires=1692624131": "13325ba8-0182-4b71-b0d9-d0f04786989d.wav",
        "13325ba8-0182-4b71-b0d9-d0f04786989d.flac": "13325ba8-0182-4b71-b0d9-d0f04786989d.wav",
        "13325ba8-0182-4b71-b0d9-d0f04786989d.wav": "13325ba8-0182-4b71-b0d9-d0f04786989d.wav",
    }

    for given, expected in test_values.items():
        assert convert_audiourl_to_filename(common_url_path + given) == expected
