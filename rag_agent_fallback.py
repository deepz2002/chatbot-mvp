"""
Fallback RAG agent without ChromaDB for maximum compatibility
Uses simple text search when vector database fails
"""
import os
import logging
import streamlit as st
from typing import List, Dict, Any
import traceback
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_api_credentials():
    """Get API credentials from environment or Streamlit secrets"""
    google_api_key = os.getenv("GOOGLE_API_KEY")
    
    if not google_api_key and hasattr(st, 'secrets'):
        try:
            google_api_key = st.secrets.get("GOOGLE_API_KEY")
            if google_api_key:
                os.environ["GOOGLE_API_KEY"] = google_api_key
        except Exception as e:
            logger.warning(f"Could not read GOOGLE_API_KEY from secrets: {e}")
    
    return google_api_key

def load_documents():
    """Load and process documents from data directory"""
    documents = []
    data_dir = "data"
    
    if not os.path.exists(data_dir):
        logger.warning(f"Data directory '{data_dir}' not found")
        return documents
    
    try:
        # Simple text extraction
        for filename in os.listdir(data_dir):
            if filename.endswith('.txt'):
                filepath = os.path.join(data_dir, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    documents.append({
                        'filename': filename,
                        'content': content
                    })
        
        logger.info(f"Loaded {len(documents)} text documents")
        
    except Exception as e:
        logger.error(f"Error loading documents: {e}")
    
    return documents

@st.cache_data
def get_documents():
    """Cache loaded documents"""
    return load_documents()

def simple_search(query: str, documents: List[Dict], limit: int = 3) -> List[Dict]:
    """Simple text-based search without vectors"""
    if not documents:
        return []
    
    query_words = query.lower().split()
    scored_docs = []
    
    for doc in documents:
        content = doc['content'].lower()
        score = 0
        
        # Simple keyword matching
        for word in query_words:
            score += content.count(word)
        
        if score > 0:
            scored_docs.append({
                **doc,
                'score': score
            })
    
    # Sort by score and return top results
    scored_docs.sort(key=lambda x: x['score'], reverse=True)
    return scored_docs[:limit]

def get_ai_response(question: str, context: str) -> str:
    """Get AI response using Google Gemini"""
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        import google.generativeai as genai
        
        api_key = get_api_credentials()
        if not api_key:
            return "❌ Google API key not found"
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""
        Based on the following context from support documents, please answer the user's question.
        
        Context:
        {context}
        
        Question: {question}
        
        Please provide a helpful and accurate answer based on the context provided.
        """
        
        response = model.generate_content(prompt)
        return response.text
        
    except Exception as e:
        logger.error(f"AI response error: {e}")
        return f"❌ AI response failed: {str(e)}"

def search_documents_only(question: str, limit: int = 3) -> str:
    """Search documents without AI"""
    try:
        documents = get_documents()
        if not documents:
            return "❌ No documents available for search."
        
        results = simple_search(question, documents, limit)
        
        if not results:
            return f"❌ No relevant documents found for: '{question}'"
        
        response_parts = [f"📄 **Found {len(results)} relevant document(s):**\n"]
        
        for i, doc in enumerate(results, 1):
            content = doc['content']
            if len(content) > 500:
                content = content[:500] + "..."
            
            response_parts.append(f"**📋 Result {i} (from {doc['filename']}):**\n{content}\n")
        
        return "\n".join(response_parts)
        
    except Exception as e:
        logger.error(f"Document search error: {e}")
        return f"❌ Search failed: {str(e)}"

def get_answer(question: str) -> str:
    """Get answer with fallback approach"""
    if not question or not question.strip():
        return "❌ Please ask a valid question."
    
    question = question.strip()
    logger.info(f"Processing question: {question[:100]}...")
    
    try:
        # Get documents
        documents = get_documents()
        
        if not documents:
            return "❌ No documents available. Please add text files to the data directory."
        
        # Search for relevant documents
        relevant_docs = simple_search(question, documents, limit=3)
        
        if not relevant_docs:
            return f"❌ No relevant information found for: '{question}'"
        
        # Create context from relevant documents
        context = "\n\n".join([doc['content'][:1000] for doc in relevant_docs])
        
        # Try to get AI response
        try:
            ai_response = get_ai_response(question, context)
            if ai_response and not ai_response.startswith("❌"):
                return ai_response
            else:
                logger.warning("AI response failed, falling back to document search")
                return search_documents_only(question)
                
        except Exception as ai_error:
            logger.warning(f"AI failed: {ai_error}, using document search")
            return search_documents_only(question)
    
    except Exception as e:
        logger.error(f"Critical error: {e}")
        return f"❌ System error: {str(e)}"

def test_setup() -> bool:
    """Test the fallback setup"""
    try:
        api_key = get_api_credentials()
        if not api_key:
            logger.error("No Google API key found")
            return False
        
        documents = get_documents()
        logger.info(f"Found {len(documents)} documents")
        
        return True
        
    except Exception as e:
        logger.error(f"Setup test failed: {e}")
        return False

def get_system_status():
    """Get system status"""
    return {
        "api_key_present": bool(get_api_credentials()),
        "documents_count": len(get_documents()),
        "mode": "fallback_text_search"
    }
