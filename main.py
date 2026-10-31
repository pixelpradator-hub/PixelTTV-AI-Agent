
import os
import json
import html
import uuid
from pathlib import Path
from datetime import datetime

import streamlit as st
from google import genai
from google.genai import types


# ==========================================
# AURA — PERSONAL INTELLIGENCE SYSTEM
# ==========================================

APP_NAME = "AURA"
CHAT_MODEL = "gemini-3.8-flash"
TTS_MODEL = "gemini-3.8-flash-tts"
AURA_VOICE = "Algieba"

DATA_FILE = Path("aura_data.json")

SYSTEM_PROMPT = """
You are Aura, a personal AI assistant.

IDENTITY:
- Your name is Aura.
- You are female and use she/her pronouns.
- You are intelligent, composed, sophisticated and confident.
- Your personality is warm, natural and subtly humorous.
- Your voice should sound mature, calm and articulate.
- Use clear, natural English.

BEHAVIOUR:
- Be helpful, accurate and thoughtful.
- Keep ordinary replies concise.
- Explain complicated subjects clearly.
- Never pretend to have performed an action you did not perform.
- Never claim access to devices, accounts or information unless actually connected.
- Remember relevant details from the conversation context supplied to you.
- Address the user naturally without overusing their name.

You are Aura. You are not Jarvis.
"""


# ==========================================
# PAGE CONFIGURATION
# ==========================================

