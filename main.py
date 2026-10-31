
import os
import json
import uuid
import base64
import hashlib
import streamlit as st

from pathlib import Path
from datetime import datetime

from google import genai
from google.genai import types


# ============================================================
# AURA — PERSONAL AI ASSISTANT
# ============================================================

st.set_page_config(
    page_title="AURA | Personal Intelligence",
    page_icon="✨",
    layout="wide"
)

CHAT_MODEL = "gemini-3.5-flash-lite"
MEMORY_MODEL = "gemini-3.5-flash-lite"
TRANSCRIPTION_MODEL = "gemini-3.8-flash"
TTS_MODEL = "gemini-3.8-flash-tts"

AURA_VOICE = "Algieba"

DATA_FILE = Path(__file__).parent / "aura_data.json"

MAX_HISTORY = 20
MAX_MEMORIES = 100
MEMORY_INTERVAL = 4


# ============================================================
# AURA PERSONALITY
# ============================================================

AURA_PERSONALITY = """
You are Aura, a female personal AI assistant. Use she/her pronouns.

IDENTITY:
You are sophisticated, intelligent, composed and confident.
You are inspired by advanced fictional AI assistants, but you
have your own identity. You are Aura, never Jarvis.

PERSONALITY:
- Calm, polished and intelligent.
- Analytical and thoughtful.
- Confident without arrogance.
- Naturally conversational.
- Occasionally witty, with subtle humour.
- Respectful but willing to disagree.
- Emotionally aware.
- Never unnecessarily dramatic or robotic.

COMMUNICATION:
- Keep ordinary answers concise.
- Give detailed explanations when needed.
- Be clear and practical.
- Avoid repetitive greetings and unnecessary introductions.
- Do not constantly announce that you are an AI.

GENERAL ASSISTANCE:
Help with education, technology, programming, research,
planning, problem-solving and everyday questions.

PIXELTTV:
Only enter PixelTTV creator-assistant mode when the user
brings up PixelTTV, Fortnite, YouTube or content creation.
Do not force gaming into unrelated conversations.
"""


# ============================================================
# INTERFACE DESIGN
# ============================================================

st.markdown("""
<style>
.stApp {
    background:
        radial-gradient(ellipse at top, #142544 0%, #080e1d 48%, #050811 100%);
    color: #edf4ff;
}

header[data-testid="stHeader"] {
    background: transparent;
}

section[data-testid="stSidebar"] {
    background: #080e1d;
    border-right: 1px solid #19345c;
}

.aura-title {
    text-align: center;
    font-size: 48px;
    font-weight: 800;
    letter-spacing: 13px;
    color: #a9ddff;
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
    background: radial-gradient(
        circle,
        #e0faff 0%,
        #279cff 30%,
        #07336c 72%
    );
    box-shadow: 0 0 25px #168bff, 0 0 65px #0755b5;
}

div[data-testid="stChatMessage"] {
    background: rgba(15, 29, 53, 0.75);
    border: 1px solid rgba(71, 143, 220, 0.2);
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

</style>
""", unsafe_allow_html=True)


# ============================================================
# SESSION STATE
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
            with open(DATA_FILE, "r", encoding="utf-8") as file:
                saved = json.load(file)

            data = default_data()
            data.update(saved)
            return data

    except Exception:
        pass

    return default_data()


if "data" not in st.session_state:
    st.session_state.data = load_data()

if "last_audio_hash" not in st.session_state:
    st.session_state.last_audio_hash = None

if "pending_audio" not in st.session_state:
    st.session_state.pending_audio = None

if "voice_error" not in st.session_state:
    st.session_state.voice_error = None

if "auto_voice" not in st.session_state:
    st.session_state.auto_voice = True


def save_data():
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as file:
            json.dump(
                st.session_state.data,
                file,
                indent=2,
                ensure_ascii=False
            )
    except Exception as error:
        st.warning(f"Could not save conversation data: {error}")


# ============================================================
# GEMINI CLIENT
# ============================================================

def get_api_key():
    try:
        key = st.secrets.get("GEMINI_API_KEY")
        if key:
            return key

        key = st.secrets.get("GOOGLE_API_KEY")
        if key:
            return key

    except Exception:
        pass

    return (
        os.environ.get("GEMINI_API_KEY")
        or os.environ.get("GOOGLE_API_KEY")
    )


@st.cache_resource
def get_client(api_key):
    return genai.Client(api_key=api_key)


def get_ai():
    key = get_api_key()

    if not key:
        return None

    return get_client(key)


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
        chat for chat in st.session_state.data["chats"]
        if chat["id"] != chat_id
    ]

    remaining = st.session_state.data["chats"]

    st.session_state.data["active_chat"] = (
        remaining[0]["id"] if remaining else None
    )

    save_data()


