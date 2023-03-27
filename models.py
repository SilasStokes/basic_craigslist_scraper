from dataclasses import dataclass
from dataclasses_json import dataclass_json
from typing import Optional

@dataclass_json
@dataclass
class Craigslist_Result_Card():
    link: str
    title: str
    id: str
