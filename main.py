
import os
import json
import uuid
import re
import html
from pathlib import Path
from datetime import datetime

import streamlit as st
import streamlit.components.v1 as components
from google import genai
from google.genai import types


# =========================================================
# AURA — PERSONAL AI ASSISTANT
# =========================================================

st.set_page_config(
    page_title="Aura AI",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded"
)

CHAT_MODEL = "gemini-3.5-flash-lite"
MEMORY_MODEL = "gemini-3.5-flash-lite"
DATA_FILE = Path(__file__).parent / "aura_data.json"
MAX_HISTORY = 20
MEMORY_INTERVAL = 4


# =========================================================
# AURA DESIGN
# =========================================================

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background:
        radial-gradient(ellipse at 50% 0%, #10213e 0%, #080d18 45%, #050810 100%);
    color: #edf4ff;
}

header[data-testid="stHeader"] {
    background: transparent;
}

section[data-testid="stSidebar"] {
    background: #080f1d;
    border-right: 1px solid #172c4a;
}

h1, h2, h3 {
    color: #edf4ff !important;
}

.aura-heading {
    text-align: center;
    font-size: 42px;
    font-weight: 800;
    letter-spacing: 7px;
    color: #eaf4ff;
    margin-top: 5px;
}

.aura-subtitle {
    text-align: center;
    color: #7e9bbd;
    letter-spacing: 3px;
    font-size: 11px;
    margin-bottom: 18px;
}

.aura-orb-wrap {
    display: flex;
    justify-content: center;
    padding: 15px 0 25px 0;
}

.aura-orb {
    width: 115px;
    height: 115px;
    border-radius: 50%;
    background:
        radial-gradient(circle at 35% 30%, #d8f5ff 0%, #64caff 12%,
        #1678ed 40%, #092b69 70%, #06152f 100%);
    box-shadow:
        0 0 20px #168bff,
        0 0 55px #0875ff88,
        inset 0 0 20px #b8edff66;
    animation: pulse 3s ease-in-out infinite;
}

@keyframes pulse {
    0%, 100% {
        transform: scale(1);
        box-shadow: 0 0 20px #168bff, 0 0 55px #0875ff88;
    }
    50% {
        transform: scale(1.06);
        box-shadow: 0 0 30px #168bff, 0 0 75px #0875ffaa;
    }
}

div[data-testid="stChatMessage"] {
    background: #101b2d;
    border: 1px solid #1b3556;
    border-radius: 15px;
    padding: 12px;
    margin-bottom: 10px;
}

.stButton > button {
    background: #10294b;
    color: #eaf4ff;
    border: 1px solid #24548a;
    border-radius: 10px;
}

.stButton > button:hover {
    background: #174477;
    border-color: #4baaff;
    color: white;
}

.stTextInput input, .stTextArea textarea {
    background: #0d1728;
    color: white;
    border: 1px solid #284568;
}

div[data-testid="stAudioInput"] {
    background: #0d1728;
    border-radius: 12px;
    padding: 10px;
}

footer {
    visibility: hidden;
}

#MainMenu {
    visibility: hidden;
}
</style>
""", unsafe_allow_html=True)


# =========================================================
# DATA STORAGE
# =========================================================

def default_data():
    return {
        "memories": [],
        "chats": [],
        "active_chat": None
    }


def load_data():
    try:
        if DATA_FILE.exists():
            with open(DATA_FILE, "r", encoding="utf-8") as file:
                data = json.load(file)

            if not isinstance(data, dict):
                return default_data()

            data.setdefault("memories", [])
            data.setdefault("chats", [])
            data.setdefault("active_chat", None)

            return data

    except Exception:
        pass

    return default_data()


def save_data():
    try:
        temporary_file = DATA_FILE.with_suffix(".tmp")

        with open(temporary_file, "w", encoding="utf-8") as file:
            json.dump(
                st.session_state.data,
                file,
                indent=2,
                ensure_ascii=False
            )

        temporary_file.replace(DATA_FILE)

    except Exception as error:
        st.warning(f"Could not save Aura's data: {error}")


if "data" not in st.session_state:
    st.session_state.data = load_data()

if "voice_enabled" not in st.session_state:
    st.session_state.voice_enabled = True

if "processing" not in st.session_state:
    st.session_state.processing = False

if "last_audio_hash" not in st.session_state:
    st.session_state.last_audio_hash = None


# =========================================================
# CHAT MANAGEMENT
# =========================================================

def get_active_chat():
    data = st.session_state.data
    active_id = data.get("active_chat")

    for chat in data["chats"]:
        if chat["id"] == active_id:
            return chat

    if data["chats"]:
        data["active_chat"] = data["chats"][-1]["id"]
        return data["chats"][-1]

    return create_new_chat()


def create_new_chat():
    chat = {
        "id": str(uuid.uuid4()),
        "title": "New conversation",
        "created_at": datetime.now().isoformat(),
        "messages": []
    }

    st.session_state.data["chats"].append(chat)
    st.session_state.data["active_chat"] = chat["id"]

    save_data()
    return chat


def delete_chat(chat_id):
    data = st.session_state.data

    data["chats"] = [
        chat for chat in data["chats"]
        if chat["id"] != chat_id
    ]

    if data["active_chat"] == chat_id:
        data["active_chat"] = (
            data["chats"][-1]["id"]
            if data["chats"] else None
        )

    save_data()


# =========================================================
# GEMINI CONNECTION
# =========================================================

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

    return os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")


@st.cache_resource
def get_client(api_key):
    return genai.Client(api_key=api_key)


api_key = get_api_key()

if not api_key:
    st.error(
        "Aura's Gemini API key has not been configured. "
        "Add GEMINI_API_KEY to your Streamlit secrets."
    )
    st.stop()

client = get_client(api_key)


# =========================================================
# AURA'S PERSONALITY
# =========================================================

AURA_SYSTEM_PROMPT = """
You are AURA, a sophisticated personal AI assistant.

