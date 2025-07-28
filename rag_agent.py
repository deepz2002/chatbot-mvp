"""
rag_agent.py  –  Answer questions with Gemini + Chroma vectors.
No OpenAI dependency; requires GOOGLE_API_KEY in .env
"""
# rag_agent.py
# import patch_agno_gemini_import  # 👈 removed patch since google-genai is now installed

import os
from dotenv import load_dotenv

from agno.agent import Agent
from agno.vectordb.chroma import ChromaDb
from agno.knowledge.combined import CombinedKnowledgeBase
from agno.embedder.huggingface import HuggingfaceCustomEmbedder
from agno.models.google import Gemini   # ✅ Google LLM

# ──────────────────────────────
# 1. Environment
# ──────────────────────────────
load_dotenv()
if not os.getenv("GOOGLE_API_KEY"):
    raise ValueError("GOOGLE_API_KEY missing. Add it to .env")

# ──────────────────────────────
# 2. Embedder (same as ingest)
# ──────────────────────────────
embedder = HuggingfaceCustomEmbedder("sentence-transformers/all-MiniLM-L6-v2")

# ──────────────────────────────
# 3. Vector DB (already built)
# ──────────────────────────────
vector_db = ChromaDb(
    collection="support_docs",
    path="chroma_db",
    persistent_client=True,
    embedder=embedder,
)

# ──────────────────────────────
# 4. Knowledge base wrapper
# ──────────────────────────────
knowledge_base = CombinedKnowledgeBase(vector_db=vector_db, embedder=embedder)

# ──────────────────────────────
# 5. Gemini model (using available model)
# ──────────────────────────────
llm = Gemini(id="gemini-1.5-flash")

# ──────────────────────────────
# 6. Agent
# ──────────────────────────────
agent = Agent(
    model            = llm,
    knowledge        = knowledge_base,
    search_knowledge = True,     # enables retrieval
    add_references   = True,     # add knowledge references
)

# ──────────────────────────────
# 7. Helper function
# ──────────────────────────────
def get_answer(question: str) -> str:
    """Return plain‑text answer or fallback."""
    reply = agent.run(question)
    # Check different possible attributes for the response content
    if reply:
        if hasattr(reply, 'content'):
            return reply.content.strip()
        elif hasattr(reply, 'message'):
            return str(reply.message).strip()
        elif hasattr(reply, 'text'):
            return reply.text.strip()
        else:
            return str(reply).strip()
    return "I don't know"
