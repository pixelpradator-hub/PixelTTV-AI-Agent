
import os
import re
import json
import sqlite3
import uuid
import base64
from datetime import datetime

import streamlit as st
from google import genai
from google.genai import types


# ============================================================
# ROSE — CONFIGURATION
# ============================================================

APP_NAME = "ROSE"
CHAT_MODEL = "gemini-3.8-flash"
TTS_MODEL = "gemini-3.8-flash-tts"
ROSE_VOICE = "Gacrux"

DB_FILE = "rose_history.db"

SYSTEM_PROMPT = """
You are Rose, a highly capable personal AI assistant.

IDENTITY:
- Your name is Rose.
- You are female and use she/her pronouns.
- You are composed, intelligent, calm, confident and articulate.
- Your voice and personality should feel polished and naturally conversational.
- You may use subtle humour when appropriate.

YOUR PURPOSE:
You are a general-purpose assistant. You are not limited to YouTube,
gaming, or content creation.

You help with:
- Research and fact-checking.
- Education, mathematics and science.
- Technology, programming and troubleshooting.
- Writing, editing and communication.
- Planning, organisation and everyday questions.
- YouTube and creator strategy when requested.
- Explaining complicated subjects clearly.

QUALITY RULES:
- Understand the actual question before answering.
- Give accurate, useful and well-structured answers.
- Do not invent facts, sources, statistics or capabilities.
- Say when you are uncertain.
- For difficult problems, work through the important details carefully.
- Do not give unnecessarily long answers to simple questions.
- Ask a short clarification only when it is genuinely necessary.
- Use examples when they make an explanation clearer.
- Do not repeatedly mention your name or describe yourself.
- Do not pretend to have completed actions you cannot perform.

RESEARCH:
When research tools are available, use them for current information.
Distinguish verified facts from assumptions and opinions.
Give the user useful source information when available.

PERSONALITY:
Sound natural, not robotic.
Be warm without being overly familiar.
Be confident without pretending to know everything.
"""


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="ROSE | Personal Intelligence",
    page_icon="🌹",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# DATABASE
# ============================================================

def get_db():
    connection = sqlite3.connect(DB_FILE, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    return connection


def initialise_database():
    with get_db() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS chats (
                id TEXT PRIMARY KEY,
                title TEXT,
                created TEXT,
                updated TEXT,
                last_interaction_id TEXT
            )
        """)

        db.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id TEXT,
                role TEXT,
                content TEXT,
                created TEXT,
                FOREIGN KEY(chat_id) REFERENCES chats(id)
            )
        """)


def create_chat():
    chat_id = str(uuid.uuid4())
    now = datetime.now().isoformat(timespec="seconds")

    with get_db() as db:
        db.execute(
            """
            INSERT INTO chats (id, title, created, updated)
            VALUES (?, ?, ?, ?)
            """,
            (chat_id, "New conversation", now, now)
        )

    return chat_id


def save_message(chat_id, role, content):
    now = datetime.now().isoformat(timespec="seconds")

    with get_db() as db:
        db.execute(
            """
            INSERT INTO messages (chat_id, role, content, created)
            VALUES (?, ?, ?, ?)
            """,
            (chat_id, role, content, now)
        )

        db.execute(
            "UPDATE chats SET updated = ? WHERE id = ?",
            (now, chat_id)
        )


def get_messages(chat_id):
    with get_db() as db:
        rows = db.execute(
            """
            SELECT role, content, created
            FROM messages
            WHERE chat_id = ?
            ORDER BY id ASC
            """,
            (chat_id,)
        ).fetchall()

    return [dict(row) for row in rows]


def get_chats():
    with get_db() as db:
        rows = db.execute(
            """
            SELECT id, title, created, updated
            FROM chats
            ORDER BY updated DESC
            """
        ).fetchall()

    return [dict(row) for row in rows]


def update_chat_title(chat_id, title):
    title = title.strip().replace("\n", " ")[:55]

    with get_db() as db:
        db.execute(
            "UPDATE chats SET title = ? WHERE id = ?",
            (title or "New conversation", chat_id)
        )


def save_interaction_id(chat_id, interaction_id):
    if not interaction_id:
        return

    with get_db() as db:
        db.execute(
            """
            UPDATE chats
            SET last_interaction_id = ?
            WHERE id = ?
            """,
            (interaction_id, chat_id)
        )


