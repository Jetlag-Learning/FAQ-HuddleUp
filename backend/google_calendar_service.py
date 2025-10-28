"""
Google Calendar Integration Service for HuddleUp FAQ System

This service handles:
- Google OAuth2 authentication
- Calendar event creation with Google Meet links
- Availability checking
- Meeting scheduling automation

Setup Requirements:
1. Google Cloud Console project with Calendar API enabled
2. OAuth2 credentials (client_id, client_secret)
3. Authorized redirect URIs configured
4. Environment variables set in .env file
"""

import os
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import pickle
from pathlib import Path

class GoogleCalendarService:
    """Google Calendar integration service with OAuth2 and Meet link generation"""
    
    # OAuth2 scopes required for calendar and meet functionality
    SCOPES = [
        'https://www.googleapis.com/auth/calendar',
        'https://www.googleapis.com/auth/calendar.events'
    ]
    
    def __init__(self):
        """Initialize the Google Calendar service"""
        # Load configuration from environment
        self.client_id = os.getenv("GOOGLE_CLIENT_ID")
        self.client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
        self.redirect_uri = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/google/callback")
        self.calendar_id = os.getenv("GOOGLE_CALENDAR_ID", "primary")  # Derek's calendar
        
        # Service state
        self.service = None
        self.credentials = None
        self.token_file = "token.pickle"
        
        # Initialize service if credentials are available
        self._initialize_service()
        
        print(f"🗓️ Google Calendar Service initialized")
        print(f"   Client ID configured: {'✅' if self.client_id else '❌'}")
        print(f"   Calendar ID: {self.calendar_id}")
        print(f"   Redirect URI: {self.redirect_uri}")
    
    def _initialize_service(self) -> None:
        """Initialize the Google Calendar service with stored or new credentials"""
        try:
            # Load existing credentials if available
            if os.path.exists(self.token_file):
                with open(self.token_file, 'rb') as token:
                    self.credentials = pickle.load(token)
            
            # If credentials are valid, build the service
            if self.credentials and self.credentials.valid:
                self.service = build('calendar', 'v3', credentials=self.credentials)
                print("✅ Google Calendar service ready with existing credentials")
            elif self.credentials and self.credentials.expired and self.credentials.refresh_token:
                # Refresh expired credentials
                self.credentials.refresh(Request())
                self.service = build('calendar', 'v3', credentials=self.credentials)
                self._save_credentials()
                print("✅ Google Calendar service ready with refreshed credentials")
            else:
                print("⚠️ Google Calendar service requires authentication")
                
        except Exception as e:
            print(f"⚠️ Could not initialize Google Calendar service: {e}")
            self.service = None
    
    def _save_credentials(self) -> None:
        """Save credentials to file for future use"""
        try:
            with open(self.token_file, 'wb') as token:
                pickle.dump(self.credentials, token)
            print("💾 Google Calendar credentials saved")
        except Exception as e:
            print(f"⚠️ Could not save credentials: {e}")
    
    def get_authorization_url(self) -> str:
        """Generate OAuth2 authorization URL for user consent"""
        if not self.client_id or not self.client_secret:
            raise Exception("Google OAuth2 credentials not configured")
        
        # Create OAuth2 flow
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [self.redirect_uri]
                }
            },
            scopes=self.SCOPES
        )
        flow.redirect_uri = self.redirect_uri
        
        # Generate authorization URL
        auth_url, _ = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'  # Force consent to get refresh token
        )
        
        return auth_url
    
    def handle_oauth_callback(self, authorization_code: str) -> Dict[str, Any]:
        """Handle OAuth2 callback and exchange code for credentials"""
        try:
            if not self.client_id or not self.client_secret:
                raise Exception("Google OAuth2 credentials not configured")
            
            # Create OAuth2 flow
            flow = Flow.from_client_config(
                {
                    "web": {
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": [self.redirect_uri]
                    }
                },
                scopes=self.SCOPES
            )
            flow.redirect_uri = self.redirect_uri
            
            # Exchange authorization code for credentials
            flow.fetch_token(code=authorization_code)
            self.credentials = flow.credentials
            
            # Initialize the service
            self.service = build('calendar', 'v3', credentials=self.credentials)
            
            # Save credentials for future use
            self._save_credentials()
            
            return {
                "success": True,
                "message": "Google Calendar connected successfully",
                "calendar_id": self.calendar_id
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"OAuth callback failed: {str(e)}"
            }
    
    def is_authenticated(self) -> bool:
        """Check if the service is properly authenticated"""
        return self.service is not None and self.credentials is not None and self.credentials.valid
    
    def create_meeting_event(self, 
                           title: str,
                           description: str,
                           start_time: datetime,
                           duration_minutes: int = 30,
                           attendee_email: Optional[str] = None,
                           include_meet_link: bool = True) -> Dict[str, Any]:
        """
        Create a calendar event with optional Google Meet link
        
        Args:
            title: Event title
            description: Event description
            start_time: Event start time
            duration_minutes: Event duration in minutes
            attendee_email: Optional attendee email
            include_meet_link: Whether to include Google Meet link
            
        Returns:
            Dict with event details or error information
        """
        if not self.is_authenticated():
            return {
                "success": False,
                "error": "Google Calendar not authenticated. Please connect your account first.",
                "auth_url": self.get_authorization_url() if self.client_id else None
            }
        
        try:
            # Calculate end time
            end_time = start_time + timedelta(minutes=duration_minutes)
            
            # Build event object
            event = {
                'summary': title,
                'description': description,
                'start': {
                    'dateTime': start_time.isoformat(),
                    'timeZone': 'America/New_York',  # Derek's timezone - make configurable
                },
                'end': {
                    'dateTime': end_time.isoformat(),
                    'timeZone': 'America/New_York',
                },
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'email', 'minutes': 24 * 60},  # 1 day before
                        {'method': 'popup', 'minutes': 15},       # 15 minutes before
                    ],
                },
            }
            
            # Add attendees if provided
            if attendee_email:
                event['attendees'] = [
                    {'email': attendee_email, 'responseStatus': 'needsAction'}
                ]
            
            # Add Google Meet link if requested
            if include_meet_link:
                event['conferenceData'] = {
                    'createRequest': {
                        'requestId': f"meet_{int(datetime.now().timestamp())}",
                        'conferenceSolutionKey': {'type': 'hangoutsMeet'}
                    }
                }
            
            # Create the event
            event_result = self.service.events().insert(
                calendarId=self.calendar_id,
                body=event,
                conferenceDataVersion=1 if include_meet_link else 0,
                sendUpdates='all' if attendee_email else 'none'
            ).execute()
            
            # Extract important information
            result = {
                "success": True,
                "event_id": event_result['id'],
                "event_url": event_result.get('htmlLink'),
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "title": title,
                "description": description
            }
            
            # Add Google Meet link if available
            if include_meet_link and 'conferenceData' in event_result:
                conference_data = event_result['conferenceData']
                if 'entryPoints' in conference_data:
                    for entry_point in conference_data['entryPoints']:
                        if entry_point.get('entryPointType') == 'video':
                            result['meet_link'] = entry_point.get('uri')
                            break
            
            print(f"✅ Calendar event created: {title} at {start_time}")
            return result
            
        except HttpError as error:
            print(f"❌ Google Calendar API error: {error}")
            return {
                "success": False,
                "error": f"Calendar API error: {error}"
            }
        except Exception as e:
            print(f"❌ Unexpected error creating calendar event: {e}")
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}"
            }
    
    def get_availability(self, 
                        start_date: datetime,
                        end_date: datetime,
                        min_duration_minutes: int = 30) -> Dict[str, Any]:
        """
        Check calendar availability and suggest meeting times
        
        Args:
            start_date: Start of availability window
            end_date: End of availability window  
            min_duration_minutes: Minimum meeting duration
            
        Returns:
            Dict with availability information
        """
        if not self.is_authenticated():
            return {
                "success": False,
                "error": "Google Calendar not authenticated"
            }
        
        try:
            # Get busy times from the calendar
            freebusy_query = {
                'timeMin': start_date.isoformat(),
                'timeMax': end_date.isoformat(),
                'items': [{'id': self.calendar_id}]
            }
            
            freebusy_result = self.service.freebusy().query(body=freebusy_query).execute()
            busy_times = freebusy_result['calendars'][self.calendar_id].get('busy', [])
            
            # Find available slots (simplified algorithm)
            available_slots = []
            current_time = start_date
            
            while current_time < end_date:
                slot_end = current_time + timedelta(minutes=min_duration_minutes)
                
                # Check if this slot conflicts with any busy time
                is_available = True
                for busy in busy_times:
                    busy_start = datetime.fromisoformat(busy['start'].replace('Z', '+00:00'))
                    busy_end = datetime.fromisoformat(busy['end'].replace('Z', '+00:00'))
                    
                    if (current_time < busy_end and slot_end > busy_start):
                        is_available = False
                        break
                
                if is_available:
                    available_slots.append({
                        'start': current_time.isoformat(),
                        'end': slot_end.isoformat(),
                        'duration_minutes': min_duration_minutes
                    })
                
                # Move to next slot (30-minute intervals)
                current_time += timedelta(minutes=30)
            
            return {
                "success": True,
                "available_slots": available_slots[:10],  # Limit to 10 suggestions
                "busy_times": busy_times
            }
            
        except Exception as e:
            print(f"❌ Error checking availability: {e}")
            return {
                "success": False,
                "error": f"Availability check failed: {str(e)}"
            }
    
    def get_quick_meeting_slots(self, days_ahead: int = 7) -> List[Dict[str, Any]]:
        """
        Get suggested meeting slots for the next few days
        
        Args:
            days_ahead: Number of days to look ahead
            
        Returns:
            List of suggested meeting slots
        """
        try:
            # Define business hours (9 AM to 5 PM, Monday to Friday)
            now = datetime.now()
            slots = []
            
            for day_offset in range(1, days_ahead + 1):
                check_date = now + timedelta(days=day_offset)
                
                # Skip weekends
                if check_date.weekday() >= 5:  # Saturday = 5, Sunday = 6
                    continue
                
                # Generate time slots for business hours
                for hour in range(9, 17):  # 9 AM to 5 PM
                    for minute in [0, 30]:  # 30-minute intervals
                        slot_time = check_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
                        
                        # Only suggest future times
                        if slot_time > now:
                            slots.append({
                                'datetime': slot_time.isoformat(),
                                'display': slot_time.strftime("%A, %B %d at %I:%M %p"),
                                'day': slot_time.strftime("%A"),
                                'date': slot_time.strftime("%B %d"),
                                'time': slot_time.strftime("%I:%M %p")
                            })
            
            return slots[:20]  # Return up to 20 suggestions
            
        except Exception as e:
            print(f"❌ Error generating quick meeting slots: {e}")
            return []
    
    def create_meeting_from_request(self, 
                                  user_email: str,
                                  user_name: str,
                                  requested_time: Optional[str] = None,
                                  message: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a meeting event from a user request
        
        Args:
            user_email: User's email address
            user_name: User's name
            requested_time: Optional requested meeting time (ISO format)
            message: Optional message from user
            
        Returns:
            Dict with meeting creation result
        """
        try:
            # Parse requested time or use default
            if requested_time:
                try:
                    meeting_time = datetime.fromisoformat(requested_time.replace('Z', '+00:00'))
                except:
                    # Fallback to next business day at 2 PM
                    meeting_time = self._get_next_business_day_default()
            else:
                meeting_time = self._get_next_business_day_default()
            
            # Create meeting title and description
            title = f"HuddleUp Demo - {user_name}"
            description = f"""HuddleUp Platform Demo

Meeting with: {user_name} ({user_email})

Agenda:
• Understand your specific challenges and goals
• Show HuddleUp features relevant to your needs
• Discuss how our platform integrates with your workflows
• Answer questions about implementation and pricing
• Share case studies from similar organizations

{f'Additional notes: {message}' if message else ''}

Looking forward to our conversation!

Best regards,
Derek - HuddleUp Team"""
            
            # Create the calendar event
            return self.create_meeting_event(
                title=title,
                description=description,
                start_time=meeting_time,
                duration_minutes=30,
                attendee_email=user_email,
                include_meet_link=True
            )
            
        except Exception as e:
            print(f"❌ Error creating meeting from request: {e}")
            return {
                "success": False,
                "error": f"Failed to create meeting: {str(e)}"
            }
    
    def _get_next_business_day_default(self) -> datetime:
        """Get default meeting time (next business day at 2 PM)"""
        now = datetime.now()
        next_day = now + timedelta(days=1)
        
        # Skip to next weekday if it's a weekend
        while next_day.weekday() >= 5:  # Weekend
            next_day += timedelta(days=1)
        
        # Set to 2 PM
        return next_day.replace(hour=14, minute=0, second=0, microsecond=0)


# Global service instance
google_calendar_service = None

def initialize_google_calendar_service():
    """Initialize the global Google Calendar service instance"""
    global google_calendar_service
    try:
        google_calendar_service = GoogleCalendarService()
        return google_calendar_service
    except Exception as e:
        print(f"⚠️ Could not initialize Google Calendar service: {e}")
        return None

# Initialize on import
google_calendar_service = initialize_google_calendar_service()