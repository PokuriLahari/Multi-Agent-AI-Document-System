import os
import time
import requests
import streamlit as st

# Page Configuration
st.set_page_config(
    page_title="Multi-Agent Document Intelligence",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Backend URL config
BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")

# Custom CSS for styling
st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        color: #6c757d;
        font-size: 1.05rem;
        margin-bottom: 1.5rem;
    }
    .status-card {
        padding: 1rem 1.25rem;
        border-radius: 8px;
        background-color: #f8f9fa;
        border-left: 5px solid #28a745;
        margin-bottom: 1rem;
    }
    .metric-badge {
        display: inline-block;
        padding: 0.25rem 0.5rem;
        border-radius: 4px;
        font-size: 0.85rem;
        font-weight: 600;
        background: #e9ecef;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("⚙️ System Control")
    st.write(f"**Backend Endpoint:** `{BACKEND_URL}`")
    
    st.markdown("---")
    st.subheader("📋 Sprint Roadmap")
    sprints = [
        ("Sprint 0", "Skeleton & Foundations", "🟢 In Progress / Demo"),
        ("Sprint 1", "Ingestion + Retrieval Core", "⚪ Pending"),
        ("Sprint 2", "Core RAG Loop & Citations", "⚪ Pending"),
        ("Sprint 3", "Routing & Multi-Capability", "⚪ Pending"),
        ("Sprint 4", "Structured Operations", "⚪ Pending"),
        ("Sprint 5", "Reasoning & Multi-turn Memory", "⚪ Pending"),
        ("Sprint 6", "Source Management & Polish", "⚪ Pending"),
    ]
    for s_id, name, status in sprints:
        st.markdown(f"**{s_id}**: {name}  \n*{status}*")

# Main Page Header
st.markdown('<div class="main-title">📄 Multi-Agent Document Intelligence System</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Sprint 0: Skeleton & End-to-End Foundations</div>', unsafe_allow_html=True)

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("🔌 Backend Health Check")
    if st.button("Check Backend Status", key="btn_health"):
        with st.spinner("Pinging FastAPI backend..."):
            start = time.perf_counter()
            try:
                resp = requests.get(f"{BACKEND_URL}/api/health", timeout=3.0)
                elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
                if resp.status_code == 200:
                    data = resp.json()
                    st.success(f" Connected successfully ({elapsed_ms} ms)")
                    st.json(data)
                else:
                    st.error(f"Backend returned status {resp.status_code}")
            except Exception as e:
                st.error(f"Failed to connect to backend: {e}")
                st.info("Make sure the backend is running with: `python -m uvicorn backend.app.main:app --port 8000`")

    st.markdown("---")
    st.subheader("👋 End-to-End Hello Test")
    user_name = st.text_input("Enter your name:", value="Solo Engineer")
    if st.button("Send Greeting to Backend", key="btn_hello"):
        with st.spinner("Sending request to /api/hello..."):
            start = time.perf_counter()
            try:
                resp = requests.get(f"{BACKEND_URL}/api/hello", params={"name": user_name}, timeout=3.0)
                elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
                if resp.status_code == 200:
                    data = resp.json()
                    st.success(f" Response received in {elapsed_ms} ms!")
                    st.json(data)
                else:
                    st.error(f"Error: {resp.status_code}")
            except Exception as e:
                st.error(f"Connection failed: {e}")

with col2:
    st.subheader("⏱️ Observability & Agent Latency Log")
    st.caption("Rule 4 Requirement: Structured logging with per-agent latency tracking")
    
    if st.button("Refresh Execution Metrics", key="btn_metrics"):
        try:
            resp = requests.get(f"{BACKEND_URL}/api/metrics", timeout=3.0)
            if resp.status_code == 200:
                metrics_data = resp.json()
                st.write(f"Total agent executions recorded: **{metrics_data.get('total_calls', 0)}**")
                items = metrics_data.get("metrics", [])
                if items:
                    st.dataframe(items, use_container_width=True)
                else:
                    st.info("No agent metrics recorded yet. Trigger backend operations to see logs.")
        except Exception as e:
            st.warning(f"Could not load metrics: {e}")

    st.markdown("---")
    st.subheader("📦 System Architecture Overview")
    st.code("""
[ Streamlit Frontend (Port 8501) ]
           │
           ▼ (HTTP / REST)
[ FastAPI Backend (Port 8000) ]
     ├── Orchestrator (Intent Routing - Sprint 3)
     ├── Agents (Plain Python Classes)
     │    ├── IngestionAgent (Sprint 1)
     │    ├── RetrievalAgent + ChromaDB (Sprint 1)
     │    ├── QAAgent + Citations (Sprint 2)
     │    ├── SummarizationAgent (Sprint 3)
     │    ├── ExplanationAgent (Sprint 3)
     │    ├── ComparisonAgent (Sprint 4)
     │    ├── ExtractionAgent (Sprint 4)
     │    ├── GenerationAgent (Sprint 5)
     │    └── MemoryManager (Sprint 5)
     ├── Observability (@timed_agent latency logging)
     └── SQLite DB (Metadata, Sources, Jobs)
    """, language="text")
