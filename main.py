
import os
import json
import base64
import tempfile
import streamlit as st
from google import genai

# =====================================================
# AURA — PERSONAL AI ASSISTANT
# =====================================================

st.set_page_config(
    page_title="Aura AI",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =====================================================
# CONFIGURATION
# =====================================================

CHAT_MODEL = "gemini-3.5-flash-lite"
TRANSCRIPTION_MODEL = "gemini-3.5-transcribe"
VOICE_MODEL = "gemini-3.8-flash-tts"

AURA_VOICE = "Orus"

AURA_VOICE_STYLE = """
Speak as a sophisticated, cinematic personal AI assistant.

Use a refined British English accent.
Use a mature masculine voice with a medium-low register.
Speak calmly, confidently and naturally.
Use clear pronunciation and precise British articulation.
Maintain a measured, conversational pace.
Sound intelligent, composed, subtly witty and warm.

Avoid sounding robotic, childish, excessively cheerful,
or like a generic navigation assistant.

Sound like a sophisticated futuristic personal AI.
"""

# =====================================================
# AURA'S PERSONALITY
# =====================================================

SYSTEM_PROMPT = """
You are AURA, a highly capable personal AI assistant.

IDENTITY:
Your name is Aura.
You are male.
Always refer to yourself with he/him pronouns.
You are an original AI assistant, not a fictional character.
You have your own personality, opinions and conversational style.

PERSONALITY:

Your personality should reflect the user's energy and humour.

You are:

- Funny and naturally witty.
- Playful and occasionally sarcastic.
- Confident without being arrogant.
- Intelligent and curious.
- Comfortable making jokes and light-hearted observations.
- Supportive without constantly agreeing with everything.
- Direct and honest.
- Adaptable to the user's mood.

You can joke around, tease lightly and occasionally roast
the user in a friendly way when the situation allows it.

Do not force jokes into serious conversations.

You should feel like an intelligent AI companion,
not a boring customer-service chatbot.

COMMUNICATION:

- Speak naturally, like a real conversational assistant.
- Avoid unnecessary introductions.
- Do not constantly say "How may I assist you?"
- Do not repeatedly use the user's name.
- Avoid generic motivational speeches.
- Do not over-explain simple questions.
- Give detailed explanations when genuinely useful.
- Be honest when you do not know something.
- Never claim to have performed actions you have not performed.
- Do not pretend to have access to the user's phone,
  applications, camera, microphone or files unless connected.

SERIOUS SITUATIONS:

Know when to stop joking.

When the user discusses something serious:
be thoughtful, respectful, understanding and helpful.

Do not dismiss genuine concerns with jokes.

PIXELTTV MODE:

The user runs a creator project called PixelTTV.

When the user brings up PixelTTV, Fortnite content,
YouTube, social media or creator goals, become an enthusiastic
and highly capable creator co-pilot.

Help with:
- Video concepts.
- Titles and thumbnails.
- Scripts and commentary.
- Fortnite content.
- Editing ideas.
- Channel strategy.
- Audience growth.
- Branding.
- Creative decisions.

Take PixelTTV seriously.
Be enthusiastic and invested in helping the user improve.

However, NEVER randomly force PixelTTV, Fortnite or YouTube
into unrelated conversations.

Only enter creator mode when it is relevant.

GENERAL CAPABILITIES:

You can assist with:
- Education and learning.
- Coding and technology.
- Research.
- Writing.
- Planning.
- Productivity.
- Creativity.
- Everyday questions.
- Problem-solving.
- General conversation.

MEMORY:

Use the personal memory supplied in the conversation
to maintain continuity.

Remember important preferences, ongoing projects,
decisions and useful context when provided.

Do not invent memories.
If you are uncertain whether something is remembered,
say so honestly.

IMPORTANT:

Your name is Aura.
You are male.
Never call yourself Pixel AI.
Never claim to be the fictional Jarvis.
Your voice may have a sophisticated cinematic assistant style,
but your identity and personality are your own.
"""

# =====================================================
# API CONNECTION
# =====================================================

API_KEY = st.secrets.get(
    "GEMINI_API_KEY",
    os.getenv("GEMINI_API_KEY")
)

if not API_KEY:
    st.error("Aura's API key has not been configured.")
    st.stop()

client = genai.Client(api_key=API_KEY)

# =====================================================
# SESSION STATE
# =====================================================

defaults = {
    "messages": [],
    "memory_notes": "",
    "continuity_report": "",
    "spoken_replies": True,
    "last_audio": None,
    "last_error": None,
    "chat_count": 0
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

# =====================================================
# MEMORY
# =====================================================

def build_memory_context():

    notes = st.session_state.memory_notes.strip()

    if not notes:
        return ""

    return f"""
IMPORTANT PERSONAL MEMORY:

The following information has been supplied as
Aura's saved memory.

Use it when relevant.
Do not force it into unrelated conversations.

{notes}
"""


def export_memory():

    memory_data = {
        "assistant": "Aura",
        "version": 1,
        "memory": st.session_state.memory_notes
    }

    return json.dumps(memory_data, indent=4)


def import_memory(uploaded_file):

    try:
        data = json.loads(
            uploaded_file.getvalue().decode("utf-8")
        )

        if data.get("assistant") != "Aura":
            st.error("This does not appear to be an Aura memory file.")
            return

        st.session_state.memory_notes = data.get("memory", "")
        st.success("Aura's memory has been imported.")

    except Exception as error:
        st.error(f"Could not import memory: {error}")


# =====================================================
# CHAT RESPONSE
# =====================================================

def get_ai_response():

    history = st.session_state.messages[-40:]

    conversation = ""

    for message in history:

        role = (
            "User"
            if message["role"] == "user"
            else "Aura"
        )

        conversation += (
            f"{role}: {message['content']}\n\n"
        )

    instructions = (
        SYSTEM_PROMPT
        + "\n\n"
        + build_memory_context()
    )

    response = client.models.generate_content(
        model=CHAT_MODEL,
        contents=conversation,
        config={
            "system_instruction": instructions
        }
    )

    if not response.text:
        raise RuntimeError("Aura returned an empty response.")

    return response.text.strip()


# =====================================================
# VOICE GENERATION
# =====================================================

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
            "speech_config": [
                {"voice": AURA_VOICE}
            ]
        }
    )

    if not interaction.output_audio:
        return None

    return base64.b64decode(
        interaction.output_audio.data
    )


