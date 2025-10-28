from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uuid
from datetime import datetime
import os
from dotenv import load_dotenv

from models import FAQRequest, FAQResponse, FAQEntry
from database import db_service
from openai_service import openai_service

load_dotenv()

app = FastAPI(
    title="HuddleUp FAQ API",
    description="FAQ chatbot API with OpenAI integration and Supabase storage",
    version="1.0.0"
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", 
        "http://localhost:3001", 
        "http://127.0.0.1:3000", 
        "http://127.0.0.1:3001"
    ],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Generate a simple session ID for demo purposes
def generate_session_id():
    return str(uuid.uuid4())

def get_fallback_response(message: str) -> str:
    """Fallback responses when backend services are not configured"""
    lowerMessage = message.lower()
    
    if any(word in lowerMessage for word in ['cost', 'price', 'pricing', 'money', 'fee']):
        return """HuddleUp offers flexible pricing plans:
      
• **Starter Plan**: $29/month for up to 100 members
• **Professional Plan**: $79/month for up to 500 members  
• **Enterprise Plan**: Custom pricing for larger organizations

All plans include core features like community management, content sharing, and basic analytics. Higher tiers include advanced integrations and priority support.

Would you like to know more about any specific plan?"""
    
    if any(word in lowerMessage for word in ['lms', 'community', 'platform', 'type']):
        return """HuddleUp is primarily a **community platform** with learning management features, rather than a traditional LMS.

Key differences:
• **Community-first**: Built around member engagement and collaboration
• **Social Learning**: Emphasizes peer-to-peer knowledge sharing
• **Flexible Content**: Supports various content types beyond courses
• **Member-driven**: Communities can be self-organizing and member-led

Think of it as a blend of community platform and learning environment, perfect for organizations wanting to foster both connection and knowledge sharing."""
    
    if any(word in lowerMessage for word in ['different', 'current', 'process', 'improve', 'workflow']):
        return """HuddleUp can enhance your current processes in several ways:

🔄 **Process Integration**: Rather than replacing what works, HuddleUp adds collaboration layers
📚 **Knowledge Capture**: Turn tribal knowledge into searchable, shareable resources  
🤝 **Cross-team Collaboration**: Break down silos between departments
📈 **Engagement Analytics**: See what content resonates and drives participation
⚡ **Automation**: Reduce manual tasks with workflow automation

To give you more specific recommendations, could you tell me about your current processes? For example:
- How do you currently share knowledge?
- What tools do you use for team collaboration?
- What challenges are you facing with your current setup?

💡 I notice you're asking about processes! I'd love to help you analyze how HuddleUp could specifically improve your current setup."""
    
    if any(word in lowerMessage for word in ['getting started', 'start', 'implementation', 'setup', 'demo']):
        return """Getting started with HuddleUp is straightforward! Here's the typical process:

**🎯 Step 1: Discovery Call (30 minutes)**
- Understand your current challenges and goals
- Explore how HuddleUp fits your specific use case
- Identify key stakeholders and success metrics

**🚀 Step 2: Free Trial Setup (Same day)**
- 14-day full-featured trial
- We help configure your initial community structure
- Import existing content and member lists if needed

**👥 Step 3: Pilot Program (2-4 weeks)**
- Start with a small group or specific use case
- Gather feedback and refine the setup
- Identify champions and early adopters

**📈 Step 4: Gradual Rollout**
- Expand to additional teams or member groups
- Provide training and support materials
- Monitor engagement and iterate

Ready to start? Just let me know what questions you have!"""
    
    # Check for integration/support related questions
    if any(word in lowerMessage for word in ['integration', 'api', 'connect', 'tool', 'slack', 'teams']):
        return """HuddleUp offers extensive integration capabilities:

**🔗 Popular Integrations:**
- **Slack & Microsoft Teams**: Sync discussions and notifications
- **Zoom & Calendar Apps**: Seamlessly schedule community events  
- **Google Workspace & Office 365**: Share documents and collaborate
- **CRM Systems**: Connect member data and engagement metrics
- **SSO Providers**: SAML, OAuth, Active Directory support

**📊 Developer Features:**
- **REST API**: Full programmatic access to all platform features
- **Webhooks**: Real-time event notifications
- **Zapier**: 5,000+ no-code app connections

Our technical team provides integration support and can help with custom implementations."""

    if any(word in lowerMessage for word in ['support', 'help', 'training', 'onboarding']):
        return """HuddleUp provides comprehensive support to ensure your success:

**📞 Support Channels:**
- **Email Support**: All plans with guaranteed response times
- **Live Chat**: Available for Professional+ plans
- **Phone Support**: Enterprise customers get dedicated phone lines

**👤 Success Team:**
- **Onboarding Specialist**: Guides initial setup and best practices
- **Account Manager**: Regular check-ins for optimization
- **Training Sessions**: Weekly group training for administrators

**📚 Resources:**
- **Help Center**: Extensive documentation and tutorials
- **Best Practices Guide**: Proven strategies from successful communities
- **Video Library**: On-demand training for all features

We're committed to your success from day one!"""
    
    return """I'm here to help with questions about HuddleUp! I can tell you about:

• **Pricing and plans** - Flexible options for all organization sizes
• **Platform capabilities** - Community + learning management features
• **Implementation** - Getting started and onboarding process
• **Integrations** - Connecting with your existing tools
• **Use cases** - How organizations use HuddleUp successfully
• **Process improvement** - Enhancing your current workflows

What would you like to know more about?

*🎯 Demo Mode: This is running with sample responses. For full AI-powered responses with your specific data, configure your OpenAI API key and Supabase database.*"""

