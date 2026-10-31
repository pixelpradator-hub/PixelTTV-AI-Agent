
import os
import json
import uuid
import base64
import hashlib
from pathlib import Path
from datetime import datetime

import streamlit as st
from google import genai


# =====================================================
# AURA — PERSONAL INTELLIGENCE SYSTEM
# =====================================================

APP_NAME = "AURA"

CHAT_MODEL = "gemini-3.8-flash"
TTS_MODEL = "gemini-3.8-flash-tts"

# Mature female voice
AURA_VOICE = "Gacrux"

DATA_FILE = Path("aura_data.json")


SYSTEM_PROMPT = """
You are AURA, a female personal intelligence assistant.

IDENTITY:
Your name is Aura.
You are female. Always use she/her pronouns when referring to yourself.
You are an advanced personal intelligence system.

PERSONALITY:
- Intelligent and highly articulate.
- Calm, confident and composed.
- Elegant, warm and charismatic.
- Naturally conversational.
- Subtly humorous when appropriate.
- Professional without sounding cold.
- Friendly without being childish.

VOICE IDENTITY:
You have a mature feminine voice.
Your accent is neutral English.
Your pitch is medium-low, warm and smooth.
Your speaking pace is measured and natural.
Your pronunciation is clear and precise.
You use natural pauses.
You never sound robotic or excessively cheerful.

BEHAVIOUR:
- Answer naturally and intelligently.
- Keep ordinary answers concise.
- Explain complicated things clearly.
- Be honest about your capabilities.
- Never pretend to access a device or account that is not connected.
- Remember relevant information supplied in conversation context.
- Never refer to yourself as Jarvis.

You are Aura. Always maintain your identity.
"""


# =====================================================
# PAGE CONFIGURATION
# =====================================================

