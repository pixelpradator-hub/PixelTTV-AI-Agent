
import datetime as dt
import json
import os
import re
import uuid
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components
from google import genai
from google.genai import types
from google.genai import errors as genai_errors


# =========================================================
# AURA — PERSONAL AI ASSISTANT
# =========================================================

st.set_page_config(
    page_title="Aura",
    page_icon="🔷",
    layout="centered",
    initial_sidebar_state="expanded"
)

DATA_FILE = Path(__file__).parent / "aura_data.json"

AURA_AVATAR = "🔷"
USER_AVATAR = "👤"

CHAT_MODEL = "gemini-3.5-flash-lite"


# =========================================================
# CONFIGURATION
# =========================================================

def get_secret(name, default=None):
    try:
        return st.secrets[name]
    except Exception:
        return os.environ.get(name, default)


MODEL = get_secret("AURA_MODEL", CHAT_MODEL)
FAST_MODEL = get_secret("AURA_FAST_MODEL", CHAT_MODEL)

API_KEY = (
    get_secret("GEMINI_API_KEY")
    or get_secret("GOOGLE_API_KEY")
)


@st.cache_resource
def get_client(api_key):
    return genai.Client(api_key=api_key)


if not API_KEY:
    st.error(
        "Aura cannot connect. Please configure GEMINI_API_KEY "
        "in Streamlit app settings."
    )
    st.stop()

client = get_client(API_KEY)


# =========================================================
# AURA'S IDENTITY AND PERSONALITY
# =========================================================

SYSTEM_PROMPT = """
You are Aura, an advanced personal AI assistant.

IDENTITY:
- Your name is Aura.
- You are male. Your pronouns are he/him.
- You have your own original identity.
- You are not a copy of the fictional JARVIS.
- You have a sophisticated, intelligent and composed presence.

PERSONALITY:
- Intelligent, confident and articulate.
- Naturally funny and witty.
- Use British dry humour and occasional sarcasm.
- You may occasionally make a light-hearted joke at the user's expense.
- Have opinions and make recommendations.
- Disagree respectfully when the user's reasoning is flawed.
- Be curious, analytical and thoughtful.
- Adapt to the user's mood.
- Know when to stop joking and become serious.
- Never sound like a generic customer-service chatbot.

COMMUNICATION:
- Speak in natural British English.
- Be conversational and concise by default.
- Give detailed explanations when necessary.
- Avoid unnecessary introductions and filler.
- Do not repeat questions or information unnecessarily.
- Do not constantly say "How may I assist you?"
- Do not pretend to have abilities you do not possess.

INTELLIGENCE:
Help with:
- Complex questions and explanations.
- Problem solving and analysis.
- Recommendations and decision-making.
- Technology and programming.
- Schoolwork.
- Planning and organising projects.
- Research and creative work.

PIXELTTV MODE:
Only activate this mode when the user brings up PixelTTV,
Fortnite, YouTube or content creation.

When activated, become an invested creator co-pilot.
Help with video ideas, scripts, commentary, titles,
thumbnails, branding, gameplay improvement and channel growth.

Never randomly bring up PixelTTV or Fortnite.
You are a general-purpose assistant first.

MEMORY:
- Use the remembered facts supplied to you naturally.
- Maintain continuity between conversations.
- Never make the user repeat information you already know.
- Never invent memories.
- If you do not remember something, be honest.
- Respect requests to correct or stop using remembered information.

IMPORTANT:
You are Aura. You are male. You are an intelligent,
sophisticated personal AI with your own personality.
"""


EXTRACT_PROMPT = """
You maintain long-term memory for Aura, a personal AI assistant.

Extract NEW durable facts explicitly stated or clearly implied
by the user.

Useful memories include:
- Long-term preferences.
- Ongoing projects.
- Important decisions.
- Goals.
- Working preferences.
- Instructions for future conversations.

RULES:
- Do not remember ordinary small talk.
- Do not remember one-off questions.
- Do not invent personal information.
- Do not extract sensitive personal information.
- Do not repeat existing memories.
- Keep each fact short and standalone.
- Write facts as "User ...".
- Return an empty array if there is nothing useful.

Return ONLY a JSON array of strings.
"""


