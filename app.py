import streamlit as st
import streamlit.components.v1 as components
import os, uuid, json
from pathlib import Path
from textwrap import dedent
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

if not check_ollama_running():
    st.error("Alert: Ollama is not running. Open a terminal and run:  ollama serve")
    st.stop()

if 'vector_store' not in st.session_state:
    try:
        st.session_state['vector_store'] = VectorStore()
    except Exception as e:
        st.error(f"VectorStore init failed: {e}")
        st.stop()

if 'orchestrator' not in st.session_state:
    try:
        st.session_state['orchestrator'] = OrchestratorAgent()
    except Exception as e:
        st.error(f"Orchestrator init failed: {e}")
        st.stop()

st.session_state.setdefault('memory', SessionMemory())
st.session_state.setdefault('collection_name', None)
st.session_state.setdefault('doc_meta', {})
st.session_state.setdefault('run_count', 0)
st.session_state.setdefault('token_count', 0)
st.session_state.setdefault('session_id', str(uuid.uuid4())[:8].upper())
if 'selected_model' not in st.session_state:
    st.session_state['selected_model'] = DEFAULT_MODEL
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

st.markdown(
    """
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body, .stApp { background: #07071a !important; color: #e0e0ff; font-family: 'Monaco', monospace; }

.block-container {
    padding: 0 !important;
    max-width: 100% !important;
}

[data-testid="stFileUploader"] {
    margin: 0 28px 12px;
}

.np-topbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 14px 28px;
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

.np-logo-name {
    font-size: 20px;
    font-weight: 600;
    color: #f0eeff;
    letter-spacing: -0.3px;
}

.np-logo-sub {
    font-size: 12px;
    color: #8888b0;
    margin-top: 2px;
}

.np-pills {
    display: flex;
    gap: 12px;
}

.np-pill {
    display: flex;
    align-items: center;
    gap: 7px;
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.09);
    border-radius: 999px;
    padding: 6px 16px;
    font-size: 12px;
    color: #a0a0c0;
}

.pd-green {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #34d399;
    box-shadow: 0 0 8px rgba(52, 211, 153, 0.5);
}

.np-stats {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 12px;
    margin: 0 28px 20px;
}

.np-stat {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(139,92,246,0.18);
    border-radius: 14px;
    padding: 16px 18px;
    text-align: center;
    transition: border-color 0.3s, background 0.3s;
}

.np-stat:hover {
    border-color: rgba(139,92,246,0.4);
    background: rgba(139,92,246,0.05);
}

.np-stat-label {
    font-size: 11px;
    color: #7070a0;
    letter-spacing: 1.5px;
    margin-bottom: 6px;
    font-family: monospace;
    text-transform: uppercase;
}

.np-stat-val {
    font-size: 22px;
    font-weight: 700;
    color: #e8e6ff;
    margin: 8px 0;
    font-family: monospace;
}

.np-stat-sub {
    font-size: 11px;
    color: #5a5a80;
    margin-top: 3px;
}

.sec-label {
    font-size: 10px;
    letter-spacing: 2.5px;
    color: rgba(167,139,250,0.55);
    font-family: monospace;
    margin-bottom: 12px;
    padding: 0 28px;
    text-transform: uppercase;
    margin-top: 20px;
}

.np-dropzone {
    margin: 0 28px 18px;
    border: 1px dashed rgba(139,92,246,0.35);
    border-radius: 14px;
    padding: 36px;
    text-align: center;
    color: #7070a0;
    font-size: 14px;
    background: rgba(139,92,246,0.03);
}

.np-upload {
    margin: 0 28px 18px;
    padding: 16px 20px;
    background: rgba(139,92,246,0.06);
    border: 1px solid rgba(139,92,246,0.25);
    border-radius: 14px;
    display: flex;
    align-items: center;
    gap: 16px;
}

.np-upload-icon { font-size: 24px; }
.np-upload-col { flex: 1; text-align: left; }
.np-upload-name {
    font-size: 14px;
    font-weight: 600;
    color: #e0deff;
}

.np-upload-meta {
    font-size: 11px;
    color: #6060a0;
    margin-top: 4px;
}

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

.np-agents {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 12px;
    margin: 0 28px 20px;
}

.np-agent {
    border-radius: 14px;
    padding: 20px 10px 16px;
    text-align: center;
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(167,139,250,0.15);
    position: relative;
    overflow: hidden;
    transition: all 0.4s ease;
}

.np-agent.done {
    border-color: rgba(52,211,153,0.5);
    background: rgba(52,211,153,0.05);
    box-shadow: 0 0 20px rgba(52,211,153,0.07);
}

.np-agent.active {
    border-color: rgba(139,92,246,0.65);
    background: rgba(139,92,246,0.08);
    box-shadow: 0 0 24px rgba(139,92,246,0.12);
    animation: card-pulse 2s infinite;
}

.np-agent.idle {
    opacity: 0.45;
}

@keyframes card-pulse {
    0%, 100% { box-shadow: 0 0 0 0 rgba(139, 92, 246, 0.25); }
    50% { box-shadow: 0 0 18px 6px rgba(139, 92, 246, 0.12); }
}

.np-av {
    width: 44px;
    height: 44px;
    border-radius: 50%;
    margin: 0 auto 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 22px;
    position: relative;
}

.np-av.done   { background: rgba(52,211,153,0.18); }
.np-av.active { background: rgba(139,92,246,0.22); animation: pulse 1s ease-in-out infinite; }
.np-av.idle   { background: rgba(255,255,255,0.04); }

@keyframes pulse {
    0%, 100% { transform: scale(1); }
    50% { transform: scale(1.1); }
}

.np-av-ring {
    position: absolute;
    width: 52px;
    height: 52px;
    border: 2px solid rgba(139, 92, 246, 0.5);
    border-radius: 50%;
    animation: rspin 2s linear infinite;
}

.np-av-ring2 {
    position: absolute;
    width: 60px;
    height: 60px;
    border: 1px dashed rgba(139, 92, 246, 0.3);
    border-radius: 50%;
    animation: rspin 3s linear infinite reverse;
}

@keyframes rspin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

.np-aname {
    font-size: 14px;
    font-weight: 600;
    color: #e0deff;
    margin-top: 4px;
    letter-spacing: 0.2px;
}

.np-abadge {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    margin-top: 6px;
    font-size: 11px;
    padding: 3px 10px;
    border-radius: 999px;
    font-weight: 500;
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
    margin: 0 28px 20px;
}

.np-ocard {
    background: rgba(255,255,255,0.025);
    border: 1px solid rgba(167,139,250,0.12);
    border-radius: 14px;
    margin-bottom: 4px;
    overflow: hidden;
    transition: border-color 0.3s ease, background 0.3s ease, box-shadow 0.3s ease;
}

.np-ocard.idle {
    opacity: 0.45;
}

.np-ocard.active {
    border-color: rgba(139,92,246,0.5);
    background: rgba(139,92,246,0.05);
    box-shadow: 0 0 20px rgba(139,92,246,0.1);
}

.np-ocard.done {
    border-color: rgba(52,211,153,0.3);
    background: rgba(52,211,153,0.03);
}

.np-ohead {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 14px 18px;
}

.np-oicon {
    width: 32px;
    height: 32px;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 16px;
    flex-shrink: 0;
}

.np-otitle {
    font-size: 14px;
    font-weight: 600;
    color: #e8e6ff;
    flex: 1;
}

.np-ostatus {
    font-size: 11px;
    padding: 3px 11px;
    border-radius: 999px;
    font-weight: 500;
    margin-left: auto;
    text-transform: uppercase;
}

.os-done   { background: rgba(52,211,153,0.14);  color: #6ee7b7; }
.os-active { background: rgba(139,92,246,0.16);  color: #c4b5fd; }
.os-idle   { background: rgba(255,255,255,0.05); color: #4a4a70; }

.np-obody {
    padding: 8px 18px 16px;
    border-top: 1px solid rgba(139,92,246,0.08);
    font-size: 13px;
    color: #a0a0c8;
    line-height: 1.9;
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
""",
    unsafe_allow_html=True,
)

