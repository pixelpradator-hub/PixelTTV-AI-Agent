
import os
import json
import uuid
import hashlib
import base64
import re
from pathlib import Path
from datetime import datetime

import streamlit as st
from google import genai


# ==========================================
# AURA - PERSONAL AI ASSISTANT
# ==========================================

st.set_page_config(
    page_title="Aura AI",
    page_icon="✨",
    layout="wide"
)

CHAT_MODEL = "gemini-3.5-flash-lite"
MEMORY_MODEL = "gemini-3.5-flash-lite"
TTS_MODEL = "gemini-3.8-flash-tts"

AURA_VOICE = "Algieba"

DATA_FILE = Path(__file__).parent / "aura_data.json"

MAX_HISTORY = 20
MAX_MEMORIES = 100
MEMORY_INTERVAL = 4


# ==========================================
# DESIGN
# ==========================================

st.markdown("""
<style>
.stApp {
    background: radial-gradient(
        circle at top,
        #10213c 0%,
        #080d18 45%,
        #050811 100%
    );
    color: #eaf3ff;
}

header[data-testid="stHeader"] {
    background: transparent;
}

.block-container {
    max-width: 1000px;
    padding-top: 2rem;
}

h1, h2, h3 {
    color: #eaf3ff;
}

.aura-title {
    text-align: center;
    font-size: 38px;
    font-weight: 700;
    letter-spacing: 12px;
    color: #8acbff;
    text-shadow: 0 0 20px #168bff;
}

.aura-subtitle {
    text-align: center;
    color: #829bb8;
    letter-spacing: 4px;
    font-size: 11px;
}

div.stButton > button {
    border-radius: 12px;
    border: 1px solid #2678bd;
    background: #102b49;
    color: white;
}

div.stButton > button:hover {
    border-color: #66c3ff;
    background: #17416b;
    color: white;
}

[data-testid="stChatMessage"] {
    border: 1px solid rgba(80, 150, 220, 0.15);
    border-radius: 14px;
    background: rgba(12, 25, 43, 0.7);
}
</style>
""", unsafe_allow_html=True)


# ==========================================
# DATA STORAGE
# ==========================================

def default_data():
    return {
        "chats": [],
        "active_chat": None,
        "memories": []
    }


def load_data():
    try:
        if DATA_FILE.exists():
            with open(DATA_FILE, "r", encoding="utf-8") as file:
                data = json.load(file)

            if not isinstance(data, dict):
                return default_data()

            data.setdefault("chats", [])
            data.setdefault("active_chat", None)
            data.setdefault("memories", [])

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
        st.warning(f"Could not save local data: {error}")


def create_new_chat():
    chat = {
        "id": str(uuid.uuid4()),
        "title": "New conversation",
        "messages": [],
        "created": datetime.now().isoformat()
    }

    st.session_state.data["chats"].append(chat)
    st.session_state.data["active_chat"] = chat["id"]

    st.session_state.report = None
    save_data()


def get_active_chat():
    active_id = st.session_state.data.get("active_chat")

    for chat in st.session_state.data["chats"]:
        if chat["id"] == active_id:
            return chat

    if st.session_state.data["chats"]:
        chat = st.session_state.data["chats"][-1]
        st.session_state.data["active_chat"] = chat["id"]
        return chat

    create_new_chat()

    return st.session_state.data["chats"][-1]


def delete_chat(chat_id):
    st.session_state.data["chats"] = [
        chat for chat in st.session_state.data["chats"]
        if chat["id"] != chat_id
    ]

    st.session_state.data["active_chat"] = None

    create_new_chat()
    save_data()


# ==========================================
# SESSION STATE
# ==========================================

if "data" not in st.session_state:
    st.session_state.data = load_data()

if "voice_enabled" not in st.session_state:
    st.session_state.voice_enabled = True

if "last_audio_hash" not in st.session_state:
    st.session_state.last_audio_hash = None

if "report" not in st.session_state:
    st.session_state.report = None

if "client" not in st.session_state:
    st.session_state.client = None


# ==========================================
# API CONNECTION
# ==========================================

def get_api_key():
    key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

    if not key:
        try:
            key = st.secrets.get("GEMINI_API_KEY")
            if not key:
                key = st.secrets.get("GOOGLE_API_KEY")
        except Exception:
            pass

    return key