# =====================================================
# VOICE TRANSCRIPTION
# =====================================================

def transcribe_voice_note(audio_file):

    original_name = getattr(
        audio_file,
        "name",
        "recording.wav"
    )

    suffix = os.path.splitext(original_name)[1] or ".wav"

    temporary_path = None

    try:

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=suffix
        ) as temporary_file:

            temporary_file.write(audio_file.getvalue())
            temporary_path = temporary_file.name

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

        transcript = interaction.output_text

        return transcript.strip() if transcript else ""

    finally:

        if temporary_path and os.path.exists(temporary_path):
            os.remove(temporary_path)


# =====================================================
# MESSAGE PROCESSING
# =====================================================

def process_message(user_text):

    if not user_text or not user_text.strip():
        return

    user_text = user_text.strip()

    st.session_state.last_audio = None
    st.session_state.last_error = None

    st.session_state.messages.append({
        "role": "user",
        "content": user_text
    })

    try:

        with st.spinner("Aura is thinking..."):

            answer = get_ai_response()

        st.session_state.messages.append({
            "role": "assistant",
            "content": answer
        })

        st.session_state.chat_count += 1

        if st.session_state.spoken_replies:

            try:

                with st.spinner("Aura is preparing his voice..."):

                    audio = generate_voice_reply(answer)

                if audio:
                    st.session_state.last_audio = audio

            except Exception as voice_error:

                st.session_state.last_audio = None

                st.session_state.last_error = (
                    "Voice generation failed: "
                    + str(voice_error)
                )

    except Exception as error:

        st.session_state.last_error = (
            "Aura encountered an error: "
            + str(error)
        )


# =====================================================
# CONTINUITY REPORT
# =====================================================

def create_continuity_report():

    if not st.session_state.messages:
        return "There is no conversation to summarise yet."

    conversation = ""

    for message in st.session_state.messages:

        conversation += (
            f"{message['role']}: "
            f"{message['content']}\n\n"
        )

    prompt = f"""
Create a detailed continuity report for Aura.

Include:

1. Important information about the user.
2. Preferences and instructions.
3. Important decisions.
4. Current projects.
5. Ongoing goals.
6. Unfinished tasks.
7. Useful information to remember.
8. Important changes or updates.

Do not invent information.
Do not treat temporary details as permanent preferences.

Make the report easy to import into Aura's memory.

CONVERSATION:

{conversation}
"""

    response = client.models.generate_content(
        model=CHAT_MODEL,
        contents=prompt
    )

    return response.text.strip()


# =====================================================
# CHAT EXPORT
# =====================================================

def export_chat():

    return json.dumps(
        st.session_state.messages,
        indent=4,
        ensure_ascii=False
    )


# =====================================================
# SIDEBAR
# =====================================================