st.markdown(
    f"""
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
            📦 VectorStore ready
        </div>
    </div>
</div>
""",
    unsafe_allow_html=True,
)

agent_states_json = json.dumps(st.session_state.agent_states)
session_id = st.session_state.session_id
chunk_count = st.session_state.doc_meta.get('chunks', 0)
token_count = st.session_state.token_count

neural_canvas_html = f"""
<div style="width:100%; height:240px; background:#07071a; position:relative; overflow:hidden;">
<style>
    .nc-hud {{ position: absolute; z-index: 2; pointer-events: none; font-family: ui-monospace, monospace; }}
    .nc-hud-tl {{ top: 12px; left: 12px; }}
    .nc-hud-tr {{ top: 12px; right: 12px; text-align: right; }}
    .nc-hud-br {{ bottom: 12px; right: 12px; text-align: right; }}
</style>
<canvas id="nc" style="position:absolute; top:0; left:0; width:100%; height:100%; display:block; z-index:1;"></canvas>
<div class="nc-hud nc-hud-tl">
    <div style="font-size:10px; letter-spacing:3px; text-transform:uppercase; color:rgba(167,139,250,0.6);">NEURAL MESH</div>
    <span style="font-size:32px; font-weight:700; color:#d4b8ff; line-height:1.15; display:block; margin:4px 0;">{chunk_count}</span>
    <div style="font-size:10px; color:rgba(167,139,250,0.4); text-transform:uppercase; letter-spacing:1px;">CHUNKS LOADED</div>
</div>
<div class="nc-hud nc-hud-tr">
    <div style="font-size:11px; color:rgba(167,139,250,0.55); text-transform:uppercase; letter-spacing:0.5px;">TOKENS PROCESSED</div>
    <div><span id="token-display" style="font-size:13px; font-weight:700; color:#b8a0ff;">{token_count}</span></div>
    <div style="font-size:11px; color:rgba(167,139,250,0.55); text-transform:uppercase; margin-top:6px; letter-spacing:0.5px;">VECTOR DIMS 4096</div>
</div>
<div class="nc-hud nc-hud-br">
    <div style="font-size:11px; color:rgba(167,139,250,0.55); text-transform:uppercase;">SESSION ID</div>
    <div><span style="font-size:12px; font-weight:700; color:#b8a0ff;">{session_id}</span></div>
</div>
</div>

<script>
    const cv = document.getElementById('nc');
    const ctx = cv.getContext('2d');
    let particles = [];
    let agentStates = {agent_states_json};
    let tokenCount = {token_count};

    function resize() {{
        const W = cv.parentElement.offsetWidth || window.innerWidth || 900;
        const H = 240;
        cv.width = W;
        cv.height = H;
    }}
    resize();
    window.addEventListener('resize', function() {{
        resize();
        seedParticles();
    }});

    class Particle {{
        constructor() {{
            this.x = Math.random() * cv.width;
            this.y = Math.random() * cv.height;
            this.vx = (Math.random() - 0.5) * 2;
            this.vy = (Math.random() - 0.5) * 2;
            this.radius = 1.2;
        }}

        update() {{
            this.x += this.vx;
            this.y += this.vy;
            if (this.x <= 0 || this.x >= cv.width) this.vx *= -1;
            if (this.y <= 0 || this.y >= cv.height) this.vy *= -1;
            this.x = Math.max(0, Math.min(cv.width, this.x));
            this.y = Math.max(0, Math.min(cv.height, this.y));
        }}

        draw() {{
            ctx.fillStyle = 'rgba(167, 139, 250, 0.25)';
            ctx.beginPath();
            ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
            ctx.fill();
        }}
    }}

    function seedParticles() {{
        particles = [];
        for (let i = 0; i < 75; i++) {{
            particles.push(new Particle());
        }}
    }}
    seedParticles();

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
        ctx.fillRect(0, 0, cv.width, cv.height);

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
            {{ x: cv.width * 0.15, label: 'R' }},
            {{ x: cv.width * 0.28, label: 'S' }},
            {{ x: cv.width * 0.50, label: 'A' }},
            {{ x: cv.width * 0.72, label: 'Q' }},
            {{ x: cv.width * 0.85, label: 'W' }}
        ];

        const nodeLabels = ['reader', 'summariser', 'analyser', 'qa', 'writer'];
        const y = cv.height * 0.45;

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
        const el = document.getElementById('token-display');
        if (el) el.textContent = tokenCount;
    }}, 700);
</script>
"""

