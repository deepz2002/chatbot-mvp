#!/usr/bin/env python
"""
Simple, Clean Streamlit Chatbot - No clutter, just works!
"""
# CRITICAL: Fix SQLite before any other imports
try:
    import sqlite_fix
except Exception as e:
    print(f"SQLite fix warning: {e}")

import streamlit as st

# Page config
st.set_page_config(
    page_title="RAG Chatbot", 
    page_icon="💬",
    layout="centered"
)

# Import the working agent
try:
    from rag_agent_safe import get_answer
except ImportError:
    try:
        from rag_agent_fallback import get_answer
    except ImportError:
        try:
            from rag_agent import get_answer
        except ImportError:
            st.error("❌ No working RAG agent found")
            st.stop()

# Initialize session state
if "history" not in st.session_state:
    st.session_state.history = []

# Simple header
st.title("💬 RAG Chatbot")
st.markdown("Ask questions about the support documents!")

# Create input area
col1, col2 = st.columns([4, 1])

with col1:
    user_input = st.text_input(
        "Ask a question:",
        placeholder="e.g., What are the coverage details?",
        key="user_input"
    )

with col2:
    send_clicked = st.button("Send", type="primary", use_container_width=True)

# Process user input
if send_clicked and user_input.strip():
    with st.spinner("Thinking..."):
        try:
            answer = get_answer(user_input.strip())
            st.session_state.history.append(("You", user_input.strip()))
            st.session_state.history.append(("Bot", answer))
            st.rerun()
        except Exception as e:
            st.error(f"Error: {str(e)}")

# Display chat history
if st.session_state.history:
    st.markdown("---")
    
    for speaker, message in reversed(st.session_state.history):
        if speaker == "You":
            st.markdown(f"**🧑 You:** {message}")
        else:
            st.markdown(f"**🤖 Bot:** {message}")
        st.markdown("---")

# Simple sidebar with just clear button
with st.sidebar:
    st.markdown("## 🛠️ Controls")
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.history = []
        st.rerun()
    
    st.markdown(f"**Messages:** {len(st.session_state.history)}")
