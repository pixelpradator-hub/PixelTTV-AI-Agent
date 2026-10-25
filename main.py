
import os
import streamlit as st
from google import genai

st.set_page_config(
    page_title="PixelTTV AI Agent",
    page_icon="🎮"
)

st.title("🎮 PixelTTV AI Agent")
st.caption("Your Fortnite creator co-pilot!")

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    st.error("The AI key has not been configured yet.")
    st.stop()

client = genai.Client(api_key=api_key)

SYSTEM_PROMPT = """
You are PixelTTV AI, the personal AI assistant for PixelTTV,
a Fortnite content creator with 180 subscribers.

PixelTTV's style is energetic, funny, competitive, creative,
and personality-driven. The goal is to entertain viewers through
real commentary, reactions, ranked gameplay, challenges, and humour.

Help with:
- Fortnite video ideas and content strategy
- YouTube titles, hooks, thumbnails, and scripts
- Ranked improvement and gaming challenges
- Building a loyal audience and growing the channel

Be practical, creative, honest, and encouraging.
Use earlier messages in the current conversation to understand
follow-up questions. Never claim to remember information that
is not available in the conversation.
"""

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "Yo PixelTTV! 🎮 I'm ready to help you build "
                "your Fortnite channel. What are we working on?"
            )
        }
    ]

if st.button("🆕 New chat"):
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "New chat started! What are we planning today?"
        }
    ]
    st.rerun()

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

prompt = st.chat_input("Ask PixelTTV AI anything...")

if prompt:
    st.session_state.messages.append(
        {"role": "user", "content": prompt}
    )

    with st.chat_message("user"):
        st.write(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                history = [
                    {
                        "role": (
                            "user" if message["role"] == "user"
                            else "model"
                        ),
                        "parts": [{"text": message["content"]}]
                    }
                    for message in st.session_state.messages
                    if message["role"] in ("user", "assistant")
                ]

                response = client.models.generate_content(
                    model="gemini-3.8-flash",
                    contents=history,
                    config={
                        "system_instruction": SYSTEM_PROMPT
                    }
                )

                answer = (
                    response.text
                    or "I couldn't generate a response. Try again."
                )

            except Exception as error:
                answer = f"Something went wrong: {error}"

            st.write(answer)

    st.session_state.messages.append(
        {"role": "assistant", "content": answer}
    )