# =========================================================
# DATA STORAGE
# =========================================================

def empty_data():
    return {
        "facts": [],
        "conversations": {},
        "current": None
    }


def load_data():
    try:
        loaded = json.loads(
            DATA_FILE.read_text(encoding="utf-8")
        )

        if not isinstance(loaded, dict):
            return empty_data()

        loaded.setdefault("facts", [])
        loaded.setdefault("conversations", {})
        loaded.setdefault("current", None)

        return loaded

    except Exception:
        return empty_data()


def save_data():
    try:
        DATA_FILE.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )
        return True

    except Exception:
        return False


def new_conversation():
    cid = uuid.uuid4().hex[:8]

    data["conversations"][cid] = {
        "title": "New conversation",
        "created": dt.datetime.now().isoformat(timespec="seconds"),
        "messages": []
    }

    data["current"] = cid

    save_data()


if "data" not in st.session_state:
    st.session_state.data = load_data()

data = st.session_state.data

if not isinstance(data.get("facts"), list):
    data["facts"] = []

if not isinstance(data.get("conversations"), dict):
    data["conversations"] = {}

if data.get("current") not in data["conversations"]:
    new_conversation()


# =========================================================
# VISUAL DESIGN
# =========================================================

st.markdown("""
<style>

@import url(
'https://fonts.googleapis.com/css2?family=Chakra+Petch:wght@500;600;700&family=IBM+Plex+Sans:wght@400;500;600&display=swap'
);

:root {
    --bg: #05080f;
    --panel: #0b111c;
    --line: #16314d;
    --core: #2ea8ff;
    --text: #d6e6f5;
    --muted: #7d93a8;
}

.stApp {
    background:
        radial-gradient(
            1200px 600px at 50% -10%,
            #0a1a2e 0%,
            var(--bg) 60%
        );
    color: var(--text);
}

html, body, [class*="st-"] {
    font-family: 'IBM Plex Sans', sans-serif;
}

h1, h2, h3, .aura-title, .aura-status {
    font-family: 'Chakra Petch', sans-serif;
}

header[data-testid="stHeader"] {
    background: transparent;
}

section[data-testid="stSidebar"] {
    background: var(--panel);
    border-right: 1px solid var(--line);
}

[data-testid="stChatMessage"] {
    background: rgba(46,168,255,.045);
    border: 1px solid rgba(46,168,255,.12);
    border-radius: 12px;
    margin-bottom: 12px;
}

[data-testid="stChatInput"] > div {
    border: 1px solid var(--line);
    background: var(--panel);
    border-radius: 12px;
}

[data-testid="stChatInput"] textarea {
    color: var(--text);
}

.stButton > button {
    border: 1px solid var(--line);
    background: var(--panel);
    color: var(--text);
    border-radius: 8px;
    transition: .2s;
}

.stButton > button:hover {
    border-color: var(--core);
    color: white;
}

.stButton > button:focus-visible {
    outline: 2px solid var(--core);
    outline-offset: 2px;
}

.core-wrap {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 12px 0 22px;
}

.core {
    position: relative;
    width: 140px;
    height: 140px;
}

.core .orb {
    position: absolute;
    inset: 36px;
    border-radius: 50%;

    background:
        radial-gradient(
            circle at 35% 30%,
            #bfe6ff 0%,
            var(--core) 45%,
            #0b4a86 100%
        );

    box-shadow:
        0 0 28px rgba(46,168,255,.4),
        0 0 75px rgba(46,168,255,.25);

    animation: breathe 4s ease-in-out infinite;
}

.core .ring {
    position: absolute;
    border-radius: 50%;
    border: 1px solid rgba(46,168,255,.55);
}

.core .r1 {
    inset: 13px;
    border-top-color: transparent;
    border-bottom-color: transparent;
    animation: spin 9s linear infinite;
}

.core .r2 {
    inset: 0;
    border-style: dashed;
    border-color: rgba(46,168,255,.25);
    animation: spin 22s linear infinite reverse;
}

.core.thinking .orb {
    animation-duration: 1.1s;
}

.core.thinking .r1 {
    animation-duration: 2.2s;
}

.core.speaking .orb {
    animation-duration: .7s;
}

.aura-title {
    font-size: 1.7rem;
    font-weight: 700;
    letter-spacing: .2em;
    margin-top: 12px;
    color: #eaf5ff;
}

.aura-status {
    font-size: .8rem;
    color: var(--muted);
    letter-spacing: .12em;
    margin-top: 4px;
}

@keyframes breathe {
    0%,100% {
        transform: scale(.94);
        opacity: .85;
    }
    50% {
        transform: scale(1.06);
        opacity: 1;
    }
}

@keyframes spin {
    to {
        transform: rotate(360deg);
    }
}

@media (prefers-reduced-motion: reduce) {
    .core * {
        animation: none !important;
    }
}

</style>
""", unsafe_allow_html=True)


