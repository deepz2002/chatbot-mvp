#!/usr/bin/env python
"""
Streamlit Cloud-ready chatbot application
"""
import streamlit as st
import os
import time

# Try importing the cloud version first, fallback to local version
try:
    from rag_agent_cloud import get_answer, test_setup
    CLOUD_VERSION = True
except ImportError:
    from rag_agent import get_answer
    CLOUD_VERSION = False

st.set_page_config(
    page_title="Agno RAG Chatbot", 
    page_icon="💬",
    layout="wide"
)

# Title and description
st.title("💬 RAG Chatbot")
st.markdown("Ask questions about the support documents and get AI-powered answers!")

# Initialize session state
if "history" not in st.session_state:
    st.session_state.history = []

if "initialized" not in st.session_state:
    st.session_state.initialized = False

# For cloud version, show initialization status
if CLOUD_VERSION and not st.session_state.initialized:
    with st.spinner("🚀 Initializing AI components... This may take a moment on first load."):
        try:
            if test_setup():
                st.session_state.initialized = True
                st.success("✅ System initialized successfully!")
            else:
                st.error("❌ Failed to initialize system. Please check your API keys.")
                st.stop()
        except Exception as e:
            st.error(f"❌ Initialization error: {str(e)}")
            st.stop()

# Create two columns for better layout
col1, col2 = st.columns([3, 1])

with col1:
    # Chat input
    user_input = st.text_input(
        "Ask a question about the support docs:",
        placeholder="e.g., How do I reset my password?",
        key="user_input"
    )

with col2:
    # Send button
    send_clicked = st.button("Send 📤", type="primary", use_container_width=True)

# Process user input
if send_clicked and user_input.strip():
    with st.spinner("🤔 Thinking..."):
        try:
            answer = get_answer(user_input.strip())
            st.session_state.history.append(("You", user_input.strip()))
            st.session_state.history.append(("Bot", answer))
            
            # Clear input by rerunning
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ Error processing your question: {str(e)}")

# Display chat history
if st.session_state.history:
    st.markdown("---")
    st.subheader("💬 Chat History")
    
    for i, (speaker, msg) in enumerate(reversed(st.session_state.history)):
        if speaker == "You":
            st.markdown(f"**🧑 You:** {msg}")
        else:
            st.markdown(f"**🤖 Bot:** {msg}")
        
        # Add separator between conversations
        if i < len(st.session_state.history) - 1:
            st.markdown("---")

# Sidebar with information
with st.sidebar:
    st.markdown("## ℹ️ About")
    st.markdown(
        """
        This chatbot uses **Retrieval-Augmented Generation (RAG)** to answer 
        questions based on your support documents.
        
        **Features:**
        - 🔍 Searches through uploaded documents
        - 🤖 Uses Google's Gemini AI for intelligent responses
        - 📄 Falls back to document search if AI quota is exceeded
        - 💾 Maintains chat history during your session
        """
    )
    
    if CLOUD_VERSION:
        st.markdown("### 🌐 Cloud Version")
        st.markdown("Running optimized version for Streamlit Cloud")
    
    # Clear chat button
    if st.button("🗑️ Clear Chat History", use_container_width=True):
        st.session_state.history = []
        st.rerun()
    
    # System status
    st.markdown("### 📊 System Status")
    if st.session_state.get("initialized", False):
        st.success("✅ System Ready")
    else:
        st.warning("⚠️ Initializing...")
    
    st.markdown(f"**Chat Messages:** {len(st.session_state.history)}")

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666;'>
        Powered by <strong>Agno</strong> RAG Framework & <strong>Google Gemini</strong>
    </div>
    """,
    unsafe_allow_html=True
)
