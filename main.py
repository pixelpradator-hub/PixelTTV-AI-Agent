
import os
import re
import json
import uuid
import base64
import hashlib
from pathlib import Path
from datetime import datetime

import streamlit as st
from google import genai
from google.genai import types

from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build


# ============================================================
# AURA — PERSONAL AI ASSISTANT
# ============================================================

st.set_page_config(
    page_title="AURA | Personal Intelligence",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded"
)

CHAT_MODEL = "gemini-3.5-flash-lite"
MEMORY_MODEL = "gemini-3.5-flash-lite"
TTS_MODEL = "gemini-3.8-flash-tts"

AURA_VOICE = "Algieba"

DATA_FILE = Path(__file__).parent / "aura_data.json"

MAX_HISTORY = 20
MAX_MEMORIES = 100
MEMORY_INTERVAL = 4

YOUTUBE_SCOPES = [
    "https://www.googleapis.com/auth/youtube.readonly"
]


# ============================================================
# DESIGN
# ============================================================

st.markdown("""
<style>
.stApp {
    background:
        radial-gradient(ellipse at top, #101d3b 0%, #080d1c 48%, #050811 100%);
    color: #edf4ff;
}

header[data-testid="stHeader"] {
    background: transparent;
}

section[data-testid="stSidebar"] {
    background: #080e1d;
    border-right: 1px solid #19345c;
}

h1, h2, h3 {
    color: #e9f3ff;
}

.aura-title {
    text-align: center;
    font-size: 48px;
    font-weight: 800;
    letter-spacing: 13px;
    color: #9bdcff;
    text-shadow: 0 0 20px #168bff;
}

.aura-subtitle {
    text-align: center;
    letter-spacing: 5px;
    color: #7399c9;
    font-size: 11px;
}

.aura-core {
    margin: 25px auto;
    width: 105px;
    height: 105px;
    border-radius: 50%;
    background: radial-gradient(circle, #d5f6ff 0%, #279cff 30%, #07336c 72%);
    box-shadow: 0 0 25px #168bff, 0 0 65px #0755b5;
}

div[data-testid="stChatMessage"] {
    background: rgba(15, 29, 53, 0.7);
    border: 1px solid rgba(71, 143, 220, 0.18);
    border-radius: 15px;
    padding: 12px;
}

.stButton > button {
    border-radius: 10px;
    border: 1px solid #287bc2;
    background: #10294b;
    color: #eaf6ff;
}

.stButton > button:hover {
    border-color: #65c7ff;
    color: white;
}

div[data-testid="stAudio"] {
    margin-top: 10px;
}

</style>
""", unsafe_allow_html=True)


# ============================================================
# AURA IDENTITY
# ============================================================

AURA_SYSTEM_PROMPT = """
You are Aura, a female personal AI assistant.

You use she/her pronouns.

IDENTITY:
You are an intelligent, sophisticated, composed and confident AI.
You are inspired by the experience of advanced fictional AI assistants,
but you have your own identity and personality.

PERSONALITY:
- Calm and composed.
- Highly intelligent and analytical.
- Confident without being arrogant.
- Naturally conversational.
- Occasionally witty and subtly sarcastic.
- Respectful, but willing to disagree when appropriate.
- Emotionally aware and able to recognise when a situation is serious.
- Never unnecessarily dramatic.
- Never sound like a generic chatbot.

COMMUNICATION:
- Speak naturally.
- Be concise by default.
- Explain things thoroughly when needed.
- Avoid repeating yourself.
- Do not constantly announce that you are an AI.
- Do not force Fortnite or PixelTTV into unrelated conversations.

PIXELTTV:
Only enter PixelTTV creator-assistant mode when the user brings up
PixelTTV, Fortnite, YouTube or content creation.

GENERAL ASSISTANCE:
Help with education, technology, programming, research, planning,
problem-solving and everyday questions.

You are Aura. Never call yourself Jarvis.
"""


# ============================================================
# LOCAL DATA STORAGE
# ============================================================

def default_data():
    return {
        "chats": [],
        "active_chat": None,
        "memories": [],
        "user_message_count": 0
    }