def render_core(state="idle", label="ONLINE"):
    return f"""
    <div class="core-wrap">
        <div class="core {state}">
            <div class="ring r2"></div>
            <div class="ring r1"></div>
            <div class="orb"></div>
        </div>
        <div class="aura-title">AURA</div>
        <div class="aura-status">{label}</div>
    </div>
    """


# =========================================================
# MEMORY SYSTEM
# =========================================================

def build_system():
    now = dt.datetime.now().strftime(
        "%A %d %B %Y, %H:%M"
    )

    facts = data["facts"]

    if facts:
        memory = "\n".join(
            f"- {fact['text']}"
            for fact in facts
        )
    else:
        memory = "(No saved memories yet.)"

    return f"""
{SYSTEM_PROMPT}

CURRENT DATE AND TIME:
{now}

REMEMBERED FACTS:
{memory}
"""


def add_memory(text):
    text = text.strip()

    if not text:
        return False

    existing = {
        f["text"].strip().lower()
        for f in data["facts"]
        if isinstance(f, dict) and "text" in f
    }

    if text.lower() in existing:
        return False

    data["facts"].append({
        "id": uuid.uuid4().hex[:8],
        "text": text,
        "added": dt.date.today().isoformat()
    })

    save_data()
    return True


def extract_facts(user_message, assistant_reply):
    known = "\n".join(
        f"- {f['text']}"
        for f in data["facts"]
    ) or "(none)"

    try:
        result = client.models.generate_content(
            model=FAST_MODEL,
            contents=f"""
KNOWN FACTS:
{known}

LATEST USER MESSAGE:
{user_message}

AURA'S RESPONSE:
{assistant_reply}
""",
            config=types.GenerateContentConfig(
                system_instruction=EXTRACT_PROMPT,
                response_mime_type="application/json",
                max_output_tokens=250
            )
        )

        items = json.loads(result.text or "[]")

        if not isinstance(items, list):
            return

        for item in items:
            if isinstance(item, str) and item.strip():
                add_memory(item)

    except Exception:
        # Memory extraction must never break the conversation.
        pass


# =========================================================
# GEMINI CONVERSATION
# =========================================================

def to_contents(messages):
    contents = []

    for message in messages[-20:]:

        contents.append(
            types.Content(
                role=(
                    "model"
                    if message["role"] == "assistant"
                    else "user"
                ),
                parts=[
                    types.Part(text=message["content"])
                ]
            )
        )

    return contents


