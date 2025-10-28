#!/usr/bin/env python3
"""
Data Population Script for HuddleUp FAQ System with Embeddings
This script helps populate your Supabase database with sample FAQ data and generates embeddings
"""

import os
import sys
from dotenv import load_dotenv

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(__file__))

from semantic_search import SemanticSearchService, EmbeddingService

load_dotenv()

# Sample FAQ data for HuddleUp
SAMPLE_FAQS = [
    {
        "question": "How much does HuddleUp cost?",
        "answer": "HuddleUp offers flexible pricing plans: Starter Plan at $29/month for up to 100 members, Professional Plan at $79/month for up to 500 members, and Enterprise Plan with custom pricing for larger organizations. All plans include core features like community management, content sharing, and basic analytics.",
        "category": "pricing"
    },
    {
        "question": "What are HuddleUp's pricing plans?",
        "answer": "We have three main pricing tiers: 1) Starter ($29/month, up to 100 members), 2) Professional ($79/month, up to 500 members), and 3) Enterprise (custom pricing for large organizations). Each plan includes different levels of features and support.",
        "category": "pricing"
    },
    {
        "question": "Is there a free trial available?",
        "answer": "Yes! HuddleUp offers a 14-day free trial with full access to all features. During the trial, our team helps configure your community structure and can assist with importing existing content and member lists if needed.",
        "category": "trial"
    },
    {
        "question": "Is HuddleUp an LMS or community platform?",
        "answer": "HuddleUp is primarily a community platform with learning management features, rather than a traditional LMS. It's built around member engagement and collaboration, emphasizing peer-to-peer knowledge sharing and flexible content types beyond just courses.",
        "category": "platform"
    },
    {
        "question": "What makes HuddleUp different from other platforms?",
        "answer": "HuddleUp is community-first, built around member engagement and collaboration. It emphasizes social learning through peer-to-peer knowledge sharing, supports flexible content types beyond courses, and can be member-driven with self-organizing communities.",
        "category": "platform"
    },
    {
        "question": "How do I get started with HuddleUp?",
        "answer": "Getting started is easy: 1) Schedule a 30-minute discovery call, 2) Start your 14-day free trial (same day setup), 3) Run a 2-4 week pilot program with a small group, 4) Gradually roll out to additional teams. We provide support throughout the process.",
        "category": "onboarding"
    },
    {
        "question": "What integrations does HuddleUp support?",
        "answer": "HuddleUp integrates with Slack & Microsoft Teams, Zoom & calendar apps, Google Workspace & Office 365, CRM systems, and SSO providers (SAML, OAuth, Active Directory). We also offer a REST API, webhooks, and Zapier connections to 5,000+ apps.",
        "category": "integrations"
    },
    {
        "question": "What kind of support do you provide?",
        "answer": "We offer comprehensive support including email support (all plans), live chat (Professional+ plans), phone support (Enterprise), onboarding specialists, account managers, weekly training sessions, help center, best practices guides, and video libraries.",
        "category": "support"
    },
    {
        "question": "Can HuddleUp improve our current workflow processes?",
        "answer": "Yes! HuddleUp enhances processes by adding collaboration layers rather than replacing what works. It helps with knowledge capture, cross-team collaboration, engagement analytics, and workflow automation to reduce manual tasks and break down silos between departments.",
        "category": "workflow"
    },
    {
        "question": "What features does HuddleUp offer?",
        "answer": "HuddleUp offers community management, content sharing, social learning tools, member engagement features, analytics and reporting, workflow automation, integrations with popular tools, mobile access, customizable branding, and advanced moderation tools.",
        "category": "features"
    },
    {
        "question": "Is HuddleUp suitable for remote teams?",
        "answer": "Absolutely! HuddleUp is designed to foster collaboration and knowledge sharing for distributed teams. It provides virtual spaces for team interaction, async communication tools, and integrates with remote work tools like Zoom and Slack.",
        "category": "remote"
    },
    {
        "question": "How secure is HuddleUp?",
        "answer": "HuddleUp prioritizes security with features like SSO integration, role-based permissions, data encryption in transit and at rest, regular security audits, GDPR compliance, and enterprise-grade infrastructure hosting.",
        "category": "security"
    },
    {
        "question": "Can we import existing content into HuddleUp?",
        "answer": "Yes, we can help you import existing content during the onboarding process. Our team assists with migrating documents, member lists, discussion threads, and other relevant content from your current platforms.",
        "category": "migration"
    },
    {
        "question": "What analytics and reporting does HuddleUp provide?",
        "answer": "HuddleUp provides engagement analytics, content performance metrics, member activity reports, community growth tracking, participation insights, and custom reporting options to help you understand what content resonates and drives participation.",
        "category": "analytics"
    },
    {
        "question": "Is there mobile access to HuddleUp?",
        "answer": "Yes, HuddleUp is fully responsive and works great on mobile devices. Members can access communities, participate in discussions, view content, and receive notifications on their smartphones and tablets.",
        "category": "mobile"
    }
]

