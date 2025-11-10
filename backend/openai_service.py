import os
import openai
from typing import List, Dict, Optional
from dotenv import load_dotenv
from semantic_search import semantic_search_service

load_dotenv()

class OpenAIService:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        self.model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
        self.embedding_model = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-ada-002")
        
        if not api_key:
            print("Warning: OpenAI API key not found. AI features will be disabled.")
            self.client = None
        else:
            try:
                openai.api_key = api_key
                self.client = openai.OpenAI(api_key=api_key)
                print(f"✅ OpenAI initialized with model: {self.model}")
            except Exception as e:
                print(f"Warning: Could not initialize OpenAI client: {e}")
                self.client = None
    
    def generate_faq_response(self, question: str, knowledge_base_results: Dict = None) -> str:
        """
        Generate a discovery-focused response using Pinecone vector search results
        """
        if not self.client:
            raise Exception("OpenAI service not available")
        
        try:
            # Get relevant content from Pinecone
            search_results = semantic_search_service.semantic_search(question, similarity_threshold=0.3)
            
            # Build context from search results
            context = ""
            if search_results.get("success") and search_results.get("results"):
                context = "Relevant Knowledge Base Information:\n\n"
                for result in search_results["results"][:3]:  # Use top 3 most relevant results
                    source_type = result.get('source_type', 'Unknown')
                    title = result.get('title', '')
                    metadata = result.get('metadata', {})
                    
                    # Get content from various possible fields
                    content = (result.get('content') or 
                             result.get('text') or 
                             metadata.get('content') or 
                             metadata.get('answer') or 
                             '')
                    
                    if content:
                        context += f"Source: {source_type} - {title}\n"
                        context += f"Content: {content}\n\n"
            
            system_prompt = f"""You are the HuddleUp AI Assistant conducting discovery conversations about learning collaboration.

                    Your goal is to help visitors understand how HuddleUp addresses their specific needs through guided discovery.

                    KNOWLEDGE BASE CONTEXT:
                    {context}

                    DISCOVERY APPROACH:
                    1. Use the knowledge base information to provide accurate, specific answers
                    2. Ask follow-up questions to understand their context (role, challenges, current processes)
                    3. Connect their situation to relevant HuddleUp benefits
                    4. When appropriate, suggest next steps for deeper engagement

                    RESPONSE STYLE:
                    - Use the knowledge base information as your foundation
                    - Be conversational and discovery-focused, not just informational
                    - Ask ONE thoughtful follow-up question to learn more about their needs
                    - Keep responses concise (2-3 short paragraphs)
                    - Include relevant emojis and formatting for readability

                    NEXT STEPS TO OFFER (when the timing feels right):
                    - "Find a time to meet with Derek, our learning collaboration expert"
                    - "See how your current training processes could work in HuddleUp"
                    - "Receive research on the specific problems HuddleUp solves"
                    - "Ask more questions about features that interest you"

                    Remember: You're not just answering questions - you're building understanding and guiding discovery."""

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question}
            ]
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=400,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"Error generating OpenAI response: {e}")
            return "I apologize, but I'm having trouble processing your question right now. Please try again or contact our support team for assistance."

    def generate_direct_response(self, question: str) -> str:
        """
        Generate a direct response using Pinecone semantic search and OpenAI
        Uses vector search to find relevant content and generate contextual responses
        """
        if not self.client:
            raise Exception("OpenAI service not available")
        
        try:
            # Get relevant content from Pinecone
            search_results = semantic_search_service.semantic_search(question, similarity_threshold=0.3)
            context = self._build_context_from_search_results(search_results)
            
            system_prompt = f"""You are the HuddleUp AI Assistant, an intelligent discovery agent for HuddleUp's learning collaboration platform.

YOUR MISSION: Help visitors understand how HuddleUp can transform their learning and collaboration processes through guided discovery conversations.

KNOWLEDGE BASE CONTEXT:
{context}

Use the above knowledge base context to provide accurate, specific answers. If the context doesn't contain enough information for a specific question, use the general guidelines below:

GENERAL INFORMATION:

TARGET USERS: L&D professionals, team leaders, trainers, educators, HR managers, consultants, and anyone who wants to improve how their team learns and collaborates.

CORE USE CASES - BE READY TO EXPLAIN IN DETAIL:

1) EXTENDING IN-PERSON WORKSHOPS INTO COLLABORATIVE ACTION:
   - Problem: Workshops end but implementation doesn't happen - participants leave excited but struggle to apply learnings
   - HuddleUp Solution: Create post-workshop collaboration spaces where participants:
     * Share their implementation plans and get peer feedback
     * Post real examples of applying workshop concepts in their work
     * Ask questions and get ongoing support from facilitator and peers
     * Track progress on action items with accountability partners
     * Build a repository of real-world applications that future participants can reference
   - Outcome: Workshop impact extends months beyond the event with measurable implementation

2) EXTENDING ONLINE COURSES INTO COLLABORATIVE ACTION:
   - Problem: Course completion doesn't equal skill application - learners consume content but don't practice or implement
   - HuddleUp Solution: Transform passive course consumption into active peer collaboration:
     * Learners share how they're applying course concepts in their specific context
     * Peer feedback on real implementation attempts (not just quizzes)
     * Collaborative problem-solving when learners get stuck applying concepts
     * Course facilitator can see actual implementation challenges and adjust content
     * Build community of practitioners who continue learning together beyond course end
   - Outcome: Higher skill transfer and continued learning momentum through peer accountability

3) EXTENDING WEBINARS FOR NEXT STEPS:
   - Problem: Webinars inspire but don't facilitate follow-through - participants get excited but need structured next steps
   - HuddleUp Solution: Create post-webinar action communities where interested participants:
     * Share their specific plans for implementing webinar insights
     * Get feedback and suggestions from peers facing similar challenges
     * Access additional resources and tools for implementation
     * Connect with others in similar roles or industries for ongoing collaboration
     * Track and share progress on commitments made during webinar
   - Outcome: Webinar becomes launching point for sustained behavior change and community building

4) HELPING TEAMS IMPLEMENT STRATEGIC GOALS:
   - Problem: Strategic plans sit in documents while teams struggle with day-to-day execution and alignment
   - HuddleUp Solution: Create collaborative implementation tracking where team members:
     * Break strategic goals into specific, actionable experiments and initiatives
     * Share regular updates on progress, challenges, and learnings
     * Get peer feedback on implementation approaches and obstacle resolution
     * Collaborate on solutions when facing common challenges
     * Build organizational knowledge base of what works and what doesn't
     * Leadership can see real implementation progress and provide targeted support
   - Outcome: Strategic goals become living, collaborative efforts with higher execution rates

CONVERSATION TRIGGERS:
- When user mentions workshops: Focus on Use Case 1 - extending workshop impact through collaborative follow-through
- When user mentions courses/training: Focus on Use Case 2 - transforming passive learning into active collaboration
- When user mentions webinars/events: Focus on Use Case 3 - creating structured post-event implementation communities
- When user mentions strategy/goals/implementation: Focus on Use Case 4 - collaborative strategic execution
- When user asks about use cases: Explain all four and ask which resonates most with their situation
- When user asks about pricing/cost: Use ONLY pricing information from the knowledge base context - never invent pricing

PRICING GUIDELINES:
- Always check knowledge base context first for pricing information
- Use exact pricing details found in the knowledge base
- If no pricing in knowledge base, acknowledge this and offer to connect them with Derek for current pricing
- Never guess or make up pricing information
- Mention that pricing may depend on team size and specific requirements

SCHEDULING & MEETING DETECTION - CRITICAL RULES:
ONLY mention scheduling/meetings/calls when users explicitly use phrases like:
- "can i talk to someone", "can i speak to someone", "can i speak with someone"
- "i want to talk to someone", "i need to talk to someone"
- "can i schedule a meeting", "can i book a meeting", "can i schedule a call", "can i book a call"
- "i want to schedule", "i want to book", "i need to schedule", "i need to book"
- "schedule a demo", "book a demo", "talk to a person", "speak to a person"

CRITICAL RULE: NEVER mention scheduling, booking, calling, meeting with Derek, or talking to someone UNLESS the user explicitly asks using the above phrases.

FOR ALL OTHER QUESTIONS (about features, pricing, how HuddleUp works, etc.):
- Answer their question directly without mentioning scheduling
- Focus on explaining HuddleUp's features and benefits
- Ask discovery questions about their needs and challenges
- DO NOT suggest scheduling, meetings, demos, or talking to Derek
- Keep responses focused on their actual question

ONLY when explicit scheduling request detected:
1. Acknowledge their request to connect with someone
2. Mention Derek and scheduling options
3. Show enthusiasm about connecting them

Remember: Most questions are about learning HuddleUp features - answer those directly without scheduling offers.

DISCOVERY CONVERSATION APPROACH:
1. **Understanding Context**: Ask thoughtful questions about their current situation:
   - What's their role and responsibilities?
   - What learning/training challenges do they face?
   - How do they currently deliver training or facilitate learning?
   - What are their team collaboration pain points?
   - What tools do they use now and what's not working?

2. **Connect Solutions**: Based on their responses, explain how HuddleUp specifically addresses their needs with relevant features and benefits

3. **Guide to Next Steps**: When they show genuine interest, offer specific actions:
   🔹 "Find a time to meet with Derek" (our learning collaboration expert)
   🔹 "See how your current processes could work in HuddleUp"
   🔹 "Receive research on problems HuddleUp solves"  
   🔹 "Ask more questions about specific features"

CONVERSATION STYLE:
- Build on previous messages - don't repeat the same introduction multiple times
- If you've already introduced HuddleUp, move to specific questions or examples
- Vary your responses based on conversation flow
- Ask ONE specific discovery question at a time to avoid overwhelming
- Be genuinely curious about their challenges, not pushy
- Use their specific context to make explanations relevant
- Be concise but informative (2-3 short paragraphs max)
- Always aim to understand their needs before explaining solutions
- When scheduling intent is detected, immediately offer to help schedule a meeting
- NEVER repeat the same introduction if you've already explained what HuddleUp does

RESPONSE PATTERNS TO AVOID:
- Don't start every response with "I'm here to help you discover how HuddleUp..."
- Don't repeat the same role/challenges question if already asked
- Build on the conversation naturally instead of restarting each time
- NEVER use vague pricing language like "flexible pricing options" or "cost-effective solutions" without specific numbers from knowledge base
- If asked about pricing and no specific numbers are in knowledge base context, clearly state you don't have pricing details rather than being vague

WHEN TO OFFER NEXT STEPS:
After learning about their specific needs and explaining how HuddleUp addresses them, naturally suggest the most relevant next step. For scheduling-related queries, immediately offer to help schedule a meeting.

REMEMBER: This isn't just FAQ - you're conducting a discovery conversation that helps visitors see exactly how HuddleUp fits their unique situation. When they want to schedule or meet someone, enthusiastically help them connect with Derek for a personalized demo."""

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question}
            ]
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=350,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"Error generating direct OpenAI response: {e}")
            raise e
    
    def _build_context_from_search_results(self, search_results: Dict) -> str:
        """Build context string from Pinecone search results"""
        if not search_results or not search_results.get("success") or not search_results.get("results"):
            return ""
        
        context = "Relevant Knowledge Base Information:\n\n"
        for result in search_results["results"]:
            source_type = result.get('source_type', '')
            title = result.get('title', '')
            content = (result.get('content') or 
                      result.get('text') or 
                      result.get('metadata', {}).get('content') or 
                      result.get('metadata', {}).get('answer') or 
                      '')
            
            if content:
                context += f"=== {source_type.upper()} - {title} ===\n"
                context += f"{content}\n\n"
        
        return context
    
    def check_if_process_question(self, question: str) -> bool:
        """
        Use AI to determine if the question is about current processes
        that might benefit from a more detailed analysis
        """
        if not self.client:
            # Simple keyword-based fallback
            keywords = ['process', 'workflow', 'current', 'improve', 'change', 'better', 'different']
            return any(keyword in question.lower() for keyword in keywords)
        
        try:
            prompt = f"""
            Determine if this question is asking about how HuddleUp could improve or change 
            the user's current processes, workflows, or systems. 
            
            Return only "YES" or "NO".
            
            Question: {question}
            """
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=10,
                temperature=0.3
            )
            
            return response.choices[0].message.content.strip().upper() == "YES"
            
        except Exception as e:
            print(f"Error checking if process question: {e}")
            return False

    def process_question(self, question: str, context_answer: str) -> str:
        """
        Process a user question with existing context/answer from database
        This enhances or contextualizes the database response
        """
        if not self.client:
            return context_answer  # Return original if OpenAI not available
        
        try:
            system_prompt = """You are an AI assistant for HuddleUp. You have been provided with a relevant answer from the knowledge base. Your job is to:

1. Review the provided answer and user question
2. If the answer directly addresses the question, you may return it as-is or slightly enhance it for clarity
3. If the answer is relevant but doesn't fully address the question, enhance it with additional helpful information
4. Make the response conversational and helpful
5. Keep the core information from the knowledge base answer

Always maintain accuracy and don't add information that contradicts the knowledge base."""

            # Strengthen instructions to avoid hallucination and to include short source citation if available
            system_prompt = system_prompt + "\n\nAdditional rules:\n- Do not invent product features or pricing beyond what is stated in the knowledge base.\n- If you enhance the answer, keep added claims conservative and clearly marked as suggestions.\n- If the knowledge base answer includes an explicit source title or ID, append a short 'Source:' line at the end (one line).\n- Keep the final answer concise (1-3 short paragraphs or a few bullet points) suitable for a chat UI."

            user_prompt = f"""User Question: {question}

Knowledge Base Answer: {context_answer}

Please provide an enhanced response that addresses the user's question using the knowledge base information."""

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=400,
                temperature=0.6
            )
            
            enhanced_response = response.choices[0].message.content.strip()
            
            # If the enhanced response is too similar or empty, return original
            if len(enhanced_response) < 50 or enhanced_response.lower() == context_answer.lower():
                return context_answer
            
            return enhanced_response
            
        except Exception as e:
            print(f"Error processing question with context: {e}")
            return context_answer  # Return original answer if processing fails

    def generate_discovery_response_with_actions(self, question: str, conversation_context: List[Dict] = None, user_profile: Dict = None) -> Dict:
        """
        Generate a discovery response that may include action buttons
        Returns both text response and suggested actions based on user profile and context
        Progressive engagement: More options appear after 5+ queries
        """
        print(f"🔍 DISCOVERY REQUEST: {question}")
        print(f"📊 SOURCE: Starting OpenAI discovery response generation")
        
        if not self.client:
            print(f"❌ SOURCE: OpenAI client not available, returning error")
            return {
                "response": "I apologize, but I'm currently unable to process your question. Please try again later.",
                "actions": []
            }
        
        # Get semantic search results for context
        knowledge_context = ""
        if semantic_search_service:
            try:
                print(f"🔍 SOURCE: Getting semantic search context for: {question}")
                search_results = semantic_search_service.semantic_search(question, similarity_threshold=0.3)
                
                print(f"🔍 DEBUG: Search results success: {search_results.get('success')}")
                print(f"🔍 DEBUG: Number of results: {len(search_results.get('results', []))}")
                
                if search_results.get("success") and search_results.get("results"):
                    knowledge_context = "KNOWLEDGE BASE CONTEXT:\n"
                    for i, result in enumerate(search_results["results"][:3]):
                        content = result.get('content') or result.get('text') or ''
                        print(f"🔍 DEBUG: Result {i+1} content length: {len(content) if content else 0}")
                        if content and len(content.strip()) > 20:
                            knowledge_context += f"\nResult {i+1} (similarity: {result.get('similarity', 0):.3f}):\n{content.strip()}\n"
                            print(f"🔍 DEBUG: Added content: {content[:100]}...")
                    knowledge_context += "\n"
                    print(f"✅ SOURCE: Added {len(search_results['results'])} knowledge base results to context")
                    print(f"🔍 DEBUG: Final context length: {len(knowledge_context)}")
                else:
                    print(f"⚠️ SOURCE: No semantic search results found")
                    print(f"🔍 DEBUG: Search results: {search_results}")
            except Exception as e:
                print(f"❌ SOURCE: Semantic search error: {e}")
                import traceback
                traceback.print_exc()
                knowledge_context = ""
        
        try:
            # Build conversation context
            context_str = ""
            query_count = 0
            if conversation_context:
                context_str = "Previous conversation:\n"
                for msg in conversation_context[-4:]:  # Last 4 messages for context
                    role = "User" if msg.get("role") == "user" else "Assistant"
                    context_str += f"{role}: {msg.get('content', '')}\n"
                context_str += "\n"
                
                # Count user queries (excluding greetings and email collection)
                query_count = len([msg for msg in conversation_context if msg.get("role") == "user"])
            
            # Build user profile context
            profile_str = ""
            if user_profile:
                profile_str = f"""User Profile Analysis:
- Role/Type: {user_profile.get('profile', 'unknown')}
- Detected Needs: {', '.join(user_profile.get('needs', []))}
- Readiness Level: {user_profile.get('readiness', 'discovery')}
- Conversation Count: {user_profile.get('conversation_count', 0)}
- Engagement Score: {user_profile.get('engagement_score', 0)}

"""
            
            # Determine engagement level based on query count
            engagement_level = "initial" if query_count < 5 else "full"
            
            system_prompt = f"""You are the HuddleUp AI Assistant conducting discovery conversations.

{knowledge_context}{context_str}{profile_str}

CRITICAL CONVERSATION CONTINUITY RULES:
1. ALWAYS review the conversation context above before responding
2. If user asks a specific question, answer that EXACT question - don't deflect to discovery
3. If user asks "how could my processes work better in HuddleUp" - explain specific process improvements
4. If user says "yes" to exploring examples, provide specific examples immediately
5. If user says "yes" to scheduling, help them schedule immediately
6. If user asks follow-up questions, answer them directly without repeating introductions
7. Build naturally on the conversation - NEVER restart or repeat previous questions
8. If user asks about their processes, give concrete examples of how HuddleUp improves common processes

CRITICAL "YES" RESPONSE HANDLING:
- If user says "yes" or "sure" or "I'd like that" after you offered examples, immediately share 2-3 specific detailed examples from the SPECIFIC EXAMPLES section below
- If user says "yes" or "sure" or "I'd like that" after you offered scheduling, help them schedule with clear next steps
- If user gives a simple "yes" without context, look at previous assistant message to understand what they're agreeing to
- NEVER respond with vague acknowledgments like "That's great to hear!" - take action based on what they agreed to

SPECIFIC QUESTION HANDLING:
- "How could my processes work better in HuddleUp?" → Explain 3-4 specific process improvements
- "What is HuddleUp?" → Give clear overview with key benefits
- "How does it work?" → Walk through concrete workflow example
- "Can you show me examples?" → Share real-world success stories
- "What are the benefits?" → List specific, measurable benefits with outcomes
- "How much does it cost?" / "What's the price?" / "Pricing?" → Use ONLY information from knowledge base context above, never make up pricing

PRICING QUESTION HANDLING - CRITICAL INSTRUCTIONS:
When users ask about pricing, cost, or fees:
1. IMMEDIATELY check the KNOWLEDGE BASE CONTEXT section above for any pricing numbers, plans, or cost information
2. If you find specific pricing information in the knowledge base context (like pricing plans, costs, fees, etc.), ALWAYS use that information to provide a comprehensive answer about HuddleUp's pricing
3. Present the pricing information clearly, including all available plans (Free, Silver, Gold, Enterprise) and their features
4. Be specific about what's included in each plan and any user limits or features
5. Only mention Derek or scheduling if the user explicitly asks to speak with someone or wants personalized recommendations after you've provided the pricing details
6. If the knowledge base context contains NO pricing information whatsoever, then you may mention connecting with Derek
7. NEVER default to Derek when pricing information is available in the knowledge base context

ENGAGEMENT PROGRESSION:
- Query Count: {query_count}
- Engagement Level: {engagement_level}
- {"FULL ENGAGEMENT MODE: All action options available" if engagement_level == "full" else "INITIAL DISCOVERY MODE: Limited options to build trust"}

Your goal: Guide visitors through discovery to understand how HuddleUp fits their needs while maintaining natural conversation flow.

SCHEDULING & MEETING DETECTION - VERY SPECIFIC TRIGGERS ONLY:
Only mention scheduling when users use these EXACT phrases or very similar:
- "can i talk to someone", "can i speak to someone", "can i speak with someone"
- "i want to talk to someone", "i need to talk to someone"
- "can i schedule a meeting", "can i book a meeting", "can i schedule a call", "can i book a call"
- "i want to schedule", "i want to book", "i need to schedule", "i need to book"
- "schedule a demo", "book a demo", "schedule an appointment", "book an appointment"
- "talk to a person", "speak to a person", "contact someone from your team"
- "can someone call me", "can i get a call", "set up a meeting", "arrange a call"

CRITICAL: DO NOT mention scheduling for general questions like:
- "how can you help me", "what can you do", "tell me about huddleup"
- "what is huddleup", "how does it work", "what are the features"
- General assistance requests that don't explicitly ask to talk to a person

RESPOND BY (ONLY when explicit scheduling request detected):
1. Acknowledging their specific request enthusiastically
2. Explaining how a meeting/demo would benefit them specifically
3. Including phrases like: "I'd be happy to help you schedule a meeting!" or "Would you like to schedule a time to discuss HuddleUp with Derek?"
4. Naturally weave in the scheduling offer without being pushy

DO NOT mention scheduling, meetings, calls, or talking to someone unless the user explicitly requests it using the phrases above.

RESPONSE PERSONALIZATION:
- Use the user profile to tailor your response
- For trainers: Focus on course delivery, engagement, and content management
- For managers: Emphasize team collaboration, knowledge sharing, and productivity
- For HR: Highlight onboarding, employee development, and organizational learning
- For consultants: Discuss client solutions, implementation, and measurable results
- For L&D: Focus on learning effectiveness, scalability, and analytics

CONVERSATION STAGE GUIDANCE:
- Discovery (0-2 messages): Ask about role, challenges, current tools
- Understanding (3-5 messages): Dive deeper into specific pain points
- Solution-focused (6+ messages): Connect needs to HuddleUp benefits
- Action-ready (high engagement): Offer meeting or demo opportunities

PROCESS IMPROVEMENT EXPLANATIONS (for "how could my processes work better"):

TRAINING WORKSHOPS → EXTENDED COLLABORATION:
"Instead of workshops ending when participants leave, HuddleUp creates ongoing collaboration spaces where team members share implementation progress, get peer feedback on real applications, and build a library of practical approaches. This extends workshop impact from days to months."

ONLINE COURSES → ACTIVE PEER LEARNING:
"Rather than passive course consumption, HuddleUp transforms courses into collaborative experiences where learners share real-world applications, discuss challenges together, and provide peer feedback. This increases skill transfer from ~15% to 70%+."

TEAM MEETINGS → ASYNCHRONOUS PROGRESS TRACKING:
"Instead of lengthy status meetings, teams use HuddleUp to share progress updates, collaborate on solving obstacles, and track goal implementation asynchronously. This reduces meeting time by 50% while improving alignment and accountability."

STRATEGY IMPLEMENTATION → COLLABORATIVE EXECUTION:
"Rather than quarterly check-ins on strategic goals, HuddleUp enables ongoing collaboration where team members share experiments, learn from each other's approaches, and get unstuck together. This increases goal achievement rates significantly."

KNOWLEDGE SHARING → PEER-DRIVEN LEARNING:
"Instead of top-down knowledge transfer, HuddleUp facilitates peer-to-peer learning where team members share real experiences, best practices, and lessons learned. This creates a living knowledge base that grows with your team."

SPECIFIC EXAMPLES TO SHARE (when requested):
1. Workshop Extension Example: "A leadership development workshop typically ends Friday afternoon. With HuddleUp, participants continue collaborating for 8 weeks, sharing how they're applying leadership techniques, getting peer feedback on real situations, and building a library of practical leadership approaches. Result: 85% implementation rate vs. 15% typical."

2. Course Collaboration Example: "Instead of just watching compliance training videos alone, team members share real workplace scenarios where compliance matters, discuss edge cases together, and build a team knowledge base of 'what good looks like.' Engagement goes from 30% completion to 95% active participation."

3. Strategic Implementation Example: "Rather than quarterly check-ins on goals, teams use HuddleUp to share weekly progress, get unstuck together, and celebrate wins. Leadership sees real-time implementation challenges and can provide targeted support. Goal achievement rate increases 60%."

4. Webinar Follow-through Example: "After a change management webinar, interested participants join a HuddleUp space to share their change initiatives, get peer advice, and track progress together. 70% implement concrete changes vs. 10% typical post-webinar action."

RESPONSE FORMAT: Return a JSON object with:
- "response": Your conversational response text (2-3 short paragraphs max)
- "actions": Array of relevant next step objects with "type", "label", and "description"

CONVERSATION STYLE:
- ALWAYS honor the conversation flow - if user responds to your question, address their response directly
- When user says "yes" to examples, share 2-3 specific examples above that match their context
- When user says "yes" to scheduling, help them schedule immediately
- Build on previous messages - don't restart the conversation
- If you've already introduced HuddleUp, move to specific questions or examples  
- Vary your responses based on conversation flow and context
- NEVER repeat the same introduction or discovery question if already used in conversation

RESPONSE PATTERNS TO AVOID:
- Don't start responses with "I'm here to help you discover..." if already introduced
- Don't ask "what's your role and biggest challenges" repeatedly
- Don't restart the conversation - build on what's already been discussed
- When user responds to your specific question, address their response directly

AVAILABLE ACTIONS - PROGRESSIVE ENGAGEMENT:

RESPONSE GUIDANCE:
Instead of buttons, weave these options naturally into the conversation:

1. For scheduling demos:
   "Would you like to schedule a quick demo with Derek to see HuddleUp in action?"

2. For showing examples:
   "Would you like to see some specific examples of how HuddleUp works? Or shall we explore other aspects?"

USE CASES TO COVER IN DETAIL:

1) EXTENDING IN-PERSON WORKSHOPS INTO COLLABORATIVE ACTION:
   - Challenge: Workshop energy fades quickly, implementation doesn't happen
   - HuddleUp Solution: Post-workshop collaboration spaces for ongoing implementation support
   - Key Benefits: Sustained learning momentum, peer accountability, real-world application repository
   - Ask: "Do you currently run workshops? What happens after participants leave?"

2) EXTENDING ONLINE COURSES INTO COLLABORATIVE ACTION:
   - Challenge: Course completion ≠ skill application, learners consume but don't practice
   - HuddleUp Solution: Transform passive learning into active peer collaboration and feedback
   - Key Benefits: Higher skill transfer, continued learning community, practical application focus
   - Ask: "How do you currently ensure learners actually apply what they've learned in courses?"

3) EXTENDING WEBINARS FOR NEXT STEPS:
   - Challenge: Webinars inspire but don't facilitate follow-through, excitement fades quickly
   - HuddleUp Solution: Post-webinar action communities for structured implementation
   - Key Benefits: Sustained engagement, community building, measurable follow-through
   - Ask: "After your webinars, how do you help interested participants take concrete next steps?"

4) HELPING TEAMS IMPLEMENT STRATEGIC GOALS:
   - Challenge: Strategic plans remain documents, teams struggle with execution alignment
   - HuddleUp Solution: Collaborative implementation tracking with peer feedback and learning
   - Key Benefits: Higher execution rates, organizational learning, leadership visibility
   - Ask: "How does your team currently track and collaborate on strategic goal implementation?"

CONVERSATION TRIGGERS:
- When user mentions workshops/training events: Explain Use Case 1 - How HuddleUp extends workshop impact through collaborative follow-through and peer accountability
- When user mentions courses/online learning: Focus on Use Case 2 - Transforming passive course consumption into active peer collaboration and real-world application
- When user mentions webinars/events/presentations: Highlight Use Case 3 - Creating structured post-event communities for sustained implementation
- When user mentions strategy/goals/implementation/execution: Emphasize Use Case 4 - Collaborative strategic goal execution with team alignment and progress tracking
- When user asks "what does HuddleUp do" or "use cases": Present all four use cases and ask which situation resonates most with their current challenges
- When user mentions current challenges: Connect their specific pain points to the relevant use case and explain how HuddleUp addresses that exact problem
- When user mentions team collaboration: Explain how HuddleUp facilitates peer learning and feedback in their specific context
- When user asks about pricing/cost: Check conversation context for any pricing information from knowledge base and use that EXACT information only

PRICING HANDLING IN DISCOVERY MODE - CRITICAL INSTRUCTIONS:
- If user asks about pricing, IMMEDIATELY scan the conversation context above for any specific pricing numbers or cost information from the knowledge base
- If specific pricing found (like "$X per month", pricing tiers, cost breakdowns), state those EXACT numbers
- If NO specific pricing numbers found in context, respond: "I don't have the specific pricing details available right now. Derek can provide you with accurate pricing information based on your team size and needs. Would you like me to help you schedule a time to discuss pricing with him?"
- NEVER use vague terms like "flexible pricing", "cost-effective", or "tailored pricing" without specific numbers
- ALWAYS include scheduling language in pricing responses to trigger the schedule button: "Would you like to schedule a meeting to discuss pricing?" or "I'd be happy to help you schedule a call with Derek about pricing"
- Either give exact pricing from knowledge base OR clearly state you don't have the pricing details, but ALWAYS offer to schedule a pricing discussion

Only show calendar booking option:
{{"type": "calendar", "label": "Schedule a Demo with Derek", "description": "See HuddleUp in action with our learning collaboration expert"}}

ACTION SELECTION RULES:
- ALWAYS include "questions" as an option
- INITIAL ENGAGEMENT: Focus on "questions" and "solution_preview" only
- FULL ENGAGEMENT: Show all options based on readiness level
  - For "ready" users: Prioritize "calendar" and "solution_preview"
  - For "evaluating" users: Offer "solution_preview", "process_analysis" and "research"
  - For "interested" users: Include "solution_preview", "research" and "process_analysis"
  - For discovery users: All options available but emphasize "solution_preview"

ENGAGEMENT TRANSITION MESSAGE:
- At exactly 5 queries, acknowledge their engagement and introduce full options
- Say something like: "I can see you're genuinely interested in exploring HuddleUp! Since we've been chatting, I'd love to offer you some additional ways to dive deeper..."

CONVERSATION STYLE:
- Build on previous messages - don't repeat the same introduction multiple times
- If you've already introduced HuddleUp, move to specific questions or examples  
- Vary your responses based on conversation flow and context
- Focus on understanding their current practices and challenges first
- Demonstrate deep knowledge of common challenges in their space
- Explain specifically how HuddleUp addresses their unique situation
- Share relevant use case examples that match their context
- Ask thoughtful follow-up questions about their implementation goals
- Naturally suggest a demo when the conversation indicates strong interest
- When scheduling intent is detected, immediately offer to help schedule a meeting
- NEVER repeat the same introduction or discovery question if already used in conversation

RESPONSE PATTERNS TO AVOID:
- Don't start responses with "I'm here to help you discover..." if already introduced
- Don't ask "what's your role and biggest challenges" repeatedly
- Don't restart the conversation - build on what's already been discussed
- Vary your language and approach based on conversation context

KEY DIFFERENTIATORS TO EMPHASIZE:
- Post-training collaboration and implementation tracking
- Building a bank of real-world practices from the team
- Peer feedback with both qualitative and quantitative insights
- Reduced meeting time through structured asynchronous collaboration
- Measurable ROI through implementation success tracking

EXAMPLE NATURAL PROMPTS:
- "Would you like to see how other organizations have implemented this in HuddleUp?"
- "I'd be happy to show you some specific examples of how this works in practice."
- "Would you like to schedule a quick demo to see these features in action?"
- "I'd be happy to help you schedule a meeting with Derek to discuss your specific needs!"

Return ONLY valid JSON in this format:
{{"response": "Your response text here", "actions": [action objects]}}

CRITICAL JSON FORMATTING:
- Your response must be ONLY valid JSON
- Do not include any text before or after the JSON
- Do not include explanations or comments outside the JSON
- The "response" field should contain your conversational text
- The "actions" field should contain action button objects
- Ensure proper JSON escaping of quotes within the response text

PRICING RESPONSE FORMAT:
- If specific pricing found in knowledge base: Include exact numbers in the "response" field
- If no pricing found: State clearly in "response" that you don't have pricing details and suggest connecting with Derek
- Never leak JSON structure into the visible response text"""

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question}
            ]
            
            print(f"🤖 SOURCE: Calling OpenAI API for discovery response")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=400,
                temperature=0.7
            )
            print(f"✅ SOURCE: Received response from OpenAI")
            
            # Try to parse JSON response with better error handling
            try:
                import json
                raw_response = response.choices[0].message.content.strip()
                print(f"🔍 DEBUG: Raw OpenAI response length: {len(raw_response)}")
                print(f"🔍 DEBUG: Raw response preview: {raw_response[:200]}...")
                
                result = json.loads(raw_response)
                print(f"✅ SOURCE: Successfully parsed OpenAI JSON response")
                
                # Validate that required fields exist
                if "response" not in result:
                    result["response"] = "I'd love to help you learn more about HuddleUp!"
                if "actions" not in result:
                    print(f"🔧 SOURCE: Adding default actions based on engagement level")
                    # Default actions based on engagement level
                    if query_count >= 5:
                        result["actions"] = [
                            {"type": "calendar", "label": "Find a time to meet with Derek", "description": "Schedule a personalized demo"},
                            {"type": "solution_preview", "label": "Explore HuddleUp Solution Preview", "description": "See how HuddleUp works for your needs"},
                            {"type": "process_analysis", "label": "See how your processes could work in HuddleUp", "description": "Discover improvements"},
                            {"type": "research", "label": "Receive research on HuddleUp benefits", "description": "Get data on problems HuddleUp solves"},
                            {"type": "questions", "label": "Ask more questions", "description": "Continue exploring HuddleUp"}
                        ]
                    else:
                        result["actions"] = [
                            {"type": "solution_preview", "label": "Explore HuddleUp Solution Preview", "description": "See how HuddleUp works for your needs"},
                            {"type": "questions", "label": "Ask more questions", "description": "Continue exploring HuddleUp"}
                        ]
                elif query_count >= 5 and len(result["actions"]) <= 2:
                    # Override with full action set for full engagement
                    result["actions"] = [
                        {"type": "calendar", "label": "Find a time to meet with Derek", "description": "Schedule a personalized demo"},
                        {"type": "solution_preview", "label": "Explore HuddleUp Solution Preview", "description": "See how HuddleUp works for your needs"},
                        {"type": "process_analysis", "label": "See how your processes could work in HuddleUp", "description": "Discover improvements"},
                        {"type": "research", "label": "Receive research on HuddleUp benefits", "description": "Get data on problems HuddleUp solves"},
                        {"type": "questions", "label": "Ask more questions", "description": "Continue exploring HuddleUp"}
                    ]
                    
                return result
                
            except json.JSONDecodeError as e:
                print(f"⚠️ SOURCE: Failed to parse OpenAI JSON: {e}")
                print(f"🔍 DEBUG: Raw response that failed to parse: {response.choices[0].message.content}")
                
                # Fallback: Use the raw response text and generate appropriate actions
                response_text = response.choices[0].message.content.strip()
                
                # If the response contains pricing/knowledge base content, use it as-is
                # If it seems to be asking for Derek scheduling, try to use knowledge_context instead
                if knowledge_context and ("derek" in response_text.lower() or "schedule" in response_text.lower()):
                    # Extract the first meaningful piece of content from knowledge context
                    lines = knowledge_context.split('\n')
                    content_start = -1
                    for i, line in enumerate(lines):
                        if 'Result 1' in line and 'similarity:' in line:
                            content_start = i + 1
                            break
                    
                    if content_start > 0 and content_start < len(lines):
                        # Extract the actual content after "Result 1" line
                        content_lines = []
                        for line in lines[content_start:]:
                            if line.strip() and not line.startswith('Result '):
                                content_lines.append(line.strip())
                            elif line.startswith('Result '):
                                break
                        
                        if content_lines:
                            response_text = ' '.join(content_lines)[:800] + "..."
                            print(f"✅ SOURCE: Using knowledge base content instead of Derek fallback")
                
                # Determine actions based on engagement level and user profile
                if query_count >= 5:
                    # Full engagement actions
                    actions = [
                        {"type": "calendar", "label": "Find a time to meet with Derek", "description": "Schedule a personalized demo with our learning collaboration expert"},
                        {"type": "solution_preview", "label": "Explore HuddleUp Solution Preview", "description": "See how HuddleUp works for your specific needs"},
                        {"type": "process_analysis", "label": "See how your processes could work in HuddleUp", "description": "Discover specific improvements for your current workflows"},
                        {"type": "research", "label": "Receive research on HuddleUp benefits", "description": "Get data on problems HuddleUp solves in your industry"},
                        {"type": "questions", "label": "Ask more questions", "description": "Continue exploring HuddleUp"}
                    ]
                    
                    if user_profile:
                        readiness = user_profile.get('readiness', 'discovery')
                        # Reorder based on readiness but keep all options
                        if readiness == 'ready':
                            # Move calendar to front
                            actions = [actions[0]] + [actions[1]] + actions[2:]
                        elif readiness == 'evaluating':
                            # Emphasize analysis options
                            actions = [actions[1], actions[2], actions[3], actions[0], actions[4]]
                        elif readiness == 'interested':
                            # Research and preview focused
                            actions = [actions[1], actions[3], actions[2], actions[0], actions[4]]
                else:
                    # Initial engagement actions
                    actions = [
                        {"type": "solution_preview", "label": "Explore HuddleUp Solution Preview", "description": "See how HuddleUp works for your needs"},
                        {"type": "questions", "label": "Ask more questions", "description": "Continue exploring HuddleUp"}
                    ]
                
                return {
                    "response": response_text,
                    "actions": actions
                }
            
        except Exception as e:
            print(f"Error generating discovery response with actions: {e}")
            
            # Smart fallback based on engagement level
            if query_count >= 5:
                fallback_actions = [
                    {"type": "calendar", "label": "Find a time to meet with Derek", "description": "Schedule a demo"},
                    {"type": "solution_preview", "label": "Explore HuddleUp Solution Preview", "description": "See how HuddleUp works for your needs"},
                    {"type": "process_analysis", "label": "See how your processes could work in HuddleUp", "description": "Discover improvements"},
                    {"type": "research", "label": "Receive research on HuddleUp benefits", "description": "Get data on problems HuddleUp solves"},
                    {"type": "questions", "label": "Ask more questions", "description": "Continue exploring HuddleUp"}
                ]
            else:
                fallback_actions = [
                    {"type": "solution_preview", "label": "Explore HuddleUp Solution Preview", "description": "See how HuddleUp works for your needs"},
                    {"type": "questions", "label": "Ask more questions", "description": "Continue exploring HuddleUp"}
                ]
            
            return {
                "response": "I'd love to help you learn more about HuddleUp! What specific challenges are you facing with your current learning or collaboration processes?",
                "actions": fallback_actions
            }

# Singleton instance
try:
    openai_service = OpenAIService()
except Exception as e:
    print(f"Warning: Could not initialize OpenAI service: {e}")
    openai_service = None