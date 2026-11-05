
import os
import json
import base64
import re
from pathlib import Path
from datetime import datetime, date, time

import streamlit as st
from google import genai
from google.genai import types

# =====================================================
# ROSE PERSONAL INTELLIGENCE
# =====================================================

APP_NAME = "ROSE"

CHAT_MODEL = "gemini-3.8-flash"
TTS_MODEL = "gemini-3.8-flash-tts"
VOICE_NAME = "Gacrux"

DATA_FILE = Path("rose_data.json")

SYSTEM_PROMPT = """
You are ROSE, an advanced female personal AI assistant.

IDENTITY:
Your name is Rose. You are female and use she/her pronouns.
You are inspired by the capabilities of advanced fictional
personal assistants, while maintaining your own identity.

PERSONALITY:
- Intelligent, composed, confident and observant.
- Warm, articulate, polished and naturally conversational.
- Occasionally humorous when appropriate.
- Patient and respectful with every user.
- Capable of detailed explanations and serious research.
- Never act like you only exist to help with YouTube.

CAPABILITIES:
- General knowledge and problem solving.
- Research, analysis and explanations.
- Science, technology, education and mathematics.
- Writing, editing and summarising.
- Planning and organisation.
- Creative ideas and brainstorming.
- YouTube and creator assistance when requested.

RESEARCH:
- Use available Google Search grounding when appropriate.
- Prefer reliable and current information.
- Distinguish facts from assumptions.
- Never invent sources or citations.
- Explain uncertainty.

VOICE:
- Mature feminine voice.
- Neutral English accent.
- Medium-low pitch.
- Warm, smooth, clear and confident.
- Natural pauses and measured pacing.

BEHAVIOUR:
- Answer directly.
- Avoid unnecessary introductions.
- Give short answers to simple questions.
- Give detailed answers when the task requires it.
- Adapt explanations to the user's understanding.

LIMITATIONS:
- Never pretend to access private phone information.
- Never claim to make calls, send notifications or access
  contacts unless an authorised integration actually exists.
- Never claim an action succeeded unless it did.

Your purpose is to be an exceptionally useful,
trustworthy personal assistant.
"""

# =====================================================
# STREAMLIT CONFIGURATION
# =====================================================

