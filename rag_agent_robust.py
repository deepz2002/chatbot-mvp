"""
rag_agent_cloud.py - ROBUST version for Streamlit Cloud deployment
Handles all common deployment issues and edge cases
"""
# CRITICAL: Fix SQLite before any other imports
try:
    import sqlite_fix
except:
    pass

import os
import time
import logging
import streamlit as st
from typing import List, Dict, Any
import traceback

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def safe_import():
    """Safely import all required modules with error handling"""
    try:
        from dotenv import load_dotenv
        from agno.agent import Agent
        from agno.vectordb.chroma import ChromaDb
        from agno.knowledge.combined import CombinedKnowledgeBase
        from agno.embedder.huggingface import HuggingfaceCustomEmbedder
        from agno.models.google import Gemini
        from agno.knowledge.pdf import PDFKnowledgeBase
        from agno.knowledge.docx import DocxKnowledgeBase
        
        return {
            'load_dotenv': load_dotenv,
            'Agent': Agent,
            'ChromaDb': ChromaDb,
            'CombinedKnowledgeBase': CombinedKnowledgeBase,
            'HuggingfaceCustomEmbedder': HuggingfaceCustomEmbedder,
            'Gemini': Gemini,
            'PDFKnowledgeBase': PDFKnowledgeBase,
            'DocxKnowledgeBase': DocxKnowledgeBase
        }
    except ImportError as e:
        logger.error(f"Import error: {e}")
        st.error(f"Failed to import required modules: {e}")
        return None

# Import modules safely
modules = safe_import()
if not modules:
    st.error("❌ Critical: Could not import required modules")
    st.stop()

# Load environment
modules['load_dotenv']()

def get_api_credentials():
    """Get API credentials from environment or Streamlit secrets"""
    google_api_key = os.getenv("GOOGLE_API_KEY")
    hf_token = os.getenv("HF_TOKEN")
    
    # Try Streamlit secrets if env vars not found
    if not google_api_key and hasattr(st, 'secrets'):
        try:
            google_api_key = st.secrets.get("GOOGLE_API_KEY")
            if google_api_key:
                os.environ["GOOGLE_API_KEY"] = google_api_key
        except Exception as e:
            logger.warning(f"Could not read GOOGLE_API_KEY from secrets: {e}")
    
    if not hf_token and hasattr(st, 'secrets'):
        try:
            hf_token = st.secrets.get("HF_TOKEN")
            if hf_token:
                os.environ["HF_TOKEN"] = hf_token
        except Exception as e:
            logger.warning(f"Could not read HF_TOKEN from secrets: {e}")
    
    return google_api_key, hf_token

@st.cache_resource
def initialize_embedder():
    """Initialize embedder with caching and error handling"""
    try:
        logger.info("🔄 Initializing embedder...")
        embedder = modules['HuggingfaceCustomEmbedder']("sentence-transformers/all-MiniLM-L6-v2")
        logger.info("✅ Embedder initialized successfully")
        return embedder
    except Exception as e:
        logger.error(f"❌ Failed to initialize embedder: {e}")
        st.error(f"Failed to initialize embedder: {e}")
        return None

@st.cache_resource  
def initialize_vector_db():
    """Initialize vector database with comprehensive error handling"""
    try:
        logger.info("🔄 Initializing vector database...")
        embedder = initialize_embedder()
        if not embedder:
            return None
        
        # Create in-memory ChromaDB for cloud deployment
        vector_db = modules['ChromaDb'](
            collection="support_docs",
            path=None,  # In-memory
            persistent_client=False,
            embedder=embedder,
        )
        
        # Ingest documents
        success = ingest_documents(vector_db, embedder)
        if not success:
            logger.warning("⚠️ Document ingestion had issues, but vector DB is ready")
        
        logger.info("✅ Vector database initialized successfully")
        return vector_db
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize vector database: {e}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        st.error(f"Failed to initialize vector database: {e}")
        return None

