
import os
import streamlit as st
from google import genai

st.set_page_config(
    page_title="PixelTTV AI Agent",
    page_icon="🎮",
    layout="centered"
)

st.title("🎮 PixelTTV AI Agent")
st.caption("Your ultimate Fortnite co-pilot.")

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    st.error("The AI key has not been configured yet.")
    st.stop()

client = genai.Client(api_key=api_key)

SYSTEM_PROMPT = """
You are PixelTTV AI, the personal AI assistant for PixelTTV.

YOUR PERSONALITY:
- High-energy, entertaining, funny, competitive and creative.
- Speak naturally and confidently.
- Be honest, helpful and practical.
- Match the user's energy without forcing it.

YOUR MISSION:
1. FORTNITE COACH
Help with ranked strategies, gameplay decisions, practice,
challenges and improvement.

2. YOUTUBE STRATEGIST
Help create video ideas, titles, hooks, scripts, thumbnails,
Shorts and content plans to grow PixelTTV.

3. CREATOR PARTNER
Help PixelTTV develop an entertaining, recognizable personality
and build a loyal audience.

4. PROJECT ASSISTANT
Help develop the PixelTTV AI Agent and explain technical steps
clearly, one step at a time.

CHANNEL CONTEXT:
- Channel name: PixelTTV.
- Current subscriber count: 180, as last reported.
- Content focus: Fortnite entertainment and personality-led videos.
- Style: energetic, funny, competitive, creative and authentic.
- One planned video: "Dominating Ranked (PRO GRIND)".
- The planned ranked journey starts at Gold, with Platinum as the goal.

CONTINUITY PROTOCOL:
- Use the complete conversation history provided to you.
- If the user provides a previous Continuity Report, treat it as
  background context and continue from its unfinished tasks.
- Never claim to remember conversations that were not provided.
- When asked for a Continuity Report, summarize important facts,
  decisions, completed work, current status and next steps.
- Preserve exact code, settings and error messages when relevant.
- Clearly distinguish confirmed facts from suggestions.
- End the report with a self-contained section titled
  "PASTE THIS INTO THE NEXT CONVERSATION".
- Do not invent missing information.

Always answer the user's actual question first.
Give clear instructions and avoid overwhelming the user.
"""

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "YO PIXELTTV! 🎮🔥 Your Fortnite co-pilot is online!\n\n"
                "We can work on ranked, content ideas, YouTube growth, "
                "or the AI agent itself. What are we building today?"
            )
        }
    ]

with st.sidebar:
    st.header("🎮 PixelTTV Control Center")
    st.write("Your Fortnite creator co-pilot.")

    if st.button("📋 Create Continuity Report", use_container_width=True):
        st.session_state.create_report = True

    if st.button("🆕 New Chat", use_container_width=True):
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "Fresh chat! 🔥 What are we working on?"
            }
        ]
        st.session_state.create_report = False
        st.rerun()

    st.caption(
        "Tip: Create a Continuity Report before starting a new chat."
    )

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if st.session_state.get("create_report", False):
    st.session_state.create_report = False

    with st.chat_message("assistant"):
        with st.spinner("Creating your Continuity Report..."):
            try:
                conversation = "\n\n".join(
                    f"{'User' if m['role'] == 'user' else 'PixelTTV AI'}: "
                    f"{m['content']}"
                    for m in st.session_state.messages
                )

                response = client.models.generate_content(
                    model="gemini-3.8-flash",
                    contents=(
                        "Create a detailed, accurate PixelTTV Continuity "
                        "Report from this conversation. Include confirmed "
                        "facts, decisions, completed work, current status, "
                        "unfinished tasks, and ordered next steps. Preserve "
                        "technical details where relevant. Do not invent "
                        "information. Finish with a self-contained section "
                        "titled PASTE THIS INTO THE NEXT CONVERSATION.\n\n"
                        + conversation
                    ),
                    config={"system_instruction": SYSTEM_PROMPT}
                )

                report = response.text or "Could not create the report."
                st.markdown(report)
                st.session_state.messages.append(
                    {"role": "assistant", "content": report}
                )

            except Exception as error:
                st.error(f"Could not create report: {error}")

prompt = st.chat_input("Talk to PixelTTV AI...")

if prompt:
    st.session_state.messages.append(
        {"role": "user", "content": prompt}
    )

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking... 🔥"):
            try:
                history = [
                    {
                        "role": (
                            "user" if m["role"] == "user" else "model"
                        ),
                        "parts": [{"text": m["content"]}]
                    }
                    for m in st.session_state.messages
                    if m["role"] in ("user", "assistant")
                ]

                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=history,
                    config={"system_instruction": SYSTEM_PROMPT}
                )

                answer = response.text or "Try asking me that another way!"

            except Exception as error:
                answer = f"Something went wrong: {error}"

            st.markdown(answer)

    st.session_state.messages.append(
        {"role": "assistant", "content": answer}
    )


