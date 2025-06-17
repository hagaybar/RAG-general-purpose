import csv
import json
from typing import List
from scripts.chunking.models import Chunk  # adjust path if needed

def load_chunks(chunks_path) -> List[Chunk]:
    chunks: List[Chunk] = []
    with open(chunks_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            chunk = Chunk(
                id=row["chunk_id"],
                doc_id=row["doc_id"],
                text=row["text"],
                meta=json.loads(row["meta_json"]),
                token_count=len(row["text"].split())  # or replace with accurate counter
            )
            chunks.append(chunk)
    return chunks
