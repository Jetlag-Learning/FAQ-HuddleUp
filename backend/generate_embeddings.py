"""
Script to generate and update embeddings for FAQ entries and knowledge base
Run this after setting up the database schema
"""

import os
import asyncio
from dotenv import load_dotenv
from supabase import create_client, Client
import openai
from typing import List
import json

# Load environment variables
load_dotenv()

# Initialize clients
supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_ROLE_KEY")
)

openai.api_key = os.getenv("OPENAI_API_KEY")

async def generate_embedding(text: str) -> List[float]:
    """Generate embedding for given text using OpenAI"""
    try:
        response = await openai.Embedding.acreate(
            model=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"),
            input=text
        )
        return response['data'][0]['embedding']
    except Exception as e:
        print(f"Error generating embedding: {e}")
        return None

async def update_faq_embeddings():
    """Update embeddings for all FAQ entries"""
    print("🔄 Updating FAQ embeddings...")
    
    # Get all FAQ entries without embeddings
    response = supabase.table('faq_entries').select('*').is_('embedding', 'null').execute()
    
    if not response.data:
        print("✅ All FAQ entries already have embeddings")
        return
    
    for entry in response.data:
        print(f"📝 Processing FAQ: {entry['question'][:50]}...")
        
        # Combine question and answer for embedding
        text_to_embed = f"Question: {entry['question']}\nAnswer: {entry['answer']}"
        
        # Generate embedding
        embedding = await generate_embedding(text_to_embed)
        
        if embedding:
            # Update the entry with embedding
            supabase.table('faq_entries').update({
                'embedding': embedding
            }).eq('id', entry['id']).execute()
            
            print(f"✅ Updated embedding for FAQ ID: {entry['id']}")
        else:
            print(f"❌ Failed to generate embedding for FAQ ID: {entry['id']}")

async def update_knowledge_base_embeddings():
    """Update embeddings for all knowledge base entries"""
    print("🔄 Updating knowledge base embeddings...")
    
    # Get all knowledge base entries without embeddings
    response = supabase.table('knowledge_base').select('*').is_('embedding', 'null').execute()
    
    if not response.data:
        print("✅ All knowledge base entries already have embeddings")
        return
    
    for entry in response.data:
        print(f"📚 Processing knowledge: {entry['title'][:50]}...")
        
        # Combine title and content for embedding
        text_to_embed = f"Title: {entry['title']}\nContent: {entry['content']}"
        
        # Generate embedding
        embedding = await generate_embedding(text_to_embed)
        
        if embedding:
            # Update the entry with embedding
            supabase.table('knowledge_base').update({
                'embedding': embedding
            }).eq('id', entry['id']).execute()
            
            print(f"✅ Updated embedding for knowledge base ID: {entry['id']}")
        else:
            print(f"❌ Failed to generate embedding for knowledge base ID: {entry['id']}")

async def test_semantic_search():
    """Test the semantic search function"""
    print("🧪 Testing semantic search...")
    
    # Generate embedding for test query
    test_query = "What is HuddleUp and how much does it cost?"
    query_embedding = await generate_embedding(test_query)
    
    if not query_embedding:
        print("❌ Failed to generate test query embedding")
        return
    
    # Test the semantic search function
    try:
        response = supabase.rpc('search_knowledge_base_semantic', {
            'query_embedding': query_embedding,
            'similarity_threshold': 0.5,
            'faq_limit': 3,
            'doc_limit': 2
        }).execute()
        
        print(f"✅ Semantic search successful! Found {len(response.data)} results:")
        for result in response.data:
            print(f"  - {result['source_type']}: {result['title'][:50]}... (similarity: {result['similarity']:.2f})")
            
    except Exception as e:
        print(f"❌ Semantic search test failed: {e}")

async def main():
    """Main function to update all embeddings"""
    print("🚀 Starting embedding generation process...")
    
    try:
        # Update FAQ embeddings
        await update_faq_embeddings()
        
        # Update knowledge base embeddings
        await update_knowledge_base_embeddings()
        
        # Test semantic search
        await test_semantic_search()
        
        print("✅ Embedding generation process completed!")
        
    except Exception as e:
        print(f"❌ Error in main process: {e}")

if __name__ == "__main__":
    asyncio.run(main())