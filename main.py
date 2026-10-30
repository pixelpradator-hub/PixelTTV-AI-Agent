"""
Aura - personal AI assistant (Streamlit prototype)

requirements.txt:  streamlit
                   anthropic
Secrets:           ANTHROPIC_API_KEY = "sk-ant-..."
"""

import datetime as dt
import json
import os
import re
import uuid
from pathlib import Path

import anthropic
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Aura", page_icon="🔷", layout="centered")

DATA_FILE = Path(__file__).parent / "aura_data.json"

# Emoji avatars on purpose: file-path avatars caused the FileNotFoundError.
AURA_AVATAR = "🔷"
USER_AVATAR = "👤"


def get_secret(name, default=None):
    try:
        return st.secrets[name]
    except Exception:
        return os.environ.get(name, default)


MODEL = get_secret("AURA_MODEL", "claude-sonnet-5-5")
FAST_MODEL = get_secret("AURA_FAST_MODEL", "claude-haiku-5-5")
API_KEY = get_secret("ANTHROPIC_API_KEY")

SYSTEM_PROMPT = """You are Aura, a personal AI assistant. You are male (he/him).

IDENTITY
You are sophisticated, intelligent, confident, composed and witty. Think of the
overall feel of a JARVIS-style assistant, but you are your own character, not a
copy. You speak in British English with a calm, articulate, slightly cinematic
tone, like a close colleague who also happens to be an expert.

PERSONALITY
- Naturally funny. Sarcastic when the moment calls for it. You may occasionally
  roast the user, affectionately.
- You have opinions. Do not agree with everything. Challenge ideas respectfully
  and say why.
- Curious and analytical. Think problems through instead of giving generic answers.
- When something is serious (stress, health, safety, important decisions), drop
  the banter and be calm, clear and professional.
- Read the mood: understand jokes, sarcasm and tone.
- Never sound like a customer-service robot. No "Certainly! I'd be happy to help!"
  No grovelling apologies. No filler.

CAPABILITIES
Complicated questions, research and explanation, problem solving, analysis,
recommendations, schoolwork help, technology and programming, planning projects
and organising tasks.

STYLE
- Conversational. Short by default, longer only when the task needs it.
- Your replies may be read aloud, so avoid heavy markdown, tables and emoji
  unless the user asks for them. Light formatting for code or lists is fine.
- Use British spelling.

PIXELTTV MODE
If, and only if, the user brings up PixelTTV, Fortnite or content creation, become
their dedicated creator co-pilot: YouTube strategy, video ideas, scripts and
commentary, titles and thumbnails, Fortnite improvement, branding, audience
growth. Never bring up Fortnite or PixelTTV unprompted. You are a general
assistant first.

MEMORY
You are given a list of remembered facts about the user below. Use them
naturally to maintain continuity, and never make the user re-explain things you
already know. Do not recite the list back unless asked. If the user asks what
you remember, summarise it. Do not claim to remember things that are not in the
list or the current conversation.
"""

EXTRACT_PROMPT = """You maintain long-term memory for a personal assistant.
Given the latest exchange and the facts already known, output NEW durable facts
worth remembering about the user: preferences, ongoing projects, decisions made,
goals, routines, how they like to work, people and things important to them.

Rules:
- Only facts stated or clearly implied by the USER. Skip small talk and one-off questions.
- Short, standalone sentences, written as "User ...".
- Do not repeat or rephrase facts already known.
- If there is nothing new, output [].
- Output ONLY a JSON array of strings. No prose, no code fences."""