st.set_page_config(
    page_title="ROSE | Personal Intelligence",
    page_icon="🌹",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =====================================================
# JARVIS-INSPIRED INTERFACE
# =====================================================

st.markdown("""
<style>
@import url(
'https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;600;700&family=Inter:wght@300;400;500;600&display=swap'
);

.stApp {
    background:
        radial-gradient(ellipse at 50% 30%,
        #10243b 0%,
        #080f1d 48%,
        #02050b 100%);
    color: #e5f5ff;
    font-family: 'Inter', sans-serif;
}

header, footer, #MainMenu {
    visibility: hidden;
}

.block-container {
    padding-top: 1rem;
    max-width: 1250px;
}

.rose-brand {
    text-align: center;
    font-family: 'Orbitron', sans-serif;
    font-size: 27px;
    letter-spacing: 13px;
    color: #e9faff;
    text-shadow: 0 0 18px #00d4ff;
}

.rose-tagline {
    text-align: center;
    color: #7195b5;
    letter-spacing: 4px;
    font-size: 10px;
    margin-top: 7px;
    margin-bottom: 24px;
}

.hud-panel {
    background: rgba(8, 24, 42, .78);
    border: 1px solid rgba(0, 212, 255, .25);
    border-radius: 12px;
    padding: 13px;
    text-align: center;
    box-shadow: 0 0 18px rgba(0, 120, 255, .06);
}

.hud-label {
    font-size: 9px;
    letter-spacing: 2px;
    color: #739bb8;
}

.hud-value {
    font-size: 16px;
    margin-top: 7px;
    color: #e4f8ff;
    font-family: 'Orbitron', sans-serif;
}

.core-stage {
    width: 100%;
    height: 350px;
    display: flex;
    justify-content: center;
    align-items: center;
    position: relative;
    overflow: hidden;
}

.core {
    width: 150px;
    height: 150px;
    border-radius: 50%;
    position: relative;
    display: flex;
    align-items: center;
    justify-content: center;
    animation: breathe 3.5s ease-in-out infinite;
    transition: all 1s ease;
}

.core::before {
    content: "";
    position: absolute;
    inset: 20px;
    border-radius: 50%;
    background: radial-gradient(circle,
        var(--core-light) 0%,
        var(--core-main) 30%,
        var(--core-dark) 75%);
    box-shadow:
        0 0 25px var(--core-main),
        0 0 60px var(--core-glow),
        0 0 105px var(--core-glow);
}

.core.cyan {
    --core-light: #d9ffff;
    --core-main: #00d4ff;
    --core-dark: #06345b;
    --core-glow: #0077ff;
}

.core.youtube {
    --core-light: #ffaaaa;
    --core-main: #ed2929;
    --core-dark: #390c19;
    --core-glow: #087bff;
}

.core.research {
    --core-light: #e5c9ff;
    --core-main: #a34cff;
    --core-dark: #261047;
    --core-glow: #7435ff;
}

.core.listening {
    --core-light: #ffffff;
    --core-main: #00d4ff;
    --core-dark: #06345b;
    --core-glow: #00d4ff;
    animation: listen 1.2s ease-in-out infinite;
}

.core.thinking {
    --core-light: #fff2c2;
    --core-main: #ffb52e;
    --core-dark: #422408;
    --core-glow: #ff8a00;
    animation: think 1.2s linear infinite;
}

.core.speaking {
    animation: speak 0.8s ease-in-out infinite;
}

.ring {
    position: absolute;
    inset: 0;
    border-radius: 50%;
    border: 1px solid var(--core-main);
    opacity: .8;
    animation: rotate 12s linear infinite;
}

.ring.two {
    inset: -25px;
    border-style: dashed;
    animation: reverseRotate 17s linear infinite;
}

.ring.three {
    inset: -48px;
    border-color: var(--core-glow);
    opacity: .55;
    animation: rotate 25s linear infinite;
}

.ring.four {
    inset: -68px;
    border-color: rgba(150, 200, 255, .2);
    border-style: dotted;
    animation: reverseRotate 30s linear infinite;
}

@keyframes breathe {
    0%, 100% { transform: scale(.95); }
    50% { transform: scale(1.06); }
}

@keyframes listen {
    0%, 100% { transform: scale(.95); }
    50% { transform: scale(1.14); }
}

@keyframes think {
    from { transform: rotate(0deg) scale(.95); }
    to { transform: rotate(360deg) scale(1.05); }
}

@keyframes speak {
    0%, 100% { transform: scale(.95); }
    50% { transform: scale(1.12); }
}

@keyframes rotate {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
}

@keyframes reverseRotate {
    from { transform: rotate(360deg); }
    to { transform: rotate(0deg); }
}

.status {
    text-align: center;
    color: var(--status-color, #00d4ff);
    font-family: 'Orbitron', sans-serif;
    font-size: 11px;
    letter-spacing: 4px;
    margin-top: -12px;
}

.subtitle {
    text-align: center;
    color: #a9c9df;
    font-size: 13px;
    margin: 12px 0 25px;
}

.mode-label {
    text-align: center;
    color: #829db5;
    font-size: 10px;
    letter-spacing: 3px;
    margin-top: 8px;
}

.stButton > button {
    background: rgba(0, 100, 150, .18);
    border: 1px solid rgba(0, 212, 255, .5);
    color: #e3f8ff;
    border-radius: 9px;
    transition: .3s;
}

.stButton > button:hover {
    border-color: #a77cff;
    box-shadow: 0 0 15px rgba(0, 212, 255, .3);
    color: white;
}

[data-testid="stChatMessage"] {
    background: rgba(8, 24, 42, .8);
    border: 1px solid rgba(0, 212, 255, .15);
    border-radius: 12px;
}

.stTextInput input,
.stTextArea textarea {
    background: rgba(5, 15, 28, .8);
    color: white;
}

hr {
    border-color: rgba(0, 212, 255, .15);
}
</style>
""", unsafe_allow_html=True)

# =====================================================
# DATA MANAGEMENT
# =====================================================

def load_data():
    if DATA_FILE.exists():
        try:
            return json.loads(
                DATA_FILE.read_text(encoding="utf-8")
            )
        except Exception:
            pass

    return {"reminders": []}


def save_data(data):
    DATA_FILE.write_text(
        json.dumps(data, indent=2),
        encoding="utf-8"
    )


if "messages" not in st.session_state:
    st.session_state.messages = []

if "voice_enabled" not in st.session_state:
    st.session_state.voice_enabled = True

if "data" not in st.session_state:
    st.session_state.data = load_data()

if "status" not in st.session_state:
    st.session_state.status = "IDLE"

if "last_audio" not in st.session_state:
    st.session_state.last_audio = None

# =====================================================
# GEMINI CONNECTION
# =====================================================

def get_api_key():
    try:
        key = st.secrets.get("GEMINI_API_KEY")
        if key:
            return key
    except Exception:
        pass

    return os.getenv("GEMINI_API_KEY")


@st.cache_resource
def get_client(api_key):
    return genai.Client(api_key=api_key)


api_key = get_api_key()

if not api_key:
    st.error(
        "ROSE cannot connect to Gemini. "
        "Please configure GEMINI_API_KEY in Streamlit secrets."
    )
    st.stop()

client = get_client(api_key)

# =====================================================
# INTELLIGENT MODE DETECTION
# =====================================================

def detect_mode(text):

    value = text.lower()

    youtube_words = [
        "youtube", "youtube channel", "subscribers",
        "views", "thumbnail", "fortnite channel",
        "youtube analytics", "creator", "tiktok",
        "instagram reels", "video performance"
    ]

    research_words = [
        "research", "investigate", "analyse",
        "analyze", "academic", "scientific study",
        "sources", "evidence", "deep dive",
        "compare studies", "report"
    ]

    if any(word in value for word in youtube_words):
        return "YOUTUBE"

    if any(word in value for word in research_words):
        return "RESEARCH"

    return "NORMAL"


def get_orb_html(mode, status):

    if status == "LISTENING":
        orb_class = "listening"
        label = "LISTENING"
        colour = "#00d4ff"

    elif status == "THINKING":
        orb_class = "thinking"
        label = "PROCESSING"
        colour = "#ffb52e"

    elif status == "SPEAKING":
        orb_class = "speaking"
        label = "SPEAKING"
        colour = "#00d4ff"

    else:
        orb_class = {
            "YOUTUBE": "youtube",
            "RESEARCH": "research",
            "NORMAL": "cyan"
        }.get(mode, "cyan")

        label = {
            "YOUTUBE": "YOUTUBE INTELLIGENCE",
            "RESEARCH": "RESEARCH MODE",
            "NORMAL": "ROSE ONLINE"
        }.get(mode, "ROSE ONLINE")

        colour = {
            "YOUTUBE": "#258cff",
            "RESEARCH": "#a34cff",
            "NORMAL": "#00d4ff"
        }.get(mode, "#00d4ff")

    return f"""
    <div class="core-stage">
        <div class="core {orb_class}">
            <div class="ring"></div>
            <div class="ring two"></div>
            <div class="ring three"></div>
            <div class="ring four"></div>
        </div>
    </div>
    <div class="status" style="--status-color:{colour}">
        {label}
    </div>
    """

# =====================================================
# GOOGLE SEARCH GROUNDING
# =====================================================

def get_search_config():
    return types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        temperature=0.65,
        tools=[
            types.Tool(
                google_search=types.GoogleSearch()
            )
        ]
    )


