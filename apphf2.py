import google.generativeai as genai
import streamlit as st
import time
import random
import huggingface_hub
from utils import SAFETY_SETTINGS
import json

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
repo_id = "airworkx/vertexchat"  # Your space ID
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

# Load conversation history
conversation_history = []
try:
    huggingface_hub.login(token=huggingface_token)
    repo = huggingface_hub.Repo(repo_id=repo_id, revision="main")
    with repo.file_obj("conversation_metadata.json", "r") as f:
        conversation_history = json.load(f)
except FileNotFoundError:
    pass  # Initialize empty if file doesn't exist
except ValueError:
    st.warning("Invalid Hugging Face Token. Please check your token.")

# Display the conversation history
for entry in conversation_history:
    if entry["role"] == "user":
        with st.chat_message("user"):
            st.markdown("[User Message]")
    elif entry["role"] == "assistant":
        with st.chat_message("assistant"):
            st.markdown("[Assistant Message]")


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
                for chunk in chat.send_message(prompt, stream=True, safety_settings=SAFETY_SETTINGS):
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

                # Update and save conversation history
                conversation_history.append({"role": "user"})
                conversation_history.append({"role": "assistant"})

                # Save to Hugging Face Hub
                try:
                    huggingface_hub.login(token=huggingface_token)
                    with open("conversation_metadata.json", "w") as f:
                        json.dump(conversation_history, f)
                    huggingface_hub.upload_file(
                        path_or_fileobj="conversation_metadata.json",
                        repo_id=repo_id,
                        repo_type="space",  # Indicate it's a space
                        revision="main",
                        path_in_repo="conversation_metadata.json"
                    )
                except ValueError:
                    st.warning("Invalid Hugging Face Token. Please check your token.")

            except genai.types.generation_types.BlockedPromptException as e:
                st.exception(e)
            except Exception as e:
                st.exception(e)