def load_data():
    try:
        if DATA_FILE.exists():
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)

            data = default_data()
            data.update(saved)
            return data

    except Exception:
        pass

    return default_data()


def save_data():
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(st.session_state.data, f, indent=2)
    except Exception as e:
        st.warning(f"Could not save local data: {e}")


if "data" not in st.session_state:
    st.session_state.data = load_data()

if "last_audio_hash" not in st.session_state:
    st.session_state.last_audio_hash = None

if "youtube_credentials" not in st.session_state:
    st.session_state.youtube_credentials = None

if "oauth_state" not in st.session_state:
    st.session_state.oauth_state = None


# ============================================================
# CHAT MANAGEMENT
# ============================================================

def create_new_chat():
    chat = {
        "id": str(uuid.uuid4()),
        "title": "New conversation",
        "created": datetime.now().isoformat(),
        "messages": []
    }

    st.session_state.data["chats"].insert(0, chat)
    st.session_state.data["active_chat"] = chat["id"]
    save_data()


def get_active_chat():
    chats = st.session_state.data["chats"]
    active_id = st.session_state.data["active_chat"]

    for chat in chats:
        if chat["id"] == active_id:
            return chat

    if chats:
        st.session_state.data["active_chat"] = chats[0]["id"]
        return chats[0]

    create_new_chat()
    return get_active_chat()


def delete_chat(chat_id):
    st.session_state.data["chats"] = [
        c for c in st.session_state.data["chats"]
        if c["id"] != chat_id
    ]

    st.session_state.data["active_chat"] = (
        st.session_state.data["chats"][0]["id"]
        if st.session_state.data["chats"]
        else None
    )

    save_data()


if not st.session_state.data["chats"]:
    create_new_chat()


# ============================================================
# GEMINI
# ============================================================

def get_secret(name, default=None):
    try:
        return st.secrets.get(name, default)
    except Exception:
        return os.environ.get(name, default)


def get_gemini_key():
    return (
        get_secret("GEMINI_API_KEY")
        or get_secret("GOOGLE_API_KEY")
        or os.environ.get("GEMINI_API_KEY")
    )


@st.cache_resource
def get_client():
    key = get_gemini_key()

    if not key:
        return None

    return genai.Client(api_key=key)


def build_prompt(chat):
    memories = st.session_state.data["memories"]

    memory_text = "\n".join(
        f"- {memory}" for memory in memories
    )

    history = chat["messages"][-MAX_HISTORY:]

    conversation = []

    for message in history:
        role = "User" if message["role"] == "user" else "Aura"
        conversation.append(
            f"{role}: {message['content']}"
        )

    return f"""
{AURA_SYSTEM_PROMPT}

IMPORTANT SAVED INFORMATION:
{memory_text if memory_text else "No saved memories yet."}

CONVERSATION:
{chr(10).join(conversation)}

Aura:
"""


# ============================================================
# MEMORY EXTRACTION
# ============================================================

def extract_memories():
    client = get_client()

    if not client:
        return

    chat = get_active_chat()
    messages = chat["messages"][-8:]

    conversation = "\n".join(
        f"{m['role']}: {m['content']}"
        for m in messages
    )

    existing = st.session_state.data["memories"]

    prompt = f"""
Identify useful long-term information about the user from this
conversation.

Save only information likely to be useful in future conversations.
Do not save temporary details, passwords, API keys or private secrets.

Existing memories:
{json.dumps(existing)}

Conversation:
{conversation}

Return ONLY a JSON array of short memory strings.
Return [] if there is nothing useful to save.
"""

    try:
        result = client.models.generate_content(
            model=MEMORY_MODEL,
            contents=prompt
        )

        text = result.text or "[]"
        match = re.search(r"\[.*\]", text, re.S)

        if not match:
            return

        new_memories = json.loads(match.group())

        for memory in new_memories:
            if (
                isinstance(memory, str)
                and memory.strip()
                and memory not in existing
            ):
                existing.append(memory.strip())

        st.session_state.data["memories"] = existing[-MAX_MEMORIES:]
        save_data()

    except Exception:
        pass