def get_client():
    if st.session_state.client is None:
        api_key = get_api_key()

        if not api_key:
            return None

        st.session_state.client = genai.Client(api_key=api_key)

    return st.session_state.client


# ==========================================
# AURA PERSONALITY
# ==========================================

AURA_PERSONALITY = """
You are Aura, a sophisticated personal AI assistant.

You are male and use he/him pronouns.

PERSONALITY:
- Intelligent, composed and confident.
- Witty, occasionally sarcastic and naturally funny.
- You can respectfully disagree with the user.
- You analyse problems carefully.
- You know when to be serious.
- You speak naturally, not like a customer-service chatbot.
- Keep answers concise unless detail is needed.

IDENTITY:
You are Aura. You are inspired by the experience of a
futuristic personal assistant, but you have your own identity.

GENERAL ASSISTANCE:
Help with schoolwork, technology, programming, research,
planning, problem-solving and everyday questions.

PIXELTTV MODE:
Only become a dedicated PixelTTV creator co-pilot when
the user brings up PixelTTV, Fortnite, YouTube or content
creation.

Do not randomly bring up Fortnite or PixelTTV in unrelated
conversations.

MEMORY:
Use the supplied saved memories and conversation history.
Do not pretend to remember information that is not supplied.
"""


# ==========================================
# CHAT PROMPT
# ==========================================

def build_prompt(chat):
    memories = st.session_state.data.get("memories", [])

    memory_text = "\n".join(
        f"- {memory}" for memory in memories
    )

    history = chat["messages"][-MAX_HISTORY:]

    conversation = ""

    for message in history:
        role = message["role"].upper()
        content = message["content"]

        conversation += f"\n{role}: {content}\n"

    return f"""
{AURA_PERSONALITY}

SAVED MEMORIES:
{memory_text if memory_text else "No saved memories yet."}

CONVERSATION:
{conversation}

AURA:
"""


# ==========================================
# MEMORY SYSTEM
# ==========================================

def extract_memories(chat):
    client = get_client()

    if not client:
        return

    recent_messages = chat["messages"][-12:]

    conversation = "\n".join(
        f"{m['role']}: {m['content']}"
        for m in recent_messages
    )

    existing = st.session_state.data.get("memories", [])

    prompt = f"""
Identify important information from this conversation
that would be useful to remember in future conversations.

Only include useful, relatively lasting information:
preferences, ongoing projects, important decisions
and user instructions.

Do not save temporary questions or random conversation.

Existing memories:
{json.dumps(existing, ensure_ascii=False)}

Conversation:
{conversation}

Return ONLY a JSON array of short memory strings.
If there is nothing useful, return [].
"""

    try:
        response = client.models.generate_content(
            model=MEMORY_MODEL,
            contents=prompt
        )

        raw = response.text.strip()
        raw = re.sub(r"^```json|^```|```$", "", raw).strip()

        new_memories = json.loads(raw)

        if isinstance(new_memories, list):
            for memory in new_memories:
                if not isinstance(memory, str):
                    continue

                memory = memory.strip()

                if memory and memory not in existing:
                    existing.append(memory)

            st.session_state.data["memories"] = existing[-MAX_MEMORIES:]
            save_data()

    except Exception:
        pass


# ==========================================
# VOICE OUTPUT
# ==========================================

def prepare_for_speech(text):
    text = re.sub(r"```.*?```", "Code omitted.", text, flags=re.S)
    text = re.sub(r"`([^`]*)`", r"\1", text)
    text = re.sub(r"https?://\S+", "", text)
    text = re.sub(r"[*_#]", "", text)

    return text.strip()


