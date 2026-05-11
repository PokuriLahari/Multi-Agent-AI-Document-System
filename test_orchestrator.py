from pipeline.chunker import chunk_document
from pipeline.embedder import VectorStore
from agents.orchestrator import OrchestratorAgent
from memory.store import SessionMemory

print("=== Testing Orchestrator ===\n")

# Step 1: Chunk and ingest document
print("Step 1: Chunking and ingesting document...")
chunks = chunk_document("uploads/my_document.pdf")
print(f"  Created {len(chunks)} chunks")

# Step 2: Create vector store and ingest
print("\nStep 2: Storing chunks in ChromaDB...")
store = VectorStore()
collection_name = "test_orchestrator"
store.ingest(chunks, collection_name)
print(f"  Ingested into collection: {collection_name}")

# Step 3: Create orchestrator
print("\nStep 3: Creating OrchestratorAgent...")
orchestrator = OrchestratorAgent()
print("  OrchestratorAgent created")

# Step 4: Test different intents
print("\nStep 4: Testing different intents...\n")

test_queries = [
    ("Summarise this document", "SUMMARISE"),
    ("What is this document about?", "QA"),
    ("Analyse the content", "ANALYSE"),
]

for query, expected_intent in test_queries:
    print(f"Query: '{query}'")
    print(f"Expected intent: {expected_intent}")
    result = orchestrator.process(query, collection_name, store)
    print(f"Detected intent: {result['intent']}")
    print(f"Chunks used: {result['chunks_used']}")
    print(f"Response: {result['response'][:150]}...\n")

# Step 5: Test SessionMemory
print("Step 5: Testing SessionMemory...\n")
memory = SessionMemory()
memory.add_turn("user", "What is a binomial heap?")
memory.add_turn("assistant", "A binomial heap is...")
memory.add_turn("user", "How does it differ from Fibonacci heap?")
memory.add_turn("assistant", "A Fibonacci heap is...")

print(f"Total turns in history: {len(memory.get_history())}")
print(f"\nLast 5 turns formatted:\n{memory.get_context_string()}")

print(f"\n\nFull history: {len(memory.get_history())} turns")
print("Clear memory...")
memory.clear()
print(f"After clear: {len(memory.get_history())} turns")

# Step 6: Cleanup
print("\n\nStep 6: Cleanup...")
store.clear(collection_name)
print(f"Collection '{collection_name}' cleared")

print("\n[OK] All orchestrator tests completed!")
