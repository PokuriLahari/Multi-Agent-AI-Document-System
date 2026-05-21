import streamlit as st
import streamlit.components.v1 as components
import os
import re
import uuid
import json
import time
import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

st.set_page_config(
    page_title="Doc Dream Team",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

from pipeline.chunker import chunk_document
from pipeline.embedder import VectorStore
from agents.orchestrator import OrchestratorAgent
from agents.crew_builder import (
    build_crew_agent, run_crew, get_predefined_configs,
    build_agent, build_task, PREDEFINED_CONFIGS
)
from memory.store import SessionMemory
from config import check_ollama_running, DEFAULT_MODEL, OLLAMA_BASE_URL


AGENT_CONFIG = {
    'reader':     {'icon': '🔍', 'label': 'Reader',
                   'desc': 'raw document extract'},
    'summariser': {'icon': '📋', 'label': 'Summariser',
                   'desc': 'structured summary'},
    'analyser':   {'icon': '🧠', 'label': 'Analyser',
                   'desc': 'critical analysis'},
    'qa':         {'icon': '💬', 'label': 'Q&A',
                   'desc': 'question answer'},
    'writer':     {'icon': '✍️',  'label': 'Writer',
                   'desc': 'generated document'},
}

INTENT_MAP = {
    'SUMMARISE': ['reader', 'summariser'],
    'ANALYSE':   ['reader', 'analyser'],
    'QA':        ['reader', 'qa'],
    'WRITE':     ['reader', 'summariser', 'writer'],
    'MULTI':     ['reader', 'summariser', 'analyser'],
    'READ':      ['reader'],
}


if not check_ollama_running():
    st.error("⚠️ Ollama is not running. Run: ollama serve")
    st.stop()


@st.cache_resource
def load_vector_store():
    from config import VECTOR_PATH
    return VectorStore(persist_dir=VECTOR_PATH)

@st.cache_resource
def load_orchestrator():
    return OrchestratorAgent()


if 'vector_store' not in st.session_state:
    st.session_state['vector_store'] = load_vector_store()
if 'orchestrator' not in st.session_state:
    st.session_state['orchestrator'] = load_orchestrator()

st.session_state.setdefault('memory', SessionMemory())
st.session_state.setdefault('collection_name', None)
st.session_state.setdefault('doc_meta', {})
st.session_state.setdefault('run_count', 0)
st.session_state.setdefault('token_count', 0)
st.session_state.setdefault('session_id',
    str(uuid.uuid4())[:8].upper())
st.session_state.setdefault('selected_agents', [])
st.session_state.setdefault('last_query', '')
st.session_state.setdefault('agent_states', {
    'reader': 'idle', 'summariser': 'idle',
    'analyser': 'idle', 'qa': 'idle', 'writer': 'idle'
})
st.session_state.setdefault('outputs', {
    'reader': None, 'summariser': None,
    'analyser': None, 'qa': None, 'writer': None
})
if 'selected_model' not in st.session_state:
    st.session_state['selected_model'] = DEFAULT_MODEL
if 'should_run' not in st.session_state:
    st.session_state['should_run'] = False
if 'agent_times' not in st.session_state:
    st.session_state['agent_times'] = {
        'reader': 0, 'summariser': 0, 'analyser': 0, 'qa': 0, 'writer': 0
    }
if 'query_history' not in st.session_state:
    st.session_state['query_history'] = []
if 'run_from_history' not in st.session_state:
    st.session_state['run_from_history'] = None


# Sidebar Query History (must be before main content)
st.sidebar.markdown('<div class="sb-title">📜 QUERY HISTORY</div>', unsafe_allow_html=True)

if st.sidebar.button("🗑️ Clear History", key="clear_history", help="Clear all history", use_container_width=True):
    st.session_state.query_history = []
    st.rerun()

st.sidebar.markdown('<hr style="margin: 12px 0; border:none; border-top:1px solid rgba(139,92,246,0.1);">', unsafe_allow_html=True)

if st.session_state.query_history:
    for idx, item in enumerate(reversed(st.session_state.query_history[-20:])):
        query_text = item.get('query', '')[:50]
        doc_name = item.get('doc_name', '—')[:30]
        timestamp = item.get('timestamp', '—')
        
        if st.sidebar.button(
            f"🔍 {query_text}...",
            key=f"hist_query_{idx}",
            use_container_width=True,
            help=f"Re-run: {item.get('query', '')}"
        ):
            st.session_state.run_from_history = {
                'query': item['query'],
                'collection': item['collection_name']
            }
            st.session_state.should_run = True
            st.rerun()
        
        st.sidebar.markdown(
            f"<div style='margin:-12px 0 12px 12px; font-size:10px; color:#4a4a70;'>"
            f"📁 <span style='color:#5050a0;'>{doc_name}</span> · 🕐 {timestamp}"
            f"</div>",
            unsafe_allow_html=True
        )
else:
    st.sidebar.markdown('<div style="color:#4a4a70; font-size:11px; padding:12px; text-align:center;">📭 No queries yet</div>', unsafe_allow_html=True)


st.markdown(
    """
<style>
#MainMenu, footer, header { visibility: hidden !important; }
[data-testid="stToolbar"] { display: none !important; }
[data-testid="stDecoration"] { display: none !important; }
.stDeployButton { display: none !important; }
.stApp, body { background: #07071a !important; }
.block-container {
    padding: 0 !important; max-width: 100% !important;
}
[data-testid="stAppViewContainer"] {
    padding-top: 0 !important;
}
[data-testid="stSidebar"] {
    background: rgba(10,10,28,0.95) !important;
    border-right: 1px solid rgba(139,92,246,0.15) !important;
}
.sb-title {
    font-size: 12px; letter-spacing: 2px;
    color: rgba(167,139,250,0.6);
    font-family: monospace; margin: 16px 0 12px;
    text-transform: uppercase; font-weight: 700;
}
.sb-item {
    background: rgba(139,92,246,0.08);
    border: 1px solid rgba(139,92,246,0.2);
    border-radius: 8px; padding: 10px 12px;
    margin-bottom: 8px; cursor: pointer;
    font-size: 12px; color: #d4d4f0;
    transition: all 0.2s ease;
}
.sb-item:hover {
    background: rgba(139,92,246,0.15);
    border-color: rgba(139,92,246,0.4);
    transform: translateX(2px);
}
.sb-query {
    font-weight: 600; color: #c4b5fd;
    white-space: nowrap; overflow: hidden;
    text-overflow: ellipsis;
}
.sb-doc {
    font-size: 10px; color: #5050a0;
    margin-top: 4px; white-space: nowrap;
    overflow: hidden; text-overflow: ellipsis;
}
.sb-time {
    font-size: 9px; color: #4a4a70;
    margin-top: 2px;
}
.np-topbar {
    display: flex; align-items: center;
    justify-content: space-between;
    padding: 16px 32px;
    border-bottom: 1px solid rgba(255,255,255,0.06);
    background: rgba(10,10,28,0.98);
    position: relative; z-index: 999;
}
.np-logo { display: flex; align-items: center; gap: 10px; }
.np-logo-mark { font-size: 24px; }
.np-logo-name {
    font-size: 18px; font-weight: 700;
    background: linear-gradient(135deg, #f0eeff 0%, #a78bfa 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
.np-logo-sub { font-size: 11px; color: #6060a0; margin-top: 2px; }
.np-pills { display: flex; gap: 10px; }
.np-pill {
    display: flex; align-items: center; gap: 7px;
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 999px; padding: 6px 16px;
    font-size: 12px; color: #9090b8; font-weight: 500;
}
.pd-green {
    width: 8px; height: 8px; border-radius: 50%;
    background: #34d399;
    box-shadow: 0 0 8px rgba(52,211,153,0.6);
    display: inline-block;
}
.np-stats {
    display: grid; grid-template-columns: repeat(4,1fr);
    gap: 12px; margin: 20px 28px;
}
.np-stat {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(139,92,246,0.18);
    border-radius: 16px; padding: 18px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.4);
    transition: border-color 0.3s, transform 0.2s;
}
.np-stat:hover {
    border-color: rgba(139,92,246,0.4);
    transform: translateY(-1px);
}
.np-stat-label {
    font-size: 10px; color: #6060a0; letter-spacing: 1.5px;
    font-family: monospace; margin-bottom: 8px;
    text-transform: uppercase;
}
.np-stat-val {
    font-size: 24px; font-weight: 800; color: #f0eeff;
    font-family: monospace; letter-spacing: -0.5px;
}
.np-stat-sub { font-size: 11px; color: #4a4a70; margin-top: 4px; }
.sec-label {
    font-size: 9px; letter-spacing: 3px;
    color: rgba(167,139,250,0.5);
    font-family: monospace; margin: 24px 0 12px;
    padding: 0 28px; text-transform: uppercase;
    font-weight: 700;
}
.np-upload {
    margin: 0 28px 16px; padding: 16px 20px;
    background: rgba(139,92,246,0.06);
    border: 1px solid rgba(139,92,246,0.25);
    border-radius: 14px; display: flex;
    align-items: center; gap: 16px;
}
.np-upload-name {
    font-size: 14px; font-weight: 600; color: #e0deff;
}
.np-upload-meta { font-size: 11px; color: #5050a0; margin-top: 4px; }
.np-prog {
    height: 3px; background: rgba(139,92,246,0.1);
    border-radius: 2px; margin-top: 8px; overflow: hidden;
}
.np-prog-fill {
    height: 100%;
    background: linear-gradient(90deg, #7c3aed, #34d399);
}
.np-dropzone {
    margin: 0 28px 16px;
    border: 1px dashed rgba(139,92,246,0.3);
    border-radius: 14px; padding: 32px;
    text-align: center; color: #6060a0;
    font-size: 13px;
    background: rgba(139,92,246,0.02);
}
.np-agents {
    display: grid; grid-template-columns: repeat(5,1fr);
    gap: 12px; margin: 0 28px 20px;
}
.np-agent {
    border-radius: 14px; padding: 20px 10px 16px;
    text-align: center;
    background: rgba(255,255,255,0.02);
    border: 1px solid rgba(255,255,255,0.06);
    box-shadow: 0 2px 10px rgba(0,0,0,0.3);
    transition: all 0.3s ease;
}
.np-agent.done {
    border-color: rgba(52,211,153,0.45);
    background: rgba(52,211,153,0.05);
    box-shadow: 0 2px 16px rgba(52,211,153,0.1);
}
.np-agent.active {
    border-color: rgba(139,92,246,0.9);
    background: rgba(139,92,246,0.14);
    box-shadow: 0 0 28px rgba(139,92,246,0.35),
                inset 0 0 16px rgba(139,92,246,0.08);
    animation: card-pulse 1.5s infinite;
}
.np-agent.idle {
    opacity: 0.75;
    border-color: rgba(139,92,246,0.22);
}
@keyframes card-pulse {
    0%,100%{ box-shadow: 0 0 8px rgba(139,92,246,0.25),
                      inset 0 0 8px rgba(139,92,246,0.04); }
    50%    { box-shadow: 0 0 32px 8px rgba(139,92,246,0.3),
                      inset 0 0 16px rgba(139,92,246,0.12); }
}
.np-av {
    width: 44px; height: 44px; border-radius: 50%;
    margin: 0 auto 10px;
    display: flex; align-items: center;
    justify-content: center; font-size: 22px;
    position: relative;
}
.np-av.done   { background: rgba(52,211,153,0.18); }
.np-av.active { background: rgba(139,92,246,0.22); }
.np-av.idle   { background: rgba(255,255,255,0.04); }
.np-av-ring {
    position: absolute; inset: -5px; border-radius: 50%;
    border: 1px solid rgba(139,92,246,0.5);
    animation: rspin 3s linear infinite;
}
.np-av-ring2 {
    position: absolute; inset: -5px; border-radius: 50%;
    border: 1px dashed rgba(139,92,246,0.2);
    animation: rspin 6s linear infinite reverse;
}
@keyframes rspin {
    from{transform:rotate(0deg);} to{transform:rotate(360deg);}
}
.np-aname {
    font-size: 13px; font-weight: 700; color: #e0deff;
    margin-top: 6px; letter-spacing: 0.2px;
}
.np-abadge {
    display: inline-flex; align-items: center; gap: 4px;
    margin-top: 6px; font-size: 9px; padding: 3px 10px;
    border-radius: 999px; font-weight: 700;
    letter-spacing: 1px; text-transform: uppercase;
}
.nb-done {
    background: rgba(52,211,153,0.15); color: #34d399;
    border: 1px solid rgba(52,211,153,0.3);
}
.nb-active {
    background: rgba(139,92,246,0.2); color: #c4b5fd;
    border: 1px solid rgba(139,92,246,0.4);
    animation: blink 1.5s infinite;
}
.nb-idle {
    background: rgba(139,92,246,0.08); color: #8b7cfa;
    border: 1px solid rgba(139,92,246,0.22);
}
@keyframes blink {
    0%,100%{opacity:1;} 50%{opacity:0.35;}
}
.bdot {
    display: inline-block; width: 5px; height: 5px;
    border-radius: 50%; background: currentColor;
}
.np-out-stack {
    display: flex; flex-direction: column;
    gap: 10px; margin: 0 28px 20px;
}
.np-ocard {
    background: rgba(255,255,255,0.02);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 14px; overflow: hidden;
    box-shadow: 0 2px 12px rgba(0,0,0,0.35);
    transition: all 0.3s ease;
}
.np-ocard.done {
    border-color: rgba(52,211,153,0.28);
    background: rgba(52,211,153,0.03);
}
.np-ocard.active {
    border-color: rgba(139,92,246,0.5);
    background: rgba(139,92,246,0.05);
    box-shadow: 0 0 24px rgba(139,92,246,0.1);
}
.np-ocard.idle { opacity: 0.38; }
.np-ohead {
    display: flex; align-items: center; gap: 12px;
    padding: 14px 18px;
}
.np-oicon {
    width: 32px; height: 32px; border-radius: 8px;
    display: flex; align-items: center;
    justify-content: center; font-size: 16px; flex-shrink: 0;
}
.oi-done   { background: rgba(52,211,153,0.14); }
.oi-active { background: rgba(139,92,246,0.18); }
.oi-idle   { background: rgba(255,255,255,0.04); }
.np-otitle {
    font-size: 14px; font-weight: 700; color: #f0eeff; flex: 1;
}
.np-ostatus {
    font-size: 10px; padding: 3px 11px;
    border-radius: 999px; font-weight: 700;
    letter-spacing: 0.5px;
}
.os-done {
    background: rgba(52,211,153,0.14); color: #34d399;
    border: 1px solid rgba(52,211,153,0.25);
}
.os-active {
    background: rgba(139,92,246,0.16); color: #c4b5fd;
    border: 1px solid rgba(139,92,246,0.3);
}
.os-idle {
    background: rgba(255,255,255,0.04); color: #3a3a60;
    border: 1px solid rgba(255,255,255,0.05);
}
.np-obody {
    padding: 8px 18px 16px;
    border-top: 1px solid rgba(139,92,246,0.08);
}
.shim-line {
    height: 7px; border-radius: 3px; margin-top: 9px;
    background: linear-gradient(90deg,
        rgba(139,92,246,0.05) 25%,
        rgba(139,92,246,0.2) 50%,
        rgba(139,92,246,0.05) 75%);
    background-size: 200% 100%;
    animation: shim 1.8s infinite;
}
@keyframes shim {
    0%{background-position:200% 0;}
    100%{background-position:-200% 0;}
}
.stTextInput > div > div > input {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(139,92,246,0.25) !important;
    border-radius: 10px !important; color: #e0deff !important;
    font-size: 13px !important;
}
.stButton > button {
    background: rgba(139,92,246,0.22) !important;
    border: 1px solid rgba(167,139,250,0.4) !important;
    border-radius: 10px !important; color: #c4b5fd !important;
    font-weight: 700 !important; font-size: 13px !important;
}
.stButton > button:hover {
    background: rgba(139,92,246,0.38) !important;
}
.stSelectbox > div > div {
    background: rgba(255,255,255,0.03) !important;
    border: 1px solid rgba(139,92,246,0.2) !important;
    border-radius: 8px !important; color: #d4d4f0 !important;
}
.streamlit-expanderHeader {
    background: rgba(139,92,246,0.08) !important;
    border-radius: 8px !important; color: #c4b5fd !important;
    font-size: 13px !important; font-weight: 600 !important;
}
</style>
    """,
    unsafe_allow_html=True
)

with st.sidebar:
    st.markdown(
        '<div style="display:flex; justify-content:space-between; align-items:center;">'
        '<div class="sb-title">📜 QUERY HISTORY</div>'
        '<button style="background:none; border:none; cursor:pointer; font-size:16px; padding:0; margin:0;" '
        'onclick="this.parentElement.nextElementSibling.value=\'CLEAR\'; this.parentElement.nextElementSibling.click();">🗑️</button>'
        '</div>',
        unsafe_allow_html=True
    )


st.markdown(
    '<div class="np-topbar">'
    '<div class="np-logo">'
    '<span class="np-logo-mark">🧠</span>'
    '<div>'
    '<div class="np-logo-name">Doc Dream Team</div>'
    '<div class="np-logo-sub">multi-agent document intelligence</div>'
    '</div>'
    '</div>'
    '<div class="np-pills">'
    '<div class="np-pill">'
    '<span class="pd-green"></span>'
    f'Ollama · {DEFAULT_MODEL}'
    '</div>'
    '<div class="np-pill">📦 VectorStore ready</div>'
    f'<div class="np-pill">🔑 {st.session_state.session_id}</div>'
    '</div>'
    '</div>',
    unsafe_allow_html=True
)


agent_states_json = json.dumps(st.session_state.agent_states)
chunk_count = st.session_state.doc_meta.get('chunks', 0)
session_id = st.session_state.session_id

canvas_html = f"""<!DOCTYPE html>
<html><head><style>
body {{ margin:0; background:#07071a; overflow:hidden; }}
canvas {{ display:block; }}
.hud {{ position:absolute; pointer-events:none;
        font-family:monospace; }}
.tl {{ top:14px; left:18px; }}
.tr {{ top:14px; right:18px; text-align:right; }}
.br {{ bottom:10px; right:18px; }}
.ht {{ font-size:9px; color:rgba(167,139,250,0.5);
       letter-spacing:2px; text-transform:uppercase; }}
.hv {{ font-size:28px; font-weight:800; color:#d4b8ff;
       line-height:1.1; }}
.hs {{ font-size:9px; color:rgba(167,139,250,0.35);
       margin-top:2px; text-transform:uppercase; }}
.hm {{ font-size:10px; color:rgba(167,139,250,0.4);
       margin-top:4px; }}
.hm span {{ color:#b8a0ff; font-weight:700; }}
</style></head>
<body>
<canvas id="c"></canvas>
<div class="hud tl">
  <div class="ht">NEURAL MESH</div>
  <div class="hv">{chunk_count}</div>
  <div class="hs">CHUNKS LOADED</div>
</div>
<div class="hud tr">
  <div class="hm">TOKENS <span id="tok">0</span></div>
  <div class="hm">DIMS <span>4096</span></div>
  <div class="hm">SIM <span id="sim">—</span></div>
</div>
<div class="hud br">
  <div class="hm">SESSION <span>{session_id}</span></div>
</div>
<script>
const cv=document.getElementById('c');
const ctx=cv.getContext('2d');
let W,H,pts=[],states={agent_states_json};
const keys=['reader','summariser','analyser','qa','writer'];
const labels=['R','S','A','Q','W'];
function resize(){{
  W=cv.width=window.innerWidth;
  H=cv.height=200;
}}
resize();
window.onresize=resize;
for(let i=0;i<75;i++){{
  pts.push({{
    x:Math.random()*1000,y:Math.random()*200,
    vx:(Math.random()-.5)*.5,vy:(Math.random()-.5)*.5
  }});
}}
function draw(){{
  ctx.fillStyle='#07071a';ctx.fillRect(0,0,W,H);
  pts.forEach(p=>{{
    p.x+=p.vx;p.y+=p.vy;
    if(p.x<0||p.x>W)p.vx*=-1;
    if(p.y<0||p.y>H)p.vy*=-1;
  }});
  for(let i=0;i<pts.length;i++){{
    for(let j=i+1;j<pts.length;j++){{
      const dx=pts[i].x-pts[j].x,dy=pts[i].y-pts[j].y;
      const d=Math.sqrt(dx*dx+dy*dy);
      if(d<85){{
        ctx.strokeStyle=`rgba(139,92,246,${{.09*(1-d/85)}})`;
        ctx.lineWidth=.5;ctx.beginPath();
        ctx.moveTo(pts[i].x,pts[i].y);
        ctx.lineTo(pts[j].x,pts[j].y);ctx.stroke();
      }}
    }}
  }}
  pts.forEach(p=>{{
    ctx.fillStyle='rgba(167,139,250,.25)';
    ctx.beginPath();ctx.arc(p.x,p.y,1.2,0,Math.PI*2);
    ctx.fill();
  }});
  const t=Date.now()*.001;
  keys.forEach((k,i)=>{{
    const x=W*[.12,.28,.50,.72,.88][i],y=H*.48;
    const s=states[k]||'idle';
    const pulse=s==='active'?(Math.sin(t*2.5+i)*.5+.5):0;
    if(s==='active'){{
      ctx.beginPath();ctx.arc(x,y,28+pulse*10,0,Math.PI*2);
      ctx.fillStyle=`rgba(139,92,246,${{.06+pulse*.06}})`;
      ctx.fill();
    }}
    if(s==='done'){{
      ctx.beginPath();ctx.arc(x,y,22,0,Math.PI*2);
      ctx.fillStyle='rgba(52,211,153,.08)';ctx.fill();
    }}
    ctx.beginPath();ctx.arc(x,y,14,0,Math.PI*2);
    ctx.fillStyle=s==='done'?'rgba(52,211,153,.18)':
                 s==='active'?'rgba(139,92,246,.28)':
                 'rgba(25,25,55,.6)';
    ctx.fill();
    ctx.strokeStyle=s==='done'?'#34d399':
                    s==='active'?'#a78bfa':
                    'rgba(60,60,100,.4)';
    ctx.lineWidth=1.5;ctx.stroke();
    ctx.fillStyle=s==='done'?'#34d399':
                 s==='active'?'#c4b5fd':
                 'rgba(80,80,130,.5)';
    ctx.font='700 10px monospace';
    ctx.textAlign='center';ctx.textBaseline='middle';
    ctx.fillText(labels[i],x,y);
    if(s==='active'){{
      const a=t*1.8;
      ctx.beginPath();ctx.arc(x,y,20,a,a+1.4);
      ctx.strokeStyle='rgba(167,139,250,.6)';
      ctx.lineWidth=1.5;ctx.stroke();
    }}
  }});
  requestAnimationFrame(draw);
}}
draw();
let tok=0;
setInterval(()=>{{
  tok+=Math.floor(Math.random()*14+4);
  const e=document.getElementById('tok');
  if(e)e.textContent=tok.toLocaleString();
}},700);
setInterval(()=>{{
  const e=document.getElementById('sim');
  if(e)e.textContent=(0.82+Math.random()*.12).toFixed(2);
}},1500);
</script>
</body></html>"""

st.html(canvas_html)


active_count = sum(
    1 for s in st.session_state.agent_states.values()
    if s in ('active', 'done')
)
doc_name = st.session_state.doc_meta.get('name', '—')
if len(doc_name) > 18:
    doc_name = doc_name[:15] + '...'

st.markdown(
    '<div class="np-stats">'
    '<div class="np-stat">'
    '<div class="np-stat-label">DOCUMENT</div>'
    f'<div class="np-stat-val">{doc_name}</div>'
    '<div class="np-stat-sub">'
    f'{st.session_state.doc_meta.get("chunks",0)} chunks'
    '</div>'
    '</div>'
    '<div class="np-stat">'
    '<div class="np-stat-label">ACTIVE AGENTS</div>'
    f'<div class="np-stat-val">{active_count} / 5</div>'
    '<div class="np-stat-sub">of 5 total</div>'
    '</div>'
    '<div class="np-stat">'
    '<div class="np-stat-label">SESSION RUNS</div>'
    f'<div class="np-stat-val">{st.session_state.run_count}</div>'
    '<div class="np-stat-sub">this session</div>'
    '</div>'
    '<div class="np-stat">'
    '<div class="np-stat-label">MODEL</div>'
    f'<div class="np-stat-val">{st.session_state.selected_model}</div>'
    '<div class="np-stat-sub">local · free</div>'
    '</div>'
    '</div>',
    unsafe_allow_html=True
)


st.markdown('<div class="sec-label">DOCUMENT LOAD</div>',
            unsafe_allow_html=True)

uploaded = st.file_uploader(
    "Upload document",
    type=["pdf", "docx", "txt"],
    label_visibility="collapsed"
)

if uploaded:
    os.makedirs("uploads", exist_ok=True)
    fpath = f"uploads/{uploaded.name}"
    with open(fpath, "wb") as f:
        f.write(uploaded.getbuffer())
    with st.spinner("Chunking and embedding..."):
        try:
            chunks = chunk_document(fpath)
            raw = Path(uploaded.name).stem
            cname = re.sub(r'[^a-zA-Z0-9_-]', '_', raw).strip('_-')
            if len(cname) < 2:
                cname = 'document'
            cname = cname[:100]
            st.session_state.vector_store.ingest(chunks, cname)
            st.session_state.collection_name = cname
            st.session_state.doc_meta = {
                'name': uploaded.name,
                'chunks': len(chunks),
                'size_kb': round(uploaded.size / 1024, 1)
            }
            for k in st.session_state.agent_states:
                st.session_state.agent_states[k] = 'idle'
            for k in st.session_state.outputs:
                st.session_state.outputs[k] = None
            m = st.session_state.doc_meta
            st.markdown(
                '<div class="np-upload">'
                '<span style="font-size:22px">📄</span>'
                '<div style="flex:1">'
                f'<div class="np-upload-name">{m["name"]}</div>'
                f'<div class="np-upload-meta">'
                f'{m["chunks"]} chunks · {m["size_kb"]} KB</div>'
                '<div class="np-prog">'
                '<div class="np-prog-fill"></div></div>'
                '</div></div>',
                unsafe_allow_html=True
            )
            st.success(f"✅ {len(chunks)} chunks ready")
        except Exception as e:
            st.error(f"Upload error: {e}")
else:
    if not st.session_state.doc_meta:
        st.markdown(
            '<div class="np-dropzone">'
            '🧠 Drop a document to begin — PDF · DOCX · TXT'
            '</div>',
            unsafe_allow_html=True
        )
    else:
        m = st.session_state.doc_meta
        st.markdown(
            '<div class="np-upload">'
            '<span style="font-size:22px">📄</span>'
            '<div style="flex:1">'
            f'<div class="np-upload-name">{m["name"]}</div>'
            f'<div class="np-upload-meta">'
            f'{m["chunks"]} chunks · {m["size_kb"]} KB · ready</div>'
            '<div class="np-prog">'
            '<div class="np-prog-fill"></div></div>'
            '</div></div>',
            unsafe_allow_html=True
        )


st.markdown('<div class="sec-label">QUERY INPUT</div>',
            unsafe_allow_html=True)

col1, col2 = st.columns([5, 1])
with col1:
    # Load from history if clicked
    if st.session_state.run_from_history:
        query_input = st.session_state.run_from_history['query']
        st.session_state.collection_name = st.session_state.run_from_history['collection']
        st.session_state.run_from_history = None
    else:
        query_input = ""
    
    query = st.text_input(
        "Query",
        placeholder="Ask something about your document...",
        label_visibility="collapsed",
        disabled=(st.session_state.collection_name is None),
        value=query_input,
        key="query_input"
    )
with col2:
    run_btn = st.button(
        "▶ Run Agents",
        disabled=(st.session_state.collection_name is None),
        use_container_width=True
    )
    if run_btn and query and st.session_state.collection_name:
        st.session_state.should_run = True

model_opts = ["llama3.2", "deepseek-r1", "qwen2.5:7b", "llama3.2:1b"]
model_idx = (model_opts.index(st.session_state.selected_model)
             if st.session_state.selected_model in model_opts else 0)
st.selectbox(
    "Model",
    model_opts,
    index=model_idx,
    label_visibility="collapsed",
    key="selected_model"
)


if st.session_state.should_run and query and st.session_state.collection_name:

    st.session_state.last_query  = query
    st.session_state.run_count  += 1
    st.session_state.outputs     = {
        k: None for k in st.session_state.outputs
    }
    
    # Reset all agents to idle first
    for k in st.session_state.agent_states:
        st.session_state.agent_states[k] = 'idle'

    try:
        intent = st.session_state.orchestrator.detect_intent(query)
        intent = str(intent).strip().upper()
        valid  = ["SUMMARISE","ANALYSE","QA","WRITE","MULTI","READ"]
        for v in valid:
            if v in intent:
                intent = v
                break
        else:
            intent = "MULTI"
    except Exception:
        intent = "MULTI"

    selected = INTENT_MAP.get(intent,
               ['reader', 'summariser', 'analyser'])
    st.session_state.selected_agents = selected

    # Set selected agents to active
    for k in selected:
        st.session_state.agent_states[k] = 'active'

    predefined    = get_predefined_configs()
    current_model = st.session_state.selected_model
    vector_store  = st.session_state.vector_store
    collection    = st.session_state.collection_name

    def run_agent_task(agent_key):
        """Execute single agent task and return result with timing"""
        start_time = time.time()
        cfg = predefined[agent_key]
        lbl = AGENT_CONFIG[agent_key]['label']

        try:
            hits = vector_store.search(
                query,
                collection,
                n_results=5
            )
            if hits:
                context = "\n---\n".join(
                    h["text"] for h in hits
                )
            else:
                all_docs = (
                    vector_store.store.get(collection, [])
                )
                context = "\n---\n".join(
                    c["text"] for c in all_docs[:5]
                ) if all_docs else "No document content."

            if len(context) > 3000:
                context = context[:2997] + "..."

            task_desc = (
                f"Using ONLY the provided document context, answer this query: {query}\n\n"
                f"Document Context:\n{context}\n\n"
                f"Provide a direct, intelligent answer based on the document. "
                f"Do not just repeat the document verbatim."
            )
            expected = (
                "A thoughtful, well-reasoned response that directly answers the query "
                "using information from the provided document context."
            )
            agent_obj, task_obj = build_crew_agent(
                cfg["role"], cfg["goal"], cfg["backstory"],
                task_desc, expected,
                model_name=current_model
            )
            result = run_crew([(agent_obj, task_obj)])
            
            # Handle list result from run_crew
            if isinstance(result, list):
                result_str = result[0] if result else ""
            else:
                result_str = str(result)
            
            result_str = result_str.strip()

            if not result_str or result_str.lower() in [
                "none", "null", "", "[]", "n/a"
            ]:
                result_str = (
                    f"{lbl} processed the document "
                    "but returned no output. "
                    "Try rephrasing your query."
                )
            
            elapsed = time.time() - start_time
            return agent_key, result_str, elapsed

        except Exception as e:
            elapsed = time.time() - start_time
            return agent_key, (
                f"⚠️ {lbl} error: {str(e)}"
            ), elapsed

    with st.spinner(f"🚀 Running {len(selected)} agents in parallel..."):
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {
                executor.submit(run_agent_task, agent_key): agent_key
                for agent_key in selected
            }

            for future in as_completed(futures):
                agent_key, result_str, elapsed = future.result()
                st.session_state.outputs[agent_key] = result_str
                st.session_state.agent_times[agent_key] = elapsed
                st.session_state.agent_states[agent_key] = 'done'

    st.session_state.memory.add_turn('user', query)
    combined = "\n\n---\n\n".join(
        v for v in st.session_state.outputs.values() if v
    )
    st.session_state.memory.add_turn('assistant', combined)
    st.session_state.token_count += (
        len(query.split()) * 2 + 500 * len(selected)
    )
    
    # Add to query history
    st.session_state.query_history.append({
        'query': query,
        'doc_name': st.session_state.doc_meta.get('name', '—'),
        'collection_name': st.session_state.collection_name,
        'timestamp': datetime.datetime.now().strftime("%H:%M")
    })
    
    st.session_state.should_run = False


# Agent Status Display (updated after execution)
def build_agent_cards():
    cards = []
    for key in ['reader','summariser','analyser','qa','writer']:
        state = st.session_state.agent_states[key]
        icon  = AGENT_CONFIG[key]['icon']
        label = AGENT_CONFIG[key]['label']
        rings = (
            '<div class="np-av-ring"></div>'
            '<div class="np-av-ring2"></div>'
        ) if state == 'active' else ''
        badge = ('✓ DONE' if state == 'done' else
                 'WORKING' if state == 'active' else
                 'WAITING')
        cards.append(
            '<div class="np-agent ' + state + '">'
            + '<div class="np-av ' + state + '">'
            + rings + '<span>' + icon + '</span>'
            + '</div>'
            + '<div class="np-aname">' + label + '</div>'
            + '<div class="np-abadge nb-' + state + '">'
            + badge + '</div>'
            + '</div>'
        )
    return ('<div class="np-agents">'
            + ''.join(cards) + '</div>')

# Show agent status if any agent has been run or is running
if any(st.session_state.agent_states[k] != 'idle' for k in st.session_state.agent_states):
    st.markdown('<div class="sec-label">AGENT STATUS</div>', unsafe_allow_html=True)
    st.markdown(build_agent_cards(), unsafe_allow_html=True)


# Display results if there are any completed agents (runs AFTER execution)
completed_agents = [
    k for k in st.session_state.outputs.keys() 
    if st.session_state.outputs[k] and st.session_state.agent_states[k] == 'done'
]

if completed_agents:
    st.success("✅ Query executed successfully!")
    st.markdown('<div class="sec-label">EXECUTION RESULTS</div>', unsafe_allow_html=True)
    
    # Sort by execution time (fastest first)
    sorted_agents = sorted(
        completed_agents,
        key=lambda k: st.session_state.agent_times.get(k, float('inf'))
    )
    
    for agent_key in sorted_agents:
        output_text = st.session_state.outputs[agent_key]
        elapsed = st.session_state.agent_times.get(agent_key, 0)
        icon = AGENT_CONFIG[agent_key]['icon']
        label = AGENT_CONFIG[agent_key]['label']
        
        with st.expander(f"{icon} {label} ({elapsed:.1f}s)", expanded=True):
            st.write(output_text)


st.markdown('<div class="sec-label">OUTPUT FEED</div>',
            unsafe_allow_html=True)

with st.expander("🔍 Debug Info", expanded=False):
    st.write(f"**Agent States:** {st.session_state.agent_states}")
    st.write(f"**Agent Times (s):** {dict((k, f'{v:.1f}s') for k, v in st.session_state.agent_times.items())}")
    st.write(f"**Outputs Keys:** {list(st.session_state.outputs.keys())}")
    for k, v in st.session_state.outputs.items():
        if v:
            st.write(f"**{k}:** {v[:100]}...")

def build_output_cards():
    cards = []
    for key in ['reader','summariser','analyser','qa','writer']:
        state  = st.session_state.agent_states[key]
        cfg    = AGENT_CONFIG[key]
        elapsed = st.session_state.agent_times.get(key, 0)
        status = ('COMPLETE'    if state == 'done'   else
                  'IN PROGRESS' if state == 'active' else
                  'WAITING')
        time_badge = f'<span style="font-size:10px; color:#8b7cfa;">{elapsed:.1f}s</span>' if state == 'done' and elapsed > 0 else ''
        body = ''
        if state == 'active':
            body = (
                '<div class="np-obody">'
                + '<div class="shim-line" style="width:100%"></div>'
                + '<div class="shim-line" style="width:75%"></div>'
                + '<div class="shim-line" style="width:100%"></div>'
                + '<div class="shim-line" style="width:55%"></div>'
                + '</div>'
            )
        card = (
            '<div class="np-ocard ' + state + '">'
            + '<div class="np-ohead">'
            + '<div class="np-oicon oi-' + state + '">'
            + cfg['icon'] + '</div>'
            + '<span class="np-otitle">'
            + cfg['label'] + ' — ' + cfg['desc'] + '</span>'
            + time_badge
            + '<span class="np-ostatus os-' + state + '">'
            + status + '</span>'
            + '</div>'
            + body
            + '</div>'
        )
        cards.append(card)
    return ('<div class="np-out-stack">'
            + ''.join(cards) + '</div>')

st.markdown(build_output_cards(), unsafe_allow_html=True)

# Sort by completion time (fastest first)
sorted_agents = sorted(
    [k for k in ['reader','summariser','analyser','qa','writer']
     if st.session_state.agent_states.get(k) == 'done' and st.session_state.outputs.get(k)],
    key=lambda k: st.session_state.agent_times.get(k, float('inf'))
)

has_outputs = False
for key in sorted_agents:
    output = st.session_state.outputs.get(key)
    state  = st.session_state.agent_states.get(key)
    if state == 'done' and output:
        has_outputs = True
        cfg = AGENT_CONFIG[key]
        elapsed = st.session_state.agent_times.get(key, 0)
        expander_label = f"{cfg['icon']}  {cfg['label']} output  •  {elapsed:.1f}s"
        with st.expander(expander_label, expanded=True):
            st.markdown(str(output))

if not has_outputs and any(st.session_state.agent_states.get(k) == 'done' for k in st.session_state.agent_states):
    st.info("⏳ Outputs are being processed... Please wait or try running again.")


if any(v for v in st.session_state.outputs.values()):
    export = (
        "# Doc Dream Team — Session Export\n\n"
        f"**Document:** {st.session_state.doc_meta.get('name','—')}\n"
        f"**Query:** {st.session_state.last_query}\n\n"
    )
    for k, v in st.session_state.outputs.items():
        if v:
            export += (
                f"## {AGENT_CONFIG[k]['label']}\n{v}\n\n"
            )
    st.download_button(
        "⬇ Export session",
        export,
        file_name="session.md",
        mime="text/markdown"
    )