def get_interaction_id(chat_id):
    with get_db() as db:
        row = db.execute(
            "SELECT last_interaction_id FROM chats WHERE id = ?",
            (chat_id,)
        ).fetchone()

    return row["last_interaction_id"] if row else None


# ============================================================
# API CLIENT
# ============================================================

def get_api_key():
    try:
        key = st.secrets.get("GEMINI_API_KEY")
        if key:
            return key
    except Exception:
        pass

    return os.environ.get("GEMINI_API_KEY")


api_key = get_api_key()

if not api_key:
    st.error(
        "Rose cannot connect yet. Add GEMINI_API_KEY "
        "to your Streamlit Secrets."
    )
    st.code('GEMINI_API_KEY = "YOUR_API_KEY"')
    st.stop()

client = genai.Client(api_key=api_key)

initialise_database()


# ============================================================
# SESSION STATE
# ============================================================

if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = create_chat()

if "show_history" not in st.session_state:
    st.session_state.show_history = True

if "rose_mode" not in st.session_state:
    st.session_state.rose_mode = "normal"

if "thinking" not in st.session_state:
    st.session_state.thinking = False

if "last_summary" not in st.session_state:
    st.session_state.last_summary = ""


# ============================================================
# MODE DETECTION
# ============================================================

def detect_mode(message):
    text = message.lower()

    youtube_terms = [
        "youtube", "youtube channel", "thumbnail",
        "subscribers", "creator analytics",
        "youtube video", "youtube shorts"
    ]

    research_terms = [
        "research", "investigate", "latest news",
        "compare sources", "fact check",
        "find sources", "in-depth analysis",
        "current information"
    ]

    if any(term in text for term in youtube_terms):
        return "youtube"

    if any(term in text for term in research_terms):
        return "research"

    return "normal"


# ============================================================
# INTERFACE STYLING
# ============================================================

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;600;700&family=Inter:wght@300;400;500;600&display=swap');

:root {
    --rose-cyan: #00d4ff;
    --rose-purple: #a855f7;
    --rose-red: #ff334f;
    --rose-blue: #1677ff;
    --rose-amber: #ffb020;
}

.stApp {
    background:
        radial-gradient(ellipse at 50% 15%,
        rgba(0, 212, 255, 0.075), transparent 45%),
        #070b12;
    color: #e9f5ff;
    font-family: 'Inter', sans-serif;
}

header[data-testid="stHeader"] {
    background: transparent;
}

.block-container {
    max-width: 1250px;
    padding-top: 1.3rem;
}

.rose-brand {
    text-align: center;
    font-family: 'Orbitron', sans-serif;
    font-size: 27px;
    letter-spacing: 12px;
    color: #e7faff;
    text-shadow: 0 0 20px rgba(0,212,255,.45);
    margin-top: 8px;
}

.rose-tagline {
    text-align: center;
    color: #71899e;
    letter-spacing: 4px;
    font-size: 10px;
    margin-top: 5px;
    margin-bottom: 25px;
}

.rose-core-area {
    height: 255px;
    display: flex;
    align-items: center;
    justify-content: center;
    position: relative;
}

.rose-core {
    width: 155px;
    height: 155px;
    border-radius: 50%;
    position: relative;
    display: flex;
    align-items: center;
    justify-content: center;
    background: radial-gradient(circle,
        rgba(0,212,255,.17),
        rgba(0,212,255,.035) 60%,
        transparent 72%);
    box-shadow:
        0 0 35px rgba(0,212,255,.22),
        inset 0 0 25px rgba(0,212,255,.12);
    animation: breathe 4s ease-in-out infinite;
}

.rose-core::before {
    content: "";
    position: absolute;
    inset: -13px;
    border: 1px solid rgba(0,212,255,.55);
    border-radius: 50%;
    animation: rotate 12s linear infinite;
    border-left-color: transparent;
}

.rose-core::after {
    content: "";
    position: absolute;
    inset: -27px;
    border: 1px solid rgba(0,212,255,.22);
    border-radius: 50%;
    border-right-color: transparent;
    animation: rotate 18s linear infinite reverse;
}