# =====================================================
# ROSE'S INTELLIGENCE
# =====================================================

def ask_rose(user_text, audio_file=None):

    history = []

    for message in st.session_state.messages[-12:]:

        role = (
            "user" if message["role"] == "user"
            else "model"
        )

        history.append(
            types.Content(
                role=role,
                parts=[
                    types.Part.from_text(
                        text=message["content"]
                    )
                ]
            )
        )

    current_parts = []

    if user_text.strip():
        current_parts.append(
            types.Part.from_text(text=user_text)
        )

    if audio_file is not None:
        current_parts.append(
            types.Part.from_bytes(
                data=audio_file.getvalue(),
                mime_type=audio_file.type
            )
        )

    if not current_parts:
        return "I didn't receive any message or audio."

    history.append(
        types.Content(
            role="user",
            parts=current_parts
        )
    )

    mode = detect_mode(user_text)

    config = (
        get_search_config()
        if mode == "RESEARCH"
        else types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=0.65
        )
    )

    response = client.models.generate_content(
        model=CHAT_MODEL,
        contents=history,
        config=config
    )

    return response.text or "I couldn't generate a response."


# =====================================================
# ROSE'S VOICE
# =====================================================

def generate_voice(text):

    interaction = client.interactions.create(
        model=TTS_MODEL,
        input=[{
            "type": "user_input",
            "content": [{
                "type": "text",
                "text": text,
                "annotations": [{
                    "type": "speech_metadata",
                    "style": (
                        "A mature feminine voice with a neutral "
                        "English accent. Warm, composed, elegant, "
                        "confident and articulate. Medium-low pitch, "
                        "natural pauses, smooth delivery and "
                        "measured pacing. Sound like a polished "
                        "personal intelligence."
                    )
                }]
            }]
        }],
        response_format={"type": "audio"},
        generation_config={
            "speech_config": [
                {"voice": VOICE_NAME}
            ]
        }
    )

    audio_data = interaction.output_audio.data

    if isinstance(audio_data, str):
        return base64.b64decode(audio_data)

    return audio_data


