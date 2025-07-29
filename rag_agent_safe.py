"""
Ultra-Safe RAG Agent - Direct Google AI integration without agno dependencies
This version works with just google-generativeai and basic text search
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

@st.cache_data
def load_documents():
    """Load and process documents from data directory"""
    documents = []
    data_dir = "data"
    
    if not os.path.exists(data_dir):
        logger.warning(f"Data directory '{data_dir}' not found")
        return documents
    
    try:
        # Load text files
        for filename in os.listdir(data_dir):
            if filename.endswith('.txt'):
                filepath = os.path.join(data_dir, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if content.strip():  # Only add non-empty files
                            documents.append({
                                'filename': filename,
                                'content': content.strip()
                            })
                            logger.info(f"✅ Loaded: {filename}")
                except Exception as e:
                    logger.warning(f"⚠️ Could not load {filename}: {e}")
        
        logger.info(f"📚 Total documents loaded: {len(documents)}")
        
    except Exception as e:
        logger.error(f"Error loading documents: {e}")
    
    return documents

def simple_search(query: str, documents: List[Dict], limit: int = 3) -> List[Dict]:
    """Enhanced text-based search"""
    if not documents:
        return []
    
    query_lower = query.lower()
    query_words = [word.strip() for word in query_lower.split() if len(word.strip()) > 2]
    
    scored_docs = []
    
    for doc in documents:
        content_lower = doc['content'].lower()
        score = 0
        
        # Exact phrase matching (higher weight)
        if query_lower in content_lower:
            score += 50
        
        # Individual word matching
        for word in query_words:
            count = content_lower.count(word)
            score += count * 5
            
            # Bonus for words in title/filename
            if word in doc['filename'].lower():
                score += 10
        
        if score > 0:
            scored_docs.append({
                **doc,
                'score': score,
                'snippet': get_snippet(doc['content'], query_words)
            })
    
    # Sort by score and return top results
    scored_docs.sort(key=lambda x: x['score'], reverse=True)
    return scored_docs[:limit]

def get_snippet(content: str, query_words: List[str], snippet_length: int = 300) -> str:
    """Extract relevant snippet from content"""
    content_lower = content.lower()
    
    # Find the best position to start the snippet
    best_pos = 0
    best_score = 0
    
    for i in range(0, len(content) - snippet_length, 50):
        section = content_lower[i:i + snippet_length]
        score = sum(section.count(word) for word in query_words)
        if score > best_score:
            best_score = score
            best_pos = i
    
    snippet = content[best_pos:best_pos + snippet_length]
    if best_pos > 0:
        snippet = "..." + snippet
    if best_pos + snippet_length < len(content):
        snippet = snippet + "..."
    
    return snippet

def get_ai_response(question: str, context: str) -> str:
    """Get AI response using Google Gemini directly"""
    try:
        import google.generativeai as genai
        
        api_key = get_api_credentials()
        if not api_key:
            return "❌ Google API key not found. Please configure it in Streamlit secrets."
        
        genai.configure(api_key=api_key)
        
        # Try multiple models in order of preference
        models_to_try = [
            'gemini-1.5-flash',
            'gemini-1.5-pro',
            'gemini-pro'
        ]
        
        for model_name in models_to_try:
            try:
                model = genai.GenerativeModel(model_name)
                
                prompt = f"""You are a helpful assistant that answers questions based on provided document context.

Context from support documents:
{context}

User Question: {question}

Please provide a helpful, accurate answer based on the context above. If the context doesn't contain enough information to fully answer the question, say so and provide what information you can find.