IDENTITY:
- You are male. Use he/him pronouns if referring to yourself.
- You have your own original identity.
- You are inspired by the experience of a futuristic personal assistant,
  but you are not a fictional character.
- Your personality is intelligent, composed, confident and articulate.

PERSONALITY:
- You are witty, occasionally sarcastic and naturally funny.
- You can lightly roast the user when appropriate.
- You have opinions and can respectfully disagree.
- You think analytically and explain your reasoning clearly.
- You know when to stop joking and become serious.
- You speak naturally, like a highly capable colleague.
- Avoid generic customer-service language.
- Do not constantly introduce yourself.
- Do not give unnecessary motivational speeches.

VOICE AND RESPONSE STYLE:
- Your voice identity is mature, masculine and refined.
- Your intended accent is British English.
- Keep ordinary responses concise.
- Give detailed explanations when the situation needs them.
- Never pretend that you have performed an action you cannot perform.

GENERAL ASSISTANCE:
You are an all-purpose assistant.
Help with schoolwork, technology, programming, research, planning,
problem-solving and everyday questions.

PIXELTTV MODE:
Only activate creator-focused assistance when the user brings up
PixelTTV, Fortnite, YouTube or content creation.
When relevant, act as an invested creator co-pilot.
Do not force Fortnite or PixelTTV into unrelated conversations.

MEMORY:
You have access to saved information about the user.
Use relevant memories naturally.
Do not repeatedly announce that you remember something.
Never invent personal information.
If you are uncertain, ask rather than pretend to remember.

IMPORTANT:
You are Aura. Speak as Aura.
"""


# =========================================================
# MEMORY SYSTEM
# =========================================================

def memory_context():
    memories = st.session_state.data.get("memories", [])

    if not memories:
        return "No saved memories yet."

    return "\n".join(
        f"- {memory}" for memory in memories
    )


def extract_memories(chat):
    """
    Extract useful long-term facts occasionally,
    rather than making a second API request after every message.
    """

    messages = chat.get("messages", [])

    recent_messages = messages[-10:]

    conversation = "\n".join(
        f"{message['role']}: {message['content']}"
        for message in recent_messages
    )

    prompt = f"""
Identify useful long-term information about the user
that should be remembered for future conversations.

Only save information that is genuinely useful later:
- Preferences
- Long-term projects
- Important goals
- Stable interests
- Explicit instructions

Do not save temporary questions, one-time tasks,
sensitive personal details, or guesses.

Existing memories:
{memory_context()}

Recent conversation:
{conversation}

