import os
import json
import logging
import datetime
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI
from llama_index.core import VectorStoreIndex, StorageContext, Document, load_index_from_storage
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI as LLamaOpenAI
import streamlit.components.v1 as components
from PIL import Image
import requests
from io import BytesIO
from pptx import Presentation
import tempfile
import fitz  # PyMuPDF
import base64
import pandas as pd  # <-- Add this line
import os
import json
import logging

from functions import init_session_state 
from functions import save_chat_history
from functions import show_analytics_dashboard
from functions import stop_speech
from functions import speak_text
from functions import generate_image
from functions import create_powerpoint_from_content
from functions import save_powerpoint
from functions import delete_chat
from functions import rename_chat
from functions import init_session_state
from functions import load_chat_history
from functions import initialize_components
from functions import get_or_create_index
from functions import query_with_sources
from functions import stream_query_with_sources
from functions import categorize_date
from functions import interactive_speak
from functions import load_css
from functions import show_auth_page

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
PERSIST_DIR = "./storage"
CHAT_HISTORY_FILE = "chat_history.json"
PDF_PATH = "networkbook.pdf"
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def main():
     # Check authentication
    if not st.session_state.get("authenticated"):
        show_auth_page()
        return
    load_css()
    init_session_state()
     # Display welcome message
    st.sidebar.write(f"Welcome, {st.session_state['username']}!")

    with st.sidebar:
       with st.sidebar:
        st.title("📚 NerdNET")
        if st.button("➕ New Chat", key="new_chat_button"):
            name = f"Chat {len(st.session_state.chats) + 1}"
            st.session_state.chats[name] = [{
                "role": "system",
                "content": "Chat started.",
                "timestamp": datetime.datetime.now().isoformat()
            }]
            st.session_state.current_chat = name
            save_chat_history()
            st.rerun()  # Force refresh to show new chat

        if st.button("📊 Analytics Dashboard", key="analytics_button"):
            st.session_state.show_analytics = not st.session_state.show_analytics
            st.rerun()

        st.divider()

        # Chat history display (same as before but now user-specific)
        chat_meta = []
        for chat_name in st.session_state.chats:
            messages = st.session_state.chats[chat_name]
            ts = messages[0]["timestamp"] if messages else datetime.datetime.now().isoformat()
            chat_meta.append({"name": chat_name, "timestamp": ts})

        grouped = {}
        for chat in chat_meta:
            label = categorize_date(chat["timestamp"])
            if label not in grouped:
                grouped[label] = []
            grouped[label].append(chat)

        for label in sorted(grouped.keys(), reverse=True):
            st.markdown(f"**{label}**")
            for chat in grouped[label]:
                chat_name = chat["name"]
                
                col1, col2 = st.columns([4, 1])
                
                with col1:
                    btn = st.button(chat_name, key=f"sidebar_{chat_name}_{label}")
                    if btn:
                        st.session_state.current_chat = chat_name
                
                with col2:
                    with st.popover("⋮"):
                        new_name = st.text_input("Rename chat", value=chat_name, 
                                               key=f"rename_{chat_name}")
                        if st.button("Rename", key=f"rename_btn_{chat_name}"):
                            if new_name and new_name != chat_name:
                                rename_chat(chat_name, new_name)
                        
                        if len(st.session_state.chats) > 1:
                            if st.button("Delete", key=f"delete_{chat_name}"):
                                delete_chat(chat_name)

        st.divider()
        if st.button("🚪 Logout", key="logout_button"):
            st.session_state.clear()
            st.rerun()
        st.markdown("Created with ❤️ by Fatima & Hiba")


    # Main content area
    if st.session_state.show_analytics:
        if st.button("← Back to Chat"):
            st.session_state.show_analytics = False
            st.rerun()
        show_analytics_dashboard()
    else:
        st.title("💬 NerdNET")
        chat_id = st.session_state.current_chat
        
        # Display chat messages
        for i, msg in enumerate(st.session_state.chats[chat_id]):
            if msg["role"] == "system":
                continue
                
            style = "user-message" if msg["role"] == "user" else "assistant-message"
            icon = "👤" if msg["role"] == "user" else "🤖"
            msg_key = f"msg_{chat_id}_{i}_{hash(msg['content'])}"
            
            with st.container():
                st.markdown(f"""
                <div class="chat-message {style}">
                    {icon} <strong>{msg["role"].capitalize()}:</strong> {msg["content"]}
                </div>
                """, unsafe_allow_html=True)

                if msg["role"] == "user":
                    col1, col2 = st.columns([1, 1])
                    
                    with col1:
                        if st.button("📋 Copy", key=f"copy_{msg_key}"):
                            components.html(f"""
                            <script>
                            function copyToClipboard() {{
                                navigator.clipboard.writeText(`{msg["content"]}`);
                            }}
                            copyToClipboard();
                            </script>
                            """, height=0)
                            st.toast("Message copied to clipboard!")
                            
                    with col2:
                        if st.button("✏️ Edit", key=f"edit_{msg_key}"):
                            st.session_state.editing = msg_key
                            st.session_state.edit_content = msg["content"]
                            st.session_state.editing_index = i
                    
                    if st.session_state.get("editing") == msg_key:
                        edited_content = st.text_area(
                            "Edit your question:",
                            value=st.session_state.get("edit_content", msg["content"]),
                            key=f"edit_area_{msg_key}"
                        )
                        
                        col_send, col_cancel = st.columns([1, 1])
                        with col_send:
                            if st.button("📤 Send", key=f"send_{msg_key}"):
                                # Update the question text
                                st.session_state.chats[chat_id][st.session_state.editing_index]["content"] = edited_content
                                
                                # Remove the old assistant response if it exists
                                if st.session_state.editing_index + 1 < len(st.session_state.chats[chat_id]):
                                    next_msg = st.session_state.chats[chat_id][st.session_state.editing_index + 1]
                                    if next_msg["role"] == "assistant":
                                        del st.session_state.chats[chat_id][st.session_state.editing_index + 1]
                                
                                # Set as pending prompt to get new response
                                st.session_state.pending_prompt = edited_content
                                st.session_state.awaiting_response = True
                                
                                # Clear editing state
                                del st.session_state.editing
                                del st.session_state.edit_content
                                del st.session_state.editing_index
                                
                                save_chat_history()
                                st.rerun()
                                
                        with col_cancel:
                            if st.button("❌ Cancel", key=f"cancel_{msg_key}"):
                                del st.session_state.editing
                                del st.session_state.edit_content
                                del st.session_state.editing_index
                                st.rerun()
                # For assistant messages, only show copy button
                elif msg["role"] == "assistant":
                    if st.button("📋 Copy", key=f"copy_{msg_key}"):
                        components.html(f"""
                        <script>
                        function copyToClipboard() {{
                            navigator.clipboard.writeText(`{msg["content"]}`);
                        }}
                        copyToClipboard();
                        </script>
                        """, height=0)
                        st.toast("Message copied to clipboard!")

                if msg.get("image_url"):
                    try:
                        response = requests.get(msg["image_url"])
                        img = Image.open(BytesIO(response.content))
                        with st.container():
                            st.markdown('<div class="image-container">', unsafe_allow_html=True)
                            st.image(img, caption="Generated Image")
                            st.markdown('</div>', unsafe_allow_html=True)
                    except Exception as e:
                        st.error(f"Couldn't load image: {str(e)}")

                if msg.get("pptx_bytes"):
                    with st.container():
                        st.markdown("---")
                        save_powerpoint(msg["pptx_bytes"], f"presentation_{msg['timestamp'][:10]}.pptx")

                if msg["role"] == "assistant":
                    with st.container():
                        interactive_speak(msg["content"])

        prompt = st.chat_input("Type your message...")
        if prompt:
            now = datetime.datetime.now().isoformat()
            st.session_state.chats[chat_id].append({
                "role": "user",
                "content": prompt,
                "timestamp": now
            })
            st.session_state.pending_prompt = prompt
            st.session_state.awaiting_response = True
            save_chat_history()
            st.rerun()

        # Process pending prompts
        if st.session_state.awaiting_response and st.session_state.pending_prompt:
            lower_prompt = st.session_state.pending_prompt.lower()
            image_keywords = ["diagram", "image", "picture", "drawing", "visual"]
            ppt_keywords = ["powerpoint", "ppt", "slides", "presentation"]

            if any(keyword in lower_prompt for keyword in image_keywords):
                with st.spinner("Generating image..."):
                    image_url = generate_image(st.session_state.pending_prompt)
                    if image_url:
                        st.session_state.chats[chat_id].append({
                            "role": "assistant",
                            "content": f"Here's the generated image for: {st.session_state.pending_prompt}",
                            "timestamp": datetime.datetime.now().isoformat(),
                            "image_url": image_url
                        })
                        if st.session_state.get("auto_read", True):
                            speak_text("I've generated an image for your request")
                            st.session_state.is_speaking = True
                    else:
                        st.session_state.chats[chat_id].append({
                            "role": "assistant",
                            "content": "I couldn't generate an image for that request. Please try again.",
                            "timestamp": datetime.datetime.now().isoformat()
                        })

                    st.session_state.pending_prompt = None
                    st.session_state.awaiting_response = False
                    save_chat_history()
                    st.rerun()

            elif any(keyword in lower_prompt for keyword in ppt_keywords):
                with st.spinner("Creating PowerPoint presentation..."):
                    embed_model, llm = initialize_components()
                    if embed_model and llm:
                        index = get_or_create_index(embed_model, llm)
                        if index:
                            try:
                                query_engine = index.as_query_engine(llm=llm, embed_model=embed_model)
                                response = query_engine.query(
                                    f"Create a PowerPoint outline with slides about: {st.session_state.pending_prompt}. "
                                    "Format each slide as: 'Slide X: [Title] - [Content]'"
                                )
                                content = str(response.response)
                                pptx_bytes = create_powerpoint_from_content(content)

                                if pptx_bytes:
                                    st.session_state.chats[chat_id].append({
                                        "role": "assistant",
                                        "content": content,
                                        "timestamp": datetime.datetime.now().isoformat(),
                                        "pptx_bytes": pptx_bytes
                                    })
                                    if st.session_state.get("auto_read", True):
                                        speak_text("I've created a PowerPoint presentation for you. You can download it below.")
                                        st.session_state.is_speaking = True
                                else:
                                    st.session_state.chats[chat_id].append({
                                        "role": "assistant",
                                        "content": content + "\n\n[I couldn't generate the PowerPoint file]",
                                        "timestamp": datetime.datetime.now().isoformat()
                                    })

                                st.session_state.pending_prompt = None
                                st.session_state.awaiting_response = False
                                save_chat_history()
                                st.rerun()

                            except Exception as e:
                                st.error(f"Failed to create PowerPoint: {str(e)}")
                                st.session_state.pending_prompt = None
                                st.session_state.awaiting_response = False

            else:
                with st.spinner("Thinking..."):
                    embed_model, llm = initialize_components()
                    if embed_model and llm:
                        index = get_or_create_index(embed_model, llm)
                        if index:
                            try:
                                full_response = stream_query_with_sources(
                                    index=index,
                                    prompt=st.session_state.pending_prompt,
                                    embed_model=embed_model,
                                    llm=llm,
                                    chat_id=chat_id
                                )

                                if st.session_state.get("auto_read", True):
                                    speak_text(full_response)
                                    st.session_state.is_speaking = True

                                st.session_state.pending_prompt = None
                                st.session_state.awaiting_response = False
                                save_chat_history()
                                st.rerun()

                            except Exception as e:
                                st.error(f"Streaming query failed: {str(e)}")
                                logger.error(f"Streaming query error: {str(e)}")
                                st.session_state.pending_prompt = None
                                st.session_state.awaiting_response = False

    # Global stop button
    with st.sidebar:
        st.divider()
        if st.button("⏹️ Stop All Speech", key="stop_all_speech"):
            stop_speech()
            st.session_state.is_speaking = False
            st.toast("All speech stopped")
            st.rerun()
if __name__ == "__main__":
    main()