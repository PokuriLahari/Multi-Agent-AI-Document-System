import re

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

def repl(pattern, replacement, count=0):
    global content
    content = re.sub(pattern, replacement, content, count=count, flags=re.DOTALL)

# FIX 1 & 4 - Streamlit chrome hiding and starting from top
css_to_add = """
  /* Hide ALL Streamlit default UI chrome */
  #MainMenu { visibility: hidden !important; display: none !important; }
  header[data-testid="stHeader"] { display: none !important; }
  footer { display: none !important; }
  .stDeployButton { display: none !important; }
  [data-testid="stToolbar"] { display: none !important; }
  [data-testid="stDecoration"] { display: none !important; }
  [data-testid="stStatusWidget"] { display: none !important; }
  div[data-testid="stAppViewBlockContainer"] {
      padding-top: 0 !important;
  }
  .stApp > header { display: none !important; }
  section[data-testid="stSidebar"] { display: none !important; }

  /* Remove top padding Streamlit adds for its header */
  .main .block-container {
      padding-top: 0 !important;
      padding-left: 0 !important;
      padding-right: 0 !important;
      max-width: 100% !important;
  }
  .stApp {
      margin-top: 0 !important;
      padding-top: 0 !important;
  }

  [data-testid="stAppViewContainer"] {
      padding-top: 0 !important;
      margin-top: 0 !important;
  }

  [data-testid="stVerticalBlock"] {
      gap: 0 !important;
  }

  /* Target the first element directly */
  [data-testid="stVerticalBlock"] > div:first-child {
      margin-top: 0 !important;
      padding-top: 0 !important;
  }
"""
repl(r'\.block-container\s*\{[^\}]+\}', css_to_add)

# FIX 2 - Topbar fixed
repl(r'\.np-topbar\s*\{[^\}]+\}', '''.np-topbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px 32px;
    border-bottom: 1px solid rgba(255,255,255,0.06);
    background: rgba(10,10,28,0.98);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    position: relative;
    z-index: 999;
    width: 100%;
    margin-top: 0;
}''')

# FIX 3 - Reduce canvas height
repl(r'components\.html\(neural_canvas_html, height=240, scrolling=False\)', 'components.html(neural_canvas_html, height=200, scrolling=False)')
repl(r'width:100%; height:240px;', 'width:100%; height:200px;')
repl(r'const H = 240;', 'const H = 200;')
repl(r'cv\.height = 240;', 'cv.height = 200;')

# FIX 5 - Add scroll-to-top on page load
scroll_script = '''components.html(
    """
    <script>
      window.parent.document.querySelector(
        '[data-testid="stAppViewContainer"]'
      ).scrollTop = 0;
    </script>
    """,
    height=0,
    scrolling=False,
)

st.markdown('''

repl(r'st\.markdown\(\n\s*\'<div class="np-topbar">\'', scroll_script + '\n    \'<div class="np-topbar">\'')

# FIX 6 - Logo text fix
repl(r'<span class="np-logo-mark">Brain</span>', '<span class="np-logo-mark">🧠</span>')
repl(r'\.np-logo-mark\s*\{[^\}]+\}', '''.np-logo-mark {
    font-size: 24px;
    line-height: 1;
}''')

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)
