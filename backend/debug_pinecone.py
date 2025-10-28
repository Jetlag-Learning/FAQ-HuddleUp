"""
Debug script to see what content is actually being returned from Pinecone
"""

import os
from dotenv import load_dotenv
from semantic_search import semantic_search_service

load_dotenv()

def debug_pinecone_content():
    """See what's actually stored in Pinecone"""
    print("🔍 Debugging Pinecone Content...")
    
    test_queries = [
        "What is HuddleUp?",
        "How much does it cost?",
        "hi"
    ]
    
    for query in test_queries:
        print(f"\n" + "="*50)
        print(f"Query: '{query}'")
        print("="*50)
        
        results = semantic_search_service.semantic_search(query, similarity_threshold=0.3)
        
        if results.get("success") and results.get("results"):
            for i, result in enumerate(results["results"][:3]):
                print(f"\nResult {i+1}:")
                print(f"  ID: {result.get('id')}")
                print(f"  Similarity: {result.get('similarity', 0):.3f}")
                print(f"  Source Type: {result.get('source_type')}")
                print(f"  Title: {result.get('title')}")
                
                # Check all possible content fields
                content_fields = ['content', 'text', 'answer', 'question']
                metadata = result.get('metadata', {})
                
                print(f"  Metadata keys: {list(metadata.keys())}")
                
                for field in content_fields:
                    value = result.get(field) or metadata.get(field)
                    if value:
                        print(f"  {field.capitalize()}: {value[:200]}...")
                
                print(f"  Full metadata: {metadata}")
        else:
            print("No results found")

if __name__ == "__main__":
    debug_pinecone_content()