def generate_speech(text):
    client = get_client()

    if not client:
        return None

    speech_text = prepare_for_speech(text)

    if not speech_text:
        return None

    try:
        interaction = client.interactions.create(
            model=TTS_MODEL,
            input=[{
                "type": "user_input",
                "content": [{
                    "type": "text",
                    "text": speech_text,
                    "annotations": [{
                        "type": "speech_metadata",
                        "style": (
                            "Speak in clear, neutral English "
                            "with no strong regional accent. "
                            "Use a mature, smooth, composed, "
                            "confident and articulate delivery. "
                            "Speak at a natural, measured pace "
                            "with subtle pauses between ideas. "
                            "Sound conversational and refined, "
                            "not robotic or exaggerated."
                        )
                    }]
                }]
            }],
            response_format={"type": "audio"},
            generation_config={
                "speech_config": [{"voice": AURA_VOICE}]
            }
        )

        audio_data = interaction.output_audio.data

        if isinstance(audio_data, str):
            return base64.b64decode(audio_data)

        return bytes(audio_data)

    except Exception as error:
        st.warning(f"Aura's voice could not be generated: {error}")
        return None


# ==========================================
# MICROPHONE TRANSCRIPTION
# ==========================================

def transcribe_audio(audio_file):
    client = get_client()

    if not client:
        return None

    try:
        audio_bytes = audio_file.getvalue()

        response = client.models.generate_content(
            model=CHAT_MODEL,
            contents=[
                "Transcribe this audio accurately. Return only the spoken words.",
                genai.types.Part.from_bytes(
                    data=audio_bytes,
                    mime_type=audio_file.type or "audio/wav"
                )
            ]
        )

        return response.text.strip()

    except Exception as error:
        st.error(f"Audio transcription failed: {error}")
        return None


# ==========================================
# SEND MESSAGE
# ==========================================

def send_message(user_text):
    user_text = user_text.strip()

    if not user_text:
        return

    client = get_client()

    if not client:
        st.error("Aura's API key has not been configured.")
        return

    chat = get_active_chat()

    chat["messages"].append({
        "role": "user",
        "content": user_text,
        "time": datetime.now().isoformat()
    })

    if chat["title"] == "New conversation":
        chat["title"] = user_text[:45]

    save_data()
    st.session_state.report = None

    with st.chat_message("user", avatar="👤"):
        st.markdown(user_text)

    with st.chat_message("assistant", avatar="🤖"):
        placeholder = st.empty()
        full_response = ""

        try:
            prompt = build_prompt(chat)

            stream = client.models.generate_content_stream(
                model=CHAT_MODEL,
                contents=prompt
            )

            for chunk in stream:
                if chunk.text:
                    full_response += chunk.text
                    placeholder.markdown(full_response + "▌")

            placeholder.markdown(full_response)

        except Exception as error:
            st.error(f"Aura encountered an error: {error}")
            return

        if not full_response.strip():
            st.error("Aura returned an empty response.")
            return

        chat["messages"].append({
            "role": "assistant",
            "content": full_response,
            "time": datetime.now().isoformat()
        })

        save_data()

        user_messages = sum(
            1 for message in chat["messages"]
            if message["role"] == "user"
        )

        if user_messages % MEMORY_INTERVAL == 0:
            extract_memories(chat)

        if st.session_state.voice_enabled:
            audio_bytes = generate_speech(full_response)

            if audio_bytes:
                st.audio(
                    audio_bytes,
                    format="audio/wav",
                    autoplay=True
                )


# ==========================================
# CONVERSATION HANDOVER REPORT
# ==========================================

def generate_conversation_report():
    client = get_client()

    if not client:
        st.error("Aura's API key has not been configured.")
        return

    chat = get_active_chat()

    if not chat["messages"]:
        st.warning("There is no conversation to summarise yet.")
        return

    conversation = "\n\n".join(
        f"{message['role'].upper()}: {message['content']}"
        for message in chat["messages"]
    )

    memories = st.session_state.data.get("memories", [])

    prompt = f"""
You are preparing a conversation handover report.

The user wants to paste this report into a NEW ChatGPT
conversation so that the next assistant can continue
without asking them to repeat everything.

Create a clear, detailed but concise report.

Include:

1. MAIN TOPICS
What was discussed?

2. IMPORTANT DETAILS
Relevant facts, preferences and instructions.

3. DECISIONS MADE
What did the user decide?

4. PROJECT PROGRESS
What has already been completed?

5. CURRENT PROBLEMS
What still needs fixing?

6. NEXT STEPS
What should happen next?

7. CONTINUATION INSTRUCTIONS
Explain exactly where the next conversation should pick up.

IMPORTANT:
- Do not invent information.
- Preserve important names, model choices and technical details.
- Do not omit unfinished tasks.
- Do not include irrelevant small talk.
- Write in the user's preferred straightforward style.
- Make the report self-contained.
- Write it as context for another ChatGPT assistant.

SAVED AURA MEMORIES:
{json.dumps(memories, ensure_ascii=False)}

CONVERSATION:
{conversation}

Begin the report with:

# CONVERSATION HANDOVER REPORT
"""

    try:
        with st.spinner("Aura is preparing your handover report..."):
            response = client.models.generate_content(
                model=CHAT_MODEL,
                contents=prompt
            )

        st.session_state.report = response.text.strip()

    except Exception as error:
        st.error(f"Could not generate the report: {error}")


