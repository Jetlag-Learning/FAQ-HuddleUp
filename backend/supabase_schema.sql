-- HuddleUp FAQ Database Schema Setup
-- Run this in your Supabase SQL Editor

-- Enable the vector extension for embeddings
CREATE EXTENSION IF NOT EXISTS vector;

-- Create the faq_entries table
CREATE TABLE IF NOT EXISTS public.faq_entries (
    id BIGSERIAL PRIMARY KEY,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    category VARCHAR(100),
    tags TEXT[],
    embedding vector(1536), -- OpenAI embedding dimension
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()),
    is_active BOOLEAN DEFAULT true
);

-- Create the knowledge_base table for additional context
CREATE TABLE IF NOT EXISTS public.knowledge_base (
    id BIGSERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    category VARCHAR(100),
    tags TEXT[],
    embedding vector(1536),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()),
    is_active BOOLEAN DEFAULT true
);

-- Create the chat_messages table for conversation history
CREATE TABLE IF NOT EXISTS public.chat_messages (
    id BIGSERIAL PRIMARY KEY,
    user_id VARCHAR(255),
    user_email VARCHAR(255),
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    question_embedding vector(1536),
    context_used JSONB,
    response_time_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS faq_entries_embedding_idx ON public.faq_entries USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS knowledge_base_embedding_idx ON public.knowledge_base USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS chat_messages_embedding_idx ON public.chat_messages USING ivfflat (question_embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS faq_entries_category_idx ON public.faq_entries(category);
CREATE INDEX IF NOT EXISTS knowledge_base_category_idx ON public.knowledge_base(category);
CREATE INDEX IF NOT EXISTS chat_messages_created_at_idx ON public.chat_messages(created_at);

-- Create the semantic search function
CREATE OR REPLACE FUNCTION public.search_knowledge_base_semantic(
    query_embedding vector(1536),
    similarity_threshold float DEFAULT 0.7,
    faq_limit int DEFAULT 5,
    doc_limit int DEFAULT 3
)
RETURNS TABLE (
    source_type text,
    id bigint,
    title text,
    content text,
    category text,
    similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    (
        -- Search FAQ entries
        SELECT 
            'faq'::text as source_type,
            f.id,
            f.question as title,
            f.answer as content,
            f.category,
            (1 - (f.embedding <=> query_embedding))::float as similarity
        FROM public.faq_entries f
        WHERE f.is_active = true
            AND f.embedding IS NOT NULL
            AND (1 - (f.embedding <=> query_embedding)) >= similarity_threshold
        ORDER BY f.embedding <=> query_embedding
        LIMIT faq_limit
    )
    UNION ALL
    (
        -- Search knowledge base
        SELECT 
            'knowledge'::text as source_type,
            k.id,
            k.title,
            k.content,
            k.category,
            (1 - (k.embedding <=> query_embedding))::float as similarity
        FROM public.knowledge_base k
        WHERE k.is_active = true
            AND k.embedding IS NOT NULL
            AND (1 - (k.embedding <=> query_embedding)) >= similarity_threshold
        ORDER BY k.embedding <=> query_embedding
        LIMIT doc_limit
    )
    ORDER BY similarity DESC;
END;
$$;

-- Insert sample FAQ data
INSERT INTO public.faq_entries (question, answer, category, tags) VALUES
('What is HuddleUp?', 'HuddleUp is a community-first platform that transforms how organizations share knowledge, collaborate, and grow together. It combines the best aspects of Learning Management Systems (LMS) with community engagement features.', 'general', ARRAY['platform', 'overview']),
('How much does HuddleUp cost?', 'HuddleUp offers flexible pricing plans: Starter Plan at $29/month for up to 100 members, Professional Plan at $79/month for up to 500 members, and Enterprise Plan with custom pricing for larger organizations.', 'pricing', ARRAY['cost', 'plans']),
('What makes HuddleUp different from other LMS platforms?', 'Unlike traditional LMS platforms, HuddleUp is community-first, emphasizing peer-to-peer collaboration, social learning, and member engagement rather than just content consumption.', 'features', ARRAY['comparison', 'lms']),
('Can HuddleUp integrate with our existing tools?', 'Yes, HuddleUp supports various integrations and can enhance your current workflows with collaboration layers and automation capabilities.', 'integrations', ARRAY['tools', 'workflow']),
('How do we get started with HuddleUp?', 'Getting started is easy! Contact our team for a demo, choose your plan, and we''ll help you set up your community with onboarding support and training.', 'getting-started', ARRAY['setup', 'onboarding']);

-- Insert sample knowledge base content
INSERT INTO public.knowledge_base (title, content, category, tags) VALUES
('Platform Features Overview', 'HuddleUp includes structured learning capabilities, progress tracking, content sharing, member engagement tools, and advanced analytics. Our platform supports various content types including courses, discussions, resources, and collaborative projects.', 'features', ARRAY['overview', 'capabilities']),
('Community Management Best Practices', 'Effective community management involves regular engagement, content curation, member recognition, and fostering peer-to-peer interactions. Set clear guidelines, encourage participation, and celebrate member achievements.', 'best-practices', ARRAY['management', 'engagement']),
('Integration Capabilities', 'HuddleUp integrates with popular tools like Slack, Microsoft Teams, Google Workspace, Zoom, and various CRM systems. API access is available for custom integrations.', 'integrations', ARRAY['api', 'tools']);

-- Create a function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION public.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = timezone('utc'::text, now());
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers to automatically update the updated_at column
CREATE TRIGGER update_faq_entries_updated_at BEFORE UPDATE ON public.faq_entries
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER update_knowledge_base_updated_at BEFORE UPDATE ON public.knowledge_base
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

-- Enable RLS (Row Level Security) - optional but recommended
ALTER TABLE public.faq_entries ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.knowledge_base ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.chat_messages ENABLE ROW LEVEL SECURITY;

-- Create policies for public read access (adjust as needed for your security requirements)
CREATE POLICY "Allow public read access on faq_entries" ON public.faq_entries
    FOR SELECT USING (is_active = true);

CREATE POLICY "Allow public read access on knowledge_base" ON public.knowledge_base
    FOR SELECT USING (is_active = true);

-- Create policies for service role (your backend) to have full access
CREATE POLICY "Allow service role full access on faq_entries" ON public.faq_entries
    USING (auth.role() = 'service_role');

CREATE POLICY "Allow service role full access on knowledge_base" ON public.knowledge_base
    USING (auth.role() = 'service_role');

CREATE POLICY "Allow service role full access on chat_messages" ON public.chat_messages
    USING (auth.role() = 'service_role');