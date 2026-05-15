import os
import json
import math
import uuid

class VectorStore:
    def __init__(self, persist_dir="./.vector_store"):
        self.persist_dir = persist_dir
        self.store = {}
        os.makedirs(persist_dir, exist_ok=True)

    def _embed(self, text: str) -> dict:
        words = text.lower().split()
        freq = {}
        for w in words:
            freq[w] = freq.get(w, 0) + 1
        total = max(len(words), 1)
        return {w: c / total for w, c in freq.items()}

    def _similarity(self, a: dict, b: dict) -> float:
        keys = set(a) & set(b)
        if not keys:
            return 0.0
        dot = sum(a[k] * b[k] for k in keys)
        mag_a = math.sqrt(sum(v*v for v in a.values()))
        mag_b = math.sqrt(sum(v*v for v in b.values()))
        if mag_a == 0 or mag_b == 0:
            return 0.0
        return dot / (mag_a * mag_b)

    def ingest(self, chunks: list, collection_name: str) -> int:
        docs = []
        for c in chunks:
            docs.append({
                "id":          str(uuid.uuid4()),
                "text":        c["text"],
                "embedding":   self._embed(c["text"]),
                "source_file": c.get("source_file", ""),
                "page_number": c.get("page_number", 0),
            })
        self.store[collection_name] = docs
        path = os.path.join(self.persist_dir, f"{collection_name}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(docs, f, ensure_ascii=False)
        return len(docs)

    def search(self, query: str, collection_name: str,
               n_results: int = 5) -> list:
        if collection_name not in self.store:
            self._load(collection_name)
        docs = self.store.get(collection_name, [])
        if not docs:
            return []
        q_emb = self._embed(query)
        scored = sorted(
            docs,
            key=lambda d: self._similarity(q_emb, d["embedding"]),
            reverse=True
        )
        return [
            {
                "text":        d["text"],
                "source_file": d["source_file"],
                "page_number": d["page_number"]
            }
            for d in scored[:n_results]
        ]

    def _load(self, collection_name: str):
        path = os.path.join(self.persist_dir, f"{collection_name}.json")
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                self.store[collection_name] = json.load(f)

    def clear(self, collection_name: str):
        self.store.pop(collection_name, None)
        path = os.path.join(self.persist_dir, f"{collection_name}.json")
        if os.path.exists(path):
            os.remove(path)