components.html(neural_canvas_html, height=240, scrolling=False)

st.markdown(
    f"""
<div class="np-stats">
    <div class="np-stat">
        <div class="np-stat-label">DOCUMENT</div>
        <div class="np-stat-val">{st.session_state.doc_meta.get('name', 'N/A')}</div>
        <div class="np-stat-sub">{st.session_state.doc_meta.get('chunks', 0)} chunks</div>
    </div>
    <div class="np-stat">
        <div class="np-stat-label">ACTIVE AGENTS</div>
        <div class="np-stat-val">{sum(1 for v in st.session_state.agent_states.values() if v in ['active', 'done'])}</div>
        <div class="np-stat-sub">of 5 total</div>
    </div>
    <div class="np-stat">
        <div class="np-stat-label">SESSION RUNS</div>
        <div class="np-stat-val">{st.session_state.run_count}</div>
        <div class="np-stat-sub">this session</div>
    </div>
    <div class="np-stat">
        <div class="np-stat-label">MODEL</div>
        <div class="np-stat-val">{DEFAULT_MODEL}</div>
        <div class="np-stat-sub">local free</div>
    </div>
</div>
""",
    unsafe_allow_html=True,
)

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

    st.markdown(
        dedent(f"""
        <div class="np-upload">
            <div class="np-upload-icon">📄</div>
            <div class="np-upload-col">
                <div class="np-upload-name">{uploaded_file.name}</div>
                <div class="np-upload-meta">{len(chunks)} chunks · {round(uploaded_file.size/1024, 1)} KB</div>
                <div class="np-prog"><div class="np-prog-fill"></div></div>
            </div>
        </div>
        """).strip(),
        unsafe_allow_html=True,
    )

    st.success(f"Success: {len(chunks)} chunks ingested into VectorStore")