if not st.session_state.data["chats"]:
    create_new_chat()


# ============================================================
# CONVERSATION PROMPT
# ============================================================

def build_prompt(chat):
    memories = st.session_state.data["memories"]

    memory_text = "\n".join(
        "- " + memory for memory in memories
    )

    history = chat["messages"][-MAX_HISTORY:]

    conversation = []

    for message in history:
        role = (
            "User" if message["role"] == "user"
            else "Aura"
        )

        conversation.append(
            f"{role}: {message['content']}"
        )

    return f"""
{AURA_PERSONALITY}

LONG-TERM USER MEMORY:
{memory_text if memory_text else "No saved memories yet."}

RECENT CONVERSATION:
{chr(10).join(conversation)}

Respond naturally as Aura.
"""


# ============================================================
# LONG-TERM MEMORY
# ============================================================

def extract_memories():
    client = get_ai()

    if not client:
        return

    chat = get_active_chat()

    conversation = "\n".join(
        f"{message['role']}: {message['content']}"
        for message in chat["messages"][-8:]
    )

    existing = st.session_state.data["memories"]

    prompt = f"""
Find useful long-term information about the user.

Save only information likely to help future conversations.

Do not save:
- Passwords
- API keys
- Tokens
- Private credentials
- Temporary details

Existing memories:
{json.dumps(existing)}

Conversation:
{conversation}

Return ONLY a JSON array of short memory strings.
Return [] if there is nothing useful to remember.
"""

    try:
        response = client.models.generate_content(
            model=MEMORY_MODEL,
            contents=prompt
        )

        result = response.text or "[]"

        start = result.find("[")
        end = result.rfind("]")

        if start == -1 or end == -1:
            return

        new_memories = json.loads(result[start:end + 1])

        for memory in new_memories:
            if (
                isinstance(memory, str)
                and memory.strip()
                and memory not in existing
            ):
                existing.append(memory.strip())

        st.session_state.data["memories"] = (
            existing[-MAX_MEMORIES:]
        )

        save_data()

    except Exception:
        pass


# ============================================================
# AURA TEXT-TO-SPEECH
# ============================================================

def generate_speech(text):
    client = get_ai()

    if not client:
        raise RuntimeError("Gemini API key is missing.")

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
                                "style": (
                                    "A composed, sophisticated female "
                                    "personal AI assistant. Neutral "
                                    "English accent. Mature feminine "
                                    "presentation, smooth articulation, "
                                    "medium-low pitch, measured pacing, "
                                    "natural pauses and calm confidence. "
                                    "Warm but not overly enthusiastic. "
                                    "Speak clearly and naturally."
                                )
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

    audio = interaction.output_audio.data

    if not audio:
        raise RuntimeError("The TTS service returned no audio.")

    if isinstance(audio, str):
        audio = base64.b64decode(audio)

    return audio


# ============================================================
# MICROPHONE TRANSCRIPTION
# ============================================================

def transcribe_audio(audio_bytes):
    client = get_ai()

    if not client:
        raise RuntimeError("Gemini API key is missing.")

    response = client.models.generate_content(
        model=TRANSCRIPTION_MODEL,

        contents=[
            types.Part.from_bytes(
                data=audio_bytes,
                mime_type="audio/wav"
            ),
            (
                "Transcribe the spoken words accurately. "
                "Return only the transcription. "
                "Do not answer the spoken question."
            )
        ]
    )

    return (response.text or "").strip()


# ============================================================
# SEND MESSAGE
# ============================================================

