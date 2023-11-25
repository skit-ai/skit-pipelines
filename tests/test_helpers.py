import os
import time
from urllib.parse import parse_qs, urlparse

import requests

from skit_pipelines import constants as const
from skit_pipelines.utils import helpers


def test_audio_url_conversion():

    common_url_path = "/2023-08-08/O10686392138/"

    test_values = {
        "13325ba8-0182-4b71-b0d9-d0f04786989d.flac?AWSAccessKeyId=FAKEXZ4E7LFCTUFAKE&Signature=FakeSignB%2FMno%2BzZc5AzPlzCo%3D&Expires=1692624131": "13325ba8-0182-4b71-b0d9-d0f04786989d.wav",
        "13325ba8-0182-4b71-b0d9-d0f04786989d.flac": "13325ba8-0182-4b71-b0d9-d0f04786989d.wav",
        "13325ba8-0182-4b71-b0d9-d0f04786989d.wav": "13325ba8-0182-4b71-b0d9-d0f04786989d.wav",
    }

    for given, expected in test_values.items():
        assert helpers.convert_audiourl_to_filename(common_url_path + given) == expected


def test_get_unix_epoch_timestamp_from_s3_presigned_url():

    sample_s3_http_turn_audio_url = f"https://{const.S3_US_PRODUCTION_TURN_RECORDINGS_BUCKET}.s3.amazonaws.com/2023-08-08/O10686392138/13325ba8-0182-4b71-b0d9-d0f04786989d.flac?AWSAccessKeyId=FAKE123FAKE123FFG243&Signature=oNoPShdKa3B%2FMno%2BzZc5AzPlzCo%3D&Expires=1692624131"
    given_unix_epoch_in_s = int("1692624131")

    expected_unix_epoch_in_s = helpers.get_unix_epoch_timestamp_from_s3_presigned_url(
        sample_s3_http_turn_audio_url
    )
    assert expected_unix_epoch_in_s == given_unix_epoch_in_s

    # checking if the re-signed logic epoch time is greater than what we have now
    time.sleep(1)
    assert int(time.time()) > expected_unix_epoch_in_s


def test_re_presigning_s3_http_turn_audio_url():

    AWS_ACCESS_KEY_ID = os.environ["AWS_ACCESS_KEY_ID"]

    sample_s3_http_turn_audio_url = f"https://{const.S3_US_PRODUCTION_TURN_RECORDINGS_BUCKET}.s3.amazonaws.com/2023-08-08/O10686392138/13325ba8-0182-4b71-b0d9-d0f04786989d.flac?AWSAccessKeyId={AWS_ACCESS_KEY_ID}&Signature=oNoPShdKa3B%2FMno%2BzZc5AzPlzCo%3D&Expires=1692624131"
    given_url_unix_epoch_in_s = helpers.get_unix_epoch_timestamp_from_s3_presigned_url(
        sample_s3_http_turn_audio_url
    )

    # present URL shouldn't be working at all
    assert requests.get(sample_s3_http_turn_audio_url).status_code != 200

    re_presigned_s3_http_audio_url = helpers.re_presign_audio_url_if_required(
        sample_s3_http_turn_audio_url
    )
    re_presigned_url_unix_epoch_in_s = (
        helpers.get_unix_epoch_timestamp_from_s3_presigned_url(
            re_presigned_s3_http_audio_url
        )
    )

    assert re_presigned_url_unix_epoch_in_s > given_url_unix_epoch_in_s

    _present_epoch_in_s = int(time.time())
    future_6day_unix_epoch_in_s = _present_epoch_in_s + (6 * 24 * 60 * 60)
    future_8day_unix_epoch_in_s = _present_epoch_in_s + (8 * 24 * 60 * 60)

    # checking if the re_presigned URL is valid for the next 7 days only
    assert re_presigned_url_unix_epoch_in_s > future_6day_unix_epoch_in_s
    assert re_presigned_url_unix_epoch_in_s < future_8day_unix_epoch_in_s

    # checking if the re_presigned URL is valid after presigning, content should be accessible only now.
    assert requests.get(re_presigned_s3_http_audio_url).status_code == 200