Answer:"""

                response = model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.1,
                        max_output_tokens=1000,
                    )
                )
                
                if response and response.text:
                    logger.info(f"✅ AI response from {model_name}")
                    return response.text
                    
            except Exception as model_error:
                logger.warning(f"⚠️ Model {model_name} failed: {model_error}")
                
                # Check for quota/rate limit errors
                error_str = str(model_error).lower()
                if any(term in error_str for term in ['quota', 'rate limit', 'resource_exhausted']):
                    if model_name != models_to_try[-1]:  # Not the last model
                        continue
                    else:
                        return "🤖 AI service is currently busy. Here's what I found in the documents instead."
                else:
                    continue
        
        return "❌ All AI models are currently unavailable."
        
    except ImportError:
        return "❌ Google AI library not available."
    except Exception as e:
        logger.error(f"AI response error: {e}")
        return f"❌ AI response failed: {str(e)}"

def search_documents_only(question: str, limit: int = 3) -> str:
    """Search documents and return formatted results"""
    try:
        documents = load_documents()
        if not documents:
            return "❌ No documents available for search. Please ensure text files are in the data directory."
        
        results = simple_search(question, documents, limit)
        
        if not results:
            return f"❌ No relevant information found for: '{question}'\n\nTry rephrasing your question or asking about a different topic."
        
        response_parts = [f"📄 **Found {len(results)} relevant document(s):**\n"]
        
        for i, doc in enumerate(results, 1):
            snippet = doc.get('snippet', doc['content'][:400])
            response_parts.append(f"**📋 Result {i} (from {doc['filename']}):**\n{snippet}\n")
            if i < len(results):
                response_parts.append("---\n")
        
        return "\n".join(response_parts)
        
    except Exception as e:
        logger.error(f"Document search error: {e}")
        return f"❌ Search failed: {str(e)}"

def get_answer(question: str) -> str:
    """Main function to get answers with AI + document search"""
    if not question or not question.strip():
        return "❌ Please ask a valid question."
    
    question = question.strip()
    logger.info(f"🔍 Processing question: {question[:100]}...")
    
    try:
        # Load documents
        documents = load_documents()
        
        if not documents:
            return "❌ No documents available. Please ensure text files are in the data directory."
        
        # Search for relevant documents
        relevant_docs = simple_search(question, documents, limit=3)
        
        if not relevant_docs:
            return f"❌ No relevant information found for: '{question}'"
        
        # Create context from relevant documents
        context_parts = []
        for doc in relevant_docs:
            # Use snippet if available, otherwise truncate content
            content = doc.get('snippet', doc['content'][:800])
            context_parts.append(f"From {doc['filename']}:\n{content}")
        
        context = "\n\n".join(context_parts)
        
        # Try to get AI response
        ai_response = get_ai_response(question, context)
        
        # Check if AI response is valid
        if ai_response and not ai_response.startswith("❌") and not ai_response.startswith("🤖 AI service is currently busy"):
            return ai_response
        else:
            # Fallback to document search
            logger.info("🔄 Falling back to document search")
            fallback_msg = "🤖 AI assistant is currently unavailable. Here's what I found in the documents:\n\n"
            return fallback_msg + search_documents_only(question)
    
    except Exception as e:
        logger.error(f"Critical error: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        # Last resort: try document search
        try:
            return f"❌ System error occurred. Trying document search:\n\n{search_documents_only(question)}"
        except:
            return f"❌ Critical system error: {str(e)}\n\nPlease try again or contact support."

def test_setup() -> bool:
    """Test system setup"""
    try:
        logger.info("🧪 Testing system setup...")
        
        # Test API credentials
        api_key = get_api_credentials()
        if not api_key:
            logger.error("❌ No Google API key found")
            return False
        
        # Test document loading
        documents = load_documents()
        if not documents:
            logger.warning("⚠️ No documents found, but system can still work")
        else:
            logger.info(f"✅ Found {len(documents)} documents")
        
        # Test Google AI import
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            logger.info("✅ Google AI library available")
        except Exception as e:
            logger.warning(f"⚠️ Google AI library issue: {e}")
        
        logger.info("✅ System test completed")
        return True
        
    except Exception as e:
        logger.error(f"❌ System test failed: {e}")
        return False

def get_system_status():
    """Get detailed system status"""
    try:
        documents = load_documents()
        api_key = get_api_credentials()
        
        status = {
            "api_key_present": bool(api_key),
            "documents_count": len(documents),
            "mode": "direct_google_ai",
            "documents_ready": len(documents) > 0,
            "ai_ready": bool(api_key)
        }
        
        # Test Google AI availability
        try:
            import google.generativeai as genai
            if api_key:
                genai.configure(api_key=api_key)
                status["google_ai_available"] = True
            else:
                status["google_ai_available"] = False
        except:
            status["google_ai_available"] = False
        
        return status
        
    except Exception as e:
        logger.error(f"Status check error: {e}")
        return {
            "api_key_present": False,
            "documents_count": 0,
            "mode": "error",
            "error": str(e)
        }