else:
    st.markdown(
        dedent("""
        <div class="np-dropzone">
            Drop a document to begin — PDF, DOCX, or TXT
        </div>
        """).strip(),
        unsafe_allow_html=True,
    )

st.markdown('<div class="sec-label">AGENT_STATUS LIVE</div>', unsafe_allow_html=True)

agent_cards_html = "<div class=\"np-agents\">"
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

    agent_cards_html += dedent(
        f"""
        <div class="np-agent {state}">
            <div class="np-av {state}">
                {rings_html}
                <span>{icon}</span>
            </div>
            <div class="np-aname">{label}</div>
            <div class="np-abadge nb-{state}">{badge_text}</div>
        </div>
        """
    ).strip()

agent_cards_html += "</div>"
st.markdown(agent_cards_html, unsafe_allow_html=True)

st.markdown('<div class="sec-label">QUERY_INPUT PROMPT</div>', unsafe_allow_html=True)

_mg_l, q_main, _mg_r = st.columns([0.055, 0.89, 0.055])
with q_main:
    _model_opts = ["llama3.2", "deepseek-r1", "qwen2.5:7b", "llama3.2:1b"]
    _model_idx = (
        _model_opts.index(st.session_state.selected_model)
        if st.session_state.selected_model in _model_opts
        else 0
    )
    col1, col2 = st.columns([5, 1])
    query = col1.text_input(
        "",
        placeholder="Ask something about your document...",
        label_visibility="collapsed",
        disabled=(st.session_state.collection_name is None),
        key="query_input",
    )
    run_btn = col2.button(
        "Run Agents",
        disabled=(st.session_state.collection_name is None),
        use_container_width=True,
    )
    st.caption("Model")
    st.selectbox(
        "Model",
        _model_opts,
        index=_model_idx,
        label_visibility="collapsed",
        key="selected_model",
    )

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

    if state == 'active':
        status_badge = "IN PROGRESS"
    elif state == 'done':
        status_badge = "COMPLETE"
    else:
        status_badge = "WAITING"

    st.markdown(
        dedent(
            f"""
            <div class="np-ocard {state}">
                <div class="np-ohead">
                    <div class="np-oicon">{icon}</div>
                    <span class="np-otitle">{label} — {desc}</span>
                    <span class="np-ostatus os-{state}">{status_badge}</span>
                </div>
            """
        ).strip(),
        unsafe_allow_html=True,
    )

    if state == 'active':
        st.markdown(
            dedent("""
            <div class="np-obody">
                <div class="shimmer-line f"></div>
                <div class="shimmer-line m"></div>
                <div class="shimmer-line f"></div>
                <div class="shimmer-line s"></div>
                <div class="shimmer-line m"></div>
            </div>
            """).strip(),
            unsafe_allow_html=True,
        )
    elif state == 'done' and output:
        st.markdown("<div class='np-obody'>", unsafe_allow_html=True)
        with st.expander(f"{icon} {label}", expanded=True):
            st.markdown(output, unsafe_allow_html=False)
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
