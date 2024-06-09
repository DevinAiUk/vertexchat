import google.generativeai as genai
import streamlit as st
import time
import random
import huggingface_hub
from utils import SAFETY_SETTINGS

st.set_page_config(
    page_title="Vertex Chat AI",
    page_icon="🔥",
    menu_items={
        'About': "# Forked from https://github.com/omphcompany/geminichat"
    }
)

st.title("Vertex Chat AI")
st.caption("Chatbot, powered by Google Gemini Pro.")

# Hugging Face Hub Integration
repo_id = "airworkx/vertexchat"  # Replace with your repo ID
huggingface_token = st.text_input("Hugging Face Token", type='password')

if "history" not in st.session_state:
    st.session_state.history = []

if "app_key" not in st.session_state:
    app_key = st.text_input("Your Gemini App Key", type='password')
    if app_key:
        st.session_state.app_key = app_key

try:
    genai.configure(api_key=st.session_state.app_key)
except AttributeError as e:
    st.warning("Please Add Your Gemini App Key.")

model = genai.GenerativeModel('gemini-1.5-flash-001')
chat = model.start_chat(history=st.session_state.history)

with st.sidebar:
    if st.button("Clear Chat Window", use_container_width=True, type="primary"):
        st.session_state.history = []
        st.rerun()

for message in chat.history:
    role = "assistant" if message.role == "model" else message.role
    with st.chat_message(role):
        st.markdown(message.parts[0].text)

if "app_key" in st.session_state and huggingface_token:
    if prompt := st.chat_input(""):
        prompt = prompt.replace('\n', '  \n')
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            message_placeholder.markdown("Thinking...")
            try:
                full_response = ""
                for chunk in chat.send_message(prompt, stream=True, safety_settings = SAFETY_SETTINGS):
                    word_count = 0
                    random_int = random.randint(5, 10)
                    for word in chunk.text:
                        full_response += word
                        word_count += 1
                        if word_count == random_int:
                            time.sleep(0.05)
                            message_placeholder.markdown(full_response + "_")
                            word_count = 0
                            random_int = random.randint(5, 10)
                message_placeholder.markdown(full_response)

                # Save to Hugging Face Hub
                huggingface_hub.login(token=huggingface_token)
                huggingface_hub.create_repo(repo_id=repo_id, exist_ok=True)
                with huggingface_hub.create_commit(repo_id=repo_id, revision="main", message="Added new conversation", commit_message="Added new conversation"):
                    with open("conversation.txt", "a") as f:
                        f.write(f"\n**User:** {prompt}\n**Assistant:** {full_response}")

            except genai.types.generation_types.BlockedPromptException as e:
                st.exception(e)
            except Exception as e:
                st.exception(e)
            st.session_state.history = chat.history