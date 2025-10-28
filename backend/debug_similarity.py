#!/usr/bin/env python3
"""
Debug Pinecone Similarity Scores
Check what similarity scores we're actually getting
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from semantic_search import SemanticSearchService

def debug_similarity_scores():
    """Debug what similarity scores we're getting from Pinecone"""
    
    print("🔍 Debugging Pinecone Similarity Scores")
    print("=" * 50)
    
    search_service = SemanticSearchService()
    
    if not search_service.pinecone_index:
        print("❌ Pinecone not connected")
        return
    
    # Test queries with very low threshold to see all results
    test_queries = [
        "What is HuddleUp?",
        "How does pricing work?", 
        "collaboration features",
        "training delivery"
    ]
    
    for query in test_queries:
        print(f"\n📝 Query: '{query}'")
        print("-" * 30)
        
        try:
            # Get embedding
            query_embedding = search_service.embedding_service.get_embedding(query)
            
            # Search with very low threshold to see all results
            search_results = search_service.pinecone_index.query(
                vector=query_embedding,
                top_k=5,
                include_metadata=True,
                include_values=False
            )
            
            print(f"🎯 Pinecone returned {len(search_results.matches)} raw matches:")
            
            for i, match in enumerate(search_results.matches):
                score = match.score
                metadata = match.metadata or {}
                content = metadata.get('content', metadata.get('text', 'No content'))[:100]
                
                print(f"  {i+1}. Score: {score:.4f} | Content: {content}...")
                
                # Show metadata keys
                if metadata:
                    keys = list(metadata.keys())
                    print(f"     Metadata keys: {keys}")
            
            # Test with different thresholds
            print(f"\n🎚️ Testing different similarity thresholds:")
            for threshold in [0.3, 0.4, 0.5, 0.6, 0.7, 0.8]:
                filtered_matches = [m for m in search_results.matches if m.score >= threshold]
                print(f"   Threshold {threshold}: {len(filtered_matches)} matches")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print(f"\n" + "=" * 50)
    print("💡 Recommendations:")
    print("- If scores are below 0.7, lower the similarity threshold")
    print("- Check if metadata contains 'content' or 'text' fields")
    print("- Verify vector dimensions match (should be 1536)")

if __name__ == "__main__":
    debug_similarity_scores()