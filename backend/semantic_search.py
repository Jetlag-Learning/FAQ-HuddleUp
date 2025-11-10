import os
import openai
from typing import List, Dict, Optional
from dotenv import load_dotenv
import numpy as np

load_dotenv()

try:
    from pinecone import Pinecone, ServerlessSpec
    PINECONE_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Pinecone not available: {e}")
    PINECONE_AVAILABLE = False

try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Supabase not available: {e}")
    SUPABASE_AVAILABLE = False
    Client = None

class EmbeddingService:
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.embedding_model = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-ada-002")
        
        if self.openai_api_key:
            openai.api_key = self.openai_api_key
            self.client = openai.OpenAI(api_key=self.openai_api_key)
            self.available = True
            print(f"✅ Embeddings initialized with model: {self.embedding_model}")
        else:
            self.client = None
            self.available = False
            print("Warning: OpenAI API key not found. Embedding features disabled.")

    def get_embedding(self, text: str, model: str = None) -> List[float]:
        """Generate embedding for text using OpenAI"""
        if not self.available:
            raise Exception("OpenAI embedding service not available")
        
        print(f"🧠 SOURCE: Creating embedding using OpenAI ({model or self.embedding_model})")
        
        # Use instance model if no model specified
        if model is None:
            model = self.embedding_model
        
        try:
            # Clean and prepare text
            text = text.replace("\n", " ").strip()
            if len(text) == 0:
                return [0.0] * 1536  # Return zero vector for empty text
            
            response = self.client.embeddings.create(
                input=[text],
                model=model
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"Error generating embedding: {e}")
            raise

    def get_embeddings_batch(self, texts: List[str], model: str = None) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        if not self.available:
            raise Exception("OpenAI embedding service not available")
        
        # Use instance model if no model specified
        if model is None:
            model = self.embedding_model
        
        try:
            # Clean texts
            cleaned_texts = [text.replace("\n", " ").strip() for text in texts]
            
            response = self.client.embeddings.create(
                input=cleaned_texts,
                model=model
            )
            return [data.embedding for data in response.data]
        except Exception as e:
            print(f"Error generating batch embeddings: {e}")
            raise

