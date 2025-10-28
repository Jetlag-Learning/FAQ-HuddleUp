-- Enhanced Supabase schema for embeddings-based FAQ system
-- Run this in your Supabase SQL editor

-- Enable the vector extension for embeddings
CREATE EXTENSION IF NOT EXISTS vector;

-- Create FAQ entries table with embedding support
CREATE TABLE IF NOT EXISTS faq_entries (
    id BIGSERIAL PRIMARY KEY,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    category VARCHAR(100) NOT NULL DEFAULT 'general',
    keywords JSONB DEFAULT '[]'::jsonb,
    question_embedding vector(1536), -- OpenAI ada-002 embeddings are 1536 dimensions
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create embeddings table for document chunks (enhance existing)
-- This will work alongside your existing document_chunks table
CREATE TABLE IF NOT EXISTS document_embeddings (
    id BIGSERIAL PRIMARY KEY,
    document_id BIGINT REFERENCES documents(id) ON DELETE CASCADE,
    chunk_id BIGINT REFERENCES document_chunks(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    embedding vector(1536),
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create chat messages table with embedding support
CREATE TABLE IF NOT EXISTS chat_messages (
    id BIGSERIAL PRIMARY KEY,
    session_id UUID NOT NULL DEFAULT gen_random_uuid(),
    user_message TEXT NOT NULL,
    user_message_embedding vector(1536),
    bot_response TEXT NOT NULL,
    knowledge_sources JSONB DEFAULT '{}'::jsonb,
    similarity_scores JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for vector similarity search
CREATE INDEX IF NOT EXISTS idx_faq_entries_embedding ON faq_entries 
USING ivfflat (question_embedding vector_cosine_ops) WITH (lists = 100);

CREATE INDEX IF NOT EXISTS idx_document_embeddings_embedding ON document_embeddings 
USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

CREATE INDEX IF NOT EXISTS idx_chat_messages_embedding ON chat_messages 
USING ivfflat (user_message_embedding vector_cosine_ops) WITH (lists = 100);

-- Create function for semantic search across FAQ entries
CREATE OR REPLACE FUNCTION search_faq_semantic(
    query_embedding vector(1536),
    similarity_threshold float DEFAULT 0.7,
    match_count int DEFAULT 5
)
RETURNS TABLE (
    id bigint,
    question text,
    answer text,
    category varchar,
    similarity float
) 
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        faq_entries.id,
        faq_entries.question,
        faq_entries.answer,
        faq_entries.category,
        1 - (faq_entries.question_embedding <=> query_embedding) AS similarity
    FROM faq_entries
    WHERE 1 - (faq_entries.question_embedding <=> query_embedding) > similarity_threshold
    ORDER BY faq_entries.question_embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- Create function for semantic search across document embeddings
CREATE OR REPLACE FUNCTION search_documents_semantic(
    query_embedding vector(1536),
    similarity_threshold float DEFAULT 0.7,
    match_count int DEFAULT 5
)
RETURNS TABLE (
    document_id bigint,
    chunk_id bigint,
    content text,
    metadata jsonb,
    similarity float
) 
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        de.document_id,
        de.chunk_id,
        de.content,
        de.metadata,
        1 - (de.embedding <=> query_embedding) AS similarity
    FROM document_embeddings de
    WHERE 1 - (de.embedding <=> query_embedding) > similarity_threshold
    ORDER BY de.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- Create comprehensive semantic search function
CREATE OR REPLACE FUNCTION search_knowledge_base_semantic(
    query_embedding vector(1536),
    similarity_threshold float DEFAULT 0.7,
    faq_limit int DEFAULT 3,
    doc_limit int DEFAULT 5
)
RETURNS TABLE (
    source_type text,
    content_id bigint,
    title text,
    content text,
    similarity float,
    metadata jsonb
) 
LANGUAGE plpgsql
AS $$
BEGIN
    -- Return FAQ results
    RETURN QUERY
    SELECT 
        'faq'::text AS source_type,
        f.id AS content_id,
        f.question AS title,
        f.answer AS content,
        1 - (f.question_embedding <=> query_embedding) AS similarity,
        jsonb_build_object('category', f.category) AS metadata
    FROM faq_entries f
    WHERE 1 - (f.question_embedding <=> query_embedding) > similarity_threshold
    ORDER BY f.question_embedding <=> query_embedding
    LIMIT faq_limit;
    
    -- Return document results
    RETURN QUERY
    SELECT 
        'document'::text AS source_type,
        de.document_id AS content_id,
        COALESCE(d.title, 'Untitled Document') AS title,
        de.content AS content,
        1 - (de.embedding <=> query_embedding) AS similarity,
        de.metadata
    FROM document_embeddings de
    LEFT JOIN documents d ON de.document_id = d.id
    WHERE 1 - (de.embedding <=> query_embedding) > similarity_threshold
    ORDER BY de.embedding <=> query_embedding
    LIMIT doc_limit;
END;
$$;

-- Create RLS policies
ALTER TABLE faq_entries ENABLE ROW LEVEL SECURITY;
ALTER TABLE document_embeddings ENABLE ROW LEVEL SECURITY;
ALTER TABLE chat_messages ENABLE ROW LEVEL SECURITY;

-- Create policies for public access (adjust based on your security requirements)
CREATE POLICY "Allow public read access on faq_entries" ON faq_entries
    FOR SELECT USING (true);

CREATE POLICY "Allow public insert on faq_entries" ON faq_entries
    FOR INSERT WITH CHECK (true);

CREATE POLICY "Allow public read access on document_embeddings" ON document_embeddings
    FOR SELECT USING (true);

CREATE POLICY "Allow public insert on document_embeddings" ON document_embeddings
    FOR INSERT WITH CHECK (true);

CREATE POLICY "Allow public insert on chat_messages" ON chat_messages
    FOR INSERT WITH CHECK (true);

CREATE POLICY "Allow public read access on chat_messages" ON chat_messages
    FOR SELECT USING (true);

-- Insert sample FAQ entries (these will need embeddings generated)
INSERT INTO faq_entries (question, answer, category, keywords) VALUES 
(
    'How much does HuddleUp cost and what are the pricing plans?',
    'HuddleUp offers flexible pricing plans designed for organizations of all sizes:

• **Starter Plan**: $29/month for up to 100 members
  - Core community features
  - Basic content sharing and discussions
  - Member management tools
  - Email support

• **Professional Plan**: $79/month for up to 500 members  
  - Everything in Starter
  - Advanced analytics and reporting
  - Custom branding options
  - Integration capabilities
  - Priority support

• **Enterprise Plan**: Custom pricing for larger organizations
  - Everything in Professional
  - Single Sign-On (SSO)
  - Advanced security features
  - Dedicated account manager
  - Custom integrations and white-label options

All plans include a 14-day free trial. Contact our sales team for volume discounts and custom enterprise solutions.',
    'pricing',
    '["cost", "price", "pricing", "plans", "subscription", "starter", "professional", "enterprise", "money", "fee", "trial"]'::jsonb
),

(
    'Is HuddleUp a Learning Management System or a Community platform?',
    'HuddleUp is primarily a **community-first platform** with integrated learning management features, rather than a traditional LMS.

**Community Platform Characteristics:**
🤝 **Member Engagement**: Built around fostering connections between members
📚 **Peer-to-Peer Learning**: Emphasizes knowledge sharing between community members
🔄 **Flexible Content**: Supports discussions, resources, events, and collaborative projects
👥 **Self-Organizing**: Communities can evolve organically with member-generated content

**vs Traditional LMS:**
- **Traditional LMS**: Course-focused, instructor-led, structured learning paths
- **HuddleUp**: Community-focused, peer-driven, organic knowledge sharing

**Best Use Cases:**
- Professional communities and associations
- Internal company knowledge sharing
- Member organizations building engagement
- Teams capturing and sharing tribal knowledge
- Cross-functional collaboration initiatives

Think of HuddleUp as where community engagement meets learning - combining the social aspects of platforms like Slack with the knowledge management capabilities of modern learning systems.',
    'platform',
    '["LMS", "community", "platform", "learning", "management", "social", "collaboration", "engagement", "peer-to-peer"]'::jsonb
),

(
    'How can HuddleUp improve our current business processes and workflows?',
    'HuddleUp is designed to **enhance** rather than replace your existing processes through strategic integration and collaboration layers:

**🔄 Process Integration Benefits:**
- **Workflow Enhancement**: Adds collaborative elements to existing systems
- **Tool Compatibility**: Works alongside your current software stack
- **Gradual Adoption**: Can be implemented incrementally without disruption

**📚 Knowledge Management Revolution:**
- **Tribal Knowledge Capture**: Transforms undocumented expertise into searchable resources
- **Living Documentation**: Community-maintained content that stays current
- **Cross-Department Visibility**: Breaks down information silos between teams

**📈 Measurable Improvements:**
- **Engagement Analytics**: Track what content drives participation and results
- **Knowledge Sharing Metrics**: Measure how information flows through your organization
- **Process Optimization**: Identify bottlenecks and improvement opportunities

**⚡ Automation & Efficiency:**
- **Smart Notifications**: Relevant updates without information overload
- **Workflow Automation**: Reduce manual knowledge transfer tasks
- **Onboarding Acceleration**: New team members get up to speed faster

**Typical ROI Improvements:**
- 60% reduction in "Where do I find..." questions
- 40% faster onboarding for new team members  
- 85% of tribal knowledge captured and made searchable
- 50% reduction in duplicate work across departments

**To provide specific recommendations for your organization:**
- What tools do you currently use for collaboration?
- How do you share knowledge and best practices now?
- What are your biggest process bottlenecks?
- What would success look like for your team?',
    'improvement',
    '["processes", "workflow", "current", "improve", "enhance", "integration", "knowledge", "management", "efficiency", "automation"]'::jsonb
)

ON CONFLICT DO NOTHING;