# HuddleUp FAQ Chat Widget

A complete FAQ chatbot solution with React frontend and Python FastAPI backend, integrated with Supabase database and OpenAI API.

## Features

- 🤖 **AI-Powered Responses**: Uses OpenAI GPT-3.5-turbo for intelligent FAQ responses
- 💬 **Interactive Chat Widget**: Modern, responsive chat interface with floating widget
- 🗄️ **Database Storage**: Stores FAQs and chat history in Supabase
- 🔍 **Smart Search**: Searches existing FAQs to provide relevant context to AI
- 🎨 **Modern UI**: Built with React, TypeScript, and Tailwind CSS
- 🌐 **REST API**: FastAPI backend with automatic OpenAPI documentation
- 📱 **Responsive Design**: Works on desktop and mobile devices

## Project Structure

```
FAQ-HuddleUp/
├── frontend/                 # React TypeScript application
│   ├── src/
│   │   ├── components/      # React components
│   │   │   └── ChatWidget.tsx
│   │   ├── services/        # API services
│   │   │   └── chatService.ts
│   │   ├── types/           # TypeScript types
│   │   │   └── chat.ts
│   │   └── App.tsx
│   ├── public/
│   └── package.json
├── backend/                  # Python FastAPI application
│   ├── main.py              # FastAPI application
│   ├── models.py            # Pydantic models
│   ├── database.py          # Supabase database service
│   ├── openai_service.py    # OpenAI integration
│   ├── database_schema.sql  # Supabase schema
│   ├── sample_data.sql      # Sample FAQ data
│   ├── requirements.txt     # Python dependencies
│   └── .env                 # Environment variables
└── README.md
```

## Setup Instructions

### Prerequisites

- Node.js 16+ and npm
- Python 3.8+
- Supabase account
- OpenAI API key

### Backend Setup

1. **Navigate to backend directory:**

   ```bash
   cd backend
   ```

2. **Install Python dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables:**

   Update `.env` file with your credentials:

   ```env
   SUPABASE_URL=your_supabase_project_url
   SUPABASE_KEY=your_supabase_anon_key
   OPENAI_API_KEY=your_openai_api_key
   HOST=localhost
   PORT=8000
   DEBUG=True
   ```

4. **Set up Supabase database:**

   In your Supabase SQL editor, run:

   ```sql
   -- Run database_schema.sql first
   -- Then run sample_data.sql for demo data
   ```

5. **Start the backend server:**

   ```bash
   python main.py
   ```

   The API will be available at `http://localhost:8000`

   API Documentation: `http://localhost:8000/docs`

### Frontend Setup

1. **Navigate to frontend directory:**

   ```bash
   cd frontend
   ```

2. **Install dependencies:**

   ```bash
   npm install
   ```

3. **Configure environment (optional):**

   The `.env` file is already configured for local development:

   ```env
   REACT_APP_API_URL=http://localhost:8000
   ```

4. **Start the React development server:**

   ```bash
   npm start
   ```

   The application will open at `http://localhost:3000`

## API Endpoints

### Main Endpoints

- **POST** `/api/faq/ask` - Send a question and get AI response
- **GET** `/api/faq/entries` - Get all FAQ entries
- **POST** `/api/faq/entries` - Create new FAQ entry
- **GET** `/api/faq/search?q=query` - Search FAQ entries

### Example Usage

```javascript
// Send a question
const response = await fetch("http://localhost:8000/api/faq/ask", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ question: "How much does HuddleUp cost?" }),
});

const data = await response.json();
console.log(data.answer); // AI-generated response
```

## Configuration

### Supabase Setup

1. Create a new Supabase project
2. Run the SQL schema from `backend/database_schema.sql`
3. Optionally run `backend/sample_data.sql` for demo data
4. Get your project URL and anon key from Settings > API

### OpenAI Setup

1. Create an OpenAI account
2. Generate an API key from the API section
3. Add the key to your `.env` file

### Environment Variables

**Backend (.env):**

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
OPENAI_API_KEY=sk-your-openai-key
PINECONE_API_KEY=your-pinecone-api-key
PINECONE_ENVIRONMENT=your-pinecone-environment
PINECONE_INDEX_NAME=huddleup-faq
GOOGLE_CLIENT_ID=your-google-oauth-client-id.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-oauth-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/google/callback
GOOGLE_CALENDAR_ID=primary
HOST=localhost
PORT=8000
DEBUG=True
```

**Frontend (.env):**

```env
REACT_APP_API_URL=http://localhost:8000
```

### Google Calendar Integration Setup

The HuddleUp FAQ system includes optional Google Calendar integration that allows users to schedule meetings with automatic Google Meet links. This feature requires Google OAuth2 setup.

#### Step 1: Google Cloud Console Setup

1. **Create/Select Project:**

   - Go to [Google Cloud Console](https://console.cloud.google.com)
   - Create a new project or select an existing one
   - Note your project ID

2. **Enable Google Calendar API:**

   - Navigate to "APIs & Services" > "Library"
   - Search for "Google Calendar API"
   - Click "Enable"

3. **Create OAuth 2.0 Credentials:**
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth 2.0 Client IDs"
   - Choose "Web application"
   - Add these authorized redirect URIs:
     - `http://localhost:8000/auth/google/callback` (development)
     - `https://yourdomain.com/auth/google/callback` (production)
   - Copy the Client ID and Client Secret