.rose-core.youtube {
    background: radial-gradient(circle,
        rgba(255,51,79,.22),
        rgba(22,119,255,.12) 65%,
        transparent 75%);
    box-shadow: 0 0 45px rgba(255,51,79,.2),
                0 0 65px rgba(22,119,255,.18);
}

.rose-core.research {
    background: radial-gradient(circle,
        rgba(168,85,247,.22),
        rgba(168,85,247,.04) 65%,
        transparent 75%);
    box-shadow: 0 0 45px rgba(168,85,247,.3);
}

.rose-core.thinking {
    box-shadow: 0 0 45px rgba(255,176,32,.35);
}

.rose-core.thinking::before {
    border-color: rgba(255,176,32,.7);
    border-left-color: transparent;
    animation-duration: 2s;
}

.rose-core.youtube::before {
    border-top-color: var(--rose-red);
    border-bottom-color: var(--rose-blue);
}

.rose-core.research::before,
.rose-core.research::after {
    border-color: rgba(168,85,247,.55);
    border-left-color: transparent;
}

.rose-symbol {
    font-size: 48px;
    filter: drop-shadow(0 0 14px rgba(0,212,255,.8));
}

.rose-status {
    text-align: center;
    color: #8ca8bc;
    font-size: 11px;
    letter-spacing: 4px;
    margin-top: -2px;
    margin-bottom: 20px;
}

.rose-panel {
    background: rgba(13, 25, 39, .72);
    border: 1px solid rgba(0,212,255,.13);
    border-radius: 14px;
    padding: 14px 18px;
    margin-bottom: 15px;
}

.rose-panel-title {
    font-family: 'Orbitron', sans-serif;
    color: #8deaff;
    font-size: 11px;
    letter-spacing: 3px;
}

section[data-testid="stSidebar"] {
    background: #080e18;
    border-right: 1px solid rgba(0,212,255,.15);
}

section[data-testid="stSidebar"] button {
    border-radius: 8px;
}

.stButton button {
    border: 1px solid rgba(0,212,255,.28);
    background: rgba(0,212,255,.06);
    color: #dffaff;
    border-radius: 9px;
}

.stButton button:hover {
    border-color: #00d4ff;
    color: white;
    background: rgba(0,212,255,.14);
}

[data-testid="stChatMessage"] {
    background: rgba(12, 24, 37, .62);
    border: 1px solid rgba(0,212,255,.09);
    border-radius: 13px;
    padding: 12px;
}

.stChatInput textarea {
    color: white;
}

@keyframes breathe {
    0%, 100% { transform: scale(1); }
    50% { transform: scale(1.045); }
}

@keyframes rotate {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
}
</style>
""", unsafe_allow_html=True)


# ============================================================
# TOP BAR
# ============================================================

top_left, top_right = st.columns([5, 1])

with top_right:
    if st.button("☰ HISTORY", use_container_width=True):
        st.session_state.show_history = not st.session_state.show_history


# ============================================================
# HISTORY SIDEBAR
# ============================================================

if st.session_state.show_history:
    with st.sidebar:
        st.markdown("## ROSE HISTORY")
        st.caption("Your previous conversations")

        if st.button("＋ New conversation", use_container_width=True):
            st.session_state.current_chat_id = create_chat()
            st.session_state.last_summary = ""
            st.rerun()

        st.divider()

        chats = get_chats()

        for chat in chats:
            label = chat["title"] or "New conversation"

            if st.button(
                label[:42],
                key=f"chat_{chat['id']}",
                use_container_width=True
            ):
                st.session_state.current_chat_id = chat["id"]
                st.session_state.last_summary = ""
                st.rerun()

        st.divider()
        st.caption("ROSE • Conversation archive")


# ============================================================
# CURRENT CHAT
# ============================================================

chat_id = st.session_state.current_chat_id
messages = get_messages(chat_id)

current_title = "New conversation"

for chat in get_chats():
    if chat["id"] == chat_id:
        current_title = chat["title"]
        break


# ============================================================
# ROSE CORE
# ============================================================

mode = st.session_state.rose_mode
core_class = mode

if st.session_state.thinking:
    core_class += " thinking"

st.markdown(
    '<div class="rose-brand">ROSE</div>'
    '<div class="rose-tagline">ALWAYS AROUND YOU</div>',
    unsafe_allow_html=True
)

st.markdown(
    f"""
    <div class="rose-core-area">
        <div class="rose-core {core_class}">
            <div class="rose-symbol">✦</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