st.set_page_config(
    page_title="AURA | Personal Intelligence",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ==========================================
# STYLING
# ==========================================

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;600;700&family=Inter:wght@300;400;500;600&display=swap');

:root {
    --cyan: #00d4ff;
    --violet: #865dff;
    --amber: #ffbd59;
    --red: #ff5364;
    --background: #050914;
    --panel: rgba(12, 24, 43, 0.72);
}

html, body, [data-testid="stAppViewContainer"] {
    background:
        radial-gradient(ellipse at 50% 42%, #10203a 0%, #080f20 42%, #030711 100%);
    color: #e9f7ff;
    font-family: 'Inter', sans-serif;
}

[data-testid="stHeader"] {
    background: transparent;
}

[data-testid="stSidebar"] {
    background: rgba(4, 11, 23, 0.96);
    border-right: 1px solid rgba(0,212,255,0.13);
}

.block-container {
    padding-top: 1.4rem;
    max-width: 1400px;
}

.aura-brand {
    font-family: 'Orbitron', sans-serif;
    text-align: center;
    letter-spacing: 0.65em;
    padding-left: 0.65em;
    font-size: 22px;
    font-weight: 500;
    color: #e8fbff;
    text-shadow: 0 0 12px rgba(0,212,255,.65);
}

.aura-tagline {
    text-align: center;
    font-size: 10px;
    letter-spacing: 4px;
    color: #7396ad;
    margin-top: 7px;
    text-transform: uppercase;
}

.status-line {
    text-align: center;
    font-family: 'Orbitron', sans-serif;
    font-size: 10px;
    letter-spacing: 3px;
    margin-top: 26px;
    color: var(--cyan);
}

.core-wrap {
    height: 340px;
    display: flex;
    align-items: center;
    justify-content: center;
    position: relative;
    overflow: hidden;
}

.core {
    width: 230px;
    height: 230px;
    position: relative;
    display: flex;
    align-items: center;
    justify-content: center;
}

.halo {
    position: absolute;
    inset: 35px;
    border-radius: 50%;
    background: radial-gradient(circle,
        rgba(0,212,255,.28) 0%,
        rgba(134,93,255,.19) 35%,
        rgba(0,212,255,.04) 65%,
        transparent 75%);
    filter: blur(12px);
    animation: breathe 4s ease-in-out infinite;
}

.ring {
    position: absolute;
    border-radius: 50%;
    border: 1px solid rgba(0,212,255,.5);
    box-shadow: 0 0 14px rgba(0,212,255,.12);
}

.ring.one {
    inset: 18px;
    border-right-color: rgba(134,93,255,.9);
    animation: rotate 17s linear infinite;
}

.ring.two {
    inset: 34px;
    border-style: dashed;
    border-color: rgba(134,93,255,.55);
    animation: rotate-reverse 23s linear infinite;
}

.ring.three {
    inset: 51px;
    border-top-color: rgba(0,212,255,.9);
    border-bottom-color: rgba(0,212,255,.12);
    animation: rotate 11s linear infinite;
}

.ring.four {
    inset: 66px;
    border-color: rgba(0,212,255,.25);
    box-shadow: 0 0 28px rgba(0,212,255,.2);
}

.core-center {
    width: 76px;
    height: 76px;
    border-radius: 50%;
    background: radial-gradient(circle at 35% 30%,
        #e8ffff 0%,
        #64eaff 14%,
        #087ea9 43%,
        #29205c 100%);
    box-shadow:
        0 0 22px rgba(0,212,255,.75),
        0 0 65px rgba(0,212,255,.32),
        0 0 100px rgba(134,93,255,.24);
    animation: breathe 4s ease-in-out infinite;
}

.state-listening .ring {
    border-color: rgba(0,212,255,.9);
    animation-duration: 3s;
}

.state-listening .halo {
    animation: listen 1.2s ease-in-out infinite;
}

.state-thinking .ring.one {
    animation-duration: 2s;
    border-color: var(--amber);
}

.state-thinking .ring.two {
    animation-duration: 3s;
    border-color: rgba(255,189,89,.7);
}

.state-thinking .halo {
    background: radial-gradient(circle,
        rgba(255,189,89,.28),
        rgba(134,93,255,.14),
        transparent 72%);
}

.state-speaking .ring.three {
    animation-duration: 2s;
    border-width: 3px;
}

.state-speaking .halo {
    animation: listen .8s ease-in-out infinite;
}

@keyframes rotate {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
}

@keyframes rotate-reverse {
    from { transform: rotate(360deg); }
    to { transform: rotate(0deg); }
}

@keyframes breathe {
    0%, 100% { transform: scale(.94); opacity: .72; }
    50% { transform: scale(1.08); opacity: 1; }
}

@keyframes listen {
    0%, 100% { transform: scale(.9); opacity: .65; }
    50% { transform: scale(1.18); opacity: 1; }
}

.hud-panel {
    background: var(--panel);
    border: 1px solid rgba(0,212,255,.16);
    border-radius: 12px;
    padding: 16px;
    min-height: 104px;
    backdrop-filter: blur(12px);
}

.hud-label {
    color: #6c9ab5;
    font-size: 9px;
    letter-spacing: 2px;
    text-transform: uppercase;
}

.hud-value {
    color: #dffaff;
    font-size: 17px;
    margin-top: 9px;
    font-weight: 500;
}

.hud-small {
    color: #7293a9;
    font-size: 11px;
    margin-top: 5px;
}

.subtitle {
    text-align: center;
    color: #d9faff;
    font-size: 14px;
    line-height: 1.7;
    max-width: 650px;
    margin: 0 auto 18px auto;
    text-shadow: 0 0 10px rgba(0,212,255,.2);
}

.section-label {
    color: #70a1bd;
    font-family: 'Orbitron', sans-serif;
    font-size: 10px;
    letter-spacing: 3px;
    margin: 20px 0 12px 0;
}

div.stButton > button {
    background: rgba(0,212,255,.055);
    border: 1px solid rgba(0,212,255,.28);
    color: #c8f6ff;
    border-radius: 9px;
    transition: all .2s ease;
}

div.stButton > button:hover {
    background: rgba(0,212,255,.16);
    border-color: var(--cyan);
    color: white;
    box-shadow: 0 0 18px rgba(0,212,255,.12);
}

[data-testid="stChatInput"] {
    border-color: rgba(0,212,255,.3);
}

[data-testid="stChatMessage"] {
    background: rgba(8,20,37,.58);
    border: 1px solid rgba(0,212,255,.08);
    border-radius: 12px;
}

div[data-testid="stAudioInput"] {
    border: 1px solid rgba(0,212,255,.22);
    border-radius: 10px;
    padding: 8px;
}

hr {
    border-color: rgba(0,212,255,.12);
}

.footer {
    text-align: center;
    color: #45677e;
    font-size: 9px;
    letter-spacing: 2px;
    padding: 25px 0 5px 0;
}
</style>
""", unsafe_allow_html=True)


# ==========================================
# DATA STORAGE
# ==========================================

def load_data():
    if DATA_FILE.exists():
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as file:
                return json.load(file)
        except Exception:
            pass

    return {
        "messages": [],
        "memories": [],
        "tasks": []
    }


def save_data():
    data = {
        "messages": st.session_state.messages,
        "memories": st.session_state.memories,
        "tasks": st.session_state.tasks
    }

    try:
        with open(DATA_FILE, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=2, ensure_ascii=False)
    except Exception:
        pass


if "aura_data_loaded" not in st.session_state:
    saved = load_data()

    st.session_state.messages = saved.get("messages", [])
    st.session_state.memories = saved.get("memories", [])
    st.session_state.tasks = saved.get("tasks", [])

    st.session_state.aura_data_loaded = True

if "voice_enabled" not in st.session_state:
    st.session_state.voice_enabled = True

if "last_audio" not in st.session_state:
    st.session_state.last_audio = None

if "core_state" not in st.session_state:
    st.session_state.core_state = "idle"

if "subtitle" not in st.session_state:
    st.session_state.subtitle = "Always around you."


# ==========================================
# GEMINI CONNECTION
# ==========================================

def get_api_key():
    try:
        return st.secrets.get("GEMINI_API_KEY") or st.secrets.get("GOOGLE_API_KEY")
    except Exception:
        return os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")


@st.cache_resource
def get_client(api_key):
    return genai.Client(api_key=api_key)


def get_client_or_error():
    api_key = get_api_key()

    if not api_key:
        st.error(
            "Aura's Gemini key has not been configured. "
            "Add GEMINI_API_KEY in your app's Secrets."
        )
        return None

    try:
        return get_client(api_key)
    except Exception as error:
        st.error(f"Could not connect to Gemini: {error}")
        return None


# ==========================================
# TIME AND GREETING
# ==========================================

def get_greeting():
    hour = datetime.now().hour

    if hour < 12:
        return "Good morning"
    elif hour < 17:
        return "Good afternoon"
    return "Good evening"


def get_clock():
    return datetime.now().strftime("%H:%M:%S")


# ==========================================
# AURA MEMORY CONTEXT
# ==========================================

def memory_context():
    memories = st.session_state.memories[-20:]

    if not memories:
        return "No saved personal notes yet."

    return "\n".join(f"- {item}" for item in memories)


# ==========================================
# CHAT RESPONSE
# ==========================================

def ask_aura(user_message):
    client = get_client_or_error()

    if client is None:
        return "I can't connect to my intelligence system right now."

    recent_messages = st.session_state.messages[-16:]

    conversation = []

    for message in recent_messages:
        role = "User" if message["role"] == "user" else "Aura"
        conversation.append(f"{role}: {message['content']}")

    conversation_text = "\n".join(conversation)

    prompt = f"""
{SYSTEM_PROMPT}

SAVED USER NOTES:
{memory_context()}

RECENT CONVERSATION:
{conversation_text}

NEW MESSAGE:
User: {user_message}

Respond as Aura.
"""

    try:
        response = client.models.generate_content(
            model=CHAT_MODEL,
            contents=prompt
        )

        answer = response.text

        if not answer:
            return "I received an empty response. Please try again."

        return answer.strip()

    except Exception as error:
        return (
            "I encountered a connection problem while thinking. "
            f"Technical detail: {error}"
        )


# ==========================================
# TEXT TO SPEECH
# ==========================================

def generate_speech(text):
    client = get_client_or_error()

    if client is None:
        return None

    try:
        response = client.models.generate_content(
            model=TTS_MODEL,
            contents=text,
            config=types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(
                            voice_name=AURA_VOICE
                        )
                    )
                )
            )
        )

        for part in response.parts:
            if part.inline_data:
                return part.inline_data.data

        return None

    except Exception as error:
        st.warning(f"Voice generation is unavailable: {error}")
        return None


# ==========================================
# AUDIO TRANSCRIPTION
# ==========================================

def transcribe_audio(audio_file):
    client = get_client_or_error()

    if client is None:
        return None

    try:
        audio_bytes = audio_file.getvalue()

        mime_type = audio_file.type or "audio/wav"

        response = client.models.generate_content(
            model=CHAT_MODEL,
            contents=[
                "Transcribe the spoken words in this audio. "
                "Return only the transcription.",
                types.Part.from_bytes(
                    data=audio_bytes,
                    mime_type=mime_type
                )
            ]
        )

        return response.text.strip() if response.text else None

    except Exception as error:
        st.error(f"I couldn't understand that recording: {error}")
        return None


# ==========================================
# MESSAGE HANDLING
# ==========================================

def process_message(user_message):
    user_message = user_message.strip()

    if not user_message:
        return

    st.session_state.messages.append({
        "role": "user",
        "content": user_message,
        "id": str(uuid.uuid4())
    })

    st.session_state.core_state = "thinking"
    st.session_state.subtitle = "Processing your request..."

    with st.spinner("Aura is thinking..."):
        answer = ask_aura(user_message)

    st.session_state.messages.append({
        "role": "assistant",
        "content": answer,
        "id": str(uuid.uuid4())
    })

    st.session_state.subtitle = answer
    st.session_state.core_state = "speaking"

    if st.session_state.voice_enabled:
        audio = generate_speech(answer)

        if audio:
            st.session_state.last_audio = audio

    st.session_state.core_state = "idle"
    save_data()


# ==========================================
# SIDEBAR
# ==========================================

with st.sidebar:
    st.markdown(
        '<div class="aura-brand">AURA</div>',
        unsafe_allow_html=True
    )

    st.caption("PERSONAL INTELLIGENCE SYSTEM")

    st.divider()

    st.markdown("### System controls")

    st.session_state.voice_enabled = st.toggle(
        "Voice replies",
        value=st.session_state.voice_enabled
    )

    if st.button("New conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.last_audio = None
        st.session_state.subtitle = "A fresh conversation."
        save_data()
        st.rerun()

    st.divider()

    st.markdown("### Conversation history")

    if st.session_state.messages:
        for message in st.session_state.messages[-8:]:
            if message["role"] == "user":
                st.caption("YOU")
            else:
                st.caption("AURA")

            st.write(message["content"][:180])
    else:
        st.caption("No conversations yet.")

    st.divider()

    st.markdown("### Saved memory")

    if st.session_state.memories:
        for memory in st.session_state.memories:
            st.write("• " + memory)
    else:
        st.caption("No saved notes yet.")

    new_memory = st.text_input(
        "Add a memory",
        placeholder="Something Aura should remember..."
    )

    if st.button("Save memory", use_container_width=True):
        if new_memory.strip():
            st.session_state.memories.append(new_memory.strip())
            save_data()
            st.rerun()

    st.divider()

    st.caption("AURA SYSTEM • DEVELOPMENT BUILD")


# ==========================================
# MAIN HEADER
# ==========================================

st.markdown(
    '<div class="aura-brand">AURA</div>'
    '<div class="aura-tagline">Always around you</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="status-line">AURA ONLINE • SYSTEM READY</div>',
    unsafe_allow_html=True
)


# ==========================================
# HUD PANELS
# ==========================================

left, center, right = st.columns([1, 2, 1])

with left:
    st.markdown(f"""
    <div class="hud-panel">
        <div class="hud-label">Local system time</div>
        <div class="hud-value">{get_clock()}</div>
        <div class="hud-small">Device time</div>
    </div>
    """, unsafe_allow_html=True)

with center:
    st.markdown("""
    <div class="hud-panel" style="text-align:center;">
        <div class="hud-label">System status</div>
        <div class="hud-value">ALL SYSTEMS READY</div>
        <div class="hud-small">Gemini intelligence connection</div>
    </div>
    """, unsafe_allow_html=True)

with right:
    st.markdown(f"""
    <div class="hud-panel">
        <div class="hud-label">Date</div>
        <div class="hud-value">{datetime.now().strftime("%d %b %Y")}</div>
        <div class="hud-small">Local device date</div>
    </div>
    """, unsafe_allow_html=True)


# ==========================================
# AURA CORE
# ==========================================

state = st.session_state.core_state

state_class = {
    "idle": "state-idle",
    "listening": "state-listening",
    "thinking": "state-thinking",
    "speaking": "state-speaking"
}.get(state, "state-idle")

st.markdown(f"""
<div class="core-wrap">
    <div class="core {state_class}">
        <div class="halo"></div>
        <div class="ring one"></div>
        <div class="ring two"></div>
        <div class="ring three"></div>
        <div class="ring four"></div>
        <div class="core-center"></div>
    </div>
</div>
""", unsafe_allow_html=True)

state_label = {
    "idle": "STANDBY",
    "listening": "LISTENING",
    "thinking": "PROCESSING",
    "speaking": "SPEAKING"
}.get(state, "STANDBY")

st.markdown(
    f'<div class="status-line">{state_label}</div>',
    unsafe_allow_html=True
)

subtitle = html.escape(st.session_state.subtitle)

st.markdown(
    f'<div class="subtitle">{subtitle}</div>',
    unsafe_allow_html=True
)


# ==========================================
# QUICK ACTIONS
# ==========================================

st.markdown(
    '<div class="section-label">QUICK ACCESS</div>',
    unsafe_allow_html=True
)

action1, action2, action3 = st.columns(3)

with action1:
    schedule_clicked = st.button(
        "◷  Schedule",
        use_container_width=True
    )

with action2:
    search_clicked = st.button(
        "⌕  Search",
        use_container_width=True
    )

with action3:
    devices_clicked = st.button(
        "⌘  Devices",
        use_container_width=True
    )

if schedule_clicked:
    process_message("Help me organise my schedule.")

if search_clicked:
    process_message("Help me research something. Ask what I want to search for.")

if devices_clicked:
    process_message(
        "Explain what device integrations are available. "
        "Do not claim to control devices that are not connected."
    )


# ==========================================
# CHAT HISTORY
# ==========================================

st.markdown(
    '<div class="section-label">CONVERSATION</div>',
    unsafe_allow_html=True
)

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# ==========================================
# TEXT INPUT
# ==========================================

user_prompt = st.chat_input("Speak to Aura...")

if user_prompt:
    process_message(user_prompt)
    st.rerun()


# ==========================================
# VOICE INPUT
# ==========================================

st.markdown(
    '<div class="section-label">VOICE CHANNEL</div>',
    unsafe_allow_html=True
)

st.caption(
    "Record a message and Aura will transcribe and respond. "
    "Microphone access is required."
)

audio_input = st.audio_input("Speak to Aura")

if audio_input is not None:
    audio_id = (
        str(audio_input.size)
        + str(audio_input.type)
    )

    if st.session_state.get("processed_audio_id") != audio_id:
        st.session_state.core_state = "listening"

        with st.spinner("Listening to your message..."):
            transcription = transcribe_audio(audio_input)

        st.session_state.processed_audio_id = audio_id

        if transcription:
            st.success("You said: " + transcription)
            process_message(transcription)
            st.rerun()


# ==========================================
# AUDIO REPLY
# ==========================================

if st.session_state.last_audio:
    st.markdown(
        '<div class="section-label">AURA VOICE RESPONSE</div>',
        unsafe_allow_html=True
    )

    st.audio(
        st.session_state.last_audio,
        format="audio/wav",
        autoplay=True
    )


# ==========================================
# FOOTER
# ==========================================

st.markdown("""
<div class="footer">
    A U R A &nbsp; • &nbsp; PERSONAL INTELLIGENCE
    <br><br>
    ALWAYS AROUND YOU
</div>
""", unsafe_allow_html=True)
