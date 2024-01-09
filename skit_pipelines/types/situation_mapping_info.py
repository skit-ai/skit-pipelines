from collections import namedtuple
from typing import NamedTuple, List, Dict

name = "SituationMappingInfo"
situation_mapping_info = "situation_mapping_info"
SituationMappingInfo = namedtuple(name, f"{situation_mapping_info}")
SituationMappingInfoResponseType = NamedTuple(name, [(situation_mapping_info, List[Dict[str, str]])])