@app.get("/")
async def root():
    return {"message": "HuddleUp FAQ API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now()}

@app.post("/api/faq/ask", response_model=FAQResponse)
async def ask_faq(request: FAQRequest):
    """
    Main FAQ endpoint that processes questions and returns AI-generated responses
    """
    try:
        if not request.question or len(request.question.strip()) == 0:
            raise HTTPException(status_code=400, detail="Question cannot be empty")
        
        # Use Supabase for knowledge search but fallback responses to avoid OpenAI costs
        response = None
        
        # Try to search Supabase first for relevant content
        try:
            if db_service:
                print("Searching Supabase knowledge base...")
                kb_results = db_service.search_knowledge_base(request.question)
                
                # Check if we found relevant FAQ entries
                faq_entries = kb_results.get('faq_entries', [])
                if faq_entries:
                    # Use the first matching FAQ entry
                    faq = faq_entries[0]
                    response = faq.get('answer', '')
                    response += f"\n\n*📚 Source: FAQ Database*"
                    
                    # Save the interaction
                    session_id = generate_session_id()
                    db_service.save_chat_message(
                        session_id=session_id,
                        user_message=request.question,
                        bot_response=response
                    )
                    print(f"Found matching FAQ entry: {faq.get('question', '')}")
                
                else:
                    print("No matching FAQ entries found in knowledge base")
                    
        except Exception as db_error:
            print(f"Database error: {db_error}")
        
        # If no response from database, use fallback
        if not response:
            print("Using fallback response system")
            response = get_fallback_response(request.question)
            response += "\n\n*🎯 Enhanced Demo Mode: Using intelligent fallback responses*"
        
        return FAQResponse(answer=response, success=True)
        
    except Exception as e:
        print(f"Error in ask_faq: {e}")
        return FAQResponse(
            answer="I apologize, but I encountered an error processing your question. Please try again.",
            success=False,
            error=str(e)
        )

@app.get("/api/faq/entries")
async def get_all_faqs():
    """Get all FAQ entries"""
    try:
        if db_service:
            entries = db_service.get_faq_entries()
            return {"faqs": entries, "count": len(entries)}
        else:
            # Return sample FAQ entries for demo mode
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
    """Create a new FAQ entry"""
    try:
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
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/faq/search")
async def search_faqs(q: str):
    """Search FAQ entries by query"""
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
            
        if db_service:
            results = db_service.search_knowledge_base(q)
            total_count = (
                len(results.get('faq_entries', [])) +
                len(results.get('documents', [])) +
                len(results.get('document_chunks', []))
            )
            return {
                "results": results,
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

if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("HOST", "localhost")
    port = int(os.getenv("PORT", 8000))
    debug = os.getenv("DEBUG", "True").lower() == "true"
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=debug
    )