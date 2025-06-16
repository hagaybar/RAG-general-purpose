import hashlib
import json
from pathlib import Path
from typing import List, Dict

import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

from scripts.chunking.models import Chunk
from scripts.core.project_manager import ProjectManager

class ChunkEmbedder:
    def __init__(self, project: ProjectManager, model_name: str = "BAAI/bge-large-en"):
        self.project = project
        self.model = SentenceTransformer(model_name)
        self.dim = self.model.get_sentence_embedding_dimension()

    def run(self, chunks: List[Chunk]) -> None:
        # Group by doc_type
        doc_type_map: Dict[str, List[Chunk]] = {}
        for chunk in chunks:
            doc_type = chunk.meta.get("doc_type", "default")
            doc_type_map.setdefault(doc_type, []).append(chunk)

        for doc_type, chunk_group in doc_type_map.items():
            print(f"Embedding {len(chunk_group)} chunks for doc_type={doc_type}...")
            self._process_doc_type(doc_type, chunk_group)

    def _process_doc_type(self, doc_type: str, chunks: List[Chunk]) -> None:
        index_path = self.project.get_faiss_path(doc_type)
        meta_path = self.project.get_metadata_path(doc_type)

        existing_ids = set()
        if index_path.exists():
            index = faiss.read_index(str(index_path))
            if meta_path.exists():
                with open(meta_path, "r", encoding="utf-8") as f:
                    for line in f:
                        meta = json.loads(line)
                        existing_ids.add(meta["id"])
        else:
            index = faiss.IndexFlatL2(self.dim)

        new_embeddings = []
        new_metadata = []

        for chunk in chunks:
            chunk_id = self._hash_text(chunk.text)
            if chunk_id in existing_ids:
                continue
            emb = self.model.encode(chunk.text)
            new_embeddings.append(emb)
            chunk.meta["id"] = chunk_id
            new_metadata.append(chunk.meta)

        if new_embeddings:
            emb_array = np.vstack(new_embeddings).astype("float32")
            index.add(emb_array)
            faiss.write_index(index, str(index_path))
            with open(meta_path, "a", encoding="utf-8") as f:
                for meta in new_metadata:
                    f.write(json.dumps(meta) + "\n")
            print(f"Appended {len(new_embeddings)} new vectors to {index_path.name}")
        else:
            print("No new chunks to embed.")

    def _hash_text(self, text: str) -> str:
        return hashlib.sha256(text.strip().encode("utf-8")).hexdigest()