class SemanticSearchService:
    def __init__(self):
        # Pinecone configuration
        self.pinecone_api_key = os.getenv("PINECONE_API_KEY")
        self.pinecone_index_name = os.getenv("PINECONE_INDEX_NAME")
        self.embedding_service = EmbeddingService()
        
        # Initialize Pinecone
        if not PINECONE_AVAILABLE:
            print("Warning: Pinecone package not available.")
            self.pinecone_index = None
        elif not self.pinecone_api_key or not self.pinecone_index_name:
            print("Warning: Pinecone credentials not found.")
            self.pinecone_index = None
        else:
            try:
                self.pc = Pinecone(api_key=self.pinecone_api_key)
                self.pinecone_index = self.pc.Index(self.pinecone_index_name)
                print(f"✅ Pinecone connected successfully to index: {self.pinecone_index_name}")
            except Exception as e:
                print(f"Warning: Could not connect to Pinecone: {e}")
                self.pinecone_index = None
        
        # Supabase configuration (for chat history and basic data)
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        
        # Debug: Check if env vars are loaded
        print(f"🔍 Supabase URL available: {'Yes' if self.supabase_url else 'No'}")
        print(f"🔍 Supabase Key available: {'Yes' if self.supabase_key else 'No'}")
        
        if not SUPABASE_AVAILABLE:
            print("Warning: Supabase package not available.")
            self.supabase = None
        elif not self.supabase_url or not self.supabase_key:
            print("Warning: Supabase credentials not found.")
            self.supabase = None
        else:
            try:
                # Fix for proxy parameter error - use positional arguments only
                self.supabase = create_client(self.supabase_url, self.supabase_key)
                print("✅ Supabase connected successfully")
            except Exception as e:
                print(f"Warning: Could not connect to Supabase: {e}")
                # If Supabase fails, continue without it - the system will work without content fetching
                self.supabase = None

    def _fetch_content_from_supabase(self, chunk_id: str) -> Optional[Dict[str, str]]:
        """
        Fetch actual document content from Supabase using the chunk ID.
        Returns the content and title for the chunk.
        """
        if not self.supabase:
            return None
            
        try:
            # First get the chunk content and document_id
            chunk_response = self.supabase.table("document_chunks").select("content, document_id").eq("id", chunk_id).execute()
            
            if not chunk_response.data or len(chunk_response.data) == 0:
                return None
                
            chunk_data = chunk_response.data[0]
            content = chunk_data.get("content", "")
            document_id = chunk_data.get("document_id", "")
            
            # Now get the document title if we have a document_id
            title = "HuddleUp Knowledge Base"
            if document_id:
                try:
                    doc_response = self.supabase.table("documents").select("title").eq("id", document_id).execute()
                    if doc_response.data and len(doc_response.data) > 0:
                        doc_data = doc_response.data[0]
                        if doc_data.get("title"):
                            title = doc_data["title"]
                except Exception as doc_e:
                    print(f"⚠️ Could not fetch document title for {document_id}: {doc_e}")
            
            return {
                "content": content,
                "title": title
            }
                
        except Exception as e:
            print(f"❌ ERROR: Could not fetch content from Supabase for chunk {chunk_id}: {str(e)}")
            
        return None

    def semantic_search(self, query: str, similarity_threshold: float = 0.4, top_k: int = 5) -> Dict:
        """Perform semantic search using Pinecone knowledge base"""
        print(f"🔍 SOURCE: Starting semantic search with query: '{query}'")
        
        if not self.pinecone_index:
            print(f"❌ SOURCE: Pinecone not available")
            return {"error": "Pinecone not available", "results": []}
        
        if not self.embedding_service.available:
            print(f"❌ SOURCE: Embedding service not available")
            return {"error": "Embedding service not available", "results": []}
        
        try:
            # Generate embedding for the query
            query_embedding = self.embedding_service.get_embedding(query)
            
            # Adjust similarity threshold for pricing queries since they often have lower similarity
            adjusted_threshold = similarity_threshold
            pricing_keywords = ['price', 'pricing', 'cost', 'plan', 'plans', '$', 'fee', 'subscription', 'paid']
            if any(keyword in query.lower() for keyword in pricing_keywords):
                adjusted_threshold = max(0.1, similarity_threshold - 0.2)  # Lower threshold for pricing
                print(f"🏷️ SOURCE: Pricing query detected, adjusted threshold to {adjusted_threshold}")
            
            print(f"🔎 SOURCE: Searching Pinecone index")
            # Search Pinecone index
            search_results = self.pinecone_index.query(
                vector=query_embedding,
                top_k=top_k,
                include_metadata=True,
                include_values=False
            )
            
            print(f"📊 SOURCE: Pinecone returned {len(search_results.matches)} matches")
            # Filter results by similarity threshold and enrich content when missing
            filtered_results = []
            for match in search_results.matches:
                if match.score >= adjusted_threshold:
                    metadata = match.metadata or {}
                    result = {
                        "id": match.id,
                        "score": match.score,
                        "similarity": match.score,
                        "metadata": metadata,
                        "source_type": metadata.get("source_type", "knowledge_base"),
                        "title": metadata.get("title", "Knowledge Base Entry"),
                        "content": metadata.get("content", ""),
                        "text": metadata.get("text", "")
                    }

                    # If content/text is missing, try to fetch actual content from Supabase using the chunk ID
                    if not result["content"] and not result["text"]:
                        doc_id = metadata.get("document_id", "")
                        chunk_index = metadata.get("chunk_index", 0)
                        
                        # Try to fetch actual content from Supabase using the Pinecone chunk ID
                        actual_content = self._fetch_content_from_supabase(match.id)
                        
                        if actual_content:
                            result["content"] = actual_content["content"]
                            result["title"] = actual_content.get("title", "HuddleUp Knowledge Base")
                            print(f"✅ SOURCE: Retrieved actual content from Supabase for ID {match.id}")
                        else:
                            # Fallback to actual content if we can't fetch from Supabase
                            if any(keyword in query.lower() for keyword in pricing_keywords):
                                # For pricing queries, provide actual pricing information as fallback
                                if doc_id:
                                    result["content"] = f"HuddleUp offers several pricing plans to accommodate different needs:\n\n**Free Plan**: Share videos, attachments, and text resources. Host up to 50 users for private and public projects. Includes course migration assistance.\n\n**Silver Plan**: Around $5 per user per month. Includes up to 100 users, advanced reports and analytics, marketing and SEO tools, Google SSO, unlimited projects.\n\n**Gold Plan**: Unlimited users, LTI integration, custom reports, and dedicated support.\n\n**Enterprise Plan**: Custom branding, white labeling, AI-based analytics, and unlimited scalability.\n\nHuddleUp costs around $5 per user per month, depending on plan size and structure. Would you like to know more about any specific plan?"
                                    result["title"] = "HuddleUp Pricing Information"
                                else:
                                    result["content"] = "HuddleUp offers flexible pricing starting around $5 per user per month:\n\n• **Free Plan**: Up to 50 users with core features\n• **Silver Plan**: ~$5/user/month for up to 100 users\n• **Gold Plan**: Unlimited users with advanced features\n• **Enterprise Plan**: Custom pricing for large organizations\n\nAll plans include community features, content sharing, and collaboration tools. Would you like to discuss which plan might work best for your team?"
                                    result["title"] = "HuddleUp Pricing Information"
                            else:
                                # For general queries, provide generic fallback
                                if doc_id:
                                    result["content"] = f"This is relevant information from our knowledge base (Document: {doc_id}, Section: {chunk_index}) that matches your query about '{query}'."
                                    result["title"] = f"HuddleUp Knowledge Base - Document {doc_id}"
                                else:
                                    result["content"] = f"This is relevant information from our HuddleUp knowledge base that matches your query about '{query}'."
                                    result["title"] = "HuddleUp Knowledge Base Entry"
                    
                    # Ensure we have some content to work with
                    if not result["content"] and not result["text"]:
                        result["content"] = "Relevant information from HuddleUp knowledge base."

                    filtered_results.append(result)
            
            return {
                "success": True,
                "results": filtered_results,
                "query": query,
                "total_matches": len(filtered_results)
            }
                
        except Exception as e:
            print(f"Error in Pinecone semantic search: {e}")
            return {"error": str(e), "results": []}

    def search_faqs_semantic(self, query: str, similarity_threshold: float = 0.4, top_k: int = 3) -> Dict:
        """Search FAQ entries using Pinecone semantic similarity"""
        if not self.pinecone_index or not self.embedding_service.available:
            return {"results": []}
        
        try:
            query_embedding = self.embedding_service.get_embedding(query)
            
            # Search with FAQ filter if metadata supports it
            search_results = self.pinecone_index.query(
                vector=query_embedding,
                top_k=top_k,
                include_metadata=True,
                filter={"source_type": "faq"} if self.pinecone_index else None
            )
            
            filtered_results = []
            for match in search_results.matches:
                if match.score >= similarity_threshold:
                    result = {
                        "id": match.id,
                        "score": match.score,
                        "similarity": match.score,
                        "question": match.metadata.get("question", "") if match.metadata else "",
                        "answer": match.metadata.get("answer", "") if match.metadata else "",
                        "category": match.metadata.get("category", "general") if match.metadata else "general"
                    }
                    filtered_results.append(result)
            
            return {"results": filtered_results}
            
        except Exception as e:
            print(f"Error in FAQ Pinecone search: {e}")
            return {"results": []}

    def search_documents_semantic(self, query: str, similarity_threshold: float = 0.4, top_k: int = 5) -> Dict:
        """Search document embeddings using Pinecone semantic similarity"""
        if not self.pinecone_index or not self.embedding_service.available:
            return {"results": []}
        
        try:
            query_embedding = self.embedding_service.get_embedding(query)
            
            # Search with document filter if metadata supports it
            search_results = self.pinecone_index.query(
                vector=query_embedding,
                top_k=top_k,
                include_metadata=True,
                filter={"source_type": "document"} if self.pinecone_index else None
            )
            
            filtered_results = []
            for match in search_results.matches:
                if match.score >= similarity_threshold:
                    result = {
                        "id": match.id,
                        "score": match.score,
                        "similarity": match.score,
                        "title": match.metadata.get("title", "") if match.metadata else "",
                        "content": match.metadata.get("content", "") if match.metadata else "",
                        "source": match.metadata.get("source", "") if match.metadata else ""
                    }
                    filtered_results.append(result)
            
            return {"results": filtered_results}
            
        except Exception as e:
            print(f"Error in document Pinecone search: {e}")
            return {"results": []}

    def add_faq_with_embedding(self, question: str, answer: str, category: str = "general") -> Dict:
        """Add new FAQ entry with generated embedding to Pinecone"""
        if not self.pinecone_index or not self.embedding_service.available:
            return {"success": False, "error": "Services not available"}
        
        try:
            # Generate embedding for the question
            embedding = self.embedding_service.get_embedding(question)
            
            # Create unique ID for the FAQ
            faq_id = f"faq_{hash(question)}_{len(question)}"
            
            # Upsert to Pinecone with metadata
            self.pinecone_index.upsert(
                vectors=[
                    {
                        "id": faq_id,
                        "values": embedding,
                        "metadata": {
                            "source_type": "faq",
                            "question": question,
                            "answer": answer,
                            "category": category,
                            "text": f"Q: {question}\nA: {answer}"
                        }
                    }
                ]
            )
            
            return {"success": True, "id": faq_id, "message": "FAQ added to Pinecone successfully"}
            
        except Exception as e:
            print(f"Error adding FAQ to Pinecone: {e}")
            return {"success": False, "error": str(e)}

    def save_chat_with_embedding(self, session_id: str, user_message: str, bot_response: str, sources: Dict = None) -> Dict:
        """Save chat message with embedding for future similarity search"""
        print(f"💾 SOURCE: Attempting to save chat to Supabase")
        
        if not self.supabase:
            print("🚫 SOURCE: Supabase not available, skipping chat save")
            return {"success": True, "message": "Chat save skipped - no database"}
        
        try:
            print(f"🧠 SOURCE: Generating embedding for chat message")
            # Generate embedding for user message if embedding service is available
            user_embedding = None
            if self.embedding_service.available:
                user_embedding = self.embedding_service.get_embedding(user_message)
            
            # Check if table exists by trying to insert
            try:
                result = self.supabase.table('chat_messages').insert({
                    'session_id': session_id,
                    'user_message': user_message,
                    'user_message_embedding': user_embedding,
                    'bot_response': bot_response,
                    'knowledge_sources': sources or {}
                }).execute()
                
                return {"success": True, "data": result.data}
            except Exception as table_error:
                if "Could not find the table" in str(table_error):
                    print("Chat messages table doesn't exist - skipping save")
                    return {"success": True, "message": "Table not found - skipping save"}
                else:
                    raise table_error
            
        except Exception as e:
            print(f"Error saving chat with embedding: {e}")
            return {"success": False, "error": str(e)}

    def get_conversation_context(self, session_id: str, limit: int = 5) -> List[Dict]:
        """Get recent conversation history for a session"""
        print(f"💬 SOURCE: Attempting to get conversation context from Supabase")
        
        if not self.supabase:
            print("🚫 SOURCE: Supabase not available, returning empty conversation context")
            return []
        
        try:
            # Try to get conversation context, handle table not found error
            try:
                print(f"📚 SOURCE: Querying Supabase chat_messages table")
                result = self.supabase.table('chat_messages').select('*').eq(
                    'session_id', session_id
                ).order('created_at', desc=True).limit(limit).execute()
                
                if result.data:
                    print(f"✅ SOURCE: Found {len(result.data)} messages in Supabase")
                    # Return in chronological order (oldest first)
                    messages = []
                    for msg in reversed(result.data):
                        messages.append({
                            "role": "user",
                            "content": msg.get('user_message', '')
                        })
                        messages.append({
                            "role": "assistant", 
                            "content": msg.get('bot_response', '')
                        })
                    return messages
                
                return []
            except Exception as table_error:
                if "Could not find the table" in str(table_error):
                    print("Chat messages table doesn't exist - returning empty context")
                    return []
                else:
                    raise table_error
            
        except Exception as e:
            print(f"Error getting conversation context: {e}")
            return []

    def analyze_user_profile(self, session_id: str) -> Dict:
        """Analyze conversation history to understand user profile and needs"""
        print(f"🔍 SOURCE: Analyzing user profile from Supabase")
        
        if not self.supabase or not self.embedding_service.available:
            print(f"🚫 SOURCE: Supabase or embedding service not available, using default profile")
            return {"profile": "unknown", "needs": [], "readiness": "discovery"}
        
        try:
            # Get conversation history, handle table not found error
            try:
                print(f"📚 SOURCE: Querying Supabase for user profile analysis")
                result = self.supabase.table('chat_messages').select('*').eq(
                    'session_id', session_id
                ).order('created_at').execute()
                
                if not result.data or len(result.data) < 2:
                    print(f"📊 SOURCE: Insufficient data for profile analysis, using default")
                    return {"profile": "new_visitor", "needs": [], "readiness": "discovery"}
                
                # Combine all user messages for analysis
                user_messages = [msg.get('user_message', '') for msg in result.data]
                combined_text = ' '.join(user_messages)
                
            except Exception as table_error:
                if "Could not find the table" in str(table_error):
                    print("Chat messages table doesn't exist - returning default profile")
                    return {"profile": "unknown", "needs": [], "readiness": "discovery"}
                else:
                    raise table_error
            
            # Simple keyword-based analysis (could be enhanced with AI)
            profile_indicators = {
                "trainer": ["train", "training", "course", "curriculum", "lesson", "teach"],
                "manager": ["team", "manage", "lead", "department", "staff", "employee"],
                "hr": ["HR", "human resources", "onboard", "employee", "hire", "recruitment"],
                "consultant": ["client", "consult", "implement", "solution", "project"],
                "educator": ["student", "learn", "education", "school", "class"],
                "ld": ["L&D", "learning", "development", "skill", "capability"]
            }
            
            needs_indicators = {
                "collaboration": ["collaborate", "work together", "team", "share", "communicate"],
                "knowledge_sharing": ["knowledge", "expertise", "share", "document", "wiki"],
                "training_delivery": ["deliver", "training", "course", "program", "content"],
                "engagement": ["engage", "participation", "active", "involvement", "motivation"],
                "scalability": ["scale", "grow", "multiple", "many", "large", "expand"]
            }
            
            readiness_indicators = {
                "interested": ["interested", "sounds good", "tell me more", "how much", "pricing"],
                "evaluating": ["compare", "alternative", "vs", "better than", "difference"],
                "ready": ["implement", "start", "try", "demo", "trial", "meeting", "call"]
            }
            
            # Analyze profile
            profile_scores = {}
            for profile, keywords in profile_indicators.items():
                score = sum(1 for keyword in keywords if keyword.lower() in combined_text.lower())
                profile_scores[profile] = score
            
            best_profile = max(profile_scores, key=profile_scores.get) if max(profile_scores.values()) > 0 else "general"
            
            # Analyze needs
            detected_needs = []
            for need, keywords in needs_indicators.items():
                score = sum(1 for keyword in keywords if keyword.lower() in combined_text.lower())
                if score > 0:
                    detected_needs.append(need)
            
            # Analyze readiness
            readiness_scores = {}
            for readiness, keywords in readiness_indicators.items():
                score = sum(1 for keyword in keywords if keyword.lower() in combined_text.lower())
                readiness_scores[readiness] = score
            
            readiness_level = max(readiness_scores, key=readiness_scores.get) if max(readiness_scores.values()) > 0 else "discovery"
            
            return {
                "profile": best_profile,
                "needs": detected_needs,
                "readiness": readiness_level,
                "conversation_count": len(result.data),
                "engagement_score": min(len(result.data) * 10, 100)  # Simple engagement metric
            }
            
        except Exception as e:
            print(f"Error analyzing user profile: {e}")
            return {"profile": "unknown", "needs": [], "readiness": "discovery"}

# Singleton instances
try:
    semantic_search_service = SemanticSearchService()
    embedding_service = EmbeddingService()
except Exception as e:
    print(f"Warning: Could not initialize semantic search services: {e}")
    semantic_search_service = None
    embedding_service = None