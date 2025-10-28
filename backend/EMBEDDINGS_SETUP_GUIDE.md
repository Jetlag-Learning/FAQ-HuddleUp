# HuddleUp FAQ System - Embeddings Setup Guide

This guide will help you implement semantic search using embeddings for your HuddleUp FAQ system.

## 🎯 Overview

The embeddings enhancement provides:

- **Semantic search** instead of keyword matching
- **More accurate responses** using vector similarity
- **Better user experience** with relevant answers
- **Learning capability** from chat interactions

## 📋 Prerequisites

1. **Supabase Project** with PostgreSQL database
2. **OpenAI API Key** with access to embeddings API
3. **Python 3.8+** environment
4. **Required Python packages** (see requirements below)

## 🚀 Step 1: Database Setup

### 1.1 Execute SQL Schema

In your Supabase SQL Editor, run the complete schema from `supabase_embeddings_setup.sql`:

```sql
-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create tables with embedding columns
-- (Full schema is in supabase_embeddings_setup.sql)
```

**Important**: This creates:

- Vector extension for embeddings
- Enhanced tables with embedding columns
- Semantic search functions
- Proper indexes for performance

### 1.2 Verify Tables

After running the schema, verify these tables exist:

- `faq_entries` (with `question_embedding` column)
- `documents` (basic document storage)
- `document_chunks` (with `chunk_embedding` column)
- `chat_messages` (with `user_message_embedding` column)

## 🔧 Step 2: Environment Setup

### 2.1 Update .env File

Add/update your environment variables:

```env
# Supabase Configuration
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key

# Server Configuration
HOST=localhost
PORT=8000
DEBUG=true
```

### 2.2 Install Required Packages

```powershell
# Navigate to backend directory
cd backend

# Install required packages
pip install supabase==1.0.3
pip install openai==1.3.7
pip install numpy
pip install python-dotenv
pip install fastapi
pip install uvicorn
```

## 📊 Step 3: Populate Sample Data

### 3.1 Run Data Population Script

```powershell
# In the backend directory
python populate_data.py
```

This script will:

- Check your database setup
- Generate embeddings for sample FAQs
- Create sample documents with chunked embeddings
- Provide setup verification

### 3.2 Manual Data Addition (Alternative)

If you prefer to add data manually, use the new API endpoint:

```bash
curl -X POST "http://localhost:8000/api/faq/add-with-embedding" \
     -H "Content-Type: application/json" \
     -d '{
       "question": "Your question here",
       "answer": "Your answer here",
       "category": "general"
     }'
```

## 🖥️ Step 4: Start Enhanced Server

### 4.1 Option A: Use New Semantic Server

```powershell
# Start the enhanced server with semantic search
python main_semantic.py
```

### 4.2 Option B: Update Existing Server

Replace your current `main.py` with `main_semantic.py`:

```powershell
# Backup current main.py
copy main.py main_backup.py

# Replace with semantic version
copy main_semantic.py main.py

# Start server
python main.py
```

## 🧪 Step 5: Test Semantic Search

### 5.1 Test Basic Functionality

Visit: `http://localhost:8000/`

You should see:

```json
{
  "message": "HuddleUp FAQ API with Semantic Search",
  "version": "2.0.0",
  "services": {
    "database": true,
    "openai": true,
    "semantic_search": true,
    "embeddings": true
  }
}
```

### 5.2 Test Semantic Search Endpoint

```bash
curl -X POST "http://localhost:8000/api/faq/semantic-search" \
     -H "Content-Type: application/json" \
     -d '{"question": "What does this platform cost?"}'
```

### 5.3 Test Main FAQ Endpoint

```bash
curl -X POST "http://localhost:8000/api/faq/ask" \
     -H "Content-Type: application/json" \
     -d '{"question": "How much money do I need to pay?"}'
```

The response should include:

- Semantic search results
- Similarity scores
- Search method used
- Source information

## 🎨 Step 6: Frontend Integration

Your existing React frontend will work without changes! The enhanced `/api/faq/ask` endpoint:

- **Maintains backward compatibility**
- **Automatically uses semantic search** when available
- **Falls back gracefully** if services are unavailable
- **Provides enhanced response metadata**

## 🔍 Step 7: Monitoring and Optimization

### 7.1 Check Search Methods

Monitor the search methods returned in responses:

- `semantic_faq` - Found match in FAQ embeddings
- `semantic_document` - Found match in document embeddings
- `traditional_faq` - Fallback to keyword search
- `intelligent_fallback` - Using predefined responses

### 7.2 Adjust Similarity Thresholds

Modify similarity thresholds in your requests:

```json
{
  "question": "your question",
  "similarity_threshold": 0.8
}
```

- **0.9-1.0**: Very strict matching
- **0.7-0.8**: Balanced (recommended)
- **0.5-0.6**: More permissive

### 7.3 Monitor Performance

- Check embedding generation time
- Monitor database query performance
- Watch for OpenAI API rate limits
- Track search accuracy

## 🚨 Troubleshooting

### Common Issues:

1. **"Semantic search service not available"**

   - Check OpenAI API key
   - Verify Supabase connection
   - Ensure packages are installed

2. **"Vector extension not found"**

   - Run the SQL schema in Supabase
   - Enable pgvector extension

3. **"No semantic search results"**

   - Check if data has embeddings
   - Lower similarity threshold
   - Verify embedding dimensions (should be 1536)

4. **Server won't start**
   - Check directory: `cd d:\WORK FILES\FAQ-HuddleUp\backend`
   - Install missing packages
   - Check .env file configuration

### Debug Commands:

```powershell
# Check current directory
pwd

# Navigate to backend
cd "d:\WORK FILES\FAQ-HuddleUp\backend"

# Test Python imports
python -c "from semantic_search import SemanticSearchService; print('OK')"

# Check environment variables
python -c "import os; print(f'OpenAI: {bool(os.getenv(\"OPENAI_API_KEY\"))}')"
```

## 📈 Next Steps

1. **Add More Content**: Use the population script or API to add your actual FAQ content
2. **Optimize Thresholds**: Adjust similarity thresholds based on your content
3. **Monitor Usage**: Track which search methods work best for your users
4. **Scale Up**: Consider batch operations for large content imports

## 🎉 Success Indicators

Your semantic search is working when you see:

- ✅ Responses marked with `search_method: "semantic_faq"` or similar
- ✅ Similarity scores in response metadata
- ✅ More relevant answers to paraphrased questions
- ✅ Better handling of synonyms and related terms

## 📞 Need Help?

If you encounter issues:

1. Check the troubleshooting section above
2. Verify all prerequisites are met
3. Test with the sample data first
4. Monitor server logs for specific error messages

Your HuddleUp FAQ system is now enhanced with semantic search capabilities! 🚀
