import faiss
import numpy as np
import json
import os
from sentence_transformers import SentenceTransformer


class VectorStore:
    def __init__(self, persist_dir: str = "./.faiss_store"):
        self.persist_dir = persist_dir
        os.makedirs(persist_dir, exist_ok=True)
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self.indexes = {}
        self.chunks = {}

    def ingest(self, chunks: list, collection_name: str) -> int:
        texts = [c["text"] for c in chunks]
        embeddings = self.model.encode(texts, show_progress_bar=False)
        embeddings = embeddings.astype("float32")

        embedding_dim = embeddings.shape[1]
        index = faiss.IndexFlatL2(embedding_dim)
        index.add(embeddings)

        self.indexes[collection_name] = index
        self.chunks[collection_name] = chunks

        index_path = os.path.join(self.persist_dir, f"{collection_name}.index")
        chunks_path = os.path.join(self.persist_dir, f"{collection_name}.json")

        faiss.write_index(index, index_path)
        with open(chunks_path, "w") as f:
            json.dump(chunks, f)

        return len(chunks)

    def search(self, query: str, collection_name: str, n_results: int = 5) -> list:
        if collection_name not in self.indexes:
            self._load(collection_name)

        if collection_name not in self.indexes:
            return []

        q_emb = self.model.encode([query])
        q_emb = q_emb.astype("float32")

        D, I = self.indexes[collection_name].search(q_emb, n_results)

        chunks = self.chunks[collection_name]
        return [chunks[i] for i in I[0] if i < len(chunks)]

    def _load(self, collection_name: str):
        index_path = os.path.join(self.persist_dir, f"{collection_name}.index")
        chunks_path = os.path.join(self.persist_dir, f"{collection_name}.json")

        if os.path.exists(index_path) and os.path.exists(chunks_path):
            self.indexes[collection_name] = faiss.read_index(index_path)
            with open(chunks_path, "r") as f:
                self.chunks[collection_name] = json.load(f)

    def clear(self, collection_name: str):
        self.indexes.pop(collection_name, None)
        self.chunks.pop(collection_name, None)

        index_path = os.path.join(self.persist_dir, f"{collection_name}.index")
        chunks_path = os.path.join(self.persist_dir, f"{collection_name}.json")

        if os.path.exists(index_path):
            os.remove(index_path)
        if os.path.exists(chunks_path):
            os.remove(chunks_path)