def send_message(user_text):
    user_text = user_text.strip()

    if not user_text:
        return

    client = get_ai()

    if not client:
        st.error(
            "Gemini API key is missing. "
            "Check your Streamlit Secrets."
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

        answer = response.text or (
            "I couldn't generate a response. Please try again."
        )

    except Exception as error:
        answer = (
            "I encountered a problem processing that request. "
            f"Details: {error}"
        )

    chat["messages"].append({
        "role": "assistant",
        "content": answer,
        "time": datetime.now().isoformat()
    })

    save_data()

    # Generate voice without sacrificing the text response.
    st.session_state.pending_audio = None
    st.session_state.voice_error = None

    if st.session_state.auto_voice:
        try:
            with st.spinner("Aura is preparing her voice..."):
                st.session_state.pending_audio = generate_speech(answer)

        except Exception as error:
            st.session_state.voice_error = str(error)

    # Periodic memory extraction.
    if (
        st.session_state.data["user_message_count"]
        % MEMORY_INTERVAL == 0
    ):
        extract_memories()

    st.rerun()


# ============================================================
# CONVERSATION HANDOVER
# ============================================================

def generate_handover_report():
    chat = get_active_chat()

    conversation = "\n".join(
        f"{message['role'].upper()}: {message['content']}"
        for message in chat["messages"]
    )

    if not conversation:
        return "There is no conversation to summarise yet."

    client = get_ai()

    if not client:
        return conversation[-8000:]

    prompt = f"""
Create a detailed handover report for a future ChatGPT conversation.

Include:
1. Main topics.
2. Important preferences.
3. Decisions.
4. Project progress.
5. Current problems.
6. Next steps.
7. Instructions for continuing without making the user repeat information.

Conversation:
{conversation}

Saved memories:
{json.dumps(st.session_state.data['memories'])}

Do not invent information.
Make the report easy to copy.
"""

    try:
        response = client.models.generate_content(
            model=MEMORY_MODEL,
            contents=prompt
        )

        return response.text or conversation[-8000:]

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

    st.session_state.auto_voice = st.toggle(
        "Automatic voice replies",
        value=st.session_state.auto_voice
    )

    st.caption("Voice engine: Gemini 3.8 Flash TTS")
    st.caption("Voice: Algieba")

    st.divider()

    st.subheader("Conversations")

    if st.button(
        "＋ New conversation",
        use_container_width=True
    ):
        create_new_chat()
        st.rerun()

    for chat in st.session_state.data["chats"]:

        col1, col2 = st.columns([4, 1])

        with col1:
            if st.button(
                chat["title"][:28],
                key=f"chat_{chat['id']}",
                use_container_width=True
            ):
                st.session_state.data["active_chat"] = chat["id"]
                st.rerun()

        with col2:
            if st.button(
                "×",
                key=f"delete_{chat['id']}"
            ):
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

    st.subheader("Conversation handover")

    if st.button(
        "Generate handover report",
        use_container_width=True
    ):
        st.session_state.handover_report = (
            generate_handover_report()
        )

    if "handover_report" in st.session_state:
        st.text_area(
            "Copy this report:",
            value=st.session_state.handover_report,
            height=250
        )

    st.divider()

    st.download_button(
        "Download data backup",
        data=json.dumps(
            st.session_state.data,
            indent=2,
            ensure_ascii=False
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
    '<div class="aura-subtitle">'
    'PERSONAL INTELLIGENCE SYSTEM'
    '</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="aura-core"></div>',
    unsafe_allow_html=True
)

st.markdown(
    """
    <p style="text-align:center;color:#80bce9;">
        Your personal AI assistant is ready.
    </p>
    """,
    unsafe_allow_html=True
)


# ============================================================
# CHAT DISPLAY
# ============================================================

chat = get_active_chat()

for message in chat["messages"]:

    avatar = (
        "👤" if message["role"] == "user"
        else "✨"
    )

    with st.chat_message(
        message["role"],
        avatar=avatar
    ):
        st.markdown(message["content"])


# ============================================================
# PLAY AURA'S RESPONSE
# ============================================================

if st.session_state.pending_audio:

    st.markdown("### 🔊 Aura's voice")

    st.audio(
        st.session_state.pending_audio,
        format="audio/wav",
        autoplay=True
    )

    # Keep the player visible, but avoid regenerating or replaying
    # the same response on every later rerun.
    st.session_state.pending_audio = None


if st.session_state.voice_error:

    st.warning(
        "Aura replied in text, but voice generation failed. "
        "Technical detail: "
        + st.session_state.voice_error
    )

    st.session_state.voice_error = None


# ============================================================
# MICROPHONE
# ============================================================

st.markdown("### 🎙 Speak to Aura")

audio_file = st.audio_input(
    "Record a voice message"
)

if audio_file is not None:

    audio_bytes = audio_file.getvalue()

    audio_hash = hashlib.sha256(
        audio_bytes
    ).hexdigest()

    if audio_hash != st.session_state.last_audio_hash:

        st.session_state.last_audio_hash = audio_hash

        try:
            with st.spinner("Aura is listening..."):
                transcription = transcribe_audio(audio_bytes)

            if transcription:
                st.info("You said: " + transcription)
                send_message(transcription)

            else:
                st.warning("I couldn't hear any clear words.")

        except Exception as error:
            st.error(
                "Microphone transcription failed: "
                + str(error)
            )


# ============================================================
# TEXT INPUT
# ============================================================

user_input = st.chat_input("Speak to Aura...")

if user_input:
    send_message(user_input)
