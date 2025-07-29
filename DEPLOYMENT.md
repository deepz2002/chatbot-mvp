# RAG Chatbot Deployment Guide

## 🚀 Streamlit Cloud Deployment

### Prerequisites
1. GitHub repository with your code
2. Google AI API key
3. Hugging Face token (optional, for custom embeddings)

### Deployment Steps

#### 1. Push to GitHub
```bash
git add .
git commit -m "Prepare for Streamlit Cloud deployment"
git push origin main
```

#### 2. Deploy on Streamlit Cloud
1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Connect your GitHub account
3. Select your repository: `chatbot-mvp`
4. Set main file path: `app_cloud.py`
5. Set Python version: `3.11`

#### 3. Configure Secrets
In Streamlit Cloud dashboard, add these secrets:

```toml
GOOGLE_API_KEY = "your_actual_google_api_key_here"
HF_TOKEN = "your_huggingface_token_here"
```

### 📁 Project Structure
```
chatbot-mvp/
├── app.py              # Original local version
├── app_cloud.py        # Cloud-optimized version
├── rag_agent.py        # Original RAG agent
├── rag_agent_cloud.py  # Cloud-optimized RAG agent
├── requirements.txt    # Dependencies
├── data/              # Support documents (PDF, DOCX)
├── .streamlit/        # Streamlit configuration
└── README.md          # This file
```

### 🔧 Local Development
For local development, use the original files:
```bash
# Activate virtual environment
source .venv/bin/activate

# Run locally
streamlit run app.py
```

### 🌐 Cloud Features
The cloud version includes:
- ✅ In-memory ChromaDB (ephemeral storage)
- ✅ Automatic document ingestion on startup
- ✅ Streamlit caching for performance
- ✅ Fallback to document search if AI quota exceeded
- ✅ Better error handling and user feedback

### 📊 Performance Notes
- First load may take 30-60 seconds to initialize embeddings
- Subsequent interactions are fast due to caching
- Documents are re-ingested on each deployment

### 🐛 Troubleshooting
1. **Initialization Error**: Check API keys in secrets
2. **No Documents Found**: Ensure `/data` folder contains PDF/DOCX files
3. **Quota Exceeded**: App automatically falls back to document search
4. **Slow Performance**: Normal on first load, improves with caching

### 🔄 Updates
To update the deployed app:
1. Push changes to GitHub
2. Streamlit Cloud will automatically redeploy
