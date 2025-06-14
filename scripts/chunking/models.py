from dataclasses import dataclass
from typing import Dict

@dataclass
class Chunk:
    text: str
    meta: Dict
    token_count: int
