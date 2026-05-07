import sys
from pathlib import Path
from pipeline.chunker import chunk_document
from pipeline.embedder import VectorStore

def create_sample_files():
    uploads_dir = Path("uploads")
    uploads_dir.mkdir(exist_ok=True)

    txt_file = uploads_dir / "sample.txt"
    if not txt_file.exists():
        with open(txt_file, "w") as f:
            f.write("""
The artificial intelligence revolution is transforming industries and society.
Machine learning models are becoming increasingly sophisticated and capable.
Natural language processing enables computers to understand and generate human language.
Deep learning networks power many modern AI applications from image recognition to language translation.
Transformer models have revolutionized natural language understanding and generation capabilities.
The future of AI lies in developing more efficient and interpretable models.
Quantum computing may further accelerate AI research and capabilities in the coming decades.
Ethical considerations are crucial as AI systems become more powerful and widespread.
""")
        print(f"Created sample text file: {txt_file}")
    
    return str(txt_file)

def test_chunking():
    print("\n=== Testing Document Chunking ===")
    txt_file = create_sample_files()
    
    chunks = chunk_document(txt_file)
    
    print(f"Total chunks created: {len(chunks)}")
    print(f"\nFirst chunk:")
    print(f"  chunk_id: {chunks[0]['chunk_id']}")
    print(f"  text: {chunks[0]['text'][:100]}...")
    print(f"  source_file: {chunks[0]['source_file']}")
    print(f"  page_number: {chunks[0]['page_number']}")
    print(f"  char_count: {chunks[0]['char_count']}")
    
    return chunks

def test_embedding(chunks):
    print("\n=== Testing Vector Storage and Embedding ===")
    
    store = VectorStore()
    collection_name = "test_docs"
    
    print(f"Ingesting {len(chunks)} chunks into collection '{collection_name}'...")
    store.ingest(chunks, collection_name)
    print("Chunks ingested successfully!")
    
    print("\n=== Testing Search ===")
    test_queries = [
        "machine learning and AI",
        "natural language processing",
        "ethics and AI"
    ]
    
    for query in test_queries:
        print(f"\nQuery: '{query}'")
        results = store.search(query, collection_name, n_results=2)
        for i, result in enumerate(results, 1):
            print(f"  Result {i}: {result['text'][:80]}...")
            print(f"    Metadata: {result['metadata']}")
    
    print("\n=== Testing Clear ===")
    store.clear(collection_name)
    print(f"Collection '{collection_name}' cleared successfully!")

if __name__ == "__main__":
    chunks = test_chunking()
    test_embedding(chunks)
    print("\n[OK] All tests completed successfully!")