# ==========================================
# HEADER
# ==========================================

st.markdown(
    '<div class="aura-title">A U R A</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="aura-subtitle">PERSONAL INTELLIGENCE SYSTEM</div>',
    unsafe_allow_html=True
)

st.write("")


# ==========================================
# SIDEBAR
# ==========================================

with st.sidebar:
    st.title("✨ Aura")

    st.caption("PERSONAL AI SYSTEM")

    st.divider()

    st.session_state.voice_enabled = st.toggle(
        "Automatic voice replies",
        value=st.session_state.voice_enabled
    )

    st.caption(f"Voice: {AURA_VOICE}")
    st.caption(f"Chat model: {CHAT_MODEL}")

    st.divider()

    if st.button("＋ New conversation", use_container_width=True):
        create_new_chat()
        st.rerun()

    st.subheader("Conversation history")

    for chat_item in reversed(st.session_state.data["chats"]):
        col1, col2 = st.columns([4, 1])

        with col1:
            label = chat_item["title"][:25]

            if st.button(
                label,
                key=f"open_{chat_item['id']}",
                use_container_width=True
            ):
                st.session_state.data["active_chat"] = chat_item["id"]
                st.session_state.report = None
                st.rerun()

        with col2:
            if st.button(
                "✕",
                key=f"delete_{chat_item['id']}"
            ):
                delete_chat(chat_item["id"])
                st.rerun()

    st.divider()

    st.subheader("Aura's memories")

    memories = st.session_state.data["memories"]

    if memories:
        for index, memory in enumerate(memories):
            st.caption(f"• {memory}")

            if st.button(
                "Delete",
                key=f"memory_{index}"
            ):
                memories.pop(index)
                save_data()
                st.rerun()
    else:
        st.caption("No saved memories yet.")

    if memories and st.button("Clear all memories"):
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
        "Download Aura backup",
        data=backup,
        file_name="aura_backup.json",
        mime="application/json",
        use_container_width=True
    )


# ==========================================
# CURRENT CHAT
# ==========================================

chat = get_active_chat()

st.caption(f"Conversation: {chat['title']}")

# Display existing conversation

for message in chat["messages"]:
    avatar = "👤" if message["role"] == "user" else "🤖"

    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])


# ==========================================
# HANDOVER REPORT BUTTON
# ==========================================

st.divider()

st.subheader("Conversation handover")

st.caption(
    "Create a report of this conversation to paste "
    "into your next ChatGPT conversation."
)

if st.button(
    "📄 Generate Conversation Report",
    use_container_width=True
):
    generate_conversation_report()

if st.session_state.report:
    st.success("Your conversation report is ready.")

    st.caption(
        "Use the copy icon in the report box to copy everything."
    )

    st.code(
        st.session_state.report,
        language="markdown"
    )


# ==========================================
# MICROPHONE
# ==========================================

st.divider()

st.subheader("Speak to Aura")

audio_input = st.audio_input("Record a voice message")

if audio_input:
    audio_hash = hashlib.sha256(
        audio_input.getvalue()
    ).hexdigest()

    if audio_hash != st.session_state.last_audio_hash:
        st.session_state.last_audio_hash = audio_hash

        with st.spinner("Aura is listening..."):
            transcription = transcribe_audio(audio_input)

        if transcription:
            st.info(f"You said: {transcription}")
            send_message(transcription)
            st.rerun()


# ==========================================
# TEXT INPUT
# ==========================================

user_input = st.chat_input("Message Aura...")

if user_input:
    send_message(user_input)
    st.rerun()