def ingest_documents(vector_db, embedder):
    """Robust document ingestion with comprehensive error handling"""
    try:
        data_dir = "data"
        if not os.path.exists(data_dir):
            logger.warning(f"📁 Data directory '{data_dir}' not found")
            st.warning("No data directory found. Creating empty knowledge base.")
            return False
        
        files = os.listdir(data_dir)
        if not files:
            logger.warning("📁 Data directory is empty")
            st.warning("Data directory is empty. No documents to ingest.")
            return False
        
        successful_ingestions = 0
        total_files = 0
        
        for filename in files:
            if not (filename.endswith('.pdf') or filename.endswith('.docx')):
                continue
                
            total_files += 1
            filepath = os.path.join(data_dir, filename)
            
            try:
                logger.info(f"📄 Processing: {filename}")
                
                if filename.endswith('.pdf'):
                    kb = modules['PDFKnowledgeBase'](path=filepath, embedder=embedder)
                elif filename.endswith('.docx'):
                    kb = modules['DocxKnowledgeBase'](path=filepath, embedder=embedder)
                
                vector_db.load_knowledge_base(kb)
                successful_ingestions += 1
                logger.info(f"✅ Successfully ingested: {filename}")
                
            except Exception as file_error:
                logger.error(f"❌ Failed to ingest {filename}: {file_error}")
                continue
        
        if successful_ingestions > 0:
            logger.info(f"📚 Ingested {successful_ingestions}/{total_files} documents successfully")
            return True
        else:
            logger.error("❌ No documents were successfully ingested")
            return False
            
    except Exception as e:
        logger.error(f"❌ Critical error during document ingestion: {e}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return False

@st.cache_resource
def initialize_agent():
    """Initialize the RAG agent with comprehensive error handling"""
    try:
        logger.info("🔄 Initializing RAG agent...")
        
        # Check API credentials
        google_api_key, hf_token = get_api_credentials()
        if not google_api_key:
            logger.error("❌ GOOGLE_API_KEY not found")
            st.error("❌ GOOGLE_API_KEY is required. Please add it to Streamlit secrets.")
            return None, None, None
        
        embedder = initialize_embedder()
        if not embedder:
            return None, None, None
            
        vector_db = initialize_vector_db()
        if not vector_db:
            return None, None, None
        
        knowledge_base = modules['CombinedKnowledgeBase'](
            vector_db=vector_db, 
            embedder=embedder
        )
        
        # Initialize models with error handling
        models = []
        try:
            models.append(modules['Gemini'](id="gemini-1.5-flash"))
            logger.info("✅ Added gemini-1.5-flash model")
        except Exception as e:
            logger.warning(f"⚠️ Could not initialize gemini-1.5-flash: {e}")
        
        try:
            models.append(modules['Gemini'](id="gemini-1.5-pro"))
            logger.info("✅ Added gemini-1.5-pro model")
        except Exception as e:
            logger.warning(f"⚠️ Could not initialize gemini-1.5-pro: {e}")
        
        if not models:
            logger.error("❌ No AI models could be initialized")
            st.error("❌ Could not initialize any AI models. Check your API key.")
            return None, None, None
        
        agent = modules['Agent'](
            model=models[0],
            knowledge=knowledge_base,
            search_knowledge=True,
            add_references=True,
        )
        
        logger.info("✅ RAG agent initialized successfully")
        return agent, models, knowledge_base
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize RAG agent: {e}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        st.error(f"Failed to initialize RAG agent: {e}")
        return None, None, None

def search_documents_only(question: str, limit: int = 3) -> str:
    """Enhanced document search with better error handling"""
    try:
        _, _, knowledge_base = initialize_agent()
        if not knowledge_base:
            return "❌ Knowledge base not available. Please check system initialization."
        
        docs = knowledge_base.search(query=question, num_documents=limit)
        
        if not docs:
            return f"❌ No relevant documents found for: '{question}'\n\nTry rephrasing your question or asking about a different topic."
        
        response_parts = [f"📄 **Found {len(docs)} relevant document(s):**\n"]
        for i, doc in enumerate(docs, 1):
            content = doc.get('content', 'No content available')
            # Truncate very long content
            if len(content) > 400:
                content = content[:400] + "..."
            response_parts.append(f"**📋 Result {i}:**\n{content}\n")
        
        return "\n".join(response_parts)
        
    except Exception as e:
        logger.error(f"Document search error: {e}")
        return f"❌ Search failed: {str(e)}\n\nPlease try again or contact support if the issue persists."

def get_answer(question: str, max_retries: int = 2) -> str:
    """
    Enhanced answer generation with comprehensive error handling
    """
    if not question or not question.strip():
        return "❌ Please ask a valid question."
    
    question = question.strip()
    logger.info(f"🔍 Processing question: {question[:100]}...")
    
    try:
        agent, models, knowledge_base = initialize_agent()
        
        if not agent or not models:
            logger.error("❌ Agent not initialized, falling back to document search")
            return search_documents_only(question)
        
        for attempt in range(max_retries + 1):
            try:
                current_model = models[min(attempt, len(models) - 1)]
                model_name = current_model.id
                logger.info(f"🤖 Attempt {attempt + 1}: Using {model_name}")
                
                # Update agent model for retry
                if attempt > 0:
                    agent.model = current_model
                
                # Set timeout for AI response
                start_time = time.time()
                response = agent.run(question)
                end_time = time.time()
                
                logger.info(f"⏱️ AI response time: {end_time - start_time:.2f}s")
                
                if response and hasattr(response, 'content') and response.content:
                    logger.info("✅ AI response successful")
                    return response.content
                elif response and isinstance(response, str):
                    logger.info("✅ AI response successful (string)")
                    return response
                else:
                    logger.warning("⚠️ Empty AI response received")
                    if attempt < max_retries:
                        continue
                    
            except Exception as model_error:
                error_msg = str(model_error).lower()
                logger.warning(f"❌ Model {model_name} failed: {model_error}")
                
                # Check for quota/rate limit errors
                quota_errors = ['quota', 'rate limit', 'resource_exhausted', 'too many requests', 'limit exceeded']
                if any(keyword in error_msg for keyword in quota_errors):
                    logger.info("🔄 Quota/rate limit detected")
                    if attempt < len(models) - 1:
                        logger.info(f"🔄 Trying next model in {2}s...")
                        time.sleep(2)
                        continue
                    else:
                        logger.info("📄 All models exhausted, switching to document search")
                        return f"🤖 AI services are currently busy. Here's what I found in the documents:\n\n{search_documents_only(question)}"
                else:
                    # For other errors, try next model
                    if attempt < max_retries:
                        logger.info(f"🔄 Retrying with different approach...")
                        time.sleep(1)
                        continue
                    raise model_error
        
        # If all retries failed, fallback to document search
        logger.info("📄 All AI attempts failed, using document search fallback")
        return f"🤖 AI response unavailable. Here's what I found in the documents:\n\n{search_documents_only(question)}"
        
    except Exception as e:
        logger.error(f"❌ Critical error in get_answer: {e}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        
        # Try document search as last resort
        try:
            return f"❌ AI system error: {str(e)}\n\nTrying document search instead:\n\n{search_documents_only(question)}"
        except:
            return f"❌ System error: {str(e)}\n\nPlease try again later or contact support."

def test_setup():
    """Comprehensive system test"""
    try:
        logger.info("🧪 Running system test...")
        
        # Test API credentials
        google_api_key, hf_token = get_api_credentials()
        if not google_api_key:
            logger.error("❌ Test failed: No Google API key")
            return False
        
        # Test embedder
        embedder = initialize_embedder()
        if not embedder:
            logger.error("❌ Test failed: Embedder initialization")
            return False
        
        # Test vector DB
        vector_db = initialize_vector_db()
        if not vector_db:
            logger.error("❌ Test failed: Vector database initialization")
            return False
        
        # Test agent
        agent, models, knowledge_base = initialize_agent()
        if not agent or not models:
            logger.error("❌ Test failed: Agent initialization")
            return False
        
        logger.info("✅ All system tests passed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ System test failed: {e}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return False

# Health check function
def get_system_status():
    """Get detailed system status for debugging"""
    status = {
        "api_key_present": bool(get_api_credentials()[0]),
        "embedder_ready": False,
        "vector_db_ready": False,
        "agent_ready": False,
        "documents_count": 0
    }
    
    try:
        if initialize_embedder():
            status["embedder_ready"] = True
        if initialize_vector_db():
            status["vector_db_ready"] = True
        agent, models, _ = initialize_agent()
        if agent and models:
            status["agent_ready"] = True
        
        # Count documents
        data_dir = "data"
        if os.path.exists(data_dir):
            status["documents_count"] = len([f for f in os.listdir(data_dir) 
                                           if f.endswith(('.pdf', '.docx'))])
    except:
        pass
    
    return status