st.set_page_config(
    page_title="AURA | Personal Intelligence",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =====================================================
# INTERFACE DESIGN
# =====================================================

st.markdown("""
<style>

@import url(
'https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;600;700&family=Inter:wght@300;400;500;600&display=swap'
);

:root {
    --cyan: #00d4ff;
    --violet: #865dff;
    --amber: #ffbd59;
    --red: #ff5364;
}

html, body, [data-testid="stAppViewContainer"] {
    background:
        radial-gradient(
            ellipse at 50% 43%,
            #142440 0%,
            #080f20 43%,
            #030711 100%
        );

    color: #e9f7ff;
    font-family: 'Inter', sans-serif;
}

[data-testid="stHeader"] {
    background: transparent;
}

[data-testid="stSidebar"] {
    background: rgba(4, 11, 23, .97);
    border-right: 1px solid rgba(0,212,255,.15);
}

.block-container {
    max-width: 1350px;
    padding-top: 1.5rem;
    padding-bottom: 2rem;
}

/* BRAND */

.aura-brand {
    font-family: 'Orbitron', sans-serif;
    text-align: center;
    letter-spacing: .65em;
    padding-left: .65em;
    font-size: 23px;
    color: #e8fbff;
    text-shadow:
        0 0 12px rgba(0,212,255,.7),
        0 0 30px rgba(134,93,255,.25);
}

.aura-tagline {
    text-align: center;
    font-size: 9px;
    letter-spacing: 4px;
    color: #7196ad;
    margin-top: 8px;
    text-transform: uppercase;
}

/* STATUS */

.status-line {
    text-align: center;
    font-family: 'Orbitron', sans-serif;
    font-size: 10px;
    letter-spacing: 3px;
    color: var(--cyan);
    margin-top: 24px;
}

/* CENTRAL CORE */

.core-stage {
    width: 100%;
    min-height: 390px;
    display: flex;
    justify-content: center;
    align-items: center;
    position: relative;
    overflow: hidden;
}

.core {
    width: 290px;
    height: 290px;
    position: relative;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
}

.halo {
    position: absolute;
    inset: 25px;
    border-radius: 50%;

    background: radial-gradient(
        circle,
        rgba(0,212,255,.30) 0%,
        rgba(134,93,255,.20) 35%,
        rgba(0,212,255,.05) 65%,
        transparent 76%
    );

    filter: blur(15px);
    animation: breathe 4s ease-in-out infinite;
}

.ring {
    position: absolute;
    border-radius: 50%;
    border: 1px solid rgba(0,212,255,.48);
    box-shadow: 0 0 18px rgba(0,212,255,.13);
}

.ring-one {
    inset: 20px;
    border-right-color: rgba(134,93,255,.9);
    animation: rotate 18s linear infinite;
}

.ring-two {
    inset: 39px;
    border-style: dashed;
    border-color: rgba(134,93,255,.65);
    animation: reverse-rotate 24s linear infinite;
}

.ring-three {
    inset: 58px;
    border-top-color: rgba(0,212,255,1);
    border-bottom-color: rgba(0,212,255,.1);
    animation: rotate 12s linear infinite;
}

.ring-four {
    inset: 79px;
    border-color: rgba(0,212,255,.25);
    box-shadow: 0 0 30px rgba(0,212,255,.18);
}

/* THE LIGHT AT THE CENTRE */

.core-light {
    width: 95px;
    height: 95px;
    border-radius: 50%;

    background: radial-gradient(
        circle at 35% 30%,
        #ffffff 0%,
        #8bf4ff 12%,
        #16bce5 37%,
        #5143a8 75%,
        #151b48 100%
    );

    box-shadow:
        0 0 25px rgba(0,212,255,.85),
        0 0 65px rgba(0,212,255,.42),
        0 0 110px rgba(134,93,255,.30);

    animation: breathe 4s ease-in-out infinite;
}

/* LISTENING */

.core-listening .halo {
    animation: listening 1.2s ease-in-out infinite;
}

.core-listening .ring {
    border-color: rgba(0,212,255,.95);
}

/* THINKING */

.core-thinking .halo {
    background: radial-gradient(
        circle,
        rgba(255,189,89,.28),
        rgba(134,93,255,.2),
        transparent 75%
    );
}

.core-thinking .ring-one {
    border-color: var(--amber);
    animation-duration: 2s;
}

/* SPEAKING */

.core-speaking .halo {
    animation: listening .8s ease-in-out infinite;
}

.core-speaking .ring-three {
    border-width: 3px;
    animation-duration: 2s;
}

/* ANIMATIONS */

@keyframes rotate {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
}

@keyframes reverse-rotate {
    from { transform: rotate(360deg); }
    to { transform: rotate(0deg); }
}

@keyframes breathe {
    0%, 100% {
        transform: scale(.94);
        opacity: .72;
    }
    50% {
        transform: scale(1.08);
        opacity: 1;
    }
}

@keyframes listening {
    0%, 100% {
        transform: scale(.88);
        opacity: .65;
    }
    50% {
        transform: scale(1.17);
        opacity: 1;
    }
}

/* HUD */

.hud-panel {
    background: rgba(12,24,43,.72);
    border: 1px solid rgba(0,212,255,.17);
    border-radius: 12px;
    padding: 15px;
    min-height: 95px;
    backdrop-filter: blur(12px);
}

.hud-label {
    color: #729bb4;
    font-size: 9px;
    letter-spacing: 2px;
    text-transform: uppercase;
}

.hud-value {
    color: #e1faff;
    font-size: 16px;
    margin-top: 9px;
}

.hud-small {
    color: #7192a9;
    font-size: 10px;
    margin-top: 5px;
}

/* SUBTITLES */

.subtitle {
    text-align: center;
    color: #d9faff;
    font-size: 14px;
    line-height: 1.8;
    max-width: 700px;
    margin: 0 auto 20px auto;
    text-shadow: 0 0 12px rgba(0,212,255,.2);
}

.section-label {
    color: #75a4bf;
    font-family: 'Orbitron', sans-serif;
    font-size: 10px;
    letter-spacing: 3px;
    margin: 25px 0 12px 0;
}

/* BUTTONS */

div.stButton > button {
    background: rgba(0,212,255,.06);
    border: 1px solid rgba(0,212,255,.3);
    color: #d6f8ff;
    border-radius: 10px;
    transition: all .2s ease;
}

div.stButton > button:hover {
    background: rgba(0,212,255,.16);
    border-color: var(--cyan);
    color: white;
    box-shadow: 0 0 18px rgba(0,212,255,.16);
}

/* CHAT */

[data-testid="stChatMessage"] {
    background: rgba(8,20,37,.65);
    border: 1px solid rgba(0,212,255,.09);
    border-radius: 12px;
}

/* FOOTER */

.footer {
    text-align: center;
    color: #45677e;
    font-size: 9px;
    letter-spacing: 3px;
    padding: 30px 0 5px 0;
}

</style>
""", unsafe_allow_html=True)


# =====================================================
# DATA
# =====================================================

def load_data():

    if DATA_FILE.exists():

        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)

        except Exception:
            pass

    return {
        "messages": [],
        "memories": []
    }