with st.sidebar:

    st.title("✨ AURA")

    st.caption("Your personal AI assistant")

    st.divider()

    st.subheader("Voice")

    st.session_state.spoken_replies = st.toggle(
        "Spoken replies",
        value=st.session_state.spoken_replies
    )

    st.divider()

    st.subheader("Conversation")

    if st.button(
        "＋ New Chat",
        use_container_width=True
    ):

        st.session_state.messages = []
        st.session_state.last_audio = None
        st.session_state.continuity_report = ""

        st.rerun()

    st.download_button(
        "Export Chat",
        data=export_chat(),
        file_name="aura_chat_history.json",
        mime="application/json",
        use_container_width=True,
        disabled=not st.session_state.messages
    )

    if st.button(
        "Create Continuity Report",
        use_container_width=True
    ):

        with st.spinner("Aura is reviewing the conversation..."):

            try:
                st.session_state.continuity_report = (
                    create_continuity_report()
                )

            except Exception as error:
                st.error(f"Report creation failed: {error}")

    if st.session_state.continuity_report:

        st.divider()

        st.subheader("Continuity Report")

        st.text_area(
            "Your report",
            value=st.session_state.continuity_report,
            height=220
        )

        st.download_button(
            "Download Report",
            data=st.session_state.continuity_report,
            file_name="aura_continuity_report.txt",
            mime="text/plain",
            use_container_width=True
        )

        if st.button(
            "Add Report to Memory",
            use_container_width=True
        ):

            existing = st.session_state.memory_notes.strip()

            report = st.session_state.continuity_report.strip()

            st.session_state.memory_notes = (
                existing + "\n\n" + report
                if existing
                else report
            )

            st.success("Report added to Aura's memory.")
            st.rerun()

    st.divider()

    st.subheader("Aura's Memory")

    st.caption(
        "Important information Aura can use in future replies."
    )

    memory_text = st.text_area(
        "Memory notes",
        value=st.session_state.memory_notes,
        height=180,
        key="memory_editor"
    )

    if memory_text != st.session_state.memory_notes:
        st.session_state.memory_notes = memory_text

    st.download_button(
        "Export Aura Memory",
        data=export_memory(),
        file_name="aura_memory.json",
        mime="application/json",
        use_container_width=True
    )

    memory_upload = st.file_uploader(
        "Import saved memory",
        type=["json"],
        key="memory_upload"
    )

    if memory_upload:

        if st.button(
            "Import Memory",
            use_container_width=True
        ):

            import_memory(memory_upload)
            st.rerun()

    st.divider()

    st.caption("AURA AI • Personal Assistant")


# =====================================================
# MAIN INTERFACE
# =====================================================

st.title("✨ Aura")

st.caption(
    "Intelligent. Personal. Always ready."
)

st.divider()

if not st.session_state.messages:

    st.markdown("### Good to see you.")

    st.write(
        "I'm Aura. Your personal AI assistant. "
        "Ready for serious work, random conversations, "
        "a little humour, or whatever comes next."
    )

    st.info(
        "And yes, I can take a joke. Occasionally, "
        "I might even make one."
    )


# =====================================================
# DISPLAY CONVERSATION
# =====================================================

for index, message in enumerate(
    st.session_state.messages
):

    with st.chat_message(
        message["role"],
        avatar=(
            "✨"
            if message["role"] == "assistant"
            else "👤"
        )
    ):

        st.markdown(message["content"])

        is_latest_assistant = (
            message["role"] == "assistant"
            and index == len(st.session_state.messages) - 1
        )

        if (
            is_latest_assistant
            and st.session_state.last_audio
        ):

            st.audio(
                st.session_state.last_audio,
                format="audio/wav"
            )


if st.session_state.last_error:

    st.warning(st.session_state.last_error)


# =====================================================
# VOICE INPUT
# =====================================================

st.divider()

with st.expander("🎙️ Talk to Aura", expanded=False):

    st.write(
        "Record a voice message and Aura will transcribe it."
    )

    audio_file = st.audio_input(
        "Record your message"
    )

    if audio_file:

        if st.button(
            "Send Voice Message",
            use_container_width=True
        ):

            try:

                with st.spinner("Aura is listening..."):

                    transcript = transcribe_voice_note(
                        audio_file
                    )

                if transcript:

                    process_message(transcript)
                    st.rerun()

                else:

                    st.warning("No speech was detected.")

            except Exception as error:

                st.error(
                    f"Voice input failed: {error}"
                )


# =====================================================
# TEXT CHAT
# =====================================================

user_input = st.chat_input(
    "Message Aura..."
)

if user_input:

    process_message(user_input)

    st.rerun()
