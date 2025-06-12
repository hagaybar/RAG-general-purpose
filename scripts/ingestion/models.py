from dataclasses import dataclass

@dataclass
class RawDoc:
    content: str
    metadata: dict

class UnsupportedFileError(Exception):
    pass
