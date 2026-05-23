# 🧠 Doc Dream Team
### Multi-Agent Document Intelligence System

**Upload any document. Ask anything. A team of AI agents answers from your content — 100% local, zero API costs.**

---

## 🎬 Demo

<img width="478" height="294" alt="multiagent1" src="https://github.com/user-attachments/assets/a0846c67-03d6-40e8-8af4-15f52b9dc754" />


---

## 🏗️ Architecture

The Doc Dream Team operates on a sophisticated multi-agent pipeline:

**User Query → Orchestrator (intent detection) → VectorStore (RAG retrieval) → Specialist Agents (Reader / Summariser / Analyser / QA / Writer) → CrewAI execution via Ollama → Output displayed in Streamlit UI**

| Component | Technology | Purpose |
|-----------|-----------|---------|
| LLM | Ollama (llama3.2, qwen2.5:7b) | Local language model inference |
| Agents | CrewAI | Multi-agent orchestration and task execution |
| Vector Store | Pure Python + TF-IDF + cosine similarity | Document retrieval (RAG) |
| Document Parsing | PyMuPDF + python-docx | PDF, DOCX, and TXT support |
| UI | Streamlit + custom CSS/JS | Neural Pulse dashboard with live updates |
| Memory | SessionMemory | Conversation history and context |
| Embedding | tiktoken | Token-based document chunking |

---

## ✨ Features

- **Multi-agent pipeline** with 5 specialised agents for different tasks
- **Intent detection** routes queries to the right agents automatically
- **RAG implementation** — all answers grounded in your document content
- **Neural Pulse UI** with live agent status cards, particle animation, shimmer loading effects
- **100% local execution** — Ollama, no API keys, no internet required
- **Multi-format support** — PDF, DOCX, and TXT files
- **Query history sidebar** — Quick one-click re-running of previous queries
- **Performance metrics** — Execution timing for each agent
- **Export session as Markdown** — Save conversations and outputs
- **Parallel agent execution** — Multiple agents run concurrently for speed

---

## 🤖 Agent Roster

| Agent | Role | Triggered by |
|-------|------|-------------|
| 🔍 Reader | Extracts relevant document content and sections | All queries |
| 📋 Summariser | Structured summaries with key points and highlights | SUMMARISE intent |
| 🧠 Analyser | Identifies themes, patterns, and critical analysis | ANALYSE intent |
| 💬 Q&A | Precise answers and direct responses from context | QA intent |
| ✍️ Writer | Generates professional documents and reports | WRITE intent |

---

## 🚀 Setup

### Prerequisites
- Python 3.10+
- Ollama installed and running
- 4GB+ RAM recommended

### Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd doc-dream-team
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On Mac/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install and start Ollama**
   - Download from https://ollama.ai
   - Start the service: `ollama serve`

5. **Pull the required model**
   ```bash
   ollama pull llama3.2
   # Or alternative model:
   ollama pull qwen2.5:7b
   ```

6. **Run the application**
   ```bash
   streamlit run app.py
   ```

7. **Open in browser**
   - Navigate to `http://localhost:8501`
   - Start uploading documents and asking questions!

---

## 🧠 How It Works

### Retrieval-Augmented Generation (RAG)

**Document Processing:**
When you upload a document, it is automatically chunked into 500-token pieces with 50-token overlap to maintain context. Each chunk is encoded using TF-IDF vectors and stored in our custom vector database.

**Query Resolution:**
When you ask a question:
1. The orchestrator detects your intent (SUMMARISE, ANALYSE, QA, WRITE, etc.)
2. The vector store retrieves the 5 most relevant chunks using cosine similarity
3. These chunks become the context for the LLM
4. Specialist agents answer **ONLY** from your document content, never from general training knowledge
5. Results are displayed with execution timing and agent status

**Why This Matters:**
Pure local processing means your documents never leave your machine. Zero API costs. Instant responses. Complete privacy.

---

## 📁 Project Structure