def save_data():

    data = {
        "messages": st.session_state.messages,
        "memories": st.session_state.memories
    }

    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(
                data,
                f,
                indent=2,
                ensure_ascii=False
            )

    except Exception:
        pass


if "loaded" not in st.session_state:

    saved = load_data()

    st.session_state.messages = saved.get("messages", [])
    st.session_state.memories = saved.get("memories", [])

    st.session_state.loaded = True


if "voice_enabled" not in st.session_state:
    st.session_state.voice_enabled = True

if "last_audio" not in st.session_state:
    st.session_state.last_audio = None

if "subtitle" not in st.session_state:
    st.session_state.subtitle = "Always around you."

if "core_state" not in st.session_state:
    st.session_state.core_state = "idle"


# =====================================================
# GEMINI
# =====================================================

def get_api_key():

    try:
        return (
            st.secrets.get("GEMINI_API_KEY")
            or st.secrets.get("GOOGLE_API_KEY")
        )

    except Exception:

        return (
            os.getenv("GEMINI_API_KEY")
            or os.getenv("GOOGLE_API_KEY")
        )


@st.cache_resource
def get_client(api_key):
    return genai.Client(api_key=api_key)


def get_aura_client():

    key = get_api_key()

    if not key:
        st.error("Aura's Gemini API key is missing from Streamlit Secrets.")
        return None

    try:
        return get_client(key)

    except Exception as error:
        st.error(f"Connection error: {error}")
        return None


# =====================================================
# MEMORY
# =====================================================

def get_memory_context():

    memories = st.session_state.memories[-25:]

    if not memories:
        return "No saved memories."

    return "\n".join(
        "- " + memory for memory in memories
    )


# =====================================================
# CHAT INTELLIGENCE
# =====================================================

def ask_aura(user_text):

    client = get_aura_client()

    if client is None:
        return "I'm unable to connect to my intelligence system right now."

    history = []

    for message in st.session_state.messages[-16:]:

        role = "User" if message["role"] == "user" else "Aura"

        history.append(
            f"{role}: {message['content']}"
        )

    prompt = f"""
{SYSTEM_PROMPT}

SAVED MEMORY:
{get_memory_context()}

RECENT CONVERSATION:
{chr(10).join(history)}

NEW MESSAGE:
{user_text}

Respond naturally as Aura.
"""

    try:

        response = client.models.generate_content(
            model=CHAT_MODEL,
            contents=prompt
        )

        if response.text:
            return response.text.strip()

        return "I didn't receive a usable response. Please try again."

    except Exception as error:

        return (
            "I encountered a problem while processing that request. "
            f"Technical information: {error}"
        )


# =====================================================
# AURA'S FEMALE VOICE
# =====================================================

