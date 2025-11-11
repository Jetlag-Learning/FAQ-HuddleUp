from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uuid
from datetime import datetime
import os
from dotenv import load_dotenv

# 🛑 Fix Render proxy issue - Remove proxy env vars before any client initialization
os.environ.pop("HTTP_PROXY", None)
os.environ.pop("HTTPS_PROXY", None)
os.environ.pop("ALL_PROXY", None)
print("🔧 Removed proxy environment variables to prevent client initialization errors")

# Import models first
from models import (
    FAQRequest, FAQResponse, DiscoveryResponse, ActionButton, 
    FAQEntry, ChatMessage, SemanticSearchRequest, SemanticSearchResult,
    EmbeddingRequest, EmbeddingResponse,
    CalendarAuthRequest, CalendarAuthResponse, CalendarOAuthCallback,
    MeetingRequest, MeetingResponse, AvailabilityRequest, AvailabilityResponse,
    QuickMeetingSlotsResponse
)

# Import services with error handling
try:
    from database import db_service
    DATABASE_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Database service not available: {e}")
    DATABASE_AVAILABLE = False
    db_service = None

try:
    from openai_service import openai_service
    OPENAI_AVAILABLE = True
except ImportError as e:
    print(f"Warning: OpenAI service not available: {e}")
    OPENAI_AVAILABLE = False
    openai_service = None

try:
    from semantic_search import semantic_search_service, embedding_service
    SEMANTIC_SEARCH_AVAILABLE = True
    print("✅ Semantic search services imported successfully")
except ImportError as e:
    print(f"Warning: Semantic search service not available: {e}")
    SEMANTIC_SEARCH_AVAILABLE = False
    semantic_search_service = None
    embedding_service = None

try:
    from google_calendar_service import google_calendar_service
    GOOGLE_CALENDAR_AVAILABLE = google_calendar_service is not None
    print(f"{'✅' if GOOGLE_CALENDAR_AVAILABLE else '⚠️'} Google Calendar service {'available' if GOOGLE_CALENDAR_AVAILABLE else 'not configured'}")
except ImportError as e:
    print(f"Warning: Google Calendar service not available: {e}")
    GOOGLE_CALENDAR_AVAILABLE = False
    google_calendar_service = None

load_dotenv()

