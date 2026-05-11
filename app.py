import streamlit as st
import streamlit.components.v1 as components
import os, uuid, time, json
from pathlib import Path
from pipeline.chunker import chunk_document
from pipeline.embedder import VectorStore
from agents.orchestrator import OrchestratorAgent
from agents.crew_builder import get_predefined_configs, build_crew_agent, run_crew
from memory.store import SessionMemory
from config import check_ollama_running, DEFAULT_MODEL

AGENT_CONFIG = {
    'reader':     {'icon': '🔍', 'label': 'Reader'},
    'summariser': {'icon': '📋', 'label': 'Summariser'},
    'analyser':   {'icon': '🧠', 'label': 'Analyser'},
    'qa':         {'icon': '💬', 'label': 'Q&A'},
    'writer':     {'icon': '✍️', 'label': 'Writer'}
}

st.set_page_config(
    page_title="Doc Dream Team",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.session_state.setdefault('vector_store', VectorStore())
st.session_state.setdefault('orchestrator', OrchestratorAgent())
st.session_state.setdefault('memory', SessionMemory())
st.session_state.setdefault('collection_name', None)
st.session_state.setdefault('doc_meta', {})
st.session_state.setdefault('run_count', 0)
st.session_state.setdefault('token_count', 0)
st.session_state.setdefault('session_id', str(uuid.uuid4())[:8].upper())
st.session_state.setdefault('selected_model', 'llama3.2')
st.session_state.setdefault('agent_states', {
    'reader': 'idle',
    'summariser': 'idle',
    'analyser': 'idle',
    'qa': 'idle',
    'writer': 'idle'
})
st.session_state.setdefault('outputs', {
    'reader': None, 'summariser': None,
    'analyser': None, 'qa': None, 'writer': None
})
st.session_state.setdefault('last_query', '')
st.session_state.setdefault('is_running', False)

if not check_ollama_running():
    st.error("Alert: Ollama is not running. Open a terminal and run:  ollama serve")
    st.stop()

st.markdown("""
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body, .stApp { background: #07071a !important; color: #e0e0ff; font-family: 'Monaco', monospace; }

.np-topbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 14px 24px;
    border-bottom: 1px solid rgba(139, 92, 246, 0.15);
    margin-bottom: 20px;
    background: rgba(15, 15, 40, 0.8);
}

.np-logo {
    display: flex;
    align-items: center;
    gap: 8px;
}

.np-logo-mark { font-size: 20px; }
.np-logo-name { font-size: 16px; font-weight: bold; color: #a78bfa; }
.np-logo-sub { font-size: 10px; color: #3a3a6a; margin-left: 4px; }

.np-pills {
    display: flex;
    gap: 12px;
}

.np-pill {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 6px 12px;
    background: rgba(139, 92, 246, 0.08);
    border: 1px solid rgba(139, 92, 246, 0.2);
    border-radius: 20px;
    font-size: 11px;
    color: #a78bfa;
}

.pd-green {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #34d399;
    box-shadow: 0 0 8px rgba(52, 211, 153, 0.5);
}

.hud-wrap {
    position: relative;
    width: 100%;
    margin-bottom: 24px;
}

canvas {
    display: block;
    width: 100%;
    height: 220px;
    background: #07071a;
    border-radius: 8px;
    border: 1px solid rgba(139, 92, 246, 0.1);
}

.nc-hud {
    position: absolute;
    font-size: 10px;
    color: #a78bfa;
    font-weight: bold;
    text-shadow: 0 0 12px rgba(139, 92, 246, 0.3);
}

.nc-hud-label { font-size: 8px; color: #6a6a9a; text-transform: uppercase; }
.nc-hud-value { font-size: 12px; color: #34d399; margin: 2px 0; }

.nc-hud-tl { top: 12px; left: 12px; }
.nc-hud-tr { top: 12px; right: 12px; text-align: right; }
.nc-hud-br { bottom: 12px; right: 12px; text-align: right; }

.np-stats {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 16px;
    margin: 24px 0;
}

.np-stat-card {
    padding: 16px;
    background: rgba(139, 92, 246, 0.05);
    border: 1px solid rgba(139, 92, 246, 0.15);
    border-radius: 8px;
    text-align: center;
}

.np-stat-label { font-size: 9px; color: #3a3a6a; text-transform: uppercase; letter-spacing: 1px; }
.np-stat-value { font-size: 24px; font-weight: bold; color: #a78bfa; margin: 8px 0; }
.np-stat-sub { font-size: 10px; color: #3a3a6a; }

.sec-label {
    font-size: 9px;
    text-transform: uppercase;
    color: #3a3a6a;
    letter-spacing: 2px;
    margin: 20px 0 12px 0;
}

.np-upload {
    padding: 16px;
    background: rgba(139, 92, 246, 0.08);
    border: 1px solid rgba(139, 92, 246, 0.2);
    border-radius: 8px;
    display: flex;
    align-items: center;
    gap: 16px;
}

.np-upload-icon { font-size: 24px; }
.np-upload-meta { flex: 1; }
.np-upload-name { font-weight: bold; color: #a78bfa; font-size: 13px; }
.np-upload-info { font-size: 10px; color: #3a3a6a; margin-top: 4px; }

.np-prog {
    width: 100%;
    height: 4px;
    background: rgba(139, 92, 246, 0.1);
    border-radius: 2px;
    overflow: hidden;
    margin-top: 8px;
}

.np-prog-fill {
    height: 100%;
    background: linear-gradient(90deg, #a78bfa, #34d399);
    width: 100%;
    border-radius: 2px;
}

.drop-zone {
    border: 1px dashed rgba(139, 92, 246, 0.2);
    border-radius: 12px;
    padding: 28px;
    text-align: center;
    color: #3a3a6a;
    font-size: 12px;
}

.np-agents {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 12px;
    margin: 20px 0;
}

.np-agent {
    padding: 12px;
    border-radius: 8px;
    border: 1px solid rgba(139, 92, 246, 0.2);
    text-align: center;
    transition: all 0.3s ease;
}

.np-agent.idle {
    opacity: 0.35;
    background: rgba(30, 30, 60, 0.3);
}

.np-agent.active {
    background: rgba(139, 92, 246, 0.1);
    border-color: rgba(139, 92, 246, 0.5);
    animation: card-pulse 1.5s ease-in-out infinite;
}

.np-agent.done {
    background: rgba(52, 211, 153, 0.1);
    border-color: rgba(52, 211, 153, 0.5);
}

@keyframes card-pulse {
    0%, 100% { box-shadow: 0 0 0 0 rgba(139, 92, 246, 0.3); }
    50% { box-shadow: 0 0 12px 4px rgba(139, 92, 246, 0.1); }
}

.np-av {
    position: relative;
    width: 32px;
    height: 32px;
    margin: 0 auto 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 16px;
}

.np-av.active {
    animation: pulse 1s ease-in-out infinite;
}

@keyframes pulse {
    0%, 100% { transform: scale(1); }
    50% { transform: scale(1.1); }
}

.np-av-ring {
    position: absolute;
    width: 40px;
    height: 40px;
    border: 2px solid rgba(139, 92, 246, 0.5);
    border-radius: 50%;
    animation: rspin 2s linear infinite;
}

.np-av-ring2 {
    position: absolute;
    width: 48px;
    height: 48px;
    border: 1px dashed rgba(139, 92, 246, 0.3);
    border-radius: 50%;
    animation: rspin 3s linear infinite reverse;
}

@keyframes rspin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

.np-aname {
    font-size: 11px;
    color: #a78bfa;
    font-weight: bold;
    margin-bottom: 6px;
}

.np-abadge {
    display: inline-block;
    font-size: 9px;
    padding: 4px 8px;
    border-radius: 12px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.np-abadge.nb-done {
    background: rgba(52, 211, 153, 0.2);
    color: #34d399;
}

.np-abadge.nb-active {
    background: rgba(139, 92, 246, 0.2);
    color: #a78bfa;
    animation: blink 1.5s ease-in-out infinite;
}

.np-abadge.nb-idle {
    background: rgba(60, 60, 90, 0.2);
    color: #6a6a9a;
}

@keyframes blink {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.4; }
}

.np-out-stack {
    display: flex;
    flex-direction: column;
    gap: 12px;
    margin: 20px 0;
}

.np-ocard {
    border-radius: 8px;
    border: 1px solid rgba(139, 92, 246, 0.2);
    overflow: hidden;
    transition: all 0.3s ease;
}

.np-ocard.idle {
    opacity: 0.35;
    background: rgba(30, 30, 60, 0.2);
}

.np-ocard.active {
    background: rgba(139, 92, 246, 0.08);
    border-color: rgba(139, 92, 246, 0.5);
}

.np-ocard.done {
    background: rgba(52, 211, 153, 0.05);
    border-color: rgba(52, 211, 153, 0.3);
}

.np-ohead {
    padding: 12px;
    display: flex;
    align-items: center;
    gap: 12px;
    border-bottom: 1px solid rgba(139, 92, 246, 0.1);
}

.np-oicon {
    font-size: 18px;
}

.np-otitle {
    flex: 1;
    font-size: 12px;
    color: #a78bfa;
    font-weight: bold;
}

.np-ostatus {
    font-size: 10px;
    padding: 4px 8px;
    border-radius: 12px;
    text-transform: uppercase;
}

.np-obody {
    padding: 12px;
}

.shimmer-line {
    height: 8px;
    background: linear-gradient(90deg, rgba(139,92,246,0.1), rgba(139,92,246,0.3), rgba(139,92,246,0.1));
    margin: 8px 0;
    border-radius: 4px;
    animation: shimmer 1.5s infinite;
}

.shimmer-line.f { width: 100%; }
.shimmer-line.m { width: 85%; }
.shimmer-line.s { width: 60%; }

@keyframes shimmer {
    0% { opacity: 0.5; }
    50% { opacity: 1; }
    100% { opacity: 0.5; }
}
</style>
""", unsafe_allow_html=True)

st.markdown(f"""
<div class="np-topbar">
    <div class="np-logo">
        <span class="np-logo-mark">Brain</span>
        <span class="np-logo-name">Doc Dream Team</span>
        <span class="np-logo-sub">multi-agent document intelligence</span>
    </div>
    <div class="np-pills">
        <div class="np-pill">
            <span class="pd-green"></span>
            Ollama · {DEFAULT_MODEL}
        </div>
        <div class="np-pill">
            Package ChromaDB ready
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

agent_states_json = json.dumps(st.session_state.agent_states)
session_id = st.session_state.session_id
chunk_count = st.session_state.doc_meta.get('chunks', 0)
token_count = st.session_state.token_count

neural_canvas_html = f"""
<div class="hud-wrap">
    <canvas id="nc" width="100%" height="220"></canvas>
    <div class="nc-hud nc-hud-tl">
        <div class="nc-hud-label">NEURAL MESH</div>
        <div class="nc-hud-value">{chunk_count}</div>
        <div class="nc-hud-label">CHUNKS LOADED</div>
    </div>
    <div class="nc-hud nc-hud-tr">
        <div class="nc-hud-label">TOKENS PROCESSED</div>
        <div class="nc-hud-value" id="token-display">{token_count}</div>
        <div class="nc-hud-label">VECTOR DIMS 4096</div>
    </div>
    <div class="nc-hud nc-hud-br">
        <div class="nc-hud-label">SESSION ID</div>
        <div class="nc-hud-value">{session_id}</div>
    </div>
</div>

<script>
    const canvas = document.getElementById('nc');
    const ctx = canvas.getContext('2d');

    canvas.width = canvas.offsetWidth;
    canvas.height = 220;

    let particles = [];
    let agentStates = {agent_states_json};
    let tokenCount = {token_count};

    class Particle {{
        constructor() {{
            this.x = Math.random() * canvas.width;
            this.y = Math.random() * canvas.height;
            this.vx = (Math.random() - 0.5) * 2;
            this.vy = (Math.random() - 0.5) * 2;
            this.radius = 1.2;
        }}

        update() {{
            this.x += this.vx;
            this.y += this.vy;
            if (this.x <= 0 || this.x >= canvas.width) this.vx *= -1;
            if (this.y <= 0 || this.y >= canvas.height) this.vy *= -1;
            this.x = Math.max(0, Math.min(canvas.width, this.x));
            this.y = Math.max(0, Math.min(canvas.height, this.y));
        }}

        draw() {{
            ctx.fillStyle = 'rgba(167, 139, 250, 0.25)';
            ctx.beginPath();
            ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
            ctx.fill();
        }}
    }}

    for (let i = 0; i < 75; i++) {{
        particles.push(new Particle());
    }}

    function drawAgentNode(x, y, label, state) {{
        const radius = 14;

        if (state === 'done') {{
            ctx.fillStyle = 'rgba(52, 211, 153, 0.07)';
            ctx.beginPath();
            ctx.arc(x, y, radius * 1.8, 0, Math.PI * 2);
            ctx.fill();
            ctx.strokeStyle = '#34d399';
            ctx.lineWidth = 1.5;
        }} else if (state === 'active') {{
            const pulse = Math.sin(Date.now() / 1000 * 2.5) * 0.5 + 0.5;
            ctx.fillStyle = 'rgba(139, 92, 246, 0.07)';
            ctx.beginPath();
            ctx.arc(x, y, radius * (1.5 + pulse * 0.5), 0, Math.PI * 2);
            ctx.fill();
            ctx.strokeStyle = '#a78bfa';
            ctx.lineWidth = 2;
        }} else {{
            ctx.fillStyle = 'rgba(30, 30, 60, 0.5)';
            ctx.strokeStyle = 'rgba(60, 60, 90, 0.4)';
            ctx.lineWidth = 1;
            ctx.globalAlpha = 0.4;
        }}

        ctx.beginPath();
        ctx.arc(x, y, radius, 0, Math.PI * 2);
        ctx.fill();
        ctx.stroke();
        ctx.globalAlpha = 1;

        ctx.fillStyle = '#a78bfa';
        ctx.font = 'bold 10px monospace';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(label, x, y);
    }}

    function animate() {{
        ctx.fillStyle = '#07071a';
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        for (let p of particles) {{
            p.update();
        }}

        for (let i = 0; i < particles.length; i++) {{
            for (let j = i + 1; j < particles.length; j++) {{
                const dx = particles[j].x - particles[i].x;
                const dy = particles[j].y - particles[i].y;
                const dist = Math.sqrt(dx * dx + dy * dy);

                if (dist < 90) {{
                    const opacity = 0.09 * (1 - dist / 90);
                    ctx.strokeStyle = 'rgba(139, 92, 246,' + opacity + ')';
                    ctx.lineWidth = 0.5;
                    ctx.beginPath();
                    ctx.moveTo(particles[i].x, particles[i].y);
                    ctx.lineTo(particles[j].x, particles[j].y);
                    ctx.stroke();
                }}
            }}
        }}

        for (let p of particles) {{
            p.draw();
        }}

        const nodePositions = [
            {{ x: canvas.width * 0.15, label: 'R' }},
            {{ x: canvas.width * 0.28, label: 'S' }},
            {{ x: canvas.width * 0.50, label: 'A' }},
            {{ x: canvas.width * 0.72, label: 'Q' }},
            {{ x: canvas.width * 0.85, label: 'W' }}
        ];

        const nodeLabels = ['reader', 'summariser', 'analyser', 'qa', 'writer'];
        const y = canvas.height * 0.45;

        for (let i = 0; i < nodePositions.length; i++) {{
            const state = agentStates[nodeLabels[i]] || 'idle';
            drawAgentNode(nodePositions[i].x, y, nodePositions[i].label, state);
        }}

        ctx.strokeStyle = 'rgba(139, 92, 246, 0.35)';
        ctx.lineWidth = 1;
        ctx.setLineDash([4, 6]);
        for (let i = 0; i < nodePositions.length - 1; i++) {{
            ctx.beginPath();
            ctx.moveTo(nodePositions[i].x, y);
            ctx.lineTo(nodePositions[i + 1].x, y);
            ctx.stroke();
        }}
        ctx.setLineDash([]);

        requestAnimationFrame(animate);
    }}

    animate();

    setInterval(function() {{
        tokenCount += Math.floor(Math.random() * 14) + 4;
        document.getElementById('token-display').textContent = tokenCount;
    }}, 700);
</script>
"""

components.html(neural_canvas_html, height=280)

st.markdown(f"""
<div class="np-stats">
    <div class="np-stat-card">
        <div class="np-stat-label">DOCUMENT</div>
        <div class="np-stat-value">{st.session_state.doc_meta.get('name', 'N/A')}</div>
        <div class="np-stat-sub">{st.session_state.doc_meta.get('chunks', 0)} chunks</div>
    </div>
    <div class="np-stat-card">
        <div class="np-stat-label">ACTIVE AGENTS</div>
        <div class="np-stat-value">{sum(1 for v in st.session_state.agent_states.values() if v in ['active', 'done'])}</div>
        <div class="np-stat-sub">of 5 total</div>
    </div>
    <div class="np-stat-card">
        <div class="np-stat-label">SESSION RUNS</div>
        <div class="np-stat-value">{st.session_state.run_count}</div>
        <div class="np-stat-sub">this session</div>
    </div>
    <div class="np-stat-card">
        <div class="np-stat-label">MODEL</div>
        <div class="np-stat-value">{DEFAULT_MODEL}</div>
        <div class="np-stat-sub">local free</div>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="sec-label">DOCUMENT_LOAD INPUT</div>', unsafe_allow_html=True)

uploaded_file = st.file_uploader("", type=["pdf", "docx", "txt"], label_visibility="collapsed")

if uploaded_file is not None:
    upload_path = Path("uploads") / uploaded_file.name
    upload_path.parent.mkdir(exist_ok=True)
    with open(upload_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    chunks = chunk_document(str(upload_path))
    collection_name = upload_path.stem

    st.session_state.vector_store.ingest(chunks, collection_name=collection_name)
    st.session_state.collection_name = collection_name
    st.session_state.doc_meta = {
        'name': uploaded_file.name,
        'chunks': len(chunks),
        'size_kb': round(uploaded_file.size / 1024, 1)
    }
    st.session_state.agent_states = {k: 'idle' for k in st.session_state.agent_states}
    st.session_state.outputs = {k: None for k in st.session_state.outputs}

    st.markdown(f"""
    <div class="np-upload">
        <div class="np-upload-icon">Document</div>
        <div class="np-upload-meta">
            <div class="np-upload-name">{uploaded_file.name}</div>
            <div class="np-upload-info">{len(chunks)} chunks {round(uploaded_file.size/1024, 1)} KB</div>
            <div class="np-prog"><div class="np-prog-fill"></div></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.success(f"Success: {len(chunks)} chunks ingested into ChromaDB")
else:
    st.markdown("""
    <div class="drop-zone">
        Brain Drop a document to begin PDF DOCX TXT
    </div>
    """, unsafe_allow_html=True)

st.markdown('<div class="sec-label">AGENT_STATUS LIVE</div>', unsafe_allow_html=True)

agent_cards_html = "<div class='np-agents'>"
for key in ['reader', 'summariser', 'analyser', 'qa', 'writer']:
    state = st.session_state.agent_states[key]
    icon = AGENT_CONFIG[key]['icon']
    label = AGENT_CONFIG[key]['label']

    rings_html = ""
    if state == 'active':
        rings_html = "<div class='np-av-ring'></div><div class='np-av-ring2'></div>"

    badge_text = state.capitalize()
    if state == 'active':
        badge_text = "working"
    elif state == 'done':
        badge_text = "done"
    else:
        badge_text = "waiting"

    agent_cards_html += f"""
    <div class="np-agent {state}">
        <div class="np-av {state}">
            {rings_html}
            <span>{icon}</span>
        </div>
        <div class="np-aname">{label}</div>
        <div class="np-abadge nb-{state}">{badge_text}</div>
    </div>
    """

agent_cards_html += "</div>"
st.markdown(agent_cards_html, unsafe_allow_html=True)

st.markdown('<div class="sec-label">QUERY_INPUT PROMPT</div>', unsafe_allow_html=True)

col1, col2 = st.columns([5, 1])
query = col1.text_input("",
                        placeholder="Ask something about your document...",
                        label_visibility="collapsed",
                        disabled=(st.session_state.collection_name is None),
                        key="query_input")
run_btn = col2.button("Run Agents",
                      disabled=(st.session_state.collection_name is None),
                      use_container_width=True)

st.caption("model")
st.selectbox("",
             options=["llama3.2","deepseek-r1","qwen2.5:7b","llama3.2:1b"],
             label_visibility="collapsed",
             key="selected_model")

if run_btn and query and st.session_state.collection_name and not st.session_state.is_running:
    st.session_state.is_running = True

    st.session_state.last_query = query
    st.session_state.run_count += 1
    st.session_state.outputs = {k: None for k in st.session_state.outputs}

    try:
        intent = st.session_state.orchestrator.detect_intent(query)

        intent_to_agents = {
            "SUMMARISE": ['reader', 'summariser'],
            "ANALYSE": ['reader', 'analyser'],
            "QA": ['reader', 'qa'],
            "WRITE": ['reader', 'summariser', 'writer'],
            "MULTI": ['reader', 'summariser', 'analyser']
        }
        selected_agents = intent_to_agents.get(intent.upper(), ['reader', 'summariser', 'analyser'])

        for key in st.session_state.agent_states:
            st.session_state.agent_states[key] = 'active' if key in selected_agents else 'idle'
        st.rerun()

    except Exception as e:
        st.error(f"Intent detection error: {str(e)}")
        st.session_state.is_running = False

if st.session_state.is_running and st.session_state.last_query:
    query = st.session_state.last_query
    intent = st.session_state.orchestrator.detect_intent(query)

    intent_to_agents = {
        "SUMMARISE": ['reader', 'summariser'],
        "ANALYSE": ['reader', 'analyser'],
        "QA": ['reader', 'qa'],
        "WRITE": ['reader', 'summariser', 'writer'],
        "MULTI": ['reader', 'summariser', 'analyser']
    }
    selected_agents = intent_to_agents.get(intent.upper(), ['reader', 'summariser', 'analyser'])

    for agent_key in selected_agents:
        if st.session_state.outputs[agent_key] is None:
            try:
                search_results = st.session_state.vector_store.search(query,
                                                                      st.session_state.collection_name,
                                                                      n_results=5)
                context_parts = [r["text"] for r in search_results]
                context = "\n---\n".join(context_parts)
                if len(context) > 3000:
                    context = context[:2997] + "..."

                predefined_configs = get_predefined_configs()
                config = predefined_configs[agent_key]
                task_desc = f"Document context:\n{context}\n\nTask: {query}"
                expected = "A thorough, well-structured response based only on the document context"

                agent, task = build_crew_agent(config['role'], config['goal'], config['backstory'],
                                               task_desc, expected, model_name=st.session_state.selected_model)
                result = run_crew([(agent, task)])

                st.session_state.outputs[agent_key] = result
                st.session_state.agent_states[agent_key] = 'done'
                st.rerun()
            except Exception as e:
                st.session_state.outputs[agent_key] = f"Error: {str(e)}"
                st.session_state.agent_states[agent_key] = 'done'
                st.rerun()

    if all(st.session_state.outputs[key] is not None for key in selected_agents):
        memory = st.session_state.memory
        memory.add_turn('user', query)
        combined_output = "\n\n---\n\n".join([out for out in st.session_state.outputs.values() if out])
        memory.add_turn('assistant', combined_output)
        st.session_state.token_count += len(query.split()) * 2 + 500 * len(selected_agents)
        st.session_state.is_running = False
        st.rerun()

st.markdown('<div class="sec-label">OUTPUT_FEED RESULTS</div>', unsafe_allow_html=True)

st.markdown("<div class='np-out-stack'>", unsafe_allow_html=True)

descriptions = {
    'reader': 'raw document extract',
    'summariser': 'structured summary',
    'analyser': 'critical analysis',
    'qa': 'question answer',
    'writer': 'generated document'
}

for key in ['reader', 'summariser', 'analyser', 'qa', 'writer']:
    state = st.session_state.agent_states[key]
    output = st.session_state.outputs.get(key)
    icon = AGENT_CONFIG[key]['icon']
    label = AGENT_CONFIG[key]['label']
    desc = descriptions.get(key, '')

    status_badge = state.capitalize()
    if state == 'active':
        status_badge = "in progress"
    elif state == 'done':
        status_badge = "complete"
    else:
        status_badge = "waiting"

    st.markdown(f"""
    <div class="np-ocard {state}">
        <div class="np-ohead">
            <div class="np-oicon">{icon}</div>
            <span class="np-otitle">{label} — {desc}</span>
            <span class="np-ostatus">{status_badge}</span>
        </div>
    """, unsafe_allow_html=True)

    if state == 'active':
        st.markdown("""
        <div class="np-obody">
            <div class="shimmer-line f"></div>
            <div class="shimmer-line m"></div>
            <div class="shimmer-line f"></div>
            <div class="shimmer-line s"></div>
            <div class="shimmer-line m"></div>
        </div>
        """, unsafe_allow_html=True)
    elif state == 'done' and output:
        st.markdown("<div class='np-obody'>", unsafe_allow_html=True)
        with st.expander(f"{icon} {label}", expanded=True):
            st.markdown(output)
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div class='np-obody'></div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

if any(st.session_state.outputs.values()):
    export_md = f"# Doc Dream Team — Session Export\n"
    export_md += f"**Document:** {st.session_state.doc_meta.get('name','—')}\n"
    export_md += f"**Query:** {st.session_state.last_query}\n\n"
    for key, output in st.session_state.outputs.items():
        if output:
            export_md += f"## {AGENT_CONFIG[key]['label']}\n{output}\n\n"
    st.download_button("Export session", export_md,
                       file_name="session.md", mime="text/markdown")