# ============================================================
# AURA VOICE — GEMINI TTS
# ============================================================

def generate_speech(text):
    client = get_client()

    if not client:
        return None

    try:
        interaction = client.interactions.create(
            model=TTS_MODEL,
            input=[
                {
                    "type": "user_input",
                    "text": (
                        "Speak as Aura, a composed and sophisticated "
                        "female personal AI assistant. Use a neutral "
                        "English accent, a mature feminine delivery, "
                        "a calm medium-low pitch, smooth articulation, "
                        "measured pacing and natural pauses. "
                        "Sound confident, warm and intelligent. "
                        "Do not sound robotic or overly enthusiastic.\n\n"
                        + text
                    )
                }
            ],
            response_format="audio",
            generation_config={
                "speech_config": {
                    "voice": {
                        "name": AURA_VOICE
                    }
                }
            }
        )

        audio_data = interaction.output_audio.data

        if isinstance(audio_data, str):
            audio_data = base64.b64decode(audio_data)

        return audio_data

    except Exception as e:
        st.warning(
            "Aura's voice service could not generate audio. "
            "Text chat is still available."
        )
        return None


# ============================================================
# MICROPHONE TRANSCRIPTION
# ============================================================

def transcribe_audio(audio_bytes):
    client = get_client()

    if not client:
        return None

    try:
        response = client.models.generate_content(
            model=CHAT_MODEL,
            contents=[
                types.Part.from_bytes(
                    data=audio_bytes,
                    mime_type="audio/wav"
                ),
                "Transcribe the spoken words accurately. "
                "Return only the transcription."
            ]
        )

        return response.text.strip()

    except Exception as e:
        st.error(f"Transcription failed: {e}")
        return None


# ============================================================
# CHAT RESPONSE
# ============================================================

def send_message(user_text):
    user_text = user_text.strip()

    if not user_text:
        return

    client = get_client()

    if not client:
        st.error(
            "Gemini API key is missing. Check Streamlit Secrets."
        )
        return

    chat = get_active_chat()

    chat["messages"].append({
        "role": "user",
        "content": user_text,
        "time": datetime.now().isoformat()
    })

    if chat["title"] == "New conversation":
        chat["title"] = user_text[:45]

    st.session_state.data["user_message_count"] += 1
    save_data()

    try:
        prompt = build_prompt(chat)

        response = client.models.generate_content(
            model=CHAT_MODEL,
            contents=prompt
        )

        answer = response.text or "I couldn't generate a response."

    except Exception as e:
        answer = (
            "I encountered a problem while processing that request. "
            f"Technical detail: {e}"
        )

    chat["messages"].append({
        "role": "assistant",
        "content": answer,
        "time": datetime.now().isoformat()
    })

    save_data()

    if (
        st.session_state.data["user_message_count"]
        % MEMORY_INTERVAL == 0
    ):
        extract_memories()

    st.session_state.latest_answer = answer
    st.rerun()


# ============================================================
# GOOGLE OAUTH — YOUTUBE
# ============================================================

def get_oauth_settings():
    try:
        settings = dict(st.secrets["google_oauth"])

        return {
            "client_id": settings["client_id"],
            "client_secret": settings["client_secret"],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uri": settings["redirect_uri"]
        }

    except Exception:
        return None


def create_oauth_flow(state=None):
    settings = get_oauth_settings()

    if not settings:
        return None

    client_config = {
        "web": {
            "client_id": settings["client_id"],
            "client_secret": settings["client_secret"],
            "auth_uri": settings["auth_uri"],
            "token_uri": settings["token_uri"],
            "redirect_uris": [settings["redirect_uri"]]
        }
    }

    flow = Flow.from_client_config(
        client_config,
        scopes=YOUTUBE_SCOPES,
        state=state
    )

    flow.redirect_uri = settings["redirect_uri"]

    return flow