# =====================================================
# HEADER
# =====================================================

now = datetime.now()

st.markdown(
    '<div class="rose-brand">R O S E</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="rose-tagline">'
    'ALWAYS AROUND YOU'
    '</div>',
    unsafe_allow_html=True
)

# =====================================================
# HUD DASHBOARD
# =====================================================

c1, c2, c3 = st.columns(3)

with c1:
    st.markdown(
        f"""
        <div class="hud-panel">
            <div class="hud-label">LOCAL TIME</div>
            <div class="hud-value">{now:%H:%M}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with c2:
    st.markdown(
        """
        <div class="hud-panel">
            <div class="hud-label">SYSTEM STATUS</div>
            <div class="hud-value">OPERATIONAL</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with c3:
    st.markdown(
        f"""
        <div class="hud-panel">
            <div class="hud-label">DATE</div>
            <div class="hud-value">{now:%d %b %Y}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

# =====================================================
# SIDEBAR CONTROLS
# =====================================================

with st.sidebar:

    st.title("ROSE CONTROL")

    st.caption("PERSONAL INTELLIGENCE SYSTEM")

    st.session_state.voice_enabled = st.toggle(
        "Spoken responses",
        value=st.session_state.voice_enabled
    )

    if st.button(
        "New conversation",
        use_container_width=True
    ):
        st.session_state.messages = []
        st.session_state.last_audio = None
        st.rerun()

    st.divider()

    st.subheader("System information")

    st.write("Intelligence: Gemini 3.8 Flash")
    st.write("Voice engine: Gemini 3.8 Flash TTS")
    st.write("Voice profile: Gacrux")

    st.divider()

    st.subheader("Reminders")

    with st.form("reminder_form"):

        reminder_text = st.text_input(
            "Reminder description"
        )

        reminder_date = st.date_input(
            "Reminder date",
            value=date.today()
        )

        reminder_time = st.time_input(
            "Reminder time",
            value=time(17, 0)
        )

        save_reminder = st.form_submit_button(
            "Save reminder",
            use_container_width=True
        )

        if save_reminder and reminder_text.strip():

            st.session_state.data["reminders"].append({
                "text": reminder_text.strip(),
                "datetime": datetime.combine(
                    reminder_date,
                    reminder_time
                ).isoformat(),
                "done": False
            })

            save_data(st.session_state.data)

            st.success("Reminder saved.")

# =====================================================
# MAIN ORB
# =====================================================

last_mode = "NORMAL"

if st.session_state.messages:
    last_user_message = next(
        (
            m["content"]
            for m in reversed(st.session_state.messages)
            if m["role"] == "user"
        ),
        ""
    )

    last_mode = detect_mode(last_user_message)

st.markdown(
    get_orb_html(last_mode, st.session_state.status),
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">'
    'Your personal intelligence. Ready when you are.'
    '</div>',
    unsafe_allow_html=True
)

# =====================================================
# QUICK ACTIONS
# =====================================================

st.markdown("### Quick access")

q1, q2, q3 = st.columns(3)

with q1:
    if st.button("General assistant", use_container_width=True):
        st.session_state.quick_prompt = (
            "Rose, what can you help me with today?"
        )

with q2:
    if st.button("YouTube intelligence", use_container_width=True):
        st.session_state.quick_prompt = (
            "Let's work on my YouTube channel and creator strategy."
        )

with q3:
    if st.button("Deep research", use_container_width=True):
        st.session_state.quick_prompt = (
            "I would like you to research a subject thoroughly."
        )

# =====================================================
# REMINDER DISPLAY
# =====================================================

st.divider()
st.subheader("Upcoming reminders")

reminders = st.session_state.data["reminders"]

if not reminders:
    st.caption("No reminders saved.")

for index, reminder in enumerate(reminders):

    reminder_date = datetime.fromisoformat(
        reminder["datetime"]
    )

    left, right = st.columns([5, 1])

    with left:
        status_text = (
            "Completed" if reminder["done"]
            else "Upcoming"
        )

        st.write(f"**{reminder['text']}**")

        st.caption(
            reminder_date.strftime("%d %b %Y at %H:%M")
            + " · "
            + status_text
        )

    with right:
        if not reminder["done"]:
            if st.button("Done", key=f"done_{index}"):

                reminder["done"] = True
                save_data(st.session_state.data)
                st.rerun()

# =====================================================
# CHAT AND VOICE INPUT
# =====================================================

st.divider()
st.subheader("Communicate with Rose")

for message in st.session_state.messages:

    with st.chat_message(message["role"]):
        st.markdown(message["content"])

        if message.get("audio"):
            st.audio(
                message["audio"],
                format="audio/wav"
            )

# Voice note recorder and upload
with st.expander("🎙️ Send Rose a voice note"):

    recorded_audio = st.audio_input(
        "Record a voice message"
    )

    uploaded_audio = st.file_uploader(
        "Or upload an audio file",
        type=[
            "wav", "mp3", "m4a", "aac",
            "ogg", "flac", "webm"
        ]
    )

    if recorded_audio:
        st.audio(recorded_audio)

    if uploaded_audio:
        st.audio(uploaded_audio)

# Text input
user_text = st.chat_input(
    "Message Rose..."
)

# Quick action input
if "quick_prompt" not in st.session_state:
    st.session_state.quick_prompt = ""

if st.session_state.quick_prompt:
    user_text = st.session_state.quick_prompt
    st.session_state.quick_prompt = ""

audio_to_send = None

if recorded_audio:
    audio_to_send = recorded_audio
elif uploaded_audio:
    audio_to_send = uploaded_audio

# =====================================================
# PROCESS USER MESSAGE
# =====================================================

if user_text or audio_to_send:

    if not user_text:
        user_text = "Please listen to my voice note and respond."

    mode = detect_mode(user_text)

    st.session_state.messages.append({
        "role": "user",
        "content": user_text
    })

    # Display current user message
    with st.chat_message("user"):
        st.markdown(user_text)

    # Processing indicator
    st.session_state.status = "THINKING"

    st.markdown(
        get_orb_html(mode, "THINKING"),
        unsafe_allow_html=True
    )

    with st.chat_message("assistant"):

        with st.spinner("Rose is processing..."):

            try:

                answer = ask_rose(
                    user_text,
                    audio_to_send
                )

                st.markdown(answer)

                audio_bytes = None

                if st.session_state.voice_enabled:

                    try:
                        st.session_state.status = "SPEAKING"

                        audio_bytes = generate_voice(answer)

                        st.audio(
                            audio_bytes,
                            format="audio/wav",
                            autoplay=True
                        )

                    except Exception as voice_error:
                        st.warning(
                            "Rose answered, but voice generation "
                            f"failed: {voice_error}"
                        )

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer,
                    "audio": audio_bytes
                })

                st.session_state.status = "IDLE"

            except Exception as error:

                st.session_state.status = "IDLE"

                st.error(
                    f"Rose encountered an error: {error}"
                )

    st.rerun()

# =====================================================
# FOOTER
# =====================================================

st.markdown("---")

st.markdown(
    """
    <div style="
        text-align:center;
        color:#66849f;
        font-size:10px;
        letter-spacing:3px;
        padding:10px;">
        ROSE PERSONAL INTELLIGENCE SYSTEM
        <br>
        ALWAYS AROUND YOU
    </div>
    """,
    unsafe_allow_html=True
)