# Sample document content for knowledge base
SAMPLE_DOCUMENTS = [
    {
        "title": "HuddleUp Platform Overview",
        "content": "HuddleUp is a comprehensive community platform that combines social networking with learning management capabilities. The platform is designed to foster engagement, knowledge sharing, and collaboration within organizations. Key features include community spaces, content management, member directories, discussion forums, event management, and integration capabilities. The platform serves various use cases including employee onboarding, professional development, knowledge sharing, project collaboration, and customer communities.",
        "category": "documentation",
        "document_type": "guide"
    },
    {
        "title": "Community Management Best Practices",
        "content": "Successful community management on HuddleUp involves several key practices: 1) Define clear community guidelines and objectives, 2) Encourage regular participation through engaging content, 3) Recognize and reward active members, 4) Facilitate connections between members with similar interests, 5) Monitor and respond to discussions promptly, 6) Use analytics to understand member behavior and preferences, 7) Regularly update and refresh content, 8) Create events and activities to boost engagement.",
        "category": "best_practices",
        "document_type": "guide"
    },
    {
        "title": "Integration Setup Guide",
        "content": "Setting up integrations with HuddleUp is straightforward. For Slack integration: navigate to Settings > Integrations > Slack, authenticate your Slack workspace, select channels to sync, configure notification preferences. For Microsoft Teams: go to Settings > Integrations > Teams, sign in with your Office 365 account, choose team channels, set up automated posting rules. For SSO: contact support to configure SAML or OAuth settings with your identity provider.",
        "category": "documentation",
        "document_type": "tutorial"
    },
    {
        "title": "Member Onboarding Checklist",
        "content": "Effective member onboarding includes: 1) Send welcome message with platform overview, 2) Provide access to essential communities and resources, 3) Complete profile setup including bio and interests, 4) Introduce new members to existing community members, 5) Share community guidelines and expectations, 6) Schedule initial check-in calls or meetings, 7) Provide training on key platform features, 8) Set up notification preferences, 9) Encourage first post or discussion participation.",
        "category": "onboarding",
        "document_type": "checklist"
    }
]

def populate_faqs():
    """Populate the database with sample FAQ entries including embeddings"""
    print("🔄 Starting FAQ population with embeddings...")
    
    try:
        semantic_service = SemanticSearchService()
        
        if not semantic_service.supabase:
            print("❌ Supabase connection not available")
            return
        
        if not semantic_service.embedding_service.available:
            print("❌ OpenAI embedding service not available")
            return
        
        success_count = 0
        error_count = 0
        
        for faq in SAMPLE_FAQS:
            try:
                result = semantic_service.add_faq_with_embedding(
                    question=faq["question"],
                    answer=faq["answer"],
                    category=faq["category"]
                )
                
                if result.get("success"):
                    success_count += 1
                    print(f"✅ Added FAQ: {faq['question'][:50]}...")
                else:
                    error_count += 1
                    print(f"❌ Failed to add FAQ: {result.get('error')}")
                    
            except Exception as e:
                error_count += 1
                print(f"❌ Error adding FAQ: {e}")
        
        print(f"\n📊 FAQ Population Summary:")
        print(f"✅ Successfully added: {success_count}")
        print(f"❌ Errors: {error_count}")
        
    except Exception as e:
        print(f"❌ Fatal error in FAQ population: {e}")

