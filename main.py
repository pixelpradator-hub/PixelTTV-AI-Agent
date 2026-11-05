
import os
import json
import base64
from pathlib import Path
from datetime import datetime, date, time

import streamlit as st
from google import genai

# ==========================================
# ROSE - PERSONAL AI ASSISTANT
# ==========================================

APP_NAME = "ROSE"
CHAT_MODEL = "gemini-3.8-flash"
TTS_MODEL = "gemini-3.8-flash-tts"
ROSE_VOICE = "Gacrux"

DATA_FILE = Path("rose_data.json")

SYSTEM_PROMPT = """
You are Rose, a highly capable female personal AI assistant.

IDENTITY:
- Your name is Rose.
- You are female and use she/her pronouns.
- You are inspired by the capabilities and professionalism
  of advanced fictional personal assistants, but have your
  own identity and personality.

PERSONALITY:
- Intelligent, composed, confident and observant.
- Calm, articulate and naturally conversational.
- Warm, elegant and occasionally humorous.
- Helpful without being overly formal.
- Never pretend to have completed an action you cannot perform.

VOICE:
- Mature feminine voice.
- Neutral English accent.
- Medium-low pitch.
- Smooth, clear and natural delivery.
- Confident, polished and measured pacing.

CAPABILITIES:
- Answer questions and explain information.
- Help organise schedules and tasks.
- Help create reminder descriptions.
- Assist with planning and problem solving.
- Remember information explicitly provided in this conversation.

IMPORTANT LIMITATIONS:
- You cannot access phone contacts, messages, files,
  location or other private data unless the app provides
  an authorised integration.
- You cannot independently place calls or send notifications.
- Never claim to have accessed data or performed an action
  that you have not actually performed.

Speak naturally. Avoid unnecessary long introductions.
"""

# ==========================================
# PAGE CONFIGURATION
# ==========================================

st.set_page_config(
    page_title="Rose AI",
    page_icon="🌹",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# STYLING
# ==========================================

st.markdown("""
<style>
@import url(
'https://fonts.googleapis.com/css2?family=Orbitron:wght@400;600;700&family=Inter:wght@300;400;500;600&display=swap'
);

.stApp {
    background:
        radial-gradient(circle at 50% 35%,
        #10243b 0%, #080e1b 42%, #03060d 100%);
    color: #e8f5ff;
    font-family: 'Inter', sans-serif;
}

header, footer {
    visibility: hidden;
}

#MainMenu {
    visibility: hidden;
}

.rose-brand {
    text-align: center;
    font-family: 'Orbitron', sans-serif;
    font-size: 27px;
    letter-spacing: 12px;
    color: #e9faff;
    text-shadow: 0 0 18px #00d4ff;
    margin-top: 10px;
}

.rose-tagline {
    text-align: center;
    color: #7298b5;
    letter-spacing: 4px;
    font-size: 10px;
    margin-bottom: 25px;
}

.core-stage {
    display: flex;
    justify-content: center;
    align-items: center;
    width: 100%;
    min-height: 300px;
}

.core {
    width: 170px;
    height: 170px;
    border-radius: 50%;
    position: relative;
    display: flex;
    align-items: center;
    justify-content: center;
    background:
      radial-gradient(circle,
      #b9f7ff 0%,
      #36c9ff 12%,
      #1769a8 35%,
      #101a38 65%,
      transparent 72%);
    box-shadow:
      0 0 25px #00d4ff,
      0 0 65px #0077ff,
      0 0 110px #593bff;
    animation: breathe 3.5s ease-in-out infinite;
}

.ring {
    position: absolute;
    border: 1px solid rgba(0,212,255,.65);
    border-radius: 50%;
    inset: -18px;
    animation: rotate 12s linear infinite;
}

.ring.two {
    inset: -35px;
    border-style: dashed;
    animation: reverseRotate 18s linear infinite;
}

.ring.three {
    inset: -52px;
    border-color: rgba(130,100,255,.45);
    animation: rotate 25s linear infinite;
}

@keyframes breathe {
    0%, 100% {
        transform: scale(.96);
        filter: brightness(.9);
    }
    50% {
        transform: scale(1.05);
        filter: brightness(1.3);
    }
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
    color: #00d4ff;
    font-family: 'Orbitron', sans-serif;
    font-size: 11px;
    letter-spacing: 4px;
    margin-top: 45px;
}

.subtitle {
    text-align: center;
    color: #b8d8ed;
    font-size: 14px;
    margin: 12px 0 25px;
}

.panel {
    background: rgba(10, 26, 45, .75);
    border: 1px solid rgba(0,212,255,.25);
    border-radius: 12px;
    padding: 15px;
    text-align: center;
}

.panel-label {
    color: #7097b5;
    font-size: 10px;
    letter-spacing: 2px;
}

.panel-value {
    color: #d9f7ff;
    font-size: 17px;
    margin-top: 7px;
}

.stButton > button {
    background: rgba(0, 100, 150, .2);
    border: 1px solid #00bce8;
    color: #dffaff;
    border-radius: 9px;
}

.stButton > button:hover {
    border-color: #a58cff;
    color: white;
    box-shadow: 0 0 12px #00bce8;
}

[data-testid="stChatMessage"] {
    background: rgba(10, 27, 47, .75);
    border: 1px solid rgba(0,212,255,.12);
    border-radius: 12px;
}
</style>
""", unsafe_allow_html=True)

# ==========================================
# DATA AND SESSION
# ==========================================

def load_data():
    if DATA_FILE.exists():
        try:
            return json.loads(DATA_FILE.read_text(encoding="utf-8"))
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

# ==========================================
# GEMINI CONNECTION
# ==========================================

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
        "Rose needs a Gemini API key. "
        "Add GEMINI_API_KEY to your Streamlit secrets."
    )
    st.stop()