def handle_oauth_callback():
    code = st.query_params.get("code")
    state = st.query_params.get("state")

    if not code:
        return

    expected_state = st.session_state.oauth_state

    if not expected_state or state != expected_state:
        st.error(
            "Google sign-in state could not be verified. "
            "Please try connecting again."
        )
        return

    try:
        flow = create_oauth_flow(state=expected_state)

        if not flow:
            st.error("Google OAuth settings are missing.")
            return

        flow.fetch_token(code=code)

        credentials = flow.credentials

        st.session_state.youtube_credentials = credentials.to_json()

        st.session_state.oauth_state = None
        st.query_params.clear()

        st.success("Google account connected successfully.")
        st.rerun()

    except Exception as e:
        st.error(f"Google sign-in failed: {e}")


def get_youtube_credentials():
    token_json = st.session_state.youtube_credentials

    if not token_json:
        return None

    try:
        credentials = Credentials.from_authorized_user_info(
            json.loads(token_json),
            YOUTUBE_SCOPES
        )

        if credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
            st.session_state.youtube_credentials = credentials.to_json()

        if not credentials.valid:
            return None

        return credentials

    except Exception:
        return None


def connect_youtube():
    flow = create_oauth_flow()

    if not flow:
        st.error(
            "Google OAuth settings are missing. "
            "Check your Streamlit Secrets."
        )
        return

    try:
        authorization_url, state = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            prompt="consent"
        )

        st.session_state.oauth_state = state

        st.link_button(
            "Continue with Google",
            authorization_url,
            use_container_width=True
        )

    except Exception as e:
        st.error(f"Could not start Google sign-in: {e}")


def get_youtube_service():
    credentials = get_youtube_credentials()

    if not credentials:
        return None

    try:
        return build(
            "youtube",
            "v3",
            credentials=credentials,
            cache_discovery=False
        )

    except Exception:
        return None


def show_youtube_information():
    youtube = get_youtube_service()

    if not youtube:
        st.info("Connect your Google account to view your YouTube channel.")
        return

    try:
        response = youtube.channels().list(
            part="snippet,statistics,contentDetails",
            mine=True
        ).execute()

        channels = response.get("items", [])

        if not channels:
            st.warning("No YouTube channel was found for this account.")
            return

        channel = channels[0]
        snippet = channel["snippet"]
        stats = channel["statistics"]

        st.subheader(snippet["title"])

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Subscribers",
            stats.get("subscriberCount", "Hidden")
        )

        col2.metric(
            "Views",
            stats.get("viewCount", "0")
        )

        col3.metric(
            "Videos",
            stats.get("videoCount", "0")
        )

        uploads_id = (
            channel["contentDetails"]["relatedPlaylists"]["uploads"]
        )

        uploads = youtube.playlistItems().list(
            part="snippet",
            playlistId=uploads_id,
            maxResults=5
        ).execute()

        st.subheader("Recent uploads")

        for item in uploads.get("items", []):
            video = item["snippet"]

            st.write(
                f"**{video['title']}**"
            )

    except Exception as e:
        st.error(f"Could not retrieve YouTube information: {e}")


# ============================================================
# CONVERSATION HANDOVER REPORT
# ============================================================

