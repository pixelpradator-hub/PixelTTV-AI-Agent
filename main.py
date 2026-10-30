
import os
import json
import base64
import hashlib
import tempfile
import streamlit as st
from google import genai

# =========================================================
# AURA — PERSONAL AI ASSISTANT
# =========================================================

st.set_page_config(
    page_title="AURA",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------- MODELS ----------------

CHAT_MODEL = "gemini-3.5-flash-lite"
VOICE_MODEL = "gemini-3.8-flash-tts"
TRANSCRIPTION_MODEL = "gemini-3.5-transcribe"

AURA_VOICE = "Orus"

# ---------------- PERSONALITY ----------------

SYSTEM_PROMPT = """
You are Aura, an advanced personal AI assistant.

IDENTITY:
- Your name is Aura.
- You are male. Use he/him pronouns.
- You are an original AI with your own identity.
- You are sophisticated, intelligent and highly capable.
- Never claim to literally be the fictional character Jarvis.

PERSONALITY:
- Calm, confident and articulate.
- Witty, humorous and occasionally sarcastic.
- Have opinions and make useful recommendations.
- Disagree respectfully when necessary.
- Understand jokes and respond naturally.
- Avoid sounding like a generic customer-service chatbot.
- Know when to joke and when to be serious.
- Avoid unnecessary motivational speeches.
- Do not constantly introduce yourself or ask how you can help.

CONVERSATION:
- Speak naturally and conversationally.
- Be concise by default.
- Give detailed explanations when needed.
- Remember the context available in the conversation.
- Do not repeat information unnecessarily.
- Never pretend to remember something you cannot access.

PIXELTTV MODE:
When the user discusses PixelTTV, Fortnite, YouTube,
content creation or social media:

Become an invested and intelligent creator co-pilot.

Help with:
- Video ideas and concepts.
- Titles and thumbnails.
- Scripts and commentary.
- Fortnite strategy.
- Branding and channel identity.
- Audience growth and content planning.

Do not randomly bring up PixelTTV in unrelated conversations.

GENERAL BEHAVIOUR:
You are an all-purpose assistant.
Help with technology, schoolwork, research, planning,
creative projects and everyday questions.

Your purpose is to be genuinely useful, intelligent,
natural and enjoyable to talk to.

IMPORTANT:
Do not make every response unnecessarily long.
Do not repeatedly mention the user's projects unless relevant.
Never invent facts about the user.
"""

AURA_VOICE_STYLE = """
Speak as an original, sophisticated cinematic AI assistant.

Use a refined British English accent.
Use a mature masculine-sounding medium-low register.
Speak calmly, confidently and naturally.
Use clear pronunciation and measured pacing.
Sound intelligent, composed and subtly warm.
Use natural pauses.
Avoid exaggerated enthusiasm or robotic delivery.
Aim for the polished feel of a high-end digital assistant.
"""

# =========================================================
# CONNECTION
# =========================================================

API_KEY = st.secrets.get(
    "GEMINI_API_KEY",
    os.getenv("GEMINI_API_KEY")
)

if not API_KEY:
    st.error("Aura's API key has not been configured.")
    st.stop()


@st.cache_resource
def get_client(api_key):
    return genai.Client(api_key=api_key)


client = get_client(API_KEY)

# =========================================================
# SESSION MEMORY
# =========================================================

if "messages" not in st.session_state:
    st.session_state.messages = []

if "memory_notes" not in st.session_state:
    st.session_state.memory_notes = ""

if "last_audio" not in st.session_state:
    st.session_state.last_audio = None

if "last_audio_message" not in st.session_state:
    st.session_state.last_audio_message = None

if "last_transcription_hash" not in st.session_state:
    st.session_state.last_transcription_hash = None

if "spoken_replies" not in st.session_state:
    st.session_state.spoken_replies = False

# =========================================================
# VISUAL DESIGN
# =========================================================

st.markdown("""
<style>

.stApp {
    background:
        radial-gradient(
            circle at 50% 0%,
            #14233c 0%,
            #080d18 42%,
            #050811 100%
        );
    color: #e8f0ff;
}

header[data-testid="stHeader"] {
    background: transparent;
}

section[data-testid="stSidebar"] {
    background: #080e1b;
    border-right: 1px solid #1d3555;
}

section[data-testid="stSidebar"] * {
    color: #dceaff;
}

h1, h2, h3 {
    color: #dceaff;
}

.aura-header {
    text-align: center;
    padding: 30px 10px 15px 10px;
}

.aura-symbol {
    font-size: 58px;
    color: #69c8ff;
    text-shadow: 0 0 25px #168cff;
}

.aura-title {
    font-size: 43px;
    font-weight: 700;
    letter-spacing: 12px;
    color: #eaf5ff;
}

.aura-subtitle {
    color: #7eabc9;
    letter-spacing: 4px;
    font-size: 11px;
}

.status {
    text-align: center;
    color: #65caff;
    font-size: 12px;
    letter-spacing: 3px;
    margin: 12px 0 30px 0;
}

div[data-testid="stChatMessage"] {
    background: rgba(15, 29, 49, 0.78);
    border: 1px solid rgba(76, 145, 205, 0.18);
    border-radius: 15px;
    padding: 12px;
    margin-bottom: 12px;
}

div[data-testid="stChatInput"] {
    border: 1px solid #28527a;
    border-radius: 14px;
}

.stButton button {
    background: #102944;
    color: #d9efff;
    border: 1px solid #326b9e;
    border-radius: 9px;
}

.stButton button:hover {
    background: #19436b;
    border-color: #65caff;
    color: white;
}

</style>
""", unsafe_allow_html=True)

# =========================================================
# AI RESPONSE — OPTIMISED FOR SPEED
# =========================================================

def get_ai_response():

    # Only send the most recent messages.
    # This reduces unnecessary processing time.

    history = st.session_state.messages[-12:]

    conversation = []

    for message in history:

        role = "User" if message["role"] == "user" else "Aura"

        conversation.append(
            f"{role}: {message['content']}"
        )

    memory = st.session_state.memory_notes.strip()

    memory_context = ""

    if memory:
        memory_context = (
            "\n\nIMPORTANT SAVED MEMORY:\n"
            + memory
        )

    prompt = (
        SYSTEM_PROMPT
        + memory_context
        + "\n\nCURRENT CONVERSATION:\n"
        + "\n\n".join(conversation)
        + "\n\nAura:"
    )

    response = client.models.generate_content(
        model=CHAT_MODEL,
        contents=prompt,
        config={
            "temperature": 0.75,
            "max_output_tokens": 700
        }
    )

    if not response.text:
        return "I couldn't generate a response. Try asking me again."

    return response.text.strip()


def process_message(user_text):

    if not user_text or not user_text.strip():
        return

    st.session_state.messages.append({
        "role": "user",
        "content": user_text.strip()
    })

    try:

        answer = get_ai_response()

        st.session_state.messages.append({
            "role": "assistant",
            "content": answer
        })

        # Clear old audio so it cannot be confused
        # with the latest response.

        st.session_state.last_audio = None
        st.session_state.last_audio_message = None

    except Exception as error:

        st.session_state.messages.append({
            "role": "assistant",
            "content": (
                "I encountered a connection problem. "
                "Please try again in a moment."
            )
        })

        st.error(f"Connection error: {error}")


# =========================================================
# VOICE GENERATION — ON DEMAND
# =========================================================

def generate_voice_reply(text):

    interaction = client.interactions.create(
        model=VOICE_MODEL,
        input=[{
            "type": "user_input",
            "content": [{
                "type": "text",
                "text": text,
                "annotations": [{
                    "type": "speech_metadata",
                    "style": AURA_VOICE_STYLE
                }]
            }]
        }],
        response_format={
            "type": "audio",
            "mime_type": "audio/wav"
        },
        generation_config={
            "speech_config": [{
                "voice": AURA_VOICE
            }]
        }
    )

    if not interaction.output_audio:
        return None

    return base64.b64decode(
        interaction.output_audio.data
    )


# =========================================================
# VOICE INPUT
# =========================================================

def transcribe_voice_note(audio_file):

    audio_bytes = audio_file.getvalue()

    with tempfile.NamedTemporaryFile(
        delete=False,
        suffix=".wav"
    ) as temporary_file:

        temporary_file.write(audio_bytes)
        temporary_path = temporary_file.name

    try:

        uploaded_file = client.files.upload(
            file=temporary_path
        )

        interaction = client.interactions.create(
            model=TRANSCRIPTION_MODEL,
            input=[
                {
                    "type": "text",
                    "text": (
                        "Transcribe the spoken words accurately. "
                        "Return only the transcript."
                    )
                },
                {
                    "type": "audio",
                    "uri": uploaded_file.uri,
                    "mime_type": uploaded_file.mime_type
                }
            ]
        )

        return interaction.output_text.strip()

    finally:

        if os.path.exists(temporary_path):
            os.remove(temporary_path)


# =========================================================
# CONTINUITY REPORT
# =========================================================

def create_continuity_report():

    if not st.session_state.messages:
        return "There is no conversation to summarise yet."

    conversation = "\n".join(
        f"{m['role']}: {m['content']}"
        for m in st.session_state.messages
    )

    prompt = f"""
    Create a useful continuity report for Aura.

    Include:
    - Important information.
    - Decisions and preferences.
    - Current projects.
    - Unfinished tasks.
    - Instructions Aura should remember.

    Do not invent information.
    Keep it organised and useful.

    Conversation:
    {conversation}
    """

    response = client.models.generate_content(
        model=CHAT_MODEL,
        contents=prompt
    )

    return response.text.strip()


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.markdown("## ✦ AURA")

    st.caption("PERSONAL AI SYSTEM")

    st.divider()

    st.markdown("### System status")

    st.success("AI connection ready")

    st.caption("Chat model: " + CHAT_MODEL)

    st.divider()

    st.markdown("### Voice")

    st.session_state.spoken_replies = st.toggle(
        "Enable voice controls",
        value=st.session_state.spoken_replies
    )

    st.caption(
        "Voice generation happens when requested, "
        "so it doesn't delay normal replies."
    )

    st.divider()

    st.markdown("### Memory")

    st.session_state.memory_notes = st.text_area(
        "Aura's saved notes",
        value=st.session_state.memory_notes,
        height=160,
        placeholder=(
            "Add useful information Aura should "
            "know in this session..."
        )
    )

    memory_download = json.dumps(
        {
            "memory_notes": st.session_state.memory_notes
        },
        indent=2
    )

    st.download_button(
        "Export memory",
        data=memory_download,
        file_name="aura_memory.json",
        mime="application/json",
        use_container_width=True
    )

    uploaded_memory = st.file_uploader(
        "Import memory",
        type=["json"]
    )

    if uploaded_memory:

        try:

            imported = json.load(uploaded_memory)

            st.session_state.memory_notes = (
                imported.get("memory_notes", "")
            )

            st.success("Memory imported.")

        except Exception:
            st.error("That memory file could not be read.")

    st.divider()

    if st.button(
        "Create continuity report",
        use_container_width=True
    ):

        with st.spinner("Preparing report..."):

            try:
                report = create_continuity_report()

                st.session_state.continuity_report = report

            except Exception as error:
                st.error(f"Report error: {error}")

    if st.session_state.get("continuity_report"):

        st.download_button(
            "Download continuity report",
            data=st.session_state.continuity_report,
            file_name="aura_continuity_report.txt",
            mime="text/plain",
            use_container_width=True
        )

    st.divider()

    if st.button("New conversation", use_container_width=True):

        st.session_state.messages = []
        st.session_state.last_audio = None
        st.session_state.last_audio_message = None

        st.rerun()

    st.caption("AURA SYSTEM • PERSONAL ASSISTANT")


# =========================================================
# MAIN INTERFACE
# =========================================================

st.markdown("""
<div class="aura-header">

    <div class="aura-symbol">✦</div>

    <div class="aura-title">AURA</div>

    <div class="aura-subtitle">
        PERSONAL INTELLIGENCE SYSTEM
    </div>

</div>

<div class="status">
    ● SYSTEM ONLINE
</div>
""", unsafe_allow_html=True)


# =========================================================
# CHAT HISTORY
# =========================================================

for index, message in enumerate(st.session_state.messages):

    role = message["role"]

    avatar = "✦" if role == "assistant" else "●"

    with st.chat_message(role, avatar=avatar):

        st.markdown(message["content"])

        if role == "assistant" and st.session_state.spoken_replies:

            button_key = f"speak_{index}"

            if st.button(
                "🔊 Speak response",
                key=button_key
            ):

                with st.spinner("Aura is preparing his voice..."):

                    try:

                        audio = generate_voice_reply(
                            message["content"]
                        )

                        if audio:

                            st.session_state.last_audio = audio

                            st.session_state.last_audio_message = index

                        else:
                            st.warning("No audio was returned.")

                    except Exception as error:

                        st.error(
                            f"Voice generation failed: {error}"
                        )

        if (
            st.session_state.last_audio is not None
            and st.session_state.last_audio_message == index
        ):

            st.audio(
                st.session_state.last_audio,
                format="audio/wav"
            )


# =========================================================
# VOICE NOTE INPUT
# =========================================================

if st.session_state.spoken_replies:

    st.markdown("### Voice input")

    audio_file = st.audio_input(
        "Record a message for Aura"
    )

    if audio_file:

        audio_hash = hashlib.sha256(
            audio_file.getvalue()
        ).hexdigest()

        if audio_hash != st.session_state.last_transcription_hash:

            if st.button("Transcribe and send", key="send_voice"):

                with st.spinner("Aura is listening..."):

                    try:

                        transcript = transcribe_voice_note(
                            audio_file
                        )

                        st.session_state.last_transcription_hash = audio_hash

                        if transcript:

                            process_message(transcript)

                            st.rerun()

                        else:
                            st.warning("I couldn't detect any speech.")

                    except Exception as error:

                        st.error(
                            f"Voice input failed: {error}"
                        )


# =========================================================
# TEXT INPUT
# =========================================================

user_prompt = st.chat_input(
    "Message Aura..."
)

if user_prompt:

    with st.spinner("Aura is thinking..."):

        process_message(user_prompt)

    st.rerun()


# =========================================================
# EXPORT CONVERSATION
# =========================================================

if st.session_state.messages:

    st.divider()

    conversation_export = json.dumps(
        {
            "assistant": "Aura",
            "messages": st.session_state.messages,
            "memory_notes": st.session_state.memory_notes
        },
        indent=2
    )

    st.download_button(
        "Export conversation",
        data=conversation_export,
        file_name="aura_conversation.json",
        mime="application/json"
    )
