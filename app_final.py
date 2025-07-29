#!/usr/bin/env python
"""
BULLETPROOF Streamlit Cloud Chatbot
This version handles all common deployment issues and provides detailed error reporting
"""
# CRITICAL: Fix SQLite before any other imports
try:
    import sqlite_fix
except Exception as e:
    print(f"SQLite fix warning: {e}")

import streamlit as st
import os
import sys
import time
import traceback

# Page config must be first
st.set_page_config(
    page_title="RAG Chatbot - Agno AI", 
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Try importing in order of preference: robust -> cloud -> fallback -> local
try:
    from rag_agent_robust import get_answer, test_setup, get_system_status
    VERSION = "robust"
    st.success("✅ Using robust cloud version with vector database")
except ImportError as e:
    st.warning(f"⚠️ Robust version failed: {e}")
    try:
        from rag_agent_cloud import get_answer, test_setup
        VERSION = "cloud"
        st.warning("⚠️ Using standard cloud version")
        # Create dummy status function
        def get_system_status():
            return {"mode": "cloud", "status": "limited"}
    except ImportError as e2:
        st.warning(f"⚠️ Cloud version failed: {e2}")
        try:
            from rag_agent_fallback import get_answer, test_setup, get_system_status
            VERSION = "fallback"
            st.info("ℹ️ Using fallback version (text search only)")
        except ImportError as e3:
            st.error(f"❌ Fallback version failed: {e3}")
            try:
                from rag_agent import get_answer
                VERSION = "local"
                st.warning("⚠️ Using local version")
                # Create dummy functions
                def test_setup():
                    return True
                def get_system_status():
                    return {"mode": "local", "status": "basic"}
            except ImportError as e4:
                st.error(f"❌ No working RAG agent found: {e4}")
                st.stop()

# App header
st.title("🤖 RAG Chatbot")
st.markdown("**Powered by Agno AI Framework + Google Gemini**")
st.markdown("Ask questions about support documents and get intelligent AI responses!")

# Initialize session state
if "history" not in st.session_state:
    st.session_state.history = []
if "initialized" not in st.session_state:
    st.session_state.initialized = False
if "initialization_error" not in st.session_state:
    st.session_state.initialization_error = None

# Sidebar for system info and controls
with st.sidebar:
    st.markdown("## 🛠️ System Control")
    
    # System status
    if st.button("🔄 Refresh System Status", use_container_width=True):
        st.session_state.initialized = False
        st.rerun()
    
    # Clear chat
    if st.button("🗑️ Clear Chat History", use_container_width=True):
        st.session_state.history = []
        st.rerun()
    
    st.markdown("---")
    
    # System information
    st.markdown("## 📊 System Status")
    
    if VERSION in ["robust", "fallback"]:
        try:
            status = get_system_status()
            st.markdown(f"**Version:** {VERSION}")
            st.markdown(f"**API Key:** {'✅' if status.get('api_key_present') else '❌'}")
            
            if VERSION == "robust":
                st.markdown(f"**Embedder:** {'✅' if status.get('embedder_ready') else '❌'}")
                st.markdown(f"**Vector DB:** {'✅' if status.get('vector_db_ready') else '❌'}")
                st.markdown(f"**AI Agent:** {'✅' if status.get('agent_ready') else '❌'}")
            
            st.markdown(f"**Documents:** {status.get('documents_count', 0)} files")
            st.markdown(f"**Mode:** {status.get('mode', 'unknown')}")
        except Exception as e:
            st.markdown(f"**Version:** {VERSION}")
            st.markdown("Status check failed")
    else:
        st.markdown(f"**Version:** {VERSION}")
        st.markdown("Limited status info")
    
    st.markdown(f"**Chat Messages:** {len(st.session_state.history)}")
    st.markdown(f"**Initialized:** {'✅' if st.session_state.initialized else '❌'}")
    
    st.markdown("---")
    st.markdown("## ℹ️ About")
    st.markdown("""
    **Features:**
    - 🔍 Document search & analysis
    - 🤖 AI-powered responses
    - 📄 Fallback to document search
    - 🔄 Multiple AI model fallback
    - 💾 Session chat history
    """)

# Main initialization
if not st.session_state.initialized:
    st.markdown("### 🚀 Initializing System...")
    
    initialization_container = st.container()
    
    with initialization_container:
        with st.spinner("🔧 Setting up AI components... This may take 30-60 seconds on first load."):
            try:
                # Test system setup
                if test_setup():
                    st.session_state.initialized = True
                    st.session_state.initialization_error = None
                    st.success("✅ System initialized successfully!")
                    st.balloons()
                    time.sleep(1)
                    st.rerun()
                else:
                    st.session_state.initialization_error = "System test failed"
                    st.error("❌ System initialization failed. Check logs for details.")
                    
            except Exception as e:
                st.session_state.initialization_error = str(e)
                st.error(f"❌ Initialization error: {str(e)}")
                
                # Show detailed error in expander
                with st.expander("🔍 Error Details"):
                    st.code(traceback.format_exc())
                
                st.markdown("### 🔧 Troubleshooting:")
                st.markdown("""
                1. **Check API Keys**: Ensure GOOGLE_API_KEY is set in Streamlit secrets
                2. **Wait and Retry**: Some components need time to initialize
                3. **Check Logs**: Look for specific error messages above
                4. **Contact Support**: If issues persist
                """)

# Main chat interface (only show if initialized)
if st.session_state.initialized:
    st.markdown("---")
    st.markdown("### 💬 Chat Interface")
    
    # Chat input area
    col1, col2 = st.columns([4, 1])
    
    with col1:
        user_input = st.text_input(
            "Ask your question:",
            placeholder="e.g., What are the coverage details for the Bronze plan?",
            key="user_input",
            label_visibility="collapsed"
        )
    
    with col2:
        send_clicked = st.button("Send 🚀", type="primary", use_container_width=True)
    
    # Process input
    if send_clicked and user_input.strip():
        question = user_input.strip()
        
        # Add user message to history immediately
        st.session_state.history.append(("user", question))
        
        # Show thinking indicator
        with st.spinner("🤔 Thinking..."):
            try:
                # Get AI response
                answer = get_answer(question)
                st.session_state.history.append(("assistant", answer))
                
            except Exception as e:
                error_msg = f"❌ Error processing question: {str(e)}"
                st.session_state.history.append(("assistant", error_msg))
                st.error(error_msg)
        
        # Clear input and refresh
        st.rerun()

    # Display chat history
    if st.session_state.history:
        st.markdown("---")
        st.markdown("### 📝 Chat History")
        
        # Reverse order to show latest first
        for i, (role, message) in enumerate(reversed(st.session_state.history)):
            if role == "user":
                st.markdown(f"**🧑 You:** {message}")
            else:
                st.markdown(f"**🤖 Assistant:** {message}")
            
            # Add separator between messages (except for last one)
            if i < len(st.session_state.history) - 1:
                st.markdown("---")

elif st.session_state.initialization_error:
    st.markdown("### ⚠️ System Not Ready")
    st.error("The system failed to initialize. Please check the error details above and try refreshing.")

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666; font-size: 0.8em;'>
        🤖 Powered by <strong>Agno AI Framework</strong> • 🧠 <strong>Google Gemini</strong> • ☁️ <strong>Streamlit Cloud</strong>
    </div>
    """,
    unsafe_allow_html=True
)