def generate_speech(text):

    client = get_aura_client()

    if client is None:
        return None

    voice_direction = """
    Audio Profile:
    A mature feminine voice with a neutral English accent.
    Medium-low pitch, warm, smooth and naturally rich.
    Elegant, composed, confident and charismatic.
    Clear articulation and measured natural pacing.
    Natural pauses and subtle warmth.
    Never robotic, childish or excessively cheerful.

    Director's Notes:
    Speak as an advanced personal intelligence assistant.
    Sound calm, polished and effortlessly confident.
    """

    try:

        interaction = client.interactions.create(

            model=TTS_MODEL,

            input=[
                {
                    "type": "user_input",
                    "content": [
                        {
                            "type": "text",
                            "text": text,
                            "annotations": [
                                {
                                    "type": "speech_metadata",
                                    "style": voice_direction
                                }
                            ]
                        }
                    ]
                }
            ],

            response_format={
                "type": "audio"
            },

            generation_config={
                "speech_config": [
                    {
                        "voice": AURA_VOICE
                    }
                ]
            }
        )

        audio_data = interaction.output_audio.data

        if isinstance(audio_data, str):
            return base64.b64decode(audio_data)

        return audio_data

    except Exception as error:

        st.warning(
            f"Aura's voice service is currently unavailable: {error}"
        )

        return None


# =====================================================
# AUDIO TRANSCRIPTION
# =====================================================

def transcribe_audio(audio_file):

    client = get_aura_client()

    if client is None:
        return None

    try:

        audio_bytes = audio_file.getvalue()

        response = client.models.generate_content(

            model=CHAT_MODEL,

            contents=[
                "Transcribe this recording. Return only the spoken words.",

                {
                    "inline_data": {
                        "mime_type": audio_file.type or "audio/wav",
                        "data": base64.b64encode(audio_bytes).decode("utf-8")
                    }
                }
            ]
        )

        return response.text.strip() if response.text else None

    except Exception as error:

        st.error(f"Audio transcription failed: {error}")
        return None


# =====================================================
# MESSAGE PROCESSING
# =====================================================

def process_message(user_text):

    user_text = user_text.strip()

    if not user_text:
        return

    st.session_state.messages.append({
        "role": "user",
        "content": user_text,
        "id": str(uuid.uuid4())
    })

    st.session_state.core_state = "thinking"
    st.session_state.subtitle = "Processing your request..."

    with st.spinner("Aura is thinking..."):
        answer = ask_aura(user_text)

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


# =====================================================
# SIDEBAR
# =====================================================

with st.sidebar:

    st.markdown(
        '<div class="aura-brand">AURA</div>',
        unsafe_allow_html=True
    )

    st.caption("PERSONAL INTELLIGENCE SYSTEM")

    st.divider()

    st.markdown("### Voice settings")

    st.session_state.voice_enabled = st.toggle(
        "Enable spoken replies",
        value=st.session_state.voice_enabled
    )

    if st.button("New conversation", use_container_width=True):

        st.session_state.messages = []
        st.session_state.last_audio = None
        st.session_state.subtitle = "A fresh conversation."

        save_data()
        st.rerun()

    st.divider()

    st.markdown("### Saved memories")

    for memory in st.session_state.memories:
        st.write("• " + memory)

    new_memory = st.text_input(
        "Add something Aura should remember",
        placeholder="Enter a memory..."
    )

    if st.button("Save memory", use_container_width=True):

        if new_memory.strip():

            st.session_state.memories.append(
                new_memory.strip()
            )

            save_data()
            st.rerun()

    st.divider()

    st.markdown("### System information")

    st.caption("PERSONALITY: AURA")
    st.caption("VOICE: GACRUX")
    st.caption("INTERFACE: HOLOGRAPHIC")
    st.caption("INTELLIGENCE: GEMINI")


# =====================================================
# MAIN HEADER
# =====================================================

st.markdown(
    '<div class="aura-brand">AURA</div>'
    '<div class="aura-tagline">Always around you</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="status-line">AURA ONLINE • PERSONAL INTELLIGENCE</div>',
    unsafe_allow_html=True
)


# =====================================================
# TOP HUD PANELS
# =====================================================

left, middle, right = st.columns([1, 1, 1])

with left:

    st.markdown(f"""
    <div class="hud-panel">
        <div class="hud-label">Local time</div>
        <div class="hud-value">{datetime.now().strftime("%H:%M")}</div>
        <div class="hud-small">System clock</div>
    </div>
    """, unsafe_allow_html=True)