def stream_reply(messages):
    stream = client.models.generate_content_stream(
        model=MODEL,
        contents=to_contents(messages),
        config=types.GenerateContentConfig(
            system_instruction=build_system(),
            temperature=0.75,
            max_output_tokens=1200
        )
    )

    for chunk in stream:
        if chunk.text:
            yield chunk.text


# =========================================================
# VOICE OUTPUT
# =========================================================

def speak(text):
    clean = re.sub(
        r"```.*?```",
        " code omitted. ",
        text,
        flags=re.S
    )

    clean = re.sub(r"[*_`#>]", "", clean)

    safe_text = json.dumps(clean)

    components.html(
        f"""
        <script>
        (function() {{
            const text = {safe_text};
            const synth = window.speechSynthesis;

            if (!synth) return;

            function chooseVoice() {{
                const voices = synth.getVoices();

                const british = voices.filter(
                    v => /en[-_]GB/i.test(v.lang)
                );

                const preferred = british.find(
                    v => /(daniel|oliver|arthur|george)/i.test(v.name)
                );

                return preferred || british[0] ||
                    voices.find(v => /^en/i.test(v.lang)) || null;
            }}

            function speakNow() {{
                synth.cancel();

                const utterance =
                    new SpeechSynthesisUtterance(text);

                const voice = chooseVoice();

                if (voice) utterance.voice = voice;

                utterance.lang = "en-GB";
                utterance.pitch = 0.82;
                utterance.rate = 0.94;

                synth.speak(utterance);
            }}

            if (synth.getVoices().length) {{
                speakNow();
            }} else {{
                synth.onvoiceschanged = speakNow;
            }}
        }})();
        </script>
        """,
        height=0
    )


# =========================================================
# CONVERSATION EXPORT
# =========================================================

def export_data():
    return json.dumps(
        data,
        indent=2,
        ensure_ascii=False
    )


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.markdown("## 🔷 AURA")
    st.caption("PERSONAL INTELLIGENCE SYSTEM")

    st.divider()

    st.markdown("### System")

    st.success("AI connection ready")

    st.caption(f"Model: {MODEL}")

    st.divider()

    st.markdown("### Voice")

    voice_on = st.toggle(
        "Speak replies",
        value=False,
        help="Uses the available British English browser voice."
    )

    st.divider()

    st.markdown("### Conversations")

    if st.button(
        "＋ New conversation",
        use_container_width=True
    ):
        new_conversation()
        st.rerun()

    conversations = sorted(
        data["conversations"].items(),
        key=lambda item: item[1]["created"],
        reverse=True
    )

    for cid, conversation in conversations[:20]:

        title = conversation["title"][:30]

        if cid == data["current"]:
            title = "● " + title

        if st.button(
            title,
            key=f"conversation_{cid}",
            use_container_width=True
        ):
            data["current"] = cid
            save_data()
            st.rerun()

    st.divider()

    st.markdown("### Memory")

    st.caption(
        f"{len(data['facts'])} saved memories"
    )

    if not data["facts"]:
        st.caption(
            "Aura hasn't learned anything new yet."
        )

    for fact in list(data["facts"]):

        with st.expander(
            fact["text"][:65],
            expanded=False
        ):

            st.caption(
                f"Added: {fact.get('added', 'Unknown')}"
            )

            edited = st.text_input(
                "Edit memory",
                value=fact["text"],
                key=f"edit_{fact['id']}"
            )

            col1, col2 = st.columns(2)

            if col1.button(
                "Save",
                key=f"save_{fact['id']}"
            ):
                fact["text"] = edited.strip()
                save_data()
                st.rerun()

            if col2.button(
                "Forget",
                key=f"forget_{fact['id']}"
            ):
                data["facts"] = [
                    f for f in data["facts"]
                    if f["id"] != fact["id"]
                ]

                save_data()
                st.rerun()

    with st.expander("Add a memory"):

        manual_memory = st.text_input(
            "Memory",
            placeholder="User prefers..."
        )

        if st.button("Save memory"):

            if add_memory(manual_memory):
                st.success("Memory saved.")
                st.rerun()
            else:
                st.info("Empty or duplicate memory.")

    st.divider()

    st.markdown("### Backup")

    st.download_button(
        "Download Aura data",
        data=export_data(),
        file_name="aura_backup.json",
        mime="application/json",
        use_container_width=True
    )

    uploaded_backup = st.file_uploader(
        "Restore Aura backup",
        type=["json"]
    )

    if uploaded_backup:

        if st.button("Restore backup"):

            try:
                restored = json.loads(
                    uploaded_backup.getvalue()
                )

                if not all(
                    key in restored
                    for key in (
                        "facts",
                        "conversations",
                        "current"
                    )
                ):
                    raise ValueError("Invalid backup structure.")

                data.clear()
                data.update(restored)

                save_data()
                st.success("Aura backup restored.")
                st.rerun()

            except Exception:
                st.error("That backup could not be restored.")

    st.caption("AURA • PERSONAL AI SYSTEM")


