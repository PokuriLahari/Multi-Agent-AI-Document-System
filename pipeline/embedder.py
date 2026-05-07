import chromadb
from typing import Optional


class VectorStore:
    def __init__(self, persist_dir: str = "./.chroma"):
        self.client = chromadb.PersistentClient(path=persist_dir)

    def ingest(self, chunks: list[dict], collection_name: str) -> None:
        collection = self.client.get_or_create_collection(name=collection_name)

        ids = []
        documents = []
        metadatas = []

        for chunk in chunks:
            ids.append(chunk["chunk_id"])
            documents.append(chunk["text"])
            metadatas.append(
                {
                    "source_file": chunk["source_file"],
                    "page_number": chunk.get("page_number"),
                    "char_count": str(chunk["char_count"]),
                }
            )

        collection.add(ids=ids, documents=documents, metadatas=metadatas)

    def search(self, query: str, collection_name: str, n_results: int = 5) -> list[dict]:
        collection = self.client.get_collection(name=collection_name)

        results = collection.query(query_texts=[query], n_results=n_results)

        search_results = []
        for i in range(len(results["ids"][0])):
            search_results.append(
                {
                    "chunk_id": results["ids"][0][i],
                    "text": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "distance": results["distances"][0][i],
                }
            )

        return search_results

    def clear(self, collection_name: str) -> None:
        try:
            self.client.delete_collection(name=collection_name)
        except Exception:
            pass
