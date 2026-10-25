
import os
import streamlit as st
from google import genai

st.set_page_config(
    page_title="PixelTTV AI Agent",
    page_icon="🎮"
)

st.title("🎮 PixelTTV AI Agent")
st.write("Your Fortnite creator co-pilot!")

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    st.error("The AI key has not been configured yet.")
    st.stop()

client = genai.Client(api_key=api_key)

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "Yo! I'm PixelTTV AI. Let's plan some Fortnite content!"
        }
    ]

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
                response = client.models.generate_content(
                    model="gemini-3.8-flash",
                    contents=prompt
                )
                answer = response.text or "I couldn't generate a response."
            except Exception as error:
                answer = f"Something went wrong: {error}"

            st.write(answer)

    st.session_state.messages.append(
        {"role": "assistant", "content": answer}
    )