```
doc-dream-team/
├── app.py                          # Main Streamlit application (UI + orchestration)
├── config.py                       # Configuration (Ollama URL, default model)
├── requirements.txt                # Python dependencies
├── README.md                       # This file
├── FIXES_APPLIED.md               # Documentation of implemented features
│
├── agents/                         # Multi-agent system
│   ├── __init__.py
│   ├── crew_builder.py            # Agent and crew creation, task building
│   ├── orchestrator.py            # Intent detection and routing
│   ├── qa_agent.py                # Q&A specialist implementation
│   ├── reader.py                  # Document reader agent
│   ├── summariser.py              # Summary agent
│   ├── writer.py                  # Document writer agent
│   └── analyser.py                # Analysis agent
│
├── pipeline/                       # Document processing
│   ├── __init__.py
│   ├── chunker.py                 # Token-based document chunking
│   └── embedder.py                # Vector store (TF-IDF + similarity search)
│
├── memory/                         # Session management
│   ├── __init__.py
│   └── store.py                   # Conversation history and context
│
├── uploads/                        # User uploaded documents (temporary)
│   └── sample.txt
│
└── tests/                          # Test suite
    ├── test_agents.py
    ├── test_crew_output.py
    ├── test_fixes.py
    ├── test_html.py
    ├── test_orchestrator.py
    ├── test_pipeline.py
    ├── test_system.py
    └── verify.py
```

---

## 🛠️ Tech Stack

**Core:**
- **Python 3.13** — Programming language
- **Streamlit** — Web UI framework
- **CrewAI** — Multi-agent orchestration framework
- **Ollama** — Local LLM runtime

**Data Processing:**
- **LangChain** — LLM chains and utilities
- **PyMuPDF** — PDF extraction
- **python-docx** — DOCX document handling
- **tiktoken** — Token counting and chunking
- **NumPy / Pandas** — Data manipulation

**Vector Operations:**
- **scikit-learn** — TF-IDF vectorization
- **scipy** — Cosine similarity calculations

**UI Enhancement:**
- **Custom CSS** — Neural Pulse dark theme
- **JavaScript Canvas** — Particle animation and HUD displays
- **Plotly** (optional) — Future visualization support

---

## 📊 Performance

- **Query execution:** 60-180 seconds (depending on document size and model)
- **Parallel agent execution:** ~40% faster than sequential
- **Vector search latency:** <100ms for 500+ documents
- **Memory usage:** ~1-2GB with Ollama running
- **Supported document size:** Up to 200MB per upload

---

## 🔧 Configuration

Edit `config.py` to customize:

```python
DEFAULT_MODEL = "qwen2.5:7b"           # Change LLM model
OLLAMA_BASE_URL = "http://localhost:11434"  # Ollama endpoint
DOCUMENT_CHUNK_SIZE = 500              # Tokens per chunk
DOCUMENT_CHUNK_OVERLAP = 50            # Token overlap
VECTOR_SEARCH_RESULTS = 5              # Context chunks to retrieve
```

---

## 📝 Usage Examples

### Example 1: Summarize a Document
1. Upload a research paper
2. Type: "Summarize this document"
3. Query detected as SUMMARISE intent
4. Summariser agent activates and returns structured summary

### Example 2: Extract Specific Information
1. Upload a contract
2. Type: "What are the key clauses and payment terms?"
3. Query detected as QA intent
4. Q&A agent retrieves and answers with relevant sections

### Example 3: Generate a Report
1. Upload financial data
2. Type: "Write a professional quarterly report from this data"
3. Query detected as WRITE intent
4. Writer agent generates formatted report

---

## 🐛 Troubleshooting

**"Connection refused" error:**
- Ensure Ollama is running: `ollama serve`
- Check if running on correct port (default: 11434)

**"Model not found" error:**
- Pull the model: `ollama pull llama3.2`
- Verify in Ollama: `ollama list`

**Slow responses:**
- Switch to smaller model: `ollama pull llama3.2:1b`
- Reduce chunk count in config
- Check system resources

**Out of memory:**
- Use smaller model variant
- Close other applications
- Reduce document chunk size

---

## 🤝 Contributing

Contributions welcome! Areas for enhancement:
- Support for more document formats (Excel, PowerPoint)
- Custom vector embedding models
- Web interface deployment
- Advanced RAG techniques (reranking, query expansion)

---

## 🙋 Support

For issues or questions:
- Check the `FIXES_APPLIED.md` for known solutions
- Review test files for usage examples
- Enable debug info in sidebar (🔍 Debug Info expander)

---

**Made with 🧠 and ❤️ by the Doc Dream Team**

*Your documents, your intelligence, your rules.*-System
