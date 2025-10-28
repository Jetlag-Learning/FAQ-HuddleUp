import os
import openai
from typing import List, Dict, Optional
from dotenv import load_dotenv

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
        Generate a discovery-focused response using knowledge base context
        Combines KB information with discovery conversation approach
        """
        if not self.client:
            raise Exception("OpenAI service not available")
        
        try:
            # Build context from knowledge base results
            context = self._build_comprehensive_context(knowledge_base_results) if knowledge_base_results else ""
            
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
        Generate a direct response using OpenAI for discovery conversations
        Focuses on understanding visitor context and guiding them to relevant solutions
        """
        if not self.client:
            raise Exception("OpenAI service not available")
        
        try:
            system_prompt = """You are the HuddleUp AI Assistant, an intelligent discovery agent for HuddleUp's learning collaboration platform.

YOUR MISSION: Help visitors understand how HuddleUp can transform their learning and collaboration processes through guided discovery conversations.

ABOUT HUDDLEUP:
HuddleUp creates "learning huddles" - interactive collaboration spaces where teams learn together more effectively than traditional training methods. Key benefits:
• Interactive learning experiences with higher engagement
• Better knowledge retention through peer collaboration  
• Scalable training solutions that grow with your team
• Breaking down silos between departments
• Real-time collaboration and knowledge sharing
• Analytics to track learning progress and engagement

TARGET USERS: L&D professionals, team leaders, trainers, educators, HR managers, consultants, and anyone who wants to improve how their team learns and collaborates.

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
- Ask ONE discovery question at a time to avoid overwhelming
- Be genuinely curious about their challenges, not pushy
- Use their specific context to make explanations relevant
- Be concise but informative (2-3 short paragraphs max)
- Always aim to understand their needs before explaining solutions

WHEN TO OFFER NEXT STEPS:
After learning about their specific needs and explaining how HuddleUp addresses them, naturally suggest the most relevant next step. Don't rush to this - build understanding first.

REMEMBER: This isn't just FAQ - you're conducting a discovery conversation that helps visitors see exactly how HuddleUp fits their unique situation."""

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
    
    def _build_context(self, faqs: List[Dict]) -> str:
        """Build context string from existing FAQ entries"""
        if not faqs:
            return ""
        
        context = "Existing FAQ information:\n"
        for faq in faqs:
            context += f"Q: {faq.get('question', '')}\n"
            context += f"A: {faq.get('answer', '')}\n\n"
        
        return context
    
    def _build_comprehensive_context(self, kb_results: Dict) -> str:
        """Build context string from comprehensive knowledge base results"""
        if not kb_results:
            return ""
        
        context = "Knowledge Base Information:\n\n"
        
        # Add FAQ entries
        faq_entries = kb_results.get('faq_entries', [])
        if faq_entries:
            context += "=== FAQ Entries ===\n"
            for faq in faq_entries:
                context += f"Q: {faq.get('question', '')}\n"
                context += f"A: {faq.get('answer', '')}\n\n"
        
        # Add documents
        documents = kb_results.get('documents', [])
        if documents:
            context += "=== Documents ===\n"
            for doc in documents:
                context += f"Title: {doc.get('title', '')}\n"
                content = doc.get('content', '')
                # Truncate content if too long
                if len(content) > 500:
                    content = content[:500] + "..."
                context += f"Content: {content}\n\n"
        
        # Add document chunks
        chunks = kb_results.get('document_chunks', [])
        if chunks:
            context += "=== Relevant Content Sections ===\n"
            for chunk in chunks:
                doc_title = chunk.get('documents', {}).get('title', 'Unknown Document')
                chunk_content = chunk.get('content', '')
                context += f"From '{doc_title}': {chunk_content}\n\n"
        
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

{context_str}{profile_str}

ENGAGEMENT PROGRESSION:
- Query Count: {query_count}
- Engagement Level: {engagement_level}
- {"FULL ENGAGEMENT MODE: All action options available" if engagement_level == "full" else "INITIAL DISCOVERY MODE: Limited options to build trust"}

Your goal: Guide visitors through discovery to understand how HuddleUp fits their needs.

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

RESPONSE FORMAT: Return a JSON object with:
- "response": Your conversational response text (2-3 short paragraphs max)
- "actions": Array of relevant next step objects with "type", "label", and "description"

AVAILABLE ACTIONS - PROGRESSIVE ENGAGEMENT:

INITIAL ENGAGEMENT (Queries 1-4):
- {{"type": "questions", "label": "Ask more questions", "description": "Continue exploring HuddleUp features and capabilities"}}
- {{"type": "solution_preview", "label": "Explore HuddleUp Solution Preview", "description": "See a tailored preview of how HuddleUp works for your specific needs"}}

FULL ENGAGEMENT (Queries 5+):
- {{"type": "calendar", "label": "Find a time to meet with Derek", "description": "Schedule a personalized demo with our learning collaboration expert"}}
- {{"type": "solution_preview", "label": "Explore HuddleUp Solution Preview", "description": "See a tailored preview of how HuddleUp works for your specific needs"}}
- {{"type": "process_analysis", "label": "See how your processes could work in HuddleUp", "description": "Discover specific improvements for your current workflows"}}
- {{"type": "research", "label": "Receive research on HuddleUp benefits", "description": "Get data on problems HuddleUp solves in your industry"}}
- {{"type": "questions", "label": "Ask more questions", "description": "Continue exploring HuddleUp features and capabilities"}}

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
- Be genuinely curious about their specific situation
- Ask ONE focused follow-up question at a time
- Use their context to make responses highly relevant
- Avoid being pushy - build understanding first
- Reference their previous comments when relevant
- Progressive disclosure: Start simple, build complexity

Return ONLY valid JSON in this format:
{{"response": "Your response text here", "actions": [action objects]}}"""

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
            
            # Try to parse JSON response
            try:
                import json
                result = json.loads(response.choices[0].message.content.strip())
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
                
            except json.JSONDecodeError:
                print(f"⚠️ SOURCE: Failed to parse OpenAI JSON, using fallback logic")
                # Fallback if JSON parsing fails
                response_text = response.choices[0].message.content.strip()
                
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