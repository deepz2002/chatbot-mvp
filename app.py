#!/usr/bin/env python
import streamlit as st
from rag_agent import get_answer

st.set_page_config(page_title="Agno RAG Chatbot", page_icon="💬")
st.title("💬 RAG Chatbot")

if "history" not in st.session_state:
    st.session_state.history = []

# --- Chat input ---
user_input = st.text_input("Ask a question about the support docs:")

# --- When Send is clicked ---
if st.button("Send") and user_input:
    answer = get_answer(user_input)
    st.session_state.history.append(("You",  user_input))
    st.session_state.history.append(("Bot", answer))
    st.session_state.user_input = ""   # clear box

# --- Display chat history ---
for speaker, msg in st.session_state.history:
    st.markdown(f"**{speaker}:** {msg}")