app = FastAPI(
    title="HuddleUp FAQ API with Semantic Search",
    description="FAQ chatbot API with OpenAI integration, Supabase storage, and semantic search",
    version="2.0.0"
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", 
        "http://localhost:3001", 
        "http://127.0.0.1:3000", 
        "http://127.0.0.1:3001",
        "https://faq-huddle-up.vercel.app",
        "https://www.faq-huddle-up.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Generate a simple session ID for demo purposes
def generate_session_id():
    return str(uuid.uuid4())

# Fallback response function removed - using only OpenAI and Supabase responses

@app.get("/")
async def root():
    """Health check endpoint"""
    services_status = {
        "database": DATABASE_AVAILABLE and db_service is not None,
        "openai": OPENAI_AVAILABLE and openai_service is not None,
        "semantic_search": SEMANTIC_SEARCH_AVAILABLE and semantic_search_service is not None,
        "embeddings": SEMANTIC_SEARCH_AVAILABLE and embedding_service is not None,
        "google_calendar": GOOGLE_CALENDAR_AVAILABLE and google_calendar_service is not None
    }
    
    return {
        "message": "HuddleUp FAQ API with Semantic Search",
        "version": "2.0.0",
        "services": services_status,
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/faq/ask")
async def ask_faq(request: FAQRequest):
    """
    Enhanced FAQ endpoint with semantic search capabilities
    Uses embeddings for more accurate question matching
    """
    try:
        print(f"\n🚀 API ENDPOINT: /api/faq/ask")
        print(f"📝 REQUEST: {request.question}")
        
        response = ""
        sources = []
        search_method = "fallback"
        
        # Try semantic search first (most accurate)
        if SEMANTIC_SEARCH_AVAILABLE and semantic_search_service:
            try:
                print("🔍 FLOW: Using semantic search for question matching...")
                semantic_results = semantic_search_service.semantic_search(
                    request.question, 
                    similarity_threshold=0.6  # Lower threshold since we're using as context
                )
                
                print(f"📊 RESULTS: Semantic search returned {len(semantic_results.get('results', []))} results")
                if semantic_results.get("success") and semantic_results.get("results"):
                    print(f"✅ Found {len(semantic_results['results'])} semantic matches")
                    
                    # Check if we have usable content from Pinecone
                    best_match = semantic_results["results"][0]
                    has_content = False
                    
                    # Try to extract content from various fields
                    content_sources = [
                        best_match.get("content"),
                        best_match.get("text"), 
                        best_match.get("answer"),
                        best_match.get("metadata", {}).get("content"),
                        best_match.get("metadata", {}).get("text"),
                        best_match.get("metadata", {}).get("answer")
                    ]
                    
                    response_content = None
                    for content in content_sources:
                        if content and len(str(content).strip()) > 10:
                            response_content = str(content).strip()
                            has_content = True
                            break
                    
                    if has_content and response_content:
                        # We have good content from Pinecone
                        response = response_content
                        sources.append({
                            "type": "knowledge_base_semantic",
                            "similarity": best_match.get("similarity"),
                            "id": best_match.get("id"),
                            "source": "pinecone_content"
                        })
                        search_method = "semantic_content"
                        
                        # Enhance with AI if available
                        if OPENAI_AVAILABLE and openai_service:
                            try:
                                print("🤖 Enhancing Pinecone result with AI...")
                                ai_enhanced = openai_service.process_question(request.question, response)
                                if ai_enhanced and ai_enhanced != response:
                                    response = ai_enhanced
                                    search_method = "semantic_content_ai_enhanced"
                            except Exception as ai_error:
                                print(f"AI enhancement failed: {ai_error}")
                    
                    else:
                        # Pinecone found relevant matches but no readable content
                        # Use this as a signal to generate a more targeted OpenAI response
                        print("📊 Pinecone found relevant matches, using for context...")
                        if OPENAI_AVAILABLE and openai_service:
                            context_prompt = f"""The user asked: "{request.question}"

Our semantic search found {len(semantic_results['results'])} relevant matches in the knowledge base with similarities: {[r.get('similarity', 0) for r in semantic_results['results'][:3]]}.

This suggests the question is about topics we have information on. Please provide a helpful, specific answer about HuddleUp based on this context."""
                            
                            try:
                                ai_response = openai_service.generate_direct_response(request.question)
                                if ai_response:
                                    response = ai_response
                                    search_method = "semantic_guided_ai"
                                    sources.append({
                                        "type": "semantic_guided",
                                        "matches_found": len(semantic_results['results']),
                                        "avg_similarity": sum(r.get('similarity', 0) for r in semantic_results['results'][:3]) / min(3, len(semantic_results['results']))
                                    })
                            except Exception as ai_error:
                                print(f"Context-guided AI response failed: {ai_error}")
                
                else:
                    print("No semantic search results found")
                    
            except Exception as semantic_error:
                print(f"Semantic search error: {semantic_error}")
        
        # Fallback to traditional database search if semantic search didn't work
        if not response and DATABASE_AVAILABLE and db_service:
            try:
                print("📊 Trying traditional database search...")
                kb_results = db_service.search_knowledge_base(request.question)
                
                if kb_results.get('faq_entries'):
                    faq = kb_results['faq_entries'][0]
                    response = faq.get('answer', '')
                    sources.append({
                        "type": "faq_traditional",
                        "question": faq.get('question'),
                        "category": faq.get('category')
                    })
                    search_method = "traditional_faq"
                elif kb_results.get('documents'):
                    doc = kb_results['documents'][0]
                    response = doc.get('content', '')
                    sources.append({
                        "type": "document_traditional",
                        "title": doc.get('title')
                    })
                    search_method = "traditional_document"
                    
            except Exception as db_error:
                print(f"Database search error: {db_error}")
        
        # Generate OpenAI response if no database results found
        if not response:
            if OPENAI_AVAILABLE and openai_service:
                try:
                    print("🤖 No database matches found, generating OpenAI response...")
                    ai_response = openai_service.generate_direct_response(request.question)
                    if ai_response:
                        response = ai_response
                        search_method = "openai_direct"
                        sources.append({
                            "type": "openai_generated",
                            "method": "direct_generation"
                        })
                    else:
                        response = "I apologize, but I couldn't find relevant information in our knowledge base and couldn't generate a suitable response. Could you please rephrase your question or contact our support team for assistance?"
                        search_method = "no_response_available"
                except Exception as ai_error:
                    print(f"OpenAI direct generation failed: {ai_error}")
                    response = "I apologize, but I'm currently unable to process your question due to a technical issue. Please try again later or contact our support team."
                    search_method = "service_error"
            else:
                response = "I apologize, but I couldn't find relevant information in our knowledge base. Please try rephrasing your question or contact our support team for assistance."
                search_method = "no_services_available"
        
        # Log search method server-side for debugging; do not append to user-visible response
        try:
            print(f"Search method: {search_method}")
        except Exception:
            pass
        
        # Save chat interaction if possible (for future learning)
        if SEMANTIC_SEARCH_AVAILABLE and semantic_search_service:
            try:
                session_id = generate_session_id()
                semantic_search_service.save_chat_with_embedding(
                    session_id, 
                    request.question, 
                    response, 
                    {"sources": sources, "method": search_method}
                )
            except Exception as save_error:
                print(f"Could not save chat interaction: {save_error}")
        
        return FAQResponse(
            answer=response,
            success=True,
            sources=sources,
            search_method=search_method
        )
        
    except Exception as e:
        print(f"Error in ask_faq: {e}")
        return FAQResponse(
            answer="I apologize, but I encountered an error processing your question. Please try again.",
            success=False,
            error=str(e)
        )

@app.post("/api/faq/semantic-search")
async def semantic_search_endpoint(request: FAQRequest):
    """
    Direct semantic search endpoint for testing embeddings
    """
    try:
        if not SEMANTIC_SEARCH_AVAILABLE or not semantic_search_service:
            raise HTTPException(
                status_code=503, 
                detail="Semantic search service not available"
            )
        
        results = semantic_search_service.semantic_search(
            request.question,
            similarity_threshold=0.6  # Lower threshold for testing
        )
        
        return {
            "query": request.question,
            "results": results,
            "service_available": True
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/faq/add-with-embedding")
async def add_faq_with_embedding(entry: FAQEntry):
    """
    Add a new FAQ entry with automatic embedding generation
    """
    try:
        if not SEMANTIC_SEARCH_AVAILABLE or not semantic_search_service:
            raise HTTPException(
                status_code=503,
                detail="Semantic search service not available" 
            )
        
        result = semantic_search_service.add_faq_with_embedding(
            entry.question,
            entry.answer,
            entry.category or "general"
        )
        
        if result.get("success"):
            return {
                "message": "FAQ entry created with embedding",
                "data": result.get("data")
            }
        else:
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to create FAQ entry")
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/faq/discovery")
async def discovery_conversation(request: FAQRequest):
    """
    Enhanced discovery endpoint that provides action buttons and guided conversations
    """
    try:
        print(f"\n🚀 API ENDPOINT: /api/faq/discovery")
        print(f"📝 REQUEST: {request.question}")
        print(f"🆔 SESSION: {request.session_id}")
        
        if not OPENAI_AVAILABLE or not openai_service:
            print(f"❌ SERVICE: OpenAI not available")
            raise HTTPException(
                status_code=503,
                detail="Discovery service not available"
            )
        
        session_id = request.session_id or generate_session_id()
        
        # Get conversation context and user profile
        conversation_context = None
        user_profile = None
        
        if SEMANTIC_SEARCH_AVAILABLE and semantic_search_service:
            print(f"🔄 FLOW: Getting conversation context and user profile")
            # Get conversation history
            conversation_context = semantic_search_service.get_conversation_context(session_id)
            
            # Analyze user profile based on conversation history
            user_profile = semantic_search_service.analyze_user_profile(session_id)
            
            print(f"👤 USER PROFILE: {user_profile}")
        
        print(f"🎯 FLOW: Generating discovery response")
        # Generate discovery response with actions
        discovery_result = openai_service.generate_discovery_response_with_actions(
            request.question,
            conversation_context,
            user_profile
        )
        
        # Save conversation
        if SEMANTIC_SEARCH_AVAILABLE and semantic_search_service:
            print(f"💾 FLOW: Saving conversation to database")
            try:
                semantic_search_service.save_chat_with_embedding(
                    session_id,
                    request.question,
                    discovery_result["response"],
                    {
                        "actions": discovery_result["actions"], 
                        "type": "discovery",
                        "user_profile": user_profile
                    }
                )
                print(f"✅ SAVE: Conversation saved successfully")
            except Exception as save_error:
                print(f"❌ SAVE ERROR: {save_error}")
        
        print(f"🎉 RESPONSE: Returning discovery result with {len(discovery_result.get('actions', []))} actions")
        return DiscoveryResponse(
            response=discovery_result["response"],
            actions=discovery_result["actions"]
        )
        
    except Exception as e:
        print(f"Error in discovery conversation: {e}")
        return DiscoveryResponse(
            response="I'd love to help you learn more about HuddleUp! What specific questions do you have?",
            actions=[
                {"type": "questions", "label": "Ask more questions", "description": "Continue exploring HuddleUp"}
            ],
            success=False,
            error=str(e)
        )

# Legacy endpoints for backward compatibility
@app.get("/api/faq/entries")
async def get_all_faqs():
    """Get all FAQ entries"""
    try:
        if db_service:
            entries = db_service.get_faq_entries()
            return {"faqs": entries, "count": len(entries)}
        else:
            sample_faqs = [
                {
                    "id": 1,
                    "question": "How much does HuddleUp cost?",
                    "answer": "HuddleUp offers flexible pricing starting at $29/month for up to 100 members.",
                    "category": "pricing"
                },
                {
                    "id": 2,
                    "question": "Is HuddleUp an LMS or Community platform?",
                    "answer": "HuddleUp is primarily a community platform with learning management features.",
                    "category": "platform"
                }
            ]
            return {"faqs": sample_faqs, "count": len(sample_faqs), "demo_mode": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/faq/entries")
async def create_faq_entry(entry: FAQEntry):
    """Create a new FAQ entry (legacy endpoint)"""
    try:
        if db_service:
            result = db_service.create_faq_entry(
                question=entry.question,
                answer=entry.answer,
                category=entry.category,
                keywords=entry.keywords
            )
            
            if result:
                return {"message": "FAQ entry created successfully", "data": result}
            else:
                raise HTTPException(status_code=500, detail="Failed to create FAQ entry")
        else:
            raise HTTPException(status_code=503, detail="Database service not available")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/faq/search")
async def search_faqs(q: str):
    """Search FAQ entries by query (legacy endpoint)"""
    try:
        if not q:
            raise HTTPException(status_code=400, detail="Search query is required")
            
        if db_service:
            results = db_service.search_faq_entries(q)
            return {"results": results, "count": len(results)}
        else:
            return {"results": [], "count": 0, "demo_mode": True}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/knowledge-base/search")
async def search_knowledge_base(q: str):
    """Search entire knowledge base (FAQs, documents, and chunks)"""
    try:
        if not q:
            raise HTTPException(status_code=400, detail="Search query is required")
            
        # Try semantic search first if available
        if SEMANTIC_SEARCH_AVAILABLE and semantic_search_service:
            semantic_results = semantic_search_service.semantic_search(q, similarity_threshold=0.6)
            if semantic_results.get("success"):
                return {
                    "results": semantic_results,
                    "search_type": "semantic",
                    "total_count": len(semantic_results.get("results", []))
                }
        
        # Fallback to traditional search
        if db_service:
            results = db_service.search_knowledge_base(q)
            total_count = (
                len(results.get('faq_entries', [])) +
                len(results.get('documents', [])) +
                len(results.get('document_chunks', []))
            )
            return {
                "results": results,
                "search_type": "traditional",
                "total_count": total_count,
                "breakdown": {
                    "faq_entries": len(results.get('faq_entries', [])),
                    "documents": len(results.get('documents', [])),
                    "document_chunks": len(results.get('document_chunks', []))
                }
            }
        else:
            return {
                "results": {"faq_entries": [], "documents": [], "document_chunks": []},
                "total_count": 0,
                "demo_mode": True
            }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/documents")
async def get_documents():
    """Get all documents from knowledge base"""
    try:
        if db_service:
            documents = db_service.get_documents()
            return {"documents": documents, "count": len(documents)}
        else:
            return {"documents": [], "count": 0, "demo_mode": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Google Calendar Integration Endpoints

@app.get("/api/calendar/auth", response_model=CalendarAuthResponse)
async def get_calendar_auth_url():
    """Get Google Calendar OAuth2 authorization URL"""
    print("🗓️ SOURCE: Calendar auth URL requested")
    
    if not GOOGLE_CALENDAR_AVAILABLE or not google_calendar_service:
        print("❌ SOURCE: Google Calendar service not available")
        raise HTTPException(
            status_code=503, 
            detail="Google Calendar integration not configured. Please set up Google OAuth2 credentials."
        )
    
    try:
        auth_url = google_calendar_service.get_authorization_url()
        print(f"✅ SOURCE: Generated calendar auth URL")
        return CalendarAuthResponse(auth_url=auth_url)
    except Exception as e:
        print(f"❌ SOURCE: Failed to generate auth URL: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate authorization URL: {str(e)}")

@app.post("/api/calendar/callback")
async def handle_calendar_callback(callback_data: CalendarOAuthCallback):
    """Handle Google Calendar OAuth2 callback"""
    print(f"🗓️ SOURCE: Calendar OAuth callback received")
    
    if not GOOGLE_CALENDAR_AVAILABLE or not google_calendar_service:
        print("❌ SOURCE: Google Calendar service not available")
        raise HTTPException(status_code=503, detail="Google Calendar integration not configured")
    
    try:
        result = google_calendar_service.handle_oauth_callback(callback_data.code)
        print(f"{'✅' if result['success'] else '❌'} SOURCE: OAuth callback {'successful' if result['success'] else 'failed'}")
        
        if result["success"]:
            return {
                "success": True,
                "message": result["message"],
                "calendar_connected": True
            }
        else:
            raise HTTPException(status_code=400, detail=result["error"])
    except Exception as e:
        print(f"❌ SOURCE: OAuth callback error: {e}")
        raise HTTPException(status_code=500, detail=f"OAuth callback failed: {str(e)}")

@app.get("/api/calendar/status")
async def get_calendar_status():
    """Check Google Calendar connection status"""
    print("🗓️ SOURCE: Calendar status check")
    
    if not GOOGLE_CALENDAR_AVAILABLE or not google_calendar_service:
        return {
            "connected": False,
            "message": "Google Calendar integration not configured",
            "auth_url": None
        }
    
    is_connected = google_calendar_service.is_authenticated()
    print(f"📊 SOURCE: Calendar connected: {is_connected}")
    
    response = {
        "connected": is_connected,
        "message": "Connected to Google Calendar" if is_connected else "Not connected to Google Calendar"
    }
    
    if not is_connected:
        try:
            response["auth_url"] = google_calendar_service.get_authorization_url()
        except:
            response["auth_url"] = None
    
    return response

@app.post("/api/calendar/meeting", response_model=MeetingResponse)
async def create_meeting(meeting_request: MeetingRequest):
    """Create a calendar meeting with Google Meet link"""
    print(f"🗓️ SOURCE: Meeting creation requested for {meeting_request.user_email}")
    
    if not GOOGLE_CALENDAR_AVAILABLE or not google_calendar_service:
        print("❌ SOURCE: Google Calendar service not available")
        return MeetingResponse(
            success=False,
            error="Google Calendar integration not configured. Please contact support to set up a meeting."
        )
    
    if not google_calendar_service.is_authenticated():
        print("❌ SOURCE: Google Calendar not authenticated")
        return MeetingResponse(
            success=False,
            error="Google Calendar not connected. Please connect calendar first."
        )
    
    try:
        result = google_calendar_service.create_meeting_from_request(
            user_email=meeting_request.user_email,
            user_name=meeting_request.user_name,
            requested_time=meeting_request.requested_time,
            message=meeting_request.message
        )
        
        print(f"{'✅' if result['success'] else '❌'} SOURCE: Meeting creation {'successful' if result['success'] else 'failed'}")
        
        return MeetingResponse(**result)
        
    except Exception as e:
        print(f"❌ SOURCE: Meeting creation error: {e}")
        return MeetingResponse(
            success=False,
            error=f"Failed to create meeting: {str(e)}"
        )

@app.get("/api/calendar/availability", response_model=AvailabilityResponse)
async def check_availability(start_date: str, end_date: str, duration_minutes: int = 30):
    """Check calendar availability for meeting scheduling"""
    print(f"🗓️ SOURCE: Availability check requested: {start_date} to {end_date}")
    
    if not GOOGLE_CALENDAR_AVAILABLE or not google_calendar_service:
        print("❌ SOURCE: Google Calendar service not available")
        return AvailabilityResponse(
            success=False,
            available_slots=[],
            error="Google Calendar integration not configured"
        )
    
    if not google_calendar_service.is_authenticated():
        print("❌ SOURCE: Google Calendar not authenticated")
        return AvailabilityResponse(
            success=False,
            available_slots=[],
            error="Google Calendar not connected"
        )
    
    try:
        from datetime import datetime
        start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        
        result = google_calendar_service.get_availability(
            start_date=start_dt,
            end_date=end_dt,
            min_duration_minutes=duration_minutes
        )
        
        print(f"{'✅' if result['success'] else '❌'} SOURCE: Availability check {'successful' if result['success'] else 'failed'}")
        
        # Convert to proper format
        if result["success"]:
            from models import MeetingTimeSlot
            slots = []
            for slot in result["available_slots"]:
                slot_dt = datetime.fromisoformat(slot["start"])
                slots.append(MeetingTimeSlot(
                    datetime=slot["start"],
                    display=slot_dt.strftime("%A, %B %d at %I:%M %p"),
                    day=slot_dt.strftime("%A"),
                    date=slot_dt.strftime("%B %d"),
                    time=slot_dt.strftime("%I:%M %p")
                ))
            
            return AvailabilityResponse(
                success=True,
                available_slots=slots,
                busy_times=result.get("busy_times", [])
            )
        else:
            return AvailabilityResponse(
                success=False,
                available_slots=[],
                error=result["error"]
            )
        
    except Exception as e:
        print(f"❌ SOURCE: Availability check error: {e}")
        return AvailabilityResponse(
            success=False,
            available_slots=[],
            error=f"Failed to check availability: {str(e)}"
        )

@app.get("/api/calendar/quick-slots", response_model=QuickMeetingSlotsResponse)
async def get_quick_meeting_slots(days_ahead: int = 7):
    """Get suggested meeting slots for the next few days"""
    print(f"🗓️ SOURCE: Quick meeting slots requested ({days_ahead} days ahead)")
    
    if not GOOGLE_CALENDAR_AVAILABLE or not google_calendar_service:
        print("❌ SOURCE: Google Calendar service not available")
        return QuickMeetingSlotsResponse(
            success=False,
            slots=[],
            error="Google Calendar integration not configured"
        )
    
    try:
        slots = google_calendar_service.get_quick_meeting_slots(days_ahead=days_ahead)
        
        from models import MeetingTimeSlot
        slot_objects = []
        for slot in slots:
            slot_objects.append(MeetingTimeSlot(**slot))
        
        print(f"✅ SOURCE: Generated {len(slot_objects)} quick meeting slots")
        
        return QuickMeetingSlotsResponse(
            success=True,
            slots=slot_objects,
            days_ahead=days_ahead
        )
        
    except Exception as e:
        print(f"❌ SOURCE: Quick slots error: {e}")
        return QuickMeetingSlotsResponse(
            success=False,
            slots=[],
            error=f"Failed to get meeting slots: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("HOST", "localhost")
    port = int(os.getenv("PORT", 8000))
    debug = os.getenv("DEBUG", "True").lower() == "true"
    
    print("🚀 Starting HuddleUp FAQ API with Semantic Search...")
    print(f"📊 Database available: {DATABASE_AVAILABLE}")
    print(f"🤖 OpenAI available: {OPENAI_AVAILABLE}")
    print(f"🔍 Semantic search available: {SEMANTIC_SEARCH_AVAILABLE}")
    print(f"🗓️ Google Calendar available: {GOOGLE_CALENDAR_AVAILABLE}")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=debug
    )