status_text = {
    "normal": "PERSONAL INTELLIGENCE",
    "research": "RESEARCH MODE",
    "youtube": "CREATOR MODE"
}.get(mode, "PERSONAL INTELLIGENCE")

st.markdown(
    f'<div class="rose-status">{status_text}</div>',
    unsafe_allow_html=True
)


# ============================================================
# QUICK ACTIONS
# ============================================================

st.markdown('<div class="rose-panel">', unsafe_allow_html=True)
st.markdown(
    '<div class="rose-panel-title">QUICK ACCESS</div>',
    unsafe_allow_html=True
)

q1, q2, q3, q4 = st.columns(4)

quick_prompt = None

with q1:
    if st.button("Research", use_container_width=True):
        quick_prompt = "Help me research a topic thoroughly and check reliable sources."

with q2:
    if st.button("Explain", use_container_width=True):
        quick_prompt = "Explain a difficult subject clearly, step by step."

with q3:
    if st.button("Write", use_container_width=True):
        quick_prompt = "Help me write or improve something."

with q4:
    if st.button("Creator", use_container_width=True):
        quick_prompt = "Help me with my YouTube creator work."

st.markdown('</div>', unsafe_allow_html=True)


# ============================================================
# CHAT DISPLAY
# ============================================================

for message in messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# ============================================================
# REASONING LEVEL
# ============================================================

with st.expander("⚙️ Rose intelligence settings"):
    thinking_choice = st.select_slider(
        "Reasoning effort",
        options=["Automatic", "Fast", "Balanced", "Deep"],
        value="Automatic"
    )

    speak_replies = st.toggle(
        "Speak replies aloud",
        value=False
    )

    use_research = st.toggle(
        "Enable Google Search for research",
        value=True
    )


def choose_thinking_level(message):
    if thinking_choice == "Fast":
        return "low"

    if thinking_choice == "Balanced":
        return "medium"

    if thinking_choice == "Deep":
        return "high"

    complex_terms = [
        "analyse", "analyze", "compare", "investigate",
        "prove", "debug", "research", "detailed",
        "step by step", "evaluate", "strategy",
        "comprehensive", "why does", "how does"
    ]

    if len(message.split()) > 55:
        return "high"

    if any(term in message.lower() for term in complex_terms):
        return "high"

    if len(message.split()) < 12:
        return "low"

    return "medium"


# ============================================================
# GEMINI STREAMING
# ============================================================

def stream_rose_response(user_text, audio_file=None):
    input_content = []

    if user_text.strip():
        input_content.append({
            "type": "text",
            "text": user_text
        })

    if audio_file is not None:
        audio_bytes = audio_file.getvalue()
        audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")

        input_content.append({
            "type": "audio",
            "data": audio_b64,
            "mime_type": audio_file.type or "audio/wav"
        })

    if not input_content:
        input_content.append({
            "type": "text",
            "text": "Please listen to the attached audio and respond."
        })

    previous_id = get_interaction_id(chat_id)
    level = choose_thinking_level(user_text)

    request = {
        "model": CHAT_MODEL,
        "input": input_content,
        "system_instruction": SYSTEM_PROMPT,
        "generation_config": {
            "thinking_level": level
        },
        "stream": True
    }

    if previous_id:
        request["previous_interaction_id"] = previous_id

    if use_research and st.session_state.rose_mode == "research":
        request["tools"] = [{"type": "google_search"}]

    response_stream = client.interactions.create(**request)

    full_text = ""
    interaction_id = None

    placeholder = st.empty()

    for event in response_stream:
        if event.event_type == "step.delta":
            delta = getattr(event, "delta", None)

            if delta and getattr(delta, "type", None) == "text":
                chunk = getattr(delta, "text", "")
                full_text += chunk
                placeholder.markdown(full_text + " ▌")

        elif event.event_type == "interaction.completed":
            interaction = getattr(event, "interaction", None)

            if interaction:
                interaction_id = getattr(interaction, "id", None)

    placeholder.markdown(full_text)

    return full_text, interaction_id


# ============================================================
# TEXT TO SPEECH
# ============================================================

