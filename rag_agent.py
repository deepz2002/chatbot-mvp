"""
rag_agent.py  –  Answer questions with Gemini + Chroma vectors.
Includes smart fallback for quota/API issues.
"""
import os
import time
import logging
from dotenv import load_dotenv
from typing import List, Dict, Any

from agno.agent import Agent
from agno.vectordb.chroma import ChromaDb
from agno.knowledge.combined import CombinedKnowledgeBase
from agno.embedder.huggingface import HuggingfaceCustomEmbedder
from agno.models.google import Gemini

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
# 5. Multiple models for fallback
# ──────────────────────────────
models = [
    Gemini(id="gemini-1.5-flash"),
    Gemini(id="gemini-1.5-pro"),
]

# ──────────────────────────────
# 6. Agent with primary model
# ──────────────────────────────
agent = Agent(
    model            = models[0],
    knowledge        = knowledge_base,
    search_knowledge = True,
    add_references   = True,
)

def search_documents_only(question: str, limit: int = 3) -> str:
    """
    Search documents directly without AI when quota is exceeded.
    """
    try:
        results = vector_db.search(question, limit=limit)
        
        if not results:
            return "❌ No relevant documents found for your question."
        
        response_parts = [f"📚 **Document Search Results** (AI currently unavailable):"]
        
        for i, result in enumerate(results, 1):
            # Extract content
            content = ""
            if hasattr(result, 'content') and result.content:
                content = result.content
            elif hasattr(result, 'text') and result.text:
                content = result.text
            else:
                content = str(result)
            
            # Truncate if too long
            if len(content) > 200:
                content = content[:200] + "..."
            
            response_parts.append(f"\n**Result {i}:** {content}")
        
        response_parts.append("\n\n💡 **Note:** AI quota exceeded. Showing direct document matches.")
        return "\n".join(response_parts)
        
    except Exception as e:
        logger.error(f"Document search failed: {e}")
        return "❌ Error searching documents. Please try again later."

def get_answer(question: str) -> str:
    """
    Main function to get answers with smart fallback handling.
    """
    # Strategy 1: Try AI with both models
    for i, model in enumerate(models):
        try:
            agent.model = model
            logger.info(f"Trying AI model: {model.id}")
            
            reply = agent.run(question)
            
            # Parse response
            if reply:
                if hasattr(reply, 'content'):
                    return reply.content.strip()
                elif hasattr(reply, 'message'):
                    return str(reply.message).strip()
                elif hasattr(reply, 'text'):
                    return reply.text.strip()
                else:
                    return str(reply).strip()
                    
        except Exception as e:
            error_msg = str(e).lower()
            
            # Check for quota/rate limit errors
            if any(term in error_msg for term in ['429', 'quota', 'resource_exhausted', 'rate limit']):
                logger.warning(f"Quota exceeded for {model.id}")
                continue  # Try next model
            else:
                logger.error(f"Error with {model.id}: {e}")
                continue
    
    # Strategy 2: All AI models failed, use document search
    logger.info("AI unavailable, using document search fallback")
    return search_documents_only(question)
