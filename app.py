import streamlit as st
import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

st.set_page_config(page_title="Code Review Bot", page_icon="🤖", layout="wide")

# ── Custom CSS (dark VS Code theme) ──────────────────────────────────────────
st.markdown("""
<style>
/* Base */
html, body, [class*="css"] {
    background-color: #1e1e1e;
    color: #d4d4d4;
    font-family: 'Segoe UI', sans-serif;
}

/* Header */
.hero {
    background: linear-gradient(135deg, #007acc 0%, #005f99 100%);
    padding: 2rem 2.5rem;
    border-radius: 12px;
    margin-bottom: 1.5rem;
}
.hero h1 { color: #ffffff; font-size: 2.2rem; margin: 0; }
.hero p  { color: #cce5ff; margin: 0.3rem 0 0; font-size: 1rem; }

/* Badge */
.badge {
    display: inline-block;
    background: #007acc;
    color: #fff;
    padding: 2px 10px;
    border-radius: 999px;
    font-size: 0.75rem;
    margin-right: 6px;
    font-weight: 600;
}
.badge.green  { background: #3a7d44; }
.badge.yellow { background: #7d6b3a; }

/* Code input area */
.stTextArea textarea {
    background-color: #252526 !important;
    color: #d4d4d4 !important;
    font-family: 'Cascadia Code', 'Courier New', monospace !important;
    font-size: 0.9rem !important;
    border: 1px solid #3c3c3c !important;
    border-radius: 8px !important;
}

/* Review sections */
.review-box {
    background: #252526;
    border-left: 4px solid #007acc;
    border-radius: 8px;
    padding: 1rem 1.2rem;
    margin-bottom: 1rem;
}
.review-box.bugs     { border-color: #f44747; }
.review-box.style    { border-color: #dcdcaa; }
.review-box.perf     { border-color: #569cd6; }
.review-box.security { border-color: #ce9178; }
.review-box.improve  { border-color: #4ec9b0; }
.review-box.code     { border-color: #c586c0; }
.review-box h3 { margin: 0 0 0.5rem; font-size: 1rem; color: #ffffff; }

/* Button */
.stButton > button {
    background: #007acc !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-size: 1rem !important;
    padding: 0.6rem 1.2rem !important;
    transition: background 0.2s;
}
.stButton > button:hover {
    background: #005f99 !important;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background-color: #252526 !important;
}

/* Selectbox / multiselect */
.stSelectbox div, .stMultiSelect div {
    background-color: #2d2d2d !important;
    color: #d4d4d4 !important;
}
</style>
""", unsafe_allow_html=True)

# ── Hero Header ───────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
    <h1>🤖 Code Review Bot</h1>
    <p>Paste your code and get an instant AI-powered review — bugs, style, performance & more</p>
</div>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Settings")
    language = st.selectbox("Programming Language", ["Python", "JavaScript", "Java", "C++", "C", "SQL", "Other"])
    review_focus = st.multiselect(
        "Focus areas",
        ["Bugs", "Style", "Performance", "Security", "Improvements"],
        default=["Bugs", "Style", "Improvements"]
    )
    st.markdown("---")
    st.markdown("**Model:** `llama-3.3-70b-versatile`")
    st.markdown("**Powered by:** Groq API")

# ── Code Input ────────────────────────────────────────────────────────────────
code_input = st.text_area("📝 Paste your code here", height=300, placeholder="# Paste your code here...")

# Line count + language badge
if code_input.strip():
    line_count = len(code_input.strip().splitlines())
    st.markdown(f"""
    <span class="badge">{language}</span>
    <span class="badge green">{line_count} lines</span>
    """, unsafe_allow_html=True)

# ── Review Button ─────────────────────────────────────────────────────────────
if st.button("🔍 Review My Code", use_container_width=True):
    if not code_input.strip():
        st.warning("Please paste some code first!")
    else:
        with st.spinner("Analyzing your code..."):
            focus_str = ", ".join(review_focus)
            backtick = "```"
            prompt = f"""You are a senior software engineer doing a thorough code review.

Review the following {language} code and provide feedback on: {focus_str}.

Structure your response exactly like this (keep these exact headings):
## 🐛 Bugs
(list any bugs or say "None found")

## 🎨 Style Issues
(list style problems or say "None found")

## ⚡ Performance
(list performance issues or say "None found")

## 🔒 Security
(list security issues or say "None found")

## ✅ Improvements
(suggest specific improvements)

## 📝 Improved Code
(rewrite the improved version of the code)

Code to review:
{backtick}{language}
{code_input}
{backtick}"""

            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            review = response.choices[0].message.content

        st.success("✅ Review complete!")
        st.markdown("---")

        # ── Parse & display sections with colored boxes ──
        section_map = {
            "🐛 Bugs":         ("bugs",     "🐛 Bugs"),
            "🎨 Style Issues": ("style",    "🎨 Style Issues"),
            "⚡ Performance":  ("perf",     "⚡ Performance"),
            "🔒 Security":     ("security", "🔒 Security"),
            "✅ Improvements": ("improve",  "✅ Improvements"),
            "📝 Improved Code":("code",     "📝 Improved Code"),
        }

        current_section = None
        current_content = []
        sections_found  = {}

        for line in review.splitlines():
            matched = False
            for heading, (css_class, label) in section_map.items():
                if heading in line:
                    if current_section:
                        sections_found[current_section] = "\n".join(current_content).strip()
                    current_section = (css_class, label)
                    current_content = []
                    matched = True
                    break
            if not matched and current_section:
                current_content.append(line)

        if current_section:
            sections_found[current_section] = "\n".join(current_content).strip()

        # Render each section
        for (css_class, label), content in sections_found.items():
            if css_class == "code":
                st.markdown(f"""
                <div class="review-box {css_class}">
                    <h3>{label}</h3>
                </div>
                """, unsafe_allow_html=True)
                st.code(content.replace("```python","").replace("```","").strip(), language=language.lower())
                st.button("📋 Copy Improved Code", key="copy_btn", help="Select the code above and copy it")
            else:
                st.markdown(f"""
                <div class="review-box {css_class}">
                    <h3>{label}</h3>
                    {content.replace(chr(10), '<br>')}
                </div>
                """, unsafe_allow_html=True)