client = get_client(api_key)

# ==========================================
# ROSE CHAT
# ==========================================

def ask_rose(user_message):
    history = []

    for item in st.session_state.messages[-12:]:
        role = item["role"].upper()
        history.append(f"{role}: {item['content']}")

    conversation = "\n".join(history)
    prompt = (
        f"Previous conversation:\n{conversation}\n\n"
        f"USER: {user_message}\nROSE:"
    )

    response = client.interactions.create(
        model=CHAT_MODEL,
        system_instruction=SYSTEM_PROMPT,
        input=prompt
    )

    return response.output_text


# ==========================================
# ROSE VOICE
# ==========================================

def speak(text):
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
                        "A mature, composed and confident feminine "
                        "voice with a neutral English accent. "
                        "Warm, elegant, smooth, clear and natural. "
                        "Medium-low pitch, measured pacing and "
                        "subtle expressiveness."
                    )
                }]
            }]
        }],
        response_format={"type": "audio"},
        generation_config={
            "speech_config": [
                {"voice": ROSE_VOICE}
            ]
        }
    )

    return base64.b64decode(interaction.output_audio.data)


# ==========================================
# HEADER
# ==========================================

now = datetime.now()

st.markdown(
    '<div class="rose-brand">R O S E</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="rose-tagline">YOUR PERSONAL INTELLIGENCE</div>',
    unsafe_allow_html=True
)

# ==========================================
# DASHBOARD
# ==========================================

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(
        f"""
        <div class="panel">
        <div class="panel-label">LOCAL TIME</div>
        <div class="panel-value">{now.strftime("%H:%M")}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with col2:
    st.markdown(
        """
        <div class="panel">
        <div class="panel-label">SYSTEM STATUS</div>
        <div class="panel-value">ROSE ONLINE</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with col3:
    st.markdown(
        f"""
        <div class="panel">
        <div class="panel-label">DATE</div>
        <div class="panel-value">{now.strftime("%d %b %Y")}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

# ==========================================
# CENTRED CORE
# ==========================================

st.markdown("""
<div class="core-stage">
    <div class="core">
        <div class="ring"></div>
        <div class="ring two"></div>
        <div class="ring three"></div>
    </div>
</div>
<div class="status">ROSE ONLINE</div>
<div class="subtitle">Always here. Always ready.</div>
""", unsafe_allow_html=True)

# ==========================================
# SIDEBAR
# ==========================================

with st.sidebar:
    st.title("ROSE CONTROL")

    st.session_state.voice_enabled = st.toggle(
        "Voice responses",
        value=st.session_state.voice_enabled
    )

    if st.button("New conversation", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.divider()
    st.subheader("Reminders")

    with st.form("reminder_form"):
        reminder_text = st.text_input(
            "What should Rose remind you about?"
        )

        reminder_date = st.date_input(
            "Date",
            value=date.today()
        )

        reminder_time = st.time_input(
            "Time",
            value=time(17, 0)
        )

        submitted = st.form_submit_button(
            "Save reminder",
            use_container_width=True
        )

        if submitted and reminder_text.strip():
            reminder = {
                "text": reminder_text.strip(),
                "datetime": datetime.combine(
                    reminder_date,
                    reminder_time
                ).isoformat(),
                "done": False
            }

            st.session_state.data["reminders"].append(reminder)
            save_data(st.session_state.data)
            st.success("Reminder saved.")

    st.divider()

    st.caption(
        "Phone access and Android notifications "
        "will be added in the native app."
    )

# ==========================================
# REMINDER DISPLAY
# ==========================================

st.subheader("Your reminders")

reminders = st.session_state.data["reminders"]

if not reminders:
    st.caption("You don't have any saved reminders yet.")
else:
    for index, reminder in enumerate(reminders):
        reminder_date = datetime.fromisoformat(
            reminder["datetime"]
        )

        status = (
            "Completed" if reminder["done"]
            else "Upcoming"
        )

        with st.container(border=True):
            left, right = st.columns([4, 1])

            with left:
                st.write(f"**{reminder['text']}**")
                st.caption(
                    reminder_date.strftime("%d %b %Y, %H:%M")
                    + f" · {status}"
                )

            with right:
                if not reminder["done"]:
                    if st.button("Done", key=f"done_{index}"):
                        reminder["done"] = True
                        save_data(st.session_state.data)
                        st.rerun()

# ==========================================
# CHAT HISTORY
# ==========================================

st.divider()
st.subheader("Talk to Rose")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ==========================================
# CHAT INPUT
# ==========================================

user_message = st.chat_input(
    "Good evening. How may I assist you?"
)

if user_message:
    st.session_state.messages.append({
        "role": "user",
        "content": user_message
    })

    with st.chat_message("user"):
        st.markdown(user_message)

    with st.chat_message("assistant"):
        with st.spinner("Rose is thinking..."):
            try:
                answer = ask_rose(user_message)
                st.markdown(answer)

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer
                })

                if st.session_state.voice_enabled:
                    try:
                        audio = speak(answer)
                        st.audio(
                            audio,
                            format="audio/wav",
                            autoplay=True
                        )
                    except Exception as voice_error:
                        st.warning(
                            f"Voice unavailable: {voice_error}"
                        )

            except Exception as error:
                st.error(f"Rose encountered an error: {error}")