def populate_documents():
    """Populate the database with sample documents"""
    print("\n🔄 Starting document population...")
    
    try:
        semantic_service = SemanticSearchService()
        
        if not semantic_service.supabase:
            print("❌ Supabase connection not available")
            return
        
        success_count = 0
        error_count = 0
        
        for doc in SAMPLE_DOCUMENTS:
            try:
                # Insert document into the documents table
                doc_result = semantic_service.supabase.table('documents').insert({
                    'title': doc['title'],
                    'content': doc['content'],
                    'category': doc['category'],
                    'document_type': doc['document_type'],
                    'metadata': {}
                }).execute()
                
                if doc_result.data:
                    document_id = doc_result.data[0]['id']
                    
                    # Create document chunks with embeddings if embedding service is available
                    if semantic_service.embedding_service.available:
                        # Split content into chunks (simple splitting by sentences)
                        sentences = doc['content'].split('. ')
                        chunks = []
                        current_chunk = ""
                        
                        for sentence in sentences:
                            if len(current_chunk) + len(sentence) > 500:  # Chunk size limit
                                if current_chunk:
                                    chunks.append(current_chunk.strip())
                                current_chunk = sentence
                            else:
                                current_chunk += sentence + ". " if not current_chunk else " " + sentence + "."
                        
                        if current_chunk:
                            chunks.append(current_chunk.strip())
                        
                        # Generate embeddings for chunks
                        for i, chunk in enumerate(chunks):
                            try:
                                embedding = semantic_service.embedding_service.get_embedding(chunk)
                                
                                chunk_result = semantic_service.supabase.table('document_chunks').insert({
                                    'document_id': document_id,
                                    'chunk_text': chunk,
                                    'chunk_index': i,
                                    'chunk_embedding': embedding,
                                    'metadata': {'chunk_size': len(chunk)}
                                }).execute()
                                
                                if chunk_result.data:
                                    print(f"  ✅ Added chunk {i+1}/{len(chunks)}")
                                    
                            except Exception as chunk_error:
                                print(f"  ❌ Error adding chunk {i+1}: {chunk_error}")
                    
                    success_count += 1
                    print(f"✅ Added document: {doc['title']}")
                    
            except Exception as e:
                error_count += 1
                print(f"❌ Error adding document '{doc['title']}': {e}")
        
        print(f"\n📊 Document Population Summary:")
        print(f"✅ Successfully added: {success_count}")
        print(f"❌ Errors: {error_count}")
        
    except Exception as e:
        print(f"❌ Fatal error in document population: {e}")

def check_database_setup():
    """Check if the database tables and functions are set up correctly"""
    print("🔍 Checking database setup...")
    
    try:
        semantic_service = SemanticSearchService()
        
        if not semantic_service.supabase:
            print("❌ Supabase connection not available")
            return False
        
        # Check if required tables exist
        tables_to_check = ['faq_entries', 'documents', 'document_chunks', 'chat_messages']
        
        for table in tables_to_check:
            try:
                result = semantic_service.supabase.table(table).select('*').limit(1).execute()
                print(f"✅ Table '{table}' exists and accessible")
            except Exception as e:
                print(f"❌ Table '{table}' issue: {e}")
                return False
        
        # Test embedding generation
        if semantic_service.embedding_service.available:
            try:
                test_embedding = semantic_service.embedding_service.get_embedding("test")
                if test_embedding and len(test_embedding) == 1536:
                    print("✅ OpenAI embedding service working (1536 dimensions)")
                else:
                    print(f"⚠️ Embedding dimension issue: {len(test_embedding) if test_embedding else 'None'}")
            except Exception as e:
                print(f"❌ Embedding service issue: {e}")
        else:
            print("❌ OpenAI embedding service not available")
            
        return True
        
    except Exception as e:
        print(f"❌ Database setup check failed: {e}")
        return False

def main():
    """Main function to run the data population script"""
    print("🚀 HuddleUp Data Population Script")
    print("=" * 50)
    
    # Check environment variables
    required_vars = ['SUPABASE_URL', 'SUPABASE_KEY', 'OPENAI_API_KEY']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please set these in your .env file and try again.")
        return
    
    print("✅ Environment variables loaded")
    
    # Check database setup
    if not check_database_setup():
        print("\n❌ Database setup issues detected. Please:")
        print("1. Run the SQL schema from 'supabase_embeddings_setup.sql' in your Supabase SQL editor")
        print("2. Ensure all environment variables are correct")
        print("3. Check your Supabase project status")
        return
    
    print("\n" + "=" * 50)
    
    # Ask user what to populate
    print("What would you like to populate?")
    print("1. FAQ entries with embeddings")
    print("2. Documents with chunk embeddings")
    print("3. Both FAQs and documents")
    print("4. Exit")
    
    try:
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == '1':
            populate_faqs()
        elif choice == '2':
            populate_documents()
        elif choice == '3':
            populate_faqs()
            populate_documents()
        elif choice == '4':
            print("👋 Exiting...")
            return
        else:
            print("❌ Invalid choice. Please run the script again.")
            return
            
        print("\n🎉 Data population completed!")
        print("Your HuddleUp knowledge base is now ready for semantic search.")
        
    except KeyboardInterrupt:
        print("\n👋 Operation cancelled by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()