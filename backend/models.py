from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict, Any

class FAQRequest(BaseModel):
    question: str
    session_id: Optional[str] = None
    similarity_threshold: Optional[float] = 0.7
    conversation_context: Optional[List[Dict[str, str]]] = None

class FAQResponse(BaseModel):
    answer: str
    success: bool
    error: Optional[str] = None
    sources: Optional[List[Dict[str, Any]]] = None
    search_method: Optional[str] = None
    similarity_scores: Optional[List[float]] = None

class DiscoveryResponse(BaseModel):
    response: str
    actions: List[Dict[str, str]]
    success: bool = True
    error: Optional[str] = None
    sources: Optional[List[Dict[str, Any]]] = None

class ActionButton(BaseModel):
    type: str  # "calendar", "process_analysis", "research", "questions"
    label: str
    description: str

class FAQEntry(BaseModel):
    id: Optional[int] = None
    question: str
    answer: str
    category: str = "general"
    keywords: List[str] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    question_embedding: Optional[List[float]] = None

class ChatMessage(BaseModel):
    id: Optional[int] = None
    session_id: str
    user_message: str
    bot_response: str
    user_message_embedding: Optional[List[float]] = None
    knowledge_sources: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None

class SemanticSearchRequest(BaseModel):
    query: str
    similarity_threshold: Optional[float] = 0.7
    search_type: Optional[str] = "all"  # "faq", "documents", "all"
    max_results: Optional[int] = 5

class SemanticSearchResult(BaseModel):
    content: str
    source: str  # "faq", "document"
    similarity: float
    metadata: Dict[str, Any]

class EmbeddingRequest(BaseModel):
    text: str
    model: Optional[str] = "text-embedding-ada-002"

class EmbeddingResponse(BaseModel):
    embedding: List[float]
    model: str
    usage: Optional[Dict[str, Any]] = None

# Google Calendar Integration Models

class CalendarAuthRequest(BaseModel):
    """Request to initiate Google Calendar OAuth flow"""
    redirect_uri: Optional[str] = None

class CalendarAuthResponse(BaseModel):
    """Response with OAuth authorization URL"""
    auth_url: str
    state: Optional[str] = None

class CalendarOAuthCallback(BaseModel):
    """OAuth callback data"""
    code: str
    state: Optional[str] = None

class MeetingRequest(BaseModel):
    """Request to schedule a meeting"""
    user_email: str
    user_name: str
    requested_time: Optional[str] = None  # ISO format datetime
    message: Optional[str] = None
    duration_minutes: Optional[int] = 30
    timezone: Optional[str] = "America/New_York"

class MeetingTimeSlot(BaseModel):
    """Available meeting time slot"""
    datetime: str  # ISO format
    display: str   # Human-readable format
    day: str
    date: str
    time: str

class MeetingResponse(BaseModel):
    """Response after creating a meeting"""
    success: bool
    event_id: Optional[str] = None
    event_url: Optional[str] = None
    meet_link: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    error: Optional[str] = None

class AvailabilityRequest(BaseModel):
    """Request to check calendar availability"""
    start_date: str  # ISO format
    end_date: str    # ISO format
    duration_minutes: Optional[int] = 30
    timezone: Optional[str] = "America/New_York"

class AvailabilityResponse(BaseModel):
    """Calendar availability response"""
    success: bool
    available_slots: List[MeetingTimeSlot]
    busy_times: Optional[List[Dict[str, str]]] = None
    error: Optional[str] = None

class QuickMeetingSlotsResponse(BaseModel):
    """Quick meeting slots for the next few days"""
    success: bool
    slots: List[MeetingTimeSlot]
    days_ahead: int = 7
    error: Optional[str] = None