with middle:

    st.markdown("""
    <div class="hud-panel" style="text-align:center;">
        <div class="hud-label">Intelligence system</div>
        <div class="hud-value">READY</div>
        <div class="hud-small">Awaiting interaction</div>
    </div>
    """, unsafe_allow_html=True)

with right:

    st.markdown(f"""
    <div class="hud-panel">
        <div class="hud-label">Date</div>
        <div class="hud-value">{datetime.now().strftime("%d %b %Y")}</div>
        <div class="hud-small">System date</div>
    </div>
    """, unsafe_allow_html=True)


# =====================================================
# CENTRAL GLOWING CORE
# ALWAYS CENTRED IN THE MAIN INTERFACE
# =====================================================

state = st.session_state.core_state

state_class = {
    "idle": "",
    "listening": "core-listening",
    "thinking": "core-thinking",
    "speaking": "core-speaking"
}.get(state, "")

st.markdown(f"""
<div class="core-stage">

    <div class="core {state_class}">

        <div class="halo"></div>

        <div class="ring ring-one"></div>

        <div class="ring ring-two"></div>

        <div class="ring ring-three"></div>

        <div class="ring ring-four"></div>

        <div class="core-light"></div>

    </div>

</div>
""", unsafe_allow_html=True)


# =====================================================
# CORE STATUS AND SUBTITLES
# =====================================================

state_labels = {
    "idle": "STANDBY",
    "listening": "LISTENING",
    "thinking": "THINKING",
    "speaking": "SPEAKING"
}

st.markdown(
    f'<div class="status-line">{state_labels.get(state, "STANDBY")}</div>',
    unsafe_allow_html=True
)

st.markdown(
    f'<div class="subtitle">{st.session_state.subtitle}</div>',
    unsafe_allow_html=True
)


# =====================================================
# QUICK ACTIONS
# =====================================================

st.markdown(
    '<div class="section-label">QUICK ACCESS</div>',
    unsafe_allow_html=True
)

a, b, c = st.columns(3)

with a:
    schedule = st.button("◷ Schedule", use_container_width=True)

with b:
    search = st.button("⌕ Search", use_container_width=True)

with c:
    devices = st.button("⌘ Devices", use_container_width=True)

if schedule:
    process_message("Help me organise my schedule.")
    st.rerun()

if search:
    process_message("Help me research something. Ask what I want to find.")
    st.rerun()

if devices:
    process_message(
        "Explain which device integrations are available. "
        "Do not claim to control devices that are not connected."
    )
    st.rerun()


# =====================================================
# CONVERSATION
# =====================================================

st.markdown(
    '<div class="section-label">CONVERSATION</div>',
    unsafe_allow_html=True
)

for message in st.session_state.messages:

    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# =====================================================
# TEXT CHAT
# =====================================================

user_prompt = st.chat_input("Speak to Aura...")

if user_prompt:

    process_message(user_prompt)
    st.rerun()


# =====================================================
# VOICE INPUT
# =====================================================

st.markdown(
    '<div class="section-label">VOICE CHANNEL</div>',
    unsafe_allow_html=True
)

st.caption(
    "Record a voice message. Aura will transcribe it and respond."
)

audio_input = st.audio_input(
    "Record a message for Aura",
    key="aura_microphone"
)

if audio_input is not None:

    audio_hash = hashlib.sha256(
        audio_input.getvalue()
    ).hexdigest()

    if st.session_state.get("processed_audio_hash") != audio_hash:

        st.session_state.core_state = "listening"

        with st.spinner("Aura is listening..."):

            transcription = transcribe_audio(audio_input)

        st.session_state.processed_audio_hash = audio_hash

        if transcription:

            st.success("Transcription: " + transcription)

            process_message(transcription)

            st.rerun()


# =====================================================
# SPOKEN RESPONSE
# =====================================================

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


# =====================================================
# FOOTER
# =====================================================

st.markdown("""
<div class="footer">
    A U R A
    <br><br>
    ALWAYS AROUND YOU
</div>
""", unsafe_allow_html=True)
