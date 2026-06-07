import streamlit as st
import time
import os

def show_loading_page():
    st.set_page_config(
        page_title="Loading...",
        page_icon="⏳",
        layout="centered",
        initial_sidebar_state="collapsed"
    )
    
    # Custom CSS for the loading page
    st.markdown("""
    <style>
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        .spinner {
            animation: spin 1.5s linear infinite;
            font-size: 50px;
            text-align: center;
            margin: 20px 0;
        }
        .loading-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 80vh;
        }
        .progress-container {
            width: 80%;
            max-width: 400px;
            margin: 20px 0;
        }
        .loading-text {
            text-align: center;
            margin: 10px 0;
            font-size: 18px;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Loading content
    with st.container():
        st.markdown("""
        <div class="loading-container">
            <div class="spinner">⏳</div>
            <h1>NerdNET is Loading</h1>
            <div class="loading-text">Initializing AI components...</div>
            <div class="progress-container">
                <stProgress>
            </div>
            <div class="loading-text"></div>
        </div>
        """, unsafe_allow_html=True)
        
        # Simulate progress
        progress_bar = st.progress(0)
        for percent_complete in range(100):
            time.sleep(0.03)  # Adjust timing to match your actual loading needs
            progress_bar.progress(percent_complete + 1)
        
        # When loading is complete
        time.sleep(0.5)
        st.success("Ready!")
        time.sleep(1)
        
        # Redirect to the main app
        st.session_state.loading_complete = True
        st.rerun()

def main():
    if not st.session_state.get("loading_complete"):
        show_loading_page()
    else:
        # Import and run the main app
        from app4 import main as app4_main
        app4_main()

if __name__ == "__main__":
    main()