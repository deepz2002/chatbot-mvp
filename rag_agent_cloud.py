"""
rag_agent_cloud.py  –  Modified for Streamlit Cloud deployment
Handles ChromaDB initialization and data ingestion on startup
"""
import os
import time
import logging
import streamlit as st
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
# 1. Environment - Handle both local .env and Streamlit secrets
# ──────────────────────────────
load_dotenv()

# Get API key from environment or Streamlit secrets
google_api_key = os.getenv("GOOGLE_API_KEY")
if not google_api_key and hasattr(st, 'secrets'):
    try:
        google_api_key = st.secrets["GOOGLE_API_KEY"]
        os.environ["GOOGLE_API_KEY"] = google_api_key
    except:
        pass

if not google_api_key:
    st.error("GOOGLE_API_KEY is missing. Please configure it in Streamlit secrets.")
    st.stop()

# Handle HF token similarly
hf_token = os.getenv("HF_TOKEN") 
if not hf_token and hasattr(st, 'secrets'):
    try:
        hf_token = st.secrets["HF_TOKEN"]
        os.environ["HF_TOKEN"] = hf_token
    except:
        pass

# ──────────────────────────────
# 2. Initialize components with caching
# ──────────────────────────────
@st.cache_resource
def initialize_embedder():
    """Initialize embedder with caching"""
    return HuggingfaceCustomEmbedder("sentence-transformers/all-MiniLM-L6-v2")

@st.cache_resource  
def initialize_vector_db():
    """Initialize vector database with caching"""
    embedder = initialize_embedder()
    
    # For Streamlit Cloud, use in-memory ChromaDB
    vector_db = ChromaDb(
        collection="support_docs",
        path=None,  # In-memory for cloud deployment
        persistent_client=False,
        embedder=embedder,
    )
    
    # Ingest documents if the collection is empty
    if not hasattr(st.session_state, 'documents_ingested'):
        ingest_documents(vector_db, embedder)
        st.session_state.documents_ingested = True
    
    return vector_db

def ingest_documents(vector_db, embedder):
    """Ingest documents into the vector database"""
    try:
        from agno.knowledge.pdf import PDFKnowledgeBase
        from agno.knowledge.docx import DocxKnowledgeBase
        
        # Check if data directory exists
        data_dir = "data"
        if not os.path.exists(data_dir):
            logger.warning(f"Data directory '{data_dir}' not found. Creating empty collection.")
            return
            
        # Process PDF and DOCX files
        for filename in os.listdir(data_dir):
            filepath = os.path.join(data_dir, filename)
            
            if filename.endswith('.pdf'):
                logger.info(f"Ingesting PDF: {filename}")
                kb = PDFKnowledgeBase(path=filepath, embedder=embedder)
                vector_db.load_knowledge_base(kb)
                
            elif filename.endswith('.docx'):
                logger.info(f"Ingesting DOCX: {filename}")
                kb = DocxKnowledgeBase(path=filepath, embedder=embedder)
                vector_db.load_knowledge_base(kb)
        
        logger.info("Document ingestion completed")
        
    except Exception as e:
        logger.error(f"Error during document ingestion: {e}")
        st.warning(f"Could not ingest documents: {e}")

@st.cache_resource
def initialize_agent():
    """Initialize the RAG agent with caching"""
    embedder = initialize_embedder()
    vector_db = initialize_vector_db()
    
    knowledge_base = CombinedKnowledgeBase(vector_db=vector_db, embedder=embedder)
    
    # Multiple models for fallback
    models = [
        Gemini(id="gemini-1.5-flash"),
        Gemini(id="gemini-1.5-pro"),
    ]
    
    agent = Agent(
        model=models[0],
        knowledge=knowledge_base,
        search_knowledge=True,
        add_references=True,
    )
    
    return agent, models, knowledge_base

def search_documents_only(question: str, limit: int = 3) -> str:
    """Search documents directly without AI when quota is exceeded."""
    try:
        _, _, knowledge_base = initialize_agent()
        docs = knowledge_base.search(query=question, num_documents=limit)
        
        if not docs:
            return "❌ No relevant documents found for your question."
        
        response_parts = ["📄 **Found relevant information:**\n"]
        for i, doc in enumerate(docs, 1):
            content = doc.get('content', 'No content available')
            # Truncate very long content
            if len(content) > 500:
                content = content[:500] + "..."
            response_parts.append(f"**Result {i}:**\n{content}\n")
        
        return "\n".join(response_parts)
        
    except Exception as e:
        logger.error(f"Document search error: {e}")
        return f"❌ Search failed: {str(e)}"

def get_answer(question: str, max_retries: int = 2) -> str:
    """
    Get answer using RAG with smart fallback handling.
    """
    if not question.strip():
        return "❌ Please ask a valid question."
    
    try:
        agent, models, _ = initialize_agent()
        
        for attempt in range(max_retries + 1):
            try:
                model_name = models[min(attempt, len(models) - 1)].id
                logger.info(f"Trying AI model: {model_name}")
                
                # Update agent model for retry
                if attempt > 0:
                    agent.model = models[min(attempt, len(models) - 1)]
                
                response = agent.run(question)
                
                if response and response.content:
                    logger.info("✅ AI response successful")
                    return response.content
                else:
                    logger.warning("⚠️ Empty AI response received")
                    
            except Exception as model_error:
                error_msg = str(model_error).lower()
                logger.warning(f"Model {model_name} failed: {model_error}")
                
                # Check for quota/rate limit errors
                if any(keyword in error_msg for keyword in 
                       ['quota', 'rate limit', 'resource_exhausted', 'too many requests']):
                    logger.info("🔄 Quota exceeded, trying next model or fallback...")
                    if attempt < len(models) - 1:
                        time.sleep(2)  # Brief delay before retry
                        continue
                    else:
                        logger.info("📄 All models exhausted, switching to document search")
                        return search_documents_only(question)
                else:
                    # For other errors, try next model
                    if attempt < max_retries:
                        continue
                    raise model_error
        
        # If all retries failed, fallback to document search
        logger.info("📄 All retries failed, using document search fallback")
        return search_documents_only(question)
        
    except Exception as e:
        logger.error(f"Critical error in get_answer: {e}")
        return f"❌ Sorry, I encountered an error: {str(e)}\n\nTrying document search instead..."

# Test function for debugging
def test_setup():
    """Test the setup to ensure everything works"""
    try:
        agent, models, knowledge_base = initialize_agent()
        logger.info("✅ Setup test passed")
        return True
    except Exception as e:
        logger.error(f"❌ Setup test failed: {e}")
        return False
