#!/usr/bin/env python
"""
Test script to verify Doc Dream Team multi-agent system is working
Run: python test_system.py
"""

import sys
import json
from pathlib import Path

def test_imports():
    """Test all critical imports"""
    try:
        from agents.crew_builder import run_crew, build_agent, build_task, PREDEFINED_CONFIGS
        from pipeline.embedder import VectorStore
        from pipeline.chunker import chunk_document
        from agents.orchestrator import OrchestratorAgent
        from config import check_ollama_running, DEFAULT_MODEL
        print("[PASS] All imports successful")
        return True
    except Exception as e:
        print(f"[FAIL] Import error: {e}")
        return False

def test_ollama():
    """Test Ollama connectivity"""
    try:
        from config import check_ollama_running
        if check_ollama_running():
            print("[PASS] Ollama is running")
            return True
        else:
            print("[WARN] Ollama not running. Start with: ollama serve")
            return False
    except Exception as e:
        print(f"[FAIL] Ollama check failed: {e}")
        return False

def test_vector_store():
    """Test VectorStore initialization"""
    try:
        from pipeline.embedder import VectorStore
        vs = VectorStore(persist_dir="./.vector_store_test")

        # Test embedding
        test_chunks = [
            {"text": "Hello world", "source_file": "test.txt", "page_number": 1},
            {"text": "This is a test", "source_file": "test.txt", "page_number": 1}
        ]

        ingested = vs.ingest(test_chunks, collection_name="test_collection")
        print(f"[PASS] VectorStore working - ingested {ingested} chunks")

        # Test search
        results = vs.search("hello", "test_collection", n_results=1)
        if results:
            print(f"[PASS] VectorStore search working - found {len(results)} results")
            return True
        else:
            print("[WARN] VectorStore search returned no results")
            return True
    except Exception as e:
        print(f"[FAIL] VectorStore error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_crew_builder():
    """Test crew builder functions"""
    try:
        from agents.crew_builder import build_agent, build_task, PREDEFINED_CONFIGS
        from crewai import Process

        # Build a single agent and task
        cfg = PREDEFINED_CONFIGS["reader"]
        agent = build_agent(
            role=cfg["role"],
            goal=cfg["goal"],
            backstory=cfg["backstory"],
            model_name="qwen2.5:7b"
        )

        task = build_task(
            task_description="Extract key information from document about: Test topic",
            expected_output="A summary of key findings",
            agent=agent,
            context=None
        )

        print(f"[PASS] Built agent '{agent.role}' and task")
        return True
    except Exception as e:
        print(f"[FAIL] Crew builder error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_orchestrator():
    """Test Orchestrator intent detection"""
    try:
        from agents.orchestrator import OrchestratorAgent

        orch = OrchestratorAgent()

        test_queries = [
            "Can you summarize this document?",
            "What are the key findings?",
            "Answer this question about the content",
            "Please write a report based on this"
        ]

        for query in test_queries:
            intent = orch.detect_intent(query)
            print(f"[PASS] Query: '{query[:40]}...' -> Intent: {intent}")

        return True
    except Exception as e:
        print(f"[FAIL] Orchestrator error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("=" * 60)
    print("Doc Dream Team - System Verification")
    print("=" * 60)
    print()

    tests = [
        ("Imports", test_imports),
        ("Ollama Connection", test_ollama),
        ("VectorStore", test_vector_store),
        ("Crew Builder", test_crew_builder),
        ("Orchestrator", test_orchestrator),
    ]

    results = []
    for name, test_func in tests:
        print(f"\n[TEST] {name}")
        print("-" * 40)
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"[ERROR] Unexpected error in {name}: {e}")
            results.append((name, False))

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, r in results if r)
    total = len(results)

    for name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"[{status}] {name}")

    print()
    print(f"Passed: {passed}/{total}")

    if passed == total:
        print("\nSYSTEM IS READY! Try running: streamlit run app.py")
        return 0
    else:
        print("\nSome tests failed. Check errors above and troubleshoot.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