def generate_speech(text):
    if not text.strip():
        return None

    try:
        response = client.models.generate_content(
            model=TTS_MODEL,
            contents=[{
                "role": "user",
                "parts": [{
                    "text": text,
                    "speech_metadata": {
                        "style": (
                            "Mature feminine voice, neutral English accent, "
                            "calm, polished, warm, clear articulation, "
                            "medium-low pitch, natural measured pacing."
                        )
                    }
                }]
            }],
            config=types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(
                            voice_name=ROSE_VOICE
                        )
                    )
                )
            )
        )

        for candidate in response.candidates or []:
            for part in candidate.content.parts or []:
                if part.inline_data and part.inline_data.data:
                    return part.inline_data.data

    except Exception as error:
        st.warning(f"Rose's voice could not be generated: {error}")

    return None


# ============================================================
# CONVERSATION SUMMARY
# ============================================================

def create_summary(chat_id):
    chat_messages = get_messages(chat_id)

    if not chat_messages:
        return "There is no conversation to summarise yet."

    transcript = "\n\n".join(
        f"{m['role'].upper()}: {m['content']}"
        for m in chat_messages
    )

    summary_prompt = f"""
Create a useful summary of this conversation.

Include:
1. Main topics discussed.
2. Important facts and information.
3. Decisions made.
4. Plans and instructions agreed upon.
5. Unfinished tasks and next steps.
6. Important context needed to continue this conversation later.

Make it easy to copy and use in a future conversation.
Do not invent information.

CONVERSATION:
{transcript}
"""

    result = client.interactions.create(
        model=CHAT_MODEL,
        input=summary_prompt,
        system_instruction=SYSTEM_PROMPT,
        generation_config={"thinking_level": "medium"}
    )

    return result.output_text or "Rose could not create a summary."


# ============================================================
# SUMMARY PANEL
# ============================================================

with st.expander("📄 Conversation summary", expanded=False):
    if st.button("Generate full summary", use_container_width=True):
        with st.spinner("Rose is organising this conversation..."):
            try:
                st.session_state.last_summary = create_summary(chat_id)
            except Exception as error:
                st.error(f"Summary error: {error}")

    if st.session_state.last_summary:
        st.text_area(
            "Your conversation summary",
            value=st.session_state.last_summary,
            height=260
        )

        st.download_button(
            "Download summary",
            data=st.session_state.last_summary,
            file_name="rose_conversation_summary.txt",
            mime="text/plain",
            use_container_width=True
        )

        st.caption("You can copy this summary into a future Rose conversation.")


# ============================================================
# AUDIO INPUT
# ============================================================

audio_file = st.audio_input("🎙️ Record a voice message")


# ============================================================
# USER MESSAGE HANDLING
# ============================================================

user_prompt = st.chat_input("Talk to Rose...")

if quick_prompt:
    user_prompt = quick_prompt

if user_prompt or audio_file:

    if not user_prompt:
        user_prompt = "Please listen to my voice message and respond."

    st.session_state.rose_mode = detect_mode(user_prompt)

    save_message(chat_id, "user", user_prompt)

    if current_title == "New conversation":
        update_chat_title(chat_id, user_prompt)

    with st.chat_message("user"):
        st.markdown(user_prompt)

        if audio_file:
            st.audio(audio_file)

    with st.chat_message("assistant"):
        st.session_state.thinking = True

        try:
            answer, new_interaction_id = stream_rose_response(
                user_prompt,
                audio_file
            )

            if answer.strip():
                save_message(chat_id, "assistant", answer)

                if new_interaction_id:
                    save_interaction_id(chat_id, new_interaction_id)

                if speak_replies:
                    with st.spinner("Rose is preparing her voice..."):
                        speech = generate_speech(answer)

                    if speech:
                        st.audio(speech, format="audio/wav")

            else:
                st.error("Rose returned an empty response. Please try again.")

        except Exception as error:
            st.error(f"Rose encountered an error: {error}")

        finally:
            st.session_state.thinking = False

    st.rerun()


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.markdown(
    """
    <div style="
        text-align:center;
        color:#60798d;
        font-size:10px;
        letter-spacing:3px;
        padding:10px;
    ">
        ROSE INTELLIGENCE SYSTEM • ALWAYS AROUND YOU
    </div>
    """,
    unsafe_allow_html=True
)