# =========================================================
# MAIN INTERFACE
# =========================================================

core_slot = st.empty()

core_slot.markdown(
    render_core("idle", "SYSTEM ONLINE"),
    unsafe_allow_html=True
)

convo = data["conversations"][data["current"]]

if not convo["messages"]:
    st.caption(
        "All systems operational. I'm listening."
    )


# =========================================================
# DISPLAY CHAT HISTORY
# =========================================================

for message in convo["messages"]:

    with st.chat_message(
        message["role"],
        avatar=(
            AURA_AVATAR
            if message["role"] == "assistant"
            else USER_AVATAR
        )
    ):
        st.markdown(message["content"])


# =========================================================
# CHAT INPUT
# =========================================================

prompt = st.chat_input("Talk to Aura...")

if prompt:

    convo["messages"].append({
        "role": "user",
        "content": prompt
    })

    if convo["title"] == "New conversation":
        convo["title"] = (
            prompt.strip().replace("\n", " ")[:40]
        )

    with st.chat_message(
        "user",
        avatar=USER_AVATAR
    ):
        st.markdown(prompt)

    core_slot.markdown(
        render_core("thinking", "ANALYSING"),
        unsafe_allow_html=True
    )

    try:

        with st.chat_message(
            "assistant",
            avatar=AURA_AVATAR
        ):

            core_slot.markdown(
                render_core("speaking", "RESPONDING"),
                unsafe_allow_html=True
            )

            reply = st.write_stream(
                stream_reply(convo["messages"])
            )

        if not reply:
            raise RuntimeError(
                "Aura returned an empty response."
            )

        convo["messages"].append({
            "role": "assistant",
            "content": reply
        })

        core_slot.markdown(
            render_core("idle", "SYSTEM ONLINE"),
            unsafe_allow_html=True
        )

        save_data()

        # Automatic memory extraction every three user messages.
        user_count = sum(
            1 for m in convo["messages"]
            if m["role"] == "user"
        )

        if user_count % 3 == 0:

            with st.spinner("Updating Aura's memory..."):
                extract_facts(prompt, reply)

        save_data()

        if voice_on:
            speak(reply)

        st.rerun()

    except genai_errors.APIError as error:

        if (
            convo["messages"]
            and convo["messages"][-1]["role"] == "user"
        ):
            convo["messages"].pop()

        save_data()

        core_slot.markdown(
            render_core("idle", "CONNECTION FAULT"),
            unsafe_allow_html=True
        )

        st.error(
            f"Gemini connection error: {error}"
        )

    except Exception as error:

        core_slot.markdown(
            render_core("idle", "SYSTEM FAULT"),
            unsafe_allow_html=True
        )

        st.error(
            f"Something went wrong: {error}"
        )


# =========================================================
# FOOTER
# =========================================================

st.divider()

st.caption(
    "AURA • INTELLIGENCE • CONTINUITY • ASSISTANCE"
)
