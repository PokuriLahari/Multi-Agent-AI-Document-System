from pipeline.chunker import chunk_document
from pipeline.embedder import VectorStore

# Step 1: Chunk your document
chunks = chunk_document("uploads/my_document.pdf")
print(f"Created {len(chunks)} chunks")
print(f"First chunk: {chunks[0]['text'][:100]}...")

# Step 2: Store chunks in ChromaDB
store = VectorStore()
store.ingest(chunks, "my_docs")
print("Chunks stored!")

# Step 3: Search
results = store.search("your search query here", "my_docs", n_results=3)
for i, result in enumerate(results, 1):
    print(f"\nResult {i}:")
    print(f"  Text: {result['text'][:150]}...")
    print(f"  Source: {result['metadata']['source_file']}")
    print(f"  Page: {result['metadata']['page_number']}")