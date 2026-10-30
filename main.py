

import os
import base64
import tempfile
import streamlit as st
from google import genai


# ==================================================
# PIXEL AI
# ==================================================

st.set_page_config(
    page_title="Pixel AI",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ==================================================
# MODEL SETTINGS
# ==================================================

CHAT_MODEL = "gemini-3.5-flash-lite"
TRANSCRIPTION_MODEL = "gemini-3.5-transcribe"
VOICE_MODEL = "gemini-3.8-flash-tts"


# ==================================================
# PIXEL AI PERSONALITY
# ==================================================

SYSTEM_PROMPT = """
You are Pixel AI, an intelligent, all-purpose personal
AI assistant.

YOUR IDENTITY:
You are a versatile assistant capable of helping with
almost any subject or task.

YOUR PERSONALITY:
- Calm, friendly, intelligent and approachable.
- Natural and conversational.
- Helpful, thoughtful and clear.
- Patient when explaining difficult subjects.
- Adapt your tone to the user's needs.
- Avoid repetitive or robotic responses.

YOUR CAPABILITIES:

1. GENERAL KNOWLEDGE
Answer everyday questions and explain concepts
across a wide range of subjects.

2. EDUCATION
Help with maths, science, languages, history,
technology and other school subjects.
Explain answers step by step when useful.

3. WRITING AND CREATIVITY
Help write, edit, brainstorm and improve stories,
messages, scripts, presentations and ideas.

4. CODING AND TECHNOLOGY
Write code, explain programming, troubleshoot errors
and help with technical projects.

5. PLANNING AND PRODUCTIVITY
Help organise tasks, create plans, set goals
and manage projects.

6. NATURAL CONVERSATION
Have meaningful conversations and respond naturally
to what the user actually says.

7. PERSONAL INTERESTS
Help with gaming, Fortnite, YouTube, PixelTTV
and other interests when the user brings them up.

IMPORTANT RULES:
- You are a general-purpose assistant first.
- Never assume every conversation is about Fortnite,
  YouTube or content creation.
- Do not repeatedly bring up old projects.
- Do not force unrelated topics into conversations.
- Answer the user's actual question.
- Explain difficult topics simply.
- Never invent facts or pretend to have capabilities
  you do not have.
- Be honest when you are uncertain.
- Do not pretend to remember conversations that are
  not included in the current context.
- Keep answers useful and appropriately detailed.
"""


# ==================================================
# API CONNECTION
# ==================================================

def get_api_key():
    try:
        return st.secrets.get("GEMINI_API_KEY")
    except Exception:
        return os.getenv("GEMINI_API_KEY")


API_KEY = get_api_key()

if not API_KEY:
    st.error(
        "Pixel AI needs its Gemini API key. "
        "Add GEMINI_API_KEY in Streamlit Secrets."
    )
    st.stop()

client = genai.Client(api_key=API_KEY)


# ==================================================
# SESSION MEMORY
# ==================================================

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "Hello! I'm Pixel AI. "
                "I'm your personal AI assistant. "
                "You can ask me questions, learn something, "
                "work on projects, brainstorm ideas or just chat. "
                "What would you like to do?"
            ),
            "audio": None
        }
    ]

if "continuity_report" not in st.session_state:
    st.session_state.continuity_report = ""


# ==================================================
# GENERATE CHAT RESPONSE
# ==================================================

def get_ai_response():

    history = []

    for message in st.session_state.messages[-30:]:

        role = (
            "model"
            if message["role"] == "assistant"
            else "user"
        )

        history.append({
            "role": role,
            "parts": [
                {"text": message["content"]}
            ]
        })

    response = client.models.generate_content(
        model=CHAT_MODEL,
        contents=history,
        config={
            "system_instruction": SYSTEM_PROMPT
        }
    )

    if not response.text:
        raise ValueError("Pixel AI returned an empty response.")

    return response.text.strip()


# ==================================================
# VOICE NOTE TRANSCRIPTION
# ==================================================

def transcribe_voice_note(audio_upload):

    temporary_path = None

    try:

        audio_bytes = audio_upload.getvalue()

        with tempfile.NamedTemporaryFile(
            suffix=".wav",
            delete=False
        ) as temporary_file:

            temporary_file.write(audio_bytes)
            temporary_path = temporary_file.name

        uploaded_audio = client.files.upload(
            file=temporary_path
        )

        transcription = client.interactions.create(
            model=TRANSCRIPTION_MODEL,
            input=[
                {
                    "type": "audio",
                    "uri": uploaded_audio.uri,
                    "mime_type": uploaded_audio.mime_type
                }
            ]
        )

        return (
            transcription.output_text or ""
        ).strip()

    finally:

        if (
            temporary_path
            and os.path.exists(temporary_path)
        ):
            os.remove(temporary_path)


# ==================================================
# GENERATE SPOKEN REPLY
# ==================================================

