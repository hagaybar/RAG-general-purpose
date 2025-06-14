import pathlib
import inspect  # Added import
from typing import List

from . import LOADER_REGISTRY
from .models import RawDoc, UnsupportedFileError


class IngestionManager:
    def ingest_path(self, path: str | pathlib.Path) -> List[RawDoc]:
        if not isinstance(path, pathlib.Path):
            path = pathlib.Path(path)

        raw_docs = []
        for item in path.rglob("*"):  # rglob for recursive search
            if item.is_file() and item.suffix in LOADER_REGISTRY:
                loader_or_class = LOADER_REGISTRY[item.suffix]
                base_metadata = {
                    'source_filepath': str(item),
                    'doc_type': item.suffix.lstrip('.')
                }
                try:
                    if inspect.isclass(loader_or_class):
                        # Handle class-based ingestors (e.g., PptxIngestor)
                        ingestor_instance = loader_or_class()
                        # PptxIngestor.ingest() returns:
                        # list[tuple[str, dict]]
                        ingested_segments = ingestor_instance.ingest(str(item))
                        for text_segment, seg_meta in ingested_segments:
                            final_meta = base_metadata.copy()
                            # segment_meta includes doc_type from PptxIngestor
                            final_meta.update(seg_meta)
                            raw_docs.append(
                                RawDoc(content=text_segment,
                                       metadata=final_meta)
                            )
                    else:
                        # Handle function-based loaders
                        # Assuming: (content: str, metadata: dict)
                        if not callable(loader_or_class):
                            # This case should ideally not be reached if LOADER_REGISTRY is set up correctly
                            print(f"Error: Loader for {item.suffix} is not callable.")
                            continue
                        content, metadata = loader_or_class(str(item))
                        final_meta = base_metadata.copy()
                        final_meta.update(metadata)
                        raw_docs.append(
                            RawDoc(content=content, metadata=final_meta)
                        )
                except UnsupportedFileError as e:
                    print(f"Skipping unsupported file {item}: {e}")
                except Exception as e:
                    # Or handle more gracefully
                    print(f"Error loading {item}: {e}")
        return raw_docs
