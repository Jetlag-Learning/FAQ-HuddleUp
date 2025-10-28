import os
from dotenv import load_dotenv

load_dotenv()

try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Supabase not available: {e}")
    SUPABASE_AVAILABLE = False
    Client = None

class DatabaseService:
    def __init__(self):
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        
        if not SUPABASE_AVAILABLE:
            print("Warning: Supabase package not available. Database features will be disabled.")
            self.supabase = None
        elif not supabase_url or not supabase_key:
            print("Warning: Supabase credentials not found. Database features will be disabled.")
            self.supabase = None
        else:
            try:
                self.supabase = create_client(supabase_url, supabase_key)
            except Exception as e:
                print(f"Warning: Could not connect to Supabase: {e}")
                self.supabase = None
    
    def get_faq_entries(self):
        """Get all FAQ entries from the database"""
        if not self.supabase:
            return []
        try:
            result = self.supabase.table('faq_entries').select('*').execute()
            return result.data
        except Exception as e:
            print(f"Error fetching FAQ entries: {e}")
            return []
    
    def get_documents(self):
        """Get all documents from the knowledge base"""
        if not self.supabase:
            return []
        try:
            result = self.supabase.table('documents').select('*').execute()
            return result.data
        except Exception as e:
            print(f"Error fetching documents: {e}")
            return []
    
    def search_documents(self, query: str):
        """Search documents by title and content"""
        if not self.supabase:
            return []
        try:
            # Search in document titles and content
            result = self.supabase.table('documents').select('*').ilike('title', f'%{query}%').execute()
            if not result.data:
                # Try searching in content if no results in titles
                result = self.supabase.table('documents').select('*').ilike('content', f'%{query}%').execute()
            return result.data
        except Exception as e:
            print(f"Error searching documents: {e}")
            return []
    
    def search_document_chunks(self, query: str, limit: int = 5):
        """Search document chunks for relevant content"""
        if not self.supabase:
            return []
        try:
            # Search in document chunks content
            result = self.supabase.table('document_chunks').select('''
                *,
                documents!inner(title, id)
            ''').ilike('content', f'%{query}%').limit(limit).execute()
            return result.data
        except Exception as e:
            print(f"Error searching document chunks: {e}")
            return []
    
    def search_faq_entries(self, query: str):
        """Search FAQ entries by question, answer, or keywords"""
        if not self.supabase:
            return []
        try:
            # Search in questions and answers using ilike (case-insensitive)
            # Use a simpler approach that works with the current supabase-py version
            result = self.supabase.table('faq_entries').select('*').ilike('question', f'%{query}%').execute()
            if not result.data:
                # Try searching in answers if no results in questions
                result = self.supabase.table('faq_entries').select('*').ilike('answer', f'%{query}%').execute()
            return result.data
        except Exception as e:
            print(f"Error searching FAQ entries: {e}")
            return []
    
    def search_knowledge_base(self, query: str):
        """Comprehensive search across all knowledge base content"""
        results = {
            'faq_entries': [],
            'documents': [],
            'document_chunks': []
        }
        
        if not self.supabase:
            return results
        
        try:
            # Search FAQ entries
            results['faq_entries'] = self.search_faq_entries(query)
            
            # Search documents
            results['documents'] = self.search_documents(query)
            
            # Search document chunks for more granular results
            results['document_chunks'] = self.search_document_chunks(query)
            
            return results
        except Exception as e:
            print(f"Error in comprehensive knowledge base search: {e}")
            return results
    
    def save_chat_message(self, session_id: str, user_message: str, bot_response: str):
        """Save a chat interaction to the database"""
        if not self.supabase:
            return None
        try:
            result = self.supabase.table('chat_messages').insert({
                'session_id': session_id,
                'user_message': user_message,
                'bot_response': bot_response
            }).execute()
            return result.data
        except Exception as e:
            print(f"Error saving chat message: {e}")
            return None
    
    def create_faq_entry(self, question: str, answer: str, category: str, keywords: list):
        """Create a new FAQ entry"""
        try:
            result = self.supabase.table('faq_entries').insert({
                'question': question,
                'answer': answer,
                'category': category,
                'keywords': keywords
            }).execute()
            return result.data
        except Exception as e:
            print(f"Error creating FAQ entry: {e}")
            return None

# Singleton instance
try:
    db_service = DatabaseService()
except Exception as e:
    print(f"Warning: Could not initialize database service: {e}")
    db_service = None