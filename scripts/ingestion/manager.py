import pathlib
from typing import List

from . import LOADER_REGISTRY
from .models import RawDoc

class IngestionManager:
    def ingest_path(self, path: str | pathlib.Path) -> List[RawDoc]:
        if not isinstance(path, pathlib.Path):
            path = pathlib.Path(path)

        raw_docs = []
        for item in path.rglob("*"):  # rglob for recursive search
            if item.is_file() and item.suffix in LOADER_REGISTRY:
                loader_func = LOADER_REGISTRY[item.suffix]
                try:
                    content, metadata = loader_func(item)
                    raw_docs.append(RawDoc(content=content, metadata=metadata))
                except Exception as e:
                    print(f"Error loading {item}: {e}")  # Or handle more gracefully
        return raw_docs
