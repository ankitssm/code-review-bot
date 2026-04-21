import streamlit as st
import os
import sqlite3
import datetime
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# ── Database setup ────────────────────────────────────────────────────────────
def init_db():
    conn = sqlite3.connect("history.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            language TEXT,
            code TEXT,
            review TEXT,
            created_at TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_review(language, code, review):
    conn = sqlite3.connect("history.db")
    c = conn.cursor()
    c.execute("INSERT INTO reviews (language, code, review, created_at) VALUES (?, ?, ?, ?)",
              (language, code, review, datetime.datetime.now().strftime("%Y-%m-%d %H:%M")))
    conn.commit()
    conn.close()

def get_history():
    conn = sqlite3.connect("history.db")
    c = conn.cursor()
    c.execute("SELECT id, language, code, review, created_at FROM reviews ORDER BY id DESC LIMIT 20")
    rows = c.fetchall()
    conn.close()
    return rows

def delete_review(review_id):
    conn = sqlite3.connect("history.db")
    c = conn.cursor()
    c.execute("DELETE FROM reviews WHERE id = ?", (review_id,))
    conn.commit()
    conn.close()

init_db()

st.set_page_config(page_title="Code Review Bot", page_icon="🤖", layout="wide")

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
html, body, [class*="css"] {
    background-color: #1e1e1e;
    color: #d4d4d4;
    font-family: 'Segoe UI', sans-serif;
}
.hero {
    background: linear-gradient(135deg, #007acc 0%, #005f99 100%);
    padding: 2rem 2.5rem;
    border-radius: 12px;
    margin-bottom: 1.5rem;
}
.hero h1 { color: #ffffff; font-size: 2.2rem; margin: 0; }
.hero p  { color: #cce5ff; margin: 0.3rem 0 0; font-size: 1rem; }
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
.badge.green { background: #3a7d44; }
.stTextArea textarea {
    background-color: #252526 !important;
    color: #d4d4d4 !important;
    font-family: 'Cascadia Code', 'Courier New', monospace !important;
    font-size: 0.9rem !important;
    border: 1px solid #3c3c3c !important;
    border-radius: 8px !important;
}
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
.history-item {
    background: #2d2d2d;
    border-radius: 8px;
    padding: 0.6rem 0.8rem;
    margin-bottom: 0.5rem;
    cursor: pointer;
    border-left: 3px solid #007acc;
}
.history-item:hover { background: #333333; }
.history-item .lang { font-size: 0.7rem; color: #007acc; font-weight: 600; }
.history-item .time { font-size: 0.7rem; color: #888; }
.history-item .preview { font-size: 0.75rem; color: #aaa; margin-top: 2px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.stButton > button {
    background: #007acc !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-size: 1rem !important;
    padding: 0.6rem 1.2rem !important;
}
.stButton > button:hover { background: #005f99 !important; }
section[data-testid="stSidebar"] { background-color: #252526 !important; }
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
    st.markdown("---")

    # ── History Section ───────────────────────────────────────────────────────
    st.markdown("### 🕓 Review History")
    history = get_history()

    if not history:
        st.caption("No reviews yet. Start reviewing code!")
    else:
        st.caption(f"{len(history)} review(s) saved")
        if st.button("🗑️ Clear All History", use_container_width=True):
            conn = sqlite3.connect("history.db")
            conn.execute("DELETE FROM reviews")
            conn.commit()
            conn.close()
            st.rerun()

        for row in history:
            review_id, lang, code, review, created_at = row
            code_preview = code.strip().splitlines()[0][:40] if code.strip() else ""
            with st.expander(f"🕐 {created_at} — {lang}"):
                st.caption(f"**Preview:** `{code_preview}...`")
                if st.button("📂 Load this review", key=f"load_{review_id}"):
                    st.session_state["loaded_review"] = review
                    st.session_state["loaded_code"] = code
                    st.session_state["loaded_lang"] = lang
                    st.rerun()
                if st.button("🗑️ Delete", key=f"del_{review_id}"):
                    delete_review(review_id)
                    st.rerun()

# ── Load from history if selected ────────────────────────────────────────────
if "loaded_review" in st.session_state:
    st.info("📂 Loaded from history")
    st.markdown("### 📝 Code")
    st.code(st.session_state["loaded_code"], language=st.session_state["loaded_lang"].lower())
    st.markdown("### 🔍 Review")
    st.markdown(st.session_state["loaded_review"])
    if st.button("❌ Clear loaded review"):
        del st.session_state["loaded_review"]
        del st.session_state["loaded_code"]
        del st.session_state["loaded_lang"]
        st.rerun()

else:
    # ── Code Input ────────────────────────────────────────────────────────────
    code_input = st.text_area("📝 Paste your code here", height=300, placeholder="# Paste your code here...")

    if code_input.strip():
        line_count = len(code_input.strip().splitlines())
        st.markdown(f'<span class="badge">{language}</span><span class="badge green">{line_count} lines</span>', unsafe_allow_html=True)

    # ── Review Button ─────────────────────────────────────────────────────────
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

            # Save to database
            save_review(language, code_input, review)

            st.success("✅ Review complete — saved to history!")
            st.markdown("---")

            # ── Parse & display sections ──────────────────────────────────
            section_map = {
                "🐛 Bugs":          ("bugs",     "🐛 Bugs"),
                "🎨 Style Issues":  ("style",    "🎨 Style Issues"),
                "⚡ Performance":   ("perf",     "⚡ Performance"),
                "🔒 Security":      ("security", "🔒 Security"),
                "✅ Improvements":  ("improve",  "✅ Improvements"),
                "📝 Improved Code": ("code",     "📝 Improved Code"),
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

            for (css_class, label), content in sections_found.items():
                if css_class == "code":
                    st.markdown(f'<div class="review-box {css_class}"><h3>{label}</h3></div>', unsafe_allow_html=True)
                    st.code(content.replace("```python","").replace("```","").strip(), language=language.lower())
                    st.button("📋 Copy Improved Code", key="copy_btn")
                else:
                    st.markdown(f"""
                    <div class="review-box {css_class}">
                        <h3>{label}</h3>
                        {content.replace(chr(10), '<br>')}
                    </div>
                    """, unsafe_allow_html=True)