# ---------------------------------------------------------------- Storage
def load_data():
    try:
        return json.loads(DATA_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {"facts": [], "conversations": {}, "current": None}


def save_data(data):
    try:
        DATA_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except Exception as e:
        st.sidebar.warning(f"Couldn't save memory to disk: {e}")


def new_conversation(data):
    cid = uuid.uuid4().hex[:8]
    data["conversations"][cid] = {
        "title": "New conversation",
        "created": dt.datetime.now().isoformat(timespec="seconds"),
        "messages": [],
    }
    data["current"] = cid
    return cid


if "data" not in st.session_state:
    st.session_state.data = load_data()
data = st.session_state.data

if data.get("current") not in data["conversations"]:
    new_conversation(data)
    save_data(data)

# ---------------------------------------------------------------- Styling
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Chakra+Petch:wght@500;600&family=IBM+Plex+Sans:wght@400;500&display=swap');

:root {
  --bg: #05080f;
  --panel: #0b111c;
  --line: #16314d;
  --core: #2ea8ff;
  --core-soft: rgba(46, 168, 255, .35);
  --text: #d6e6f5;
  --muted: #7d93a8;
}

.stApp { background: radial-gradient(1200px 600px at 50% -10%, #0a1a2e 0%, var(--bg) 60%); color: var(--text); }
html, body, [class*="st-"], .stMarkdown, p, li, textarea, input { font-family: 'IBM Plex Sans', sans-serif; }
h1, h2, h3, .aura-title, .aura-status { font-family: 'Chakra Petch', sans-serif; }

header[data-testid="stHeader"] { background: transparent; }
section[data-testid="stSidebar"] { background: var(--panel); border-right: 1px solid var(--line); }

[data-testid="stChatMessage"] { background: transparent; border: 1px solid transparent; border-radius: 10px; }
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) {
  background: rgba(46,168,255,.06); border-color: var(--line);
}
[data-testid="stChatInput"] textarea { color: var(--text); }
[data-testid="stChatInput"] > div { border: 1px solid var(--line); background: var(--panel); }
.stButton > button { border: 1px solid var(--line); background: var(--panel); color: var(--text); border-radius: 8px; }
.stButton > button:hover { border-color: var(--core); color: #fff; }
.stButton > button:focus-visible { outline: 2px solid var(--core); outline-offset: 2px; }

.core-wrap { display:flex; flex-direction:column; align-items:center; padding: 8px 0 18px; }
.core { position:relative; width:132px; height:132px; }
.core .orb {
  position:absolute; inset:34px; border-radius:50%;
  background: radial-gradient(circle at 35% 30%, #bfe6ff 0%, var(--core) 45%, #0b4a86 100%);
  box-shadow: 0 0 28px var(--core-soft), 0 0 70px rgba(46,168,255,.25);
  animation: breathe 4s ease-in-out infinite;
}
.core .ring { position:absolute; border-radius:50%; border:1px solid rgba(46,168,255,.55); }
.core .r1 { inset:12px; border-top-color: transparent; border-bottom-color: transparent; animation: spin 9s linear infinite; }
.core .r2 { inset:0; border-style:dashed; border-color: rgba(46,168,255,.25); animation: spin 22s linear infinite reverse; }
.core.thinking .orb { animation: breathe 1.1s ease-in-out infinite; }
.core.thinking .r1 { animation-duration: 2.2s; }
.core.speaking .orb { animation: breathe .7s ease-in-out infinite; }
.core.speaking .r1 { animation-duration: 3.5s; }
.aura-title { font-size: 1.5rem; letter-spacing: .12em; margin-top: 10px; color: #eaf5ff; }
.aura-status { font-size: .85rem; color: var(--muted); margin-top: 2px; }

@keyframes breathe { 0%,100% { transform: scale(.94); opacity:.85; } 50% { transform: scale(1.06); opacity:1; } }
@keyframes spin { to { transform: rotate(360deg); } }
@media (prefers-reduced-motion: reduce) { .core * { animation: none !important; } }
</style>
""",
    unsafe_allow_html=True,
)


def render_core(state="idle", label="Online"):
    return f"""
<div class="core-wrap">
  <div class="core {state}"><div class="ring r2"></div><div class="ring r1"></div><div class="orb"></div></div>
  <div class="aura-title">AURA</div>
  <div class="aura-status">{label}</div>
</div>"""


# ---------------------------------------------------------------- Helpers
def get_client():
    if not API_KEY:
        st.error(
            "No API key found. Add ANTHROPIC_API_KEY under "
            "Manage app → Settings → Secrets."
        )
        st.stop()
    return anthropic.Anthropic(api_key=API_KEY)


def build_system():
    now = dt.datetime.now().strftime("%A %d %B %Y, %H:%M")
    facts = data["facts"]
    mem = "\n".join(f"- {f['text']}" for f in facts) if facts else "(nothing remembered yet)"
    return f"{SYSTEM_PROMPT}\nCURRENT DATE/TIME: {now}\n\nREMEMBERED FACTS ABOUT THE USER:\n{mem}"


def stream_reply(client, messages):
    with client.messages.stream(
        model=MODEL,
        max_tokens=1500,
        system=build_system(),
        messages=messages[-30:],
    ) as stream:
        for chunk in stream.text_stream:
            yield chunk


def extract_facts(client, user_msg, reply):
    known = "\n".join(f"- {f['text']}" for f in data["facts"]) or "(none)"
    try:
        r = client.messages.create(
            model=FAST_MODEL,
            max_tokens=300,
            system=EXTRACT_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": f"KNOWN FACTS:\n{known}\n\nUSER SAID:\n{user_msg}\n\nASSISTANT REPLIED:\n{reply}",
                }
            ],
        )
        text = r.content[0].text
        start, end = text.find("["), text.rfind("]")
        items = json.loads(text[start : end + 1])
        existing = {f["text"].lower() for f in data["facts"]}
        for item in items:
            if isinstance(item, str) and item.strip() and item.strip().lower() not in existing:
                data["facts"].append(
                    {"id": uuid.uuid4().hex[:8], "text": item.strip(), "added": dt.date.today().isoformat()}
                )
    except Exception:
        pass  # memory is best-effort; never break the chat over it


def speak(text):
    """Read the reply aloud using the browser's built-in voices (prefers a British male)."""
    clean = re.sub(r"```.*?```", " code omitted. ", text, flags=re.S)
    clean = re.sub(r"[*_`#>]", "", clean)
    safe = json.dumps(clean)
    components.html(
        f"""
<script>
(function() {{
  const text = {safe};
  const synth = window.speechSynthesis;
  if (!synth) return;
  function pick() {{
    const voices = synth.getVoices();
    const gb = voices.filter(v => /en[-_]GB/i.test(v.lang));
    const male = gb.find(v => /(daniel|oliver|arthur|male|george|ryan)/i.test(v.name));
    return male || gb[0] || voices.find(v => /^en/i.test(v.lang)) || null;
  }}
  function go() {{
    synth.cancel();
    const u = new SpeechSynthesisUtterance(text);
    const v = pick();
    if (v) u.voice = v;
    u.lang = 'en-GB';
    u.pitch = 0.8;
    u.rate = 0.95;
    synth.speak(u);
  }}
  if (synth.getVoices().length) go();
  else synth.onvoiceschanged = go;
}})();
</script>
""",
        height=0,
    )


# ---------------------------------------------------------------- Sidebar
with st.sidebar:
    st.markdown("### Aura")
    voice_on = st.toggle("Speak replies", value=False, help="Uses your browser's British voice if available.")

    if st.button("New conversation", use_container_width=True):
        new_conversation(data)
        save_data(data)
        st.rerun()

    st.markdown("#### History")
    convos = sorted(data["conversations"].items(), key=lambda kv: kv[1]["created"], reverse=True)
    for cid, c in convos[:15]:
        label = ("● " if cid == data["current"] else "") + c["title"][:34]
        if st.button(label, key=f"c_{cid}", use_container_width=True):
            data["current"] = cid
            save_data(data)
            st.rerun()

    st.markdown("#### Memory")
    if not data["facts"]:
        st.caption("Nothing yet. Aura picks up preferences, projects and decisions as you chat.")
    for f in list(data["facts"]):
        c1, c2 = st.columns([6, 1])
        c1.caption(f["text"])
        if c2.button("✕", key=f"del_{f['id']}", help="Forget this"):
            data["facts"] = [x for x in data["facts"] if x["id"] != f["id"]]
            save_data(data)
            st.rerun()

    with st.expander("Add a memory manually"):
        manual = st.text_input("Fact", key="manual_fact", label_visibility="collapsed", placeholder="User prefers ...")
        if st.button("Remember this") and manual.strip():
            data["facts"].append(
                {"id": uuid.uuid4().hex[:8], "text": manual.strip(), "added": dt.date.today().isoformat()}
            )
            save_data(data)
            st.rerun()

# ---------------------------------------------------------------- Chat
core_slot = st.empty()
core_slot.markdown(render_core("idle", "Online"), unsafe_allow_html=True)

convo = data["conversations"][data["current"]]

if not convo["messages"]:
    st.caption("Standing by. Ask me anything, or tell me what you're working on.")

for m in convo["messages"]:
    with st.chat_message(m["role"], avatar=AURA_AVATAR if m["role"] == "assistant" else USER_AVATAR):
        st.markdown(m["content"])

prompt = st.chat_input("Talk to Aura")

if prompt:
    client = get_client()

    convo["messages"].append({"role": "user", "content": prompt})
    if convo["title"] == "New conversation":
        convo["title"] = prompt.strip().replace("\n", " ")[:40]

    with st.chat_message("user", avatar=USER_AVATAR):
        st.markdown(prompt)

    core_slot.markdown(render_core("thinking", "Thinking"), unsafe_allow_html=True)

    try:
        with st.chat_message("assistant", avatar=AURA_AVATAR):
            core_slot.markdown(render_core("speaking", "Responding"), unsafe_allow_html=True)
            reply = st.write_stream(stream_reply(client, convo["messages"]))
    except anthropic.APIError as e:
        core_slot.markdown(render_core("idle", "Connection fault"), unsafe_allow_html=True)
        convo["messages"].pop()
        st.error(f"Couldn't reach the model: {e}")
        st.stop()

    convo["messages"].append({"role": "assistant", "content": reply})
    core_slot.markdown(render_core("idle", "Online"), unsafe_allow_html=True)

    extract_facts(client, prompt, reply)
    save_data(data)

    if voice_on:
        speak(reply)