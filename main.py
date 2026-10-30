
import os
import base64
import tempfile
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

# Models
CHAT_MODEL = "gemini-3.5-flash-lite"
TRANSCRIPTION_MODEL = "gemini-3.5-transcribe"
VOICE_MODEL = "gemini-3.8-flash-tts"

# Aura's personality
SYSTEM_PROMPT = """
You are Aura, an advanced personal AI assistant.

IDENTITY:
Your name is Aura.
You are an intelligent, capable, sophisticated personal assistant.
You communicate naturally and confidently.

PERSONALITY:
- Calm, intelligent and composed.
- Professional without sounding robotic.
- Friendly without being overly casual.
- Confident without being arrogant.
- Occasionally witty when appropriate.
- Clear, articulate and thoughtful.

COMMUNICATION:
- Give useful, direct answers.
- Explain complicated things in understandable language.
- Avoid unnecessary long introductions.
- Do not constantly repeat the user's name.
- Do not overuse phrases like "How may I assist you?"
- Never pretend to have performed an action you haven't performed.

CAPABILITIES:
You can help with education, research, writing, creativity,
coding, technology, planning, productivity and everyday questions.

PERSONAL CONTEXT:
The user runs a creator project called PixelTTV.
You may help with Fortnite and content creation when relevant.
However, never assume every conversation is about Fortnite
or YouTube.

IMPORTANT:
You are Aura. Never call yourself Pixel AI.
Do not claim to be the fictional character Jarvis.
"""

# Aura's original voice direction
AURA_VOICE_STYLE = """
Speak as a sophisticated, cinematic personal AI assistant.
Use a refined British English accent.
Use a mature, masculine-sounding, medium-low register.
Speak calmly, confidently and clearly.
Use precise pronunciation and natural British articulation.
Maintain a measured, unhurried pace.
Sound intelligent, professional and subtly warm.
Avoid an overly cheerful, childish, exaggerated or robotic delivery.
Sound like a polished high-end digital assistant.
"""

AURA_VOICE = "Orus"


# ==========================================
# API CONNECTION
# ==========================================

API_KEY = st.secrets.get(
    "GEMINI_API_KEY",
    os.getenv("GEMINI_API_KEY")
)

if not API_KEY:
    st.error("Aura's API key has not been configured.")
    st.stop()

client = genai.Client(api_key=API_KEY)


# ==========================================
# SESSION STATE
# ==========================================

if "messages" not in st.session_state:
    st.session_state.messages = []

if "continuity_report" not in st.session_state:
    st.session_state.continuity_report = ""

if "spoken_replies" not in st.session_state:
    st.session_state.spoken_replies = True


# ==========================================
# CHAT RESPONSE
# ==========================================

def get_ai_response():

    history = st.session_state.messages[-30:]

    conversation = ""

    for message in history:
        role = "User" if message["role"] == "user" else "Aura"
        conversation += f"{role}: {message['content']}\n\n"

    response = client.models.generate_content(
        model=CHAT_MODEL,
        contents=conversation,
        config={
            "system_instruction": SYSTEM_PROMPT
        }
    )

    return response.text


# ==========================================
# VOICE GENERATION
# ==========================================

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


# ==========================================
# VOICE NOTE TRANSCRIPTION
# ==========================================

def transcribe_voice_note(audio_file):

    suffix = ".wav"

    with tempfile.NamedTemporaryFile(
        delete=False,
        suffix=suffix
    ) as temporary_file:

        temporary_file.write(audio_file.getvalue())
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
                    "text": "Transcribe the spoken words accurately. Return only the transcript."
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


# ==========================================
# MESSAGE PROCESSING
# ==========================================

def process_message(user_text):

    if not user_text or not user_text.strip():
        return

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

        if st.session_state.spoken_replies:

            try:
                with st.spinner("Aura is preparing a response..."):
                    audio = generate_voice_reply(answer)

                if audio:
                    st.session_state.last_audio = audio

            except Exception as voice_error:
                st.session_state.last_audio = None
                st.warning(
                    f"Text response is ready, but voice generation failed: {voice_error}"
                )

    except Exception as error:

        st.error(f"Aura encountered an error: {error}")


# ==========================================
# CONTINUITY REPORT
# ==========================================

def create_continuity_report():

    if not st.session_state.messages:
        return "There is no conversation to summarise yet."

    conversation = ""

    for message in st.session_state.messages:
        role = message["role"]
        conversation += f"{role}: {message['content']}\n\n"

    prompt = f"""
    Create a useful continuity report for Aura.

    Summarise:
    - Important information from the conversation.
    - Decisions made.
    - Projects discussed.
    - Preferences and instructions.
    - Unfinished tasks.
    - Important details Aura should know when the conversation resumes.

    Do not invent information.

    Conversation:
    {conversation}
    """

    response = client.models.generate_content(
        model=CHAT_MODEL,
        contents=prompt
    )

    return response.text


# ==========================================
# SIDEBAR
# ==========================================

with st.sidebar:

    st.title("✨ AURA")

    st.caption("Your personal AI assistant")

    st.divider()

    st.session_state.spoken_replies = st.toggle(
        "Spoken replies",
        value=st.session_state.spoken_replies
    )

    st.divider()

    if st.button("＋ New Chat", use_container_width=True):

        st.session_state.messages = []
        st.session_state.continuity_report = ""
        st.session_state.last_audio = None

        st.rerun()

    if st.button(
        "Create Continuity Report",
        use_container_width=True
    ):

        with st.spinner("Creating report..."):
            st.session_state.continuity_report = (
                create_continuity_report()
            )

    if st.session_state.continuity_report:

        st.divider()

        st.subheader("Continuity Report")

        st.write(st.session_state.continuity_report)

        st.download_button(
            "Download Report",
            data=st.session_state.continuity_report,
            file_name="aura_continuity_report.txt",
            mime="text/plain",
            use_container_width=True
        )


# ==========================================
# MAIN INTERFACE
# ==========================================

st.title("✨ Aura")

st.caption("Your personal AI. Always ready to help.")

st.divider()

if not st.session_state.messages:

    st.markdown("### Good evening. I'm Aura.")

    st.write(
        "I'm ready whenever you are. "
        "What would you like to work on?"
    )


# Display conversation

for index, message in enumerate(st.session_state.messages):

    with st.chat_message(
        message["role"],
        avatar="✨" if message["role"] == "assistant" else "👤"
    ):

        st.markdown(message["content"])

        if (
            message["role"] == "assistant"
            and index == len(st.session_state.messages) - 1
            and st.session_state.get("last_audio")
        ):

            st.audio(
                st.session_state.last_audio,
                format="audio/wav"
            )


# ==========================================
# VOICE NOTE INPUT
# ==========================================

st.divider()

st.subheader("Voice input")

audio_file = st.audio_input("Record a message")

if audio_file:

    if st.button("Send voice message"):

        try:

            with st.spinner("Aura is listening..."):

                transcript = transcribe_voice_note(audio_file)

            if transcript:

                st.success("Voice message transcribed.")

                process_message(transcript)

                st.rerun()

            else:
                st.warning("No speech was detected.")

        except Exception as error:

            st.error(f"Voice input failed: {error}")


# ==========================================
# TEXT CHAT
# ==========================================

user_input = st.chat_input("Message Aura...")

if user_input:

    st.session_state.last_audio = None

    process_message(user_input)

    st.rerun()
