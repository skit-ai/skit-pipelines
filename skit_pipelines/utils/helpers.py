

def convert_audiourl_to_filename(audiourl):
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