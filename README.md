# RAG Chatbot with Gemini AI

A smart document-powered chatbot that uses Retrieval-Augmented Generation (RAG) to answer questions based on your documentation. Built with Google's Gemini AI, ChromaDB vector storage, and Streamlit.

## 🚀 Features

- **Smart AI Responses**: Uses Google Gemini models for intelligent question answering
- **Document Search**: RAG-powered retrieval from your knowledge base
- **Quota-Aware Fallback**: Automatically switches to document-only search when AI quota is exceeded
- **Multiple Model Support**: Falls back between Gemini 1.5 Flash and Pro models
- **Simple Web Interface**: Clean Streamlit-based chat interface
- **Robust Error Handling**: Never fails completely, always provides some response

## 🏗️ Architecture

### How It Works

1. **Document Ingestion** (`ingest.py`):
   - Processes PDF and Word documents from the `data/` folder
   - Converts documents into embeddings using sentence-transformers
   - Stores embeddings in ChromaDB vector database

2. **RAG Pipeline** (`rag_agent.py`):
   - **Vector Search**: Finds relevant document chunks for user questions
   - **AI Enhancement**: Uses Gemini AI to generate contextual responses
   - **Smart Fallback**: Falls back to document-only search when AI is unavailable

3. **Web Interface** (`app.py`):
   - Simple chat interface built with Streamlit
   - Real-time question answering
   - Chat history preservation

### LLM Models Used

- **Primary**: Google Gemini 1.5 Flash
  - Fast responses, good for most queries
  - 1,500 requests/day free tier
- **Fallback**: Google Gemini 1.5 Pro  
  - More powerful but limited (50 requests/day free tier)
  - Used when Flash model fails
- **Document Search**: HuggingFace sentence-transformers
  - Model: `sentence-transformers/all-MiniLM-L6-v2`
  - Used for both embeddings and fallback search

## 📁 Project Structure

```
RAG-Chatbot/
├── app.py                 # Streamlit web interface
├── rag_agent.py          # RAG logic with AI and fallback
├── ingest.py             # Document processing and indexing
├── requirements.txt      # Python dependencies
├── .env                  # API keys (create this)
├── data/                 # Put your documents here
│   ├── document1.pdf
│   └── document2.docx
└── chroma_db/           # Vector database (auto-created)
    └── ...
```

## 🛠️ Setup Instructions

### 1. Clone and Install

```bash
# Clone the repository
git clone https://github.com/deepz2002/chatbot-mvp.git
cd RAG-Chatbot

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# Mac/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Get Google Gemini API Key

1. Go to [Google AI Studio](https://ai.google.dev/)
2. Create a new API key
3. Copy the API key

### 3. Configure Environment

Create a `.env` file in the project root:

```env
GOOGLE_API_KEY=your_api_key_here
```

### 4. Add Your Documents

1. Put your PDF and Word documents in the `data/` folder
2. Run the ingestion script to process them:

```bash
python ingest.py
```

This will:
- Process all documents in `data/`
- Create embeddings 
- Store them in the `chroma_db/` vector database

### 5. Run the Chatbot

```bash
streamlit run app.py
```

The chatbot will be available at `http://localhost:8501`

## 💡 Usage

### Basic Usage

1. Open the web interface
2. Type your question in the text box
3. Click "Send"
4. Get AI-powered responses based on your documents

### Example Questions

- "What are the system requirements?"
- "How do I install the software?"
- "What's the troubleshooting process for login issues?"
- "Explain the configuration options"

### Smart Fallback Behavior

The chatbot intelligently handles different scenarios:

- **Normal Operation**: AI analyzes documents and provides enhanced responses
- **Quota Exceeded**: Falls back to direct document search with basic formatting
- **API Errors**: Provides document excerpts instead of failing completely

## 🔧 Technical Details

### Vector Database

- **Engine**: ChromaDB (persistent storage)
- **Embeddings**: sentence-transformers/all-MiniLM-L6-v2
- **Collection**: "support_docs"
- **Search**: Semantic similarity search

### AI Models

- **Framework**: Agno (LLM orchestration)
- **Primary LLM**: Google Gemini 1.5 Flash
- **Fallback LLM**: Google Gemini 1.5 Pro
- **Context**: Document chunks + user question

### Error Handling

- **Quota Detection**: Automatically detects 429/quota errors
- **Model Switching**: Tries multiple Gemini models
- **Graceful Degradation**: Falls back to document search
- **Never Fails**: Always provides some response

## 📊 API Limits (Free Tier)

| Model | Requests/Minute | Requests/Day | Tokens/Minute |
|-------|----------------|--------------|---------------|
| Gemini 1.5 Flash | 15 | 1,500 | 1M |
| Gemini 1.5 Pro | 2 | 50 | 32K |

## 🐛 Troubleshooting

### Common Issues

1. **"API Key Missing" Error**:
   - Ensure `.env` file exists with `GOOGLE_API_KEY=your_key`
   - Check API key is valid at Google AI Studio

2. **"No Documents Found" Response**:
   - Run `python ingest.py` to process documents
   - Check documents are in `data/` folder
   - Verify `chroma_db/` folder was created

3. **"AI Service Unavailable" Messages**:
   - You've hit the daily quota limit
   - Wait 24 hours for quota reset, or upgrade to paid tier
   - The chatbot will still work with document search

4. **Import Errors**:
   - Ensure virtual environment is activated
   - Run `pip install -r requirements.txt`

### Performance Tips

- **Optimize Documents**: Use clear, well-structured documents
- **Specific Questions**: More specific questions get better responses
- **Document Size**: Break large documents into smaller sections
- **API Quota**: Monitor usage at [Google AI Studio](https://ai.google.dev/)

## 🔮 Future Enhancements

- [ ] Support for more document types (Markdown, TXT, etc.)
- [ ] Multiple knowledge bases
- [ ] Advanced search filters
- [ ] Response quality rating
- [ ] Multi-language support
- [ ] Integration with other LLM providers

## 📄 License

This project is open source. Feel free to modify and distribute.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

**Built with ❤️ using Google Gemini AI, ChromaDB, and Streamlit**