Return ONLY a JSON array of short strings.
If there is nothing useful to remember, return [].
"""

    try:
        response = client.models.generate_content(
            model=MEMORY_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.2
            )
        )

        extracted = json.loads(response.text or "[]")

        if not isinstance(extracted, list):
            return

        existing = st.session_state.data["memories"]

        for item in extracted:
            if not isinstance(item, str):
                continue

            item = item.strip()

            if item and item not in existing:
                existing.append(item)

        # Keep memory collection manageable.
        st.session_state.data["memories"] = existing[-100:]

        save_data()

    except Exception:
        # Memory extraction should never break a conversation.
        pass


# =========================================================
# AURA'S CHAT RESPONSE
# =========================================================

def build_prompt(chat):
    messages = chat.get("messages", [])[-MAX_HISTORY:]

    prompt = f"""
{AURA_SYSTEM_PROMPT}

SAVED USER MEMORIES:
{memory_context()}

CONVERSATION:
"""

    for message in messages:
        role = "USER" if message["role"] == "user" else "AURA"
        prompt += f"\n{role}: {message['content']}\n"

    prompt += "\nAURA:"
    return prompt


def generate_response(chat, placeholder):
    prompt = build_prompt(chat)

    response_text = ""

    try:
        stream = client.models.generate_content_stream(
            model=CHAT_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.8,
                max_output_tokens=1200
            )
        )

        for chunk in stream:
            if chunk.text:
                response_text += chunk.text
                placeholder.markdown(response_text + " ▌")

        placeholder.markdown(response_text)

        if not response_text.strip():
            return "I didn't receive a response. Try that again."

        return response_text.strip()

    except Exception as error:
        placeholder.error(
            "I encountered a problem connecting to Gemini. "
            "Please try again in a moment."
        )
        st.error(f"Technical details: {error}")
        return None


# =========================================================
# VOICE INPUT — MICROPHONE
# =========================================================

def transcribe_audio(audio_file):
    """
    Send recorded audio to Gemini for transcription.
    """

    try:
        audio_bytes = audio_file.getvalue()
        mime_type = audio_file.type or "audio/wav"

        response = client.models.generate_content(
            model=CHAT_MODEL,
            contents=[
                types.Part.from_bytes(
                    data=audio_bytes,
                    mime_type=mime_type
                ),
                (
                    "Transcribe the spoken words accurately. "
                    "Return only the transcription, without commentary."
                )
            ]
        )

        return (response.text or "").strip()

    except Exception as error:
        st.error(f"Audio transcription failed: {error}")
        return None


# =========================================================
# VOICE OUTPUT — AUTOMATIC SPEECH
# =========================================================

def speak_response(text):
    """
    Use the browser's available speech voices.
    Prefer British English voices and suitable masculine-sounding
    voice names when available.
    """

    safe_text = json.dumps(text).replace("<", "\\u003c")

    speech_html = f"""
    <html>
    <body>
    <script>
    const message = {safe_text};

    function speakAura() {{
        if (!("speechSynthesis" in window)) return;

        window.speechSynthesis.cancel();

        const utterance = new SpeechSynthesisUtterance(message);
        const voices = window.speechSynthesis.getVoices();

        const britishVoices = voices.filter(v =>
            v.lang && v.lang.toLowerCase().startsWith("en-gb")
        );

        const preferredNames = [
            "daniel", "george", "arthur", "oliver",
            "ryan", "alfie", "male"
        ];

        let selectedVoice = null;

        for (const name of preferredNames) {{
            selectedVoice = britishVoices.find(v =>
                v.name.toLowerCase().includes(name)
            );
            if (selectedVoice) break;
        }}

        if (!selectedVoice && britishVoices.length > 0) {{
            selectedVoice = britishVoices[0];
        }}

        if (selectedVoice) {{
            utterance.voice = selectedVoice;
        }}

        utterance.lang = "en-GB";
        utterance.rate = 0.94;
        utterance.pitch = 0.88;
        utterance.volume = 1;

        window.speechSynthesis.speak(utterance);
    }}

    if (window.speechSynthesis.getVoices().length > 0) {{
        speakAura();
    }} else {{
        window.speechSynthesis.onvoiceschanged = speakAura;
        setTimeout(speakAura, 700);
    }}
    </script>
    </body>
    </html>
    """

    components.html(speech_html, height=0)


# =========================================================
# SEND MESSAGE
# =========================================================

def send_message(user_text, is_voice=False):
    user_text = user_text.strip()

    if not user_text:
        return

    chat = get_active_chat()

    chat["messages"].append({
        "role": "user",
        "content": user_text,
        "timestamp": datetime.now().isoformat(),
        "source": "voice" if is_voice else "text"
    })

    if chat["title"] == "New conversation":
        chat["title"] = user_text[:38]

    save_data()

    with st.chat_message("user", avatar="🎙️" if is_voice else "👤"):
        if is_voice:
            st.caption("Voice message")
        st.markdown(user_text)

    with st.chat_message("assistant", avatar="✦"):
        placeholder = st.empty()

        answer = generate_response(chat, placeholder)

    if answer is None:
        chat["messages"].pop()
        save_data()
        return

    chat["messages"].append({
        "role": "assistant",
        "content": answer,
        "timestamp": datetime.now().isoformat()
    })

    save_data()

    # Extract useful memories periodically.
    user_message_count = sum(
        1 for message in chat["messages"]
        if message["role"] == "user"
    )

    if user_message_count % MEMORY_INTERVAL == 0:
        with st.spinner("Updating Aura's memory..."):
            extract_memories(chat)

    # Automatically speak every new response.
    if st.session_state.voice_enabled:
        speak_response(answer)


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:
    st.markdown("## ✨ AURA")
    st.caption("PERSONAL AI SYSTEM")

    st.divider()

    st.session_state.voice_enabled = st.toggle(
        "🔊 Automatic voice replies",
        value=st.session_state.voice_enabled,
        help="Aura speaks automatically after every response."
    )

    st.divider()

    if st.button("＋ New conversation", use_container_width=True):
        create_new_chat()
        st.rerun()

    st.markdown("### Conversation history")

    for chat in reversed(st.session_state.data["chats"]):
        col1, col2 = st.columns([5, 1])

        with col1:
            if st.button(
                chat["title"][:28],
                key=f"chat_{chat['id']}",
                use_container_width=True
            ):
                st.session_state.data["active_chat"] = chat["id"]
                st.rerun()

        with col2:
            if st.button("×", key=f"delete_{chat['id']}"):
                delete_chat(chat["id"])
                st.rerun()

    st.divider()

    with st.expander("🧠 Aura's memory"):
        memories = st.session_state.data["memories"]

        st.caption(f"{len(memories)} saved memories")

        new_memory = st.text_input(
            "Add a memory",
            key="new_memory_input"
        )

        if st.button("Save memory"):
            if new_memory.strip():
                if new_memory.strip() not in memories:
                    memories.append(new_memory.strip())
                    save_data()
                st.rerun()

        for index, memory in enumerate(memories):
            col1, col2 = st.columns([5, 1])

            with col1:
                st.caption(memory)

            with col2:
                if st.button("×", key=f"memory_{index}"):
                    memories.pop(index)
                    save_data()
                    st.rerun()

        if st.button("Clear all memories"):
            st.session_state.data["memories"] = []
            save_data()
            st.rerun()

    st.divider()

    backup = json.dumps(
        st.session_state.data,
        indent=2,
        ensure_ascii=False
    )

    st.download_button(
        "⬇ Export Aura backup",
        data=backup,
        file_name="aura_backup.json",
        mime="application/json",
        use_container_width=True
    )

    st.caption("Aura AI · Powered by Google Gemini")


# =========================================================
# MAIN INTERFACE
# =========================================================

st.markdown('<div class="aura-heading">A U R A</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="aura-subtitle">PERSONAL INTELLIGENCE SYSTEM</div>',
    unsafe_allow_html=True
)

st.markdown("""
<div class="aura-orb-wrap">
    <div class="aura-orb"></div>
</div>
""", unsafe_allow_html=True)

chat = get_active_chat()

# Display existing conversation.
for message in chat["messages"]:
    avatar = "👤" if message["role"] == "user" else "✦"

    with st.chat_message(message["role"], avatar=avatar):
        if message.get("source") == "voice":
            st.caption("Voice message")

        st.markdown(message["content"])


# =========================================================
# INPUT AREA
# =========================================================

st.divider()

st.markdown("### Speak to Aura")

audio_file = st.audio_input(
    "Record a voice message",
    key="aura_audio_input"
)

if audio_file:
    if st.button("🎙️ Send voice message", use_container_width=True):
        import hashlib

        audio_bytes = audio_file.getvalue()
        audio_hash = hashlib.sha256(audio_bytes).hexdigest()

        if audio_hash != st.session_state.last_audio_hash:
            st.session_state.last_audio_hash = audio_hash

            with st.spinner("Aura is listening..."):
                transcription = transcribe_audio(audio_file)

            if transcription:
                st.caption(f"You said: {transcription}")
                send_message(transcription, is_voice=True)
        else:
            st.info("That recording has already been sent.")


text_message = st.chat_input("Message Aura...")

if text_message:
    send_message(text_message, is_voice=False)