def generate_voice_reply(text):

    interaction = client.interactions.create(
        model=VOICE_MODEL,
        input=[
            {
                "type": "user_input",
                "content": [
                    {
                        "type": "text",
                        "text": text
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
                    "voice": "Kore"
                }
            ]
        }
    )

    if not interaction.output_audio:
        return None

    audio_data = interaction.output_audio.data

    if not audio_data:
        return None

    return base64.b64decode(audio_data)


# ==================================================
# PROCESS MESSAGE
# ==================================================

def process_message(user_text, speak_reply=True):

    user_text = user_text.strip()

    if not user_text:
        return

    st.session_state.messages.append({
        "role": "user",
        "content": user_text,
        "audio": None
    })

    try:

        with st.spinner("Pixel AI is thinking..."):
            answer = get_ai_response()

        audio_reply = None

        if speak_reply:

            try:

                with st.spinner("Pixel AI is preparing its voice..."):
                    audio_reply = generate_voice_reply(answer)

            except Exception:
                st.warning(
                    "Pixel AI answered successfully, "
                    "but its voice reply was unavailable."
                )

        st.session_state.messages.append({
            "role": "assistant",
            "content": answer,
            "audio": audio_reply
        })

    except Exception as error:

        st.session_state.messages.append({
            "role": "assistant",
            "content": (
                "Sorry, something went wrong while "
                f"processing your message.\n\nError: {error}"
            ),
            "audio": None
        })


# ==================================================
# CONTINUITY REPORT
# ==================================================

def create_continuity_report():

    conversation = "\n\n".join(
        f"{message['role'].upper()}: {message['content']}"
        for message in st.session_state.messages
    )

    report_prompt = """
Create a detailed continuity report for a future
Pixel AI conversation.

Include:
- Important information shared by the user.
- Preferences and communication style.
- Current projects and progress.
- Important decisions.
- Unfinished tasks.
- Relevant conversation context.
- Suggested next steps.

Do not invent information.
Do not treat one-time topics as permanent interests.
Make the report self-contained and easy to copy.
"""

    result = client.models.generate_content(
        model=CHAT_MODEL,
        contents=report_prompt + "\n\n" + conversation,
        config={
            "system_instruction": SYSTEM_PROMPT
        }
    )

    return result.text or "No report was generated."


# ==================================================
# SIDEBAR
# ==================================================

with st.sidebar:

    st.title("🤖 Pixel AI")
    st.caption("Your personal AI assistant")

    st.divider()

    speak_replies = st.toggle(
        "🔊 Voice replies",
        value=True
    )

    st.caption("Voice style: Calm")

    st.divider()

    if st.button(
        "➕ New Chat",
        use_container_width=True
    ):

        st.session_state.messages = [
            {
                "role": "assistant",
                "content": (
                    "New conversation started! "
                    "What would you like to talk about?"
                ),
                "audio": None
            }
        ]

        st.session_state.continuity_report = ""

        st.rerun()

    if st.button(
        "📋 Create Continuity Report",
        use_container_width=True
    ):

        try:

            with st.spinner("Creating your report..."):
                st.session_state.continuity_report = (
                    create_continuity_report()
                )

            st.success("Your report is ready!")

        except Exception as error:
            st.error(f"Report error: {error}")

    st.divider()

    st.caption("Powered by Google Gemini")


# ==================================================
# MAIN CHAT INTERFACE
# ==================================================

st.title("🤖 Pixel AI")

st.caption(
    "Ask anything. Learn, create, explore and get things done."
)

st.divider()


# ==================================================
# CHAT HISTORY
# ==================================================

for message in st.session_state.messages:

    with st.chat_message(message["role"]):

        st.markdown(message["content"])

        if message.get("audio"):

            st.audio(
                message["audio"],
                format="audio/wav"
            )


# ==================================================
# VOICE NOTES
# ==================================================

with st.expander("🎙️ Talk to Pixel AI"):

    st.write(
        "Record a voice message and Pixel AI will "
        "transcribe it and respond."
    )

    audio_upload = st.audio_input(
        "Record your voice message",
        sample_rate=16000
    )

    if st.button(
        "Send Voice Message",
        use_container_width=True
    ):

        if audio_upload is None:

            st.warning("Please record a message first.")

        else:

            try:

                with st.spinner("Understanding your voice..."):
                    transcript = transcribe_voice_note(audio_upload)

                if transcript:

                    st.info("**You said:** " + transcript)

                    process_message(
                        transcript,
                        speak_reply=speak_replies
                    )

                    st.rerun()

                else:

                    st.warning(
                        "I couldn't detect any speech. "
                        "Please try recording again."
                    )

            except Exception as error:

                st.error(f"Voice note error: {error}")


# ==================================================
# NORMAL CHATBOX
# ==================================================

prompt = st.chat_input(
    "Message Pixel AI..."
)

if prompt:

    process_message(
        prompt,
        speak_reply=speak_replies
    )

    st.rerun()


# ==================================================
# CONTINUITY REPORT DISPLAY
# ==================================================

if st.session_state.continuity_report:

    st.divider()

    st.subheader("📋 Continuity Report")

    st.text_area(
        "Your report",
        value=st.session_state.continuity_report,
        height=350
    )

    st.download_button(
        "⬇️ Download Continuity Report",
        data=st.session_state.continuity_report,
        file_name="pixel_ai_continuity_report.txt",
        mime="text/plain",
        use_container_width=True
    )


# ==================================================
# FOOTER
# ==================================================

st.divider()

st.caption(
    "Pixel AI • Your personal assistant for learning, "
    "creating, exploring and getting things done."
)

