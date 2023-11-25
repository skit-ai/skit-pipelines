import time
import traceback
from urllib.parse import parse_qs, urlparse

import boto3
from loguru import logger
from skit_calls.data.model import S3_CLIENT, generate_presigned_url

from skit_pipelines import constants as const


def convert_audiourl_to_filename(audiourl: str) -> str:
    """
    converts s3 http turn audio url into the actual filename with .wav extension.
    """

    fn = audiourl.rsplit("/", 1)[-1]
    if "?" in fn:
        fn = fn.split("?")[0]

    # this is done so that it'd be easier for downstream to read it as .wav files
    # else could have returned the name without extension.
    # this returns with .wav extension always, irrespective of format or query args in s3 url.

    if fn.endswith(".flac"):
        return fn[:-5] + ".wav"
    if fn.endswith(".mp3"):
        return fn[:-4] + ".wav"

    return fn


def get_unix_epoch_timestamp_from_s3_presigned_url(s3_http_turn_audio_url: str) -> int:
    """
    returns unix epoch timestamp present in URL which is assumed to be in seconds
    """

    s3_url_parsed = urlparse(s3_http_turn_audio_url)
    return int((parse_qs(s3_url_parsed.query))["Expires"][0])


def re_presign_audio_url_if_required(s3_http_turn_audio_url: str) -> str:
    """
    check if the s3 http url for turn audio is valid or not - for downloading purposes only
    if not re-presign URLs using s3 client, for the next 7 days.

    this is highly specific to US, since the bucket is private there.
    """

    # checking if audio belongs to US production turn audios, and has expiry params
    if all(
        (
            substring in s3_http_turn_audio_url
            for substring in [
                "?",
                "Expires",
                const.S3_US_PRODUCTION_TURN_RECORDINGS_BUCKET,
            ]
        )
    ):

        # this is usually 7 days in the future for links already signed by skit-calls
        # if not, coming from transcription_pipeline, then it can be expired.
        unix_epoch_expiry_time_of_url = get_unix_epoch_timestamp_from_s3_presigned_url(
            s3_http_turn_audio_url
        )

        # in seconds
        present_epoch_time = int(time.time())

        # re-presign if the audio_url is expired
        if unix_epoch_expiry_time_of_url <= present_epoch_time:

            # inconveniently done again, but cheap. to extract s3 object key this time.
            s3_object_key = urlparse(s3_http_turn_audio_url).path.lstrip("/")

            # assumption that audio url won't change further, and will have bucket information in it.
            method_parameters = {
                "Bucket": const.S3_US_PRODUCTION_TURN_RECORDINGS_BUCKET,
                "Key": s3_object_key,
            }
            seven_days_in_seconds = 604800  # 7 days

            try:
                re_presigned_s3_url = generate_presigned_url(
                    s3_client=S3_CLIENT,
                    client_method="get_object",
                    method_parameters=method_parameters,
                    expires_in=seven_days_in_seconds,
                )
                return re_presigned_s3_url

            except Exception as e:
                logger.exception(e)
                # continue to return the given s3 url itself, in case of exception

    return s3_http_turn_audio_url
