from collections import namedtuple
from typing import NamedTuple

name = "TaggingResponse"
errors = "errors"
df_sizes = "df_sizes"
TaggingResponse = namedtuple(name, f"{errors} {df_sizes}")
TaggingResponseType = NamedTuple(name, [(errors, str), (df_sizes, str)])