#### Step 2: Environment Configuration

Add the Google Calendar credentials to your `.env` file:

```env
GOOGLE_CLIENT_ID=your-client-id.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/google/callback
GOOGLE_CALENDAR_ID=primary
```

#### Step 3: Authentication Flow

1. **Start the Backend:**

   ```bash
   cd backend
   python main.py
   ```

2. **Connect Google Calendar:**

   - Make a GET request to `/api/calendar/auth` to get the authorization URL
   - Visit the URL to grant calendar permissions
   - The system will automatically handle the OAuth callback

3. **Verify Connection:**
   - Check `/api/calendar/status` to confirm the connection
   - The system will show "connected: true" when ready

#### Step 4: Using Calendar Features

Once connected, the system provides:

- **Automatic Meeting Creation:** When users click "Meet" button, calendar events are created
- **Google Meet Links:** Each meeting automatically includes a Google Meet video link
- **Email Invitations:** Attendees receive calendar invites with meeting details
- **Availability Checking:** System can check Derek's calendar for free time slots
- **Quick Booking:** Pre-generated time slots for easy scheduling

#### API Endpoints

- `GET /api/calendar/auth` - Get OAuth authorization URL
- `POST /api/calendar/callback` - Handle OAuth callback
- `GET /api/calendar/status` - Check connection status
- `POST /api/calendar/meeting` - Create meeting with Google Meet link
- `GET /api/calendar/availability` - Check calendar availability
- `GET /api/calendar/quick-slots` - Get suggested meeting times

#### Optional Configuration

If Google Calendar is not configured, the system gracefully falls back to:

- Email contact information
- Manual scheduling instructions
- Direct contact details

The chat experience remains fully functional without calendar integration.

## Features in Detail

### Chat Widget

- Floating chat button in bottom-right corner
- Minimizable chat window
- Real-time typing indicators
- Message history with timestamps
- Error handling and fallback responses

### AI Integration

- Uses OpenAI GPT-3.5-turbo model
- Contextual responses based on existing FAQs
- Identifies process improvement questions
- Fallback responses when API is unavailable

### Database Schema

- **faq_entries**: Stores FAQ questions, answers, categories, and keywords
- **chat_messages**: Logs all chat interactions for analytics
- Full-text search capabilities
- Proper indexing for performance

## Demo FAQ Topics

The system comes with sample FAQs covering:

- ✅ **Pricing and Plans**: Cost structure and plan comparisons
- ✅ **Platform Type**: LMS vs Community platform explanation
- ✅ **Process Improvement**: How HuddleUp enhances current workflows
- ✅ **Use Cases**: Common implementation scenarios
- ✅ **Getting Started**: Implementation and onboarding process
- ✅ **Integrations**: Tool compatibility and API connections
- ✅ **Support**: Customer service and training options
- ✅ **Knowledge Management**: Improving organizational knowledge sharing

## Customization

### Adding New FAQs

Use the admin endpoint or add directly to Supabase:

```sql
INSERT INTO faq_entries (question, answer, category, keywords) VALUES
('Your question', 'Your answer', 'category', '["keyword1", "keyword2"]');
```

### Styling

The frontend uses Tailwind CSS. Customize the chat widget appearance in:

- `frontend/src/components/ChatWidget.tsx`
- `frontend/tailwind.config.js`

### AI Behavior

Modify the AI system prompt in:

- `backend/openai_service.py` - `generate_faq_response()` method

## Troubleshooting

### Common Issues

1. **CORS Errors**: Ensure backend CORS is configured for frontend URL
2. **Database Connection**: Verify Supabase credentials and network access
3. **OpenAI Errors**: Check API key and billing status
4. **Port Conflicts**: Ensure ports 3000 and 8000 are available

### Logs

- Backend logs appear in terminal where `python main.py` is running
- Frontend errors appear in browser developer console
- Supabase logs available in dashboard

## Production Deployment

### Backend Deployment

1. Set production environment variables
2. Use a production WSGI server like Gunicorn
3. Configure proper CORS origins
4. Set up monitoring and logging

### Frontend Deployment

1. Build the production version: `npm run build`
2. Serve static files with a web server
3. Update `REACT_APP_API_URL` to production backend URL

## License

MIT License - feel free to use and modify for your needs.

## Support

For questions or issues:

- Check the FastAPI docs at `/docs` endpoint
- Review Supabase dashboard for database issues
- Check OpenAI usage and billing in OpenAI dashboard