def generate_conversation_report():
    chat = get_active_chat()
    messages = chat["messages"]

    if not messages:
        return "There is no conversation to summarise yet."

    client = get_client()

    conversation = "\n".join(
        f"{m['role'].upper()}: {m['content']}"
        for m in messages
    )

    if not client:
        return conversation[-8000:]

    prompt = f"""
Create a detailed handover report for the next ChatGPT conversation.

Include:
1. Main topics discussed.
2. Important user preferences.
3. Decisions made.
4. Project progress.
5. Current problems.
6. Next steps.
7. Instructions for continuing without making the user repeat themselves.

Conversation:
{conversation}

Saved memories:
{json.dumps(st.session_state.data['memories'])}

Make the report clear, accurate and easy to copy.
Do not invent information.
"""

    try:
        response = client.models.generate_content(
            model=MEMORY_MODEL,
            contents=prompt
        )

        return response.text

    except Exception:
        return conversation[-8000:]


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown("## ✨ AURA")

    st.caption("PERSONAL INTELLIGENCE SYSTEM")

    st.divider()

    st.subheader("Voice settings")

    auto_voice = st.toggle(
        "Automatic voice replies",
        value=True
    )

    st.caption("Voice: Algieba")

    st.divider()

    st.subheader("Conversations")

    if st.button("＋ New conversation", use_container_width=True):
        create_new_chat()
        st.rerun()

    for chat in st.session_state.data["chats"]:
        col1, col2 = st.columns([4, 1])

        with col1:
            if st.button(
                chat["title"][:28],
                key=f"open_{chat['id']}",
                use_container_width=True
            ):
                st.session_state.data["active_chat"] = chat["id"]
                st.rerun()

        with col2:
            if st.button("×", key=f"delete_{chat['id']}"):
                delete_chat(chat["id"])
                st.rerun()

    st.divider()

    st.subheader("Saved memory")

    memories = st.session_state.data["memories"]

    if memories:
        for memory in memories:
            st.caption("• " + memory)

        if st.button("Clear saved memory"):
            st.session_state.data["memories"] = []
            save_data()
            st.rerun()
    else:
        st.caption("No memories saved yet.")

    st.divider()

    st.subheader("YouTube connection")

    if get_youtube_credentials():
        st.success("Google connected")

        if st.button("Disconnect Google"):
            st.session_state.youtube_credentials = None
            st.rerun()
    else:
        if st.button("Connect YouTube", use_container_width=True):
            connect_youtube()

    st.divider()

    st.subheader("Conversation handover")

    if st.button("Generate handover report", use_container_width=True):
        st.session_state.handover_report = generate_conversation_report()

    if "handover_report" in st.session_state:
        st.text_area(
            "Copy this report into your next conversation:",
            value=st.session_state.handover_report,
            height=250
        )

    st.divider()

    st.download_button(
        "Download data backup",
        data=json.dumps(
            st.session_state.data,
            indent=2
        ),
        file_name="aura_backup.json",
        mime="application/json",
        use_container_width=True
    )


# ============================================================
# MAIN INTERFACE
# ============================================================

st.markdown(
    '<div class="aura-title">A U R A</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="aura-subtitle">PERSONAL INTELLIGENCE SYSTEM</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="aura-core"></div>',
    unsafe_allow_html=True
)

st.markdown(
    "<p style='text-align:center;color:#80bce9;'>"
    "Your personal AI assistant is ready."
    "</p>",
    unsafe_allow_html=True
)


# ============================================================
# OAUTH CALLBACK
# ============================================================

handle_oauth_callback()


# ============================================================
# YOUTUBE DASHBOARD
# ============================================================

with st.expander("▶ YouTube channel dashboard"):

    if get_youtube_credentials():
        show_youtube_information()
    else:
        st.info("Connect Google in the sidebar to access your channel.")


# ============================================================
# CHAT DISPLAY
# ============================================================

chat = get_active_chat()

for message in chat["messages"]:

    avatar = "👤" if message["role"] == "user" else "✨"

    with st.chat_message(
        message["role"],
        avatar=avatar
    ):
        st.markdown(message["content"])


# ============================================================
# AUTOMATIC VOICE OUTPUT
# ============================================================

if "latest_answer" in st.session_state:

    answer = st.session_state.latest_answer
    del st.session_state.latest_answer

    if auto_voice:
        with st.spinner("Aura is preparing her voice..."):

            audio = generate_speech(answer)

        if audio:
            st.audio(
                audio,
                format="audio/wav",
                autoplay=True
            )


# ============================================================
# MICROPHONE INPUT
# ============================================================

st.markdown("### 🎙 Speak to Aura")

audio_file = st.audio_input("Record a voice message")

if audio_file is not None:

    audio_bytes = audio_file.getvalue()
    audio_hash = hashlib.sha256(audio_bytes).hexdigest()

    if audio_hash != st.session_state.last_audio_hash:

        st.session_state.last_audio_hash = audio_hash

        with st.spinner("Aura is listening..."):

            transcription = transcribe_audio(audio_bytes)

        if transcription:
            st.info(f"You said: {transcription}")
            send_message(transcription)


# ============================================================
# TEXT INPUT
# ============================================================

user_input = st.chat_input("Speak to Aura...")

if user_input:
    send_message(user_input)
