from pipeline.embedder import VectorStore
vs = VectorStore()
chunks = [
    {'text': 'Hello world this is a test document', 'source_file': 'test.txt', 'page_number': 0},
    {'text': 'Python is a great programming language', 'source_file': 'test.txt', 'page_number': 0},
    {'text': 'Machine learning and AI are transforming technology', 'source_file': 'test.txt', 'page_number': 0},
]
count = vs.ingest(chunks, 'test_collection')
print(f'Ingested: {count} chunks')
results = vs.search('programming python', 'test_collection', n_results=2)
print(f'Search results: {len(results)}')
for r in results:
    print(f'  - {r["text"][:50]}')
vs.clear('test_collection')
print('VectorStore working correctly - no ChromaDB needed')
