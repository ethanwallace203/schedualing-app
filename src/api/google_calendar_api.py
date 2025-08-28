"""
Google Calendar API integration for posting scheduled tasks and events
"""
import os
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import json

from ..models.schedule import TimeBlock, BlockType
from ..config.settings import settings

logger = logging.getLogger(__name__)

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/calendar']

class GoogleCalendarAPI:
    """Google Calendar API integration"""
    
    def __init__(self, credentials_file: str = None, token_file: str = None):
        self.credentials_file = credentials_file or settings.google_credentials_file
        self.token_file = token_file or settings.google_token_file
        self.calendar_id = settings.google_calendar_id
        
        if not self.credentials_file:
            raise ValueError("Google credentials file is required")
        
        self.service = None
        self.logger = logging.getLogger(__name__)
        
        # Authenticate and build service
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Google Calendar API"""
        creds = None
        
        # The file token.json stores the user's access and refresh tokens
        if self.token_file and os.path.exists(self.token_file):
            try:
                creds = Credentials.from_authorized_user_file(self.token_file, SCOPES)
            except Exception as e:
                self.logger.warning(f"Error loading token file: {e}")
        
        # If there are no (valid) credentials available, let the user log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    self.logger.error(f"Error refreshing credentials: {e}")
                    creds = None
            
            if not creds:
                try:
                    flow = InstalledAppFlow.from_client_secrets_file(self.credentials_file, SCOPES)
                    creds = flow.run_local_server(port=0)
                except Exception as e:
                    self.logger.error(f"Error running OAuth flow: {e}")
                    raise
            
            # Save the credentials for the next run
            if self.token_file:
                try:
                    os.makedirs(os.path.dirname(self.token_file), exist_ok=True)
                    with open(self.token_file, 'w') as token:
                        token.write(creds.to_json())
                except Exception as e:
                    self.logger.warning(f"Could not save token file: {e}")
        
        try:
            self.service = build('calendar', 'v3', credentials=creds)
            self.logger.info("Successfully authenticated with Google Calendar API")
        except Exception as e:
            self.logger.error(f"Error building calendar service: {e}")
            raise
    
    def test_connection(self) -> bool:
        """Test if the Google Calendar API connection is working"""
        try:
            if not self.service:
                return False
            
            # Try to get calendar list
            calendar_list = self.service.calendarList().list().execute()
            return 'items' in calendar_list
        except Exception as e:
            self.logger.error(f"Google Calendar API connection test failed: {e}")
            return False
    
    def get_calendars(self) -> List[Dict[str, Any]]:
        """Get list of available calendars"""
        try:
            if not self.service:
                return []
            
            calendar_list = self.service.calendarList().list().execute()
            return calendar_list.get('items', [])
        except Exception as e:
            self.logger.error(f"Error getting calendars: {e}")
            return []
    
    def create_event(self, time_block: TimeBlock, 
                    description: str = None,
                    location: str = None) -> Optional[str]:
        """
        Create a calendar event from a time block
        
        Args:
            time_block: The time block to create an event for
            description: Additional description for the event
            location: Location for the event
            
        Returns:
            Event ID if successful, None otherwise
        """
        try:
            if not self.service:
                self.logger.error("Calendar service not initialized")
                return None
            
            # Prepare event data
            event = {
                'summary': time_block.title,
                'description': self._create_event_description(time_block, description),
                'start': {
                    'dateTime': time_block.start_time.isoformat(),
                    'timeZone': settings.timezone,
                },
                'end': {
                    'dateTime': time_block.end_time.isoformat(),
                    'timeZone': settings.timezone,
                },
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'popup', 'minutes': 15},
                        {'method': 'email', 'minutes': 60},
                    ],
                },
            }
            
            if location:
                event['location'] = location
            
            # Add color coding based on block type
            color_id = self._get_color_id(time_block.block_type)
            if color_id:
                event['colorId'] = color_id
            
            # Create the event
            event = self.service.events().insert(
                calendarId=self.calendar_id,
                body=event
            ).execute()
            
            self.logger.info(f"Created calendar event: {event.get('id')} - {time_block.title}")
            return event.get('id')
            
        except HttpError as e:
            self.logger.error(f"HTTP error creating event: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error creating calendar event: {e}")
            return None
    
    def create_events_from_schedule(self, time_blocks: List[TimeBlock],
                                   description: str = None,
                                   location: str = None) -> Dict[str, str]:
        """
        Create multiple calendar events from a list of time blocks
        
        Args:
            time_blocks: List of time blocks to create events for
            description: Additional description for events
            location: Location for events
            
        Returns:
            Dictionary mapping time block titles to event IDs
        """
        results = {}
        
        for block in time_blocks:
            event_id = self.create_event(block, description, location)
            if event_id:
                results[block.title] = event_id
            else:
                self.logger.warning(f"Failed to create event for: {block.title}")
        
        self.logger.info(f"Created {len(results)} calendar events")
        return results
    
    def update_event(self, event_id: str, 
                    time_block: TimeBlock,
                    description: str = None,
                    location: str = None) -> bool:
        """
        Update an existing calendar event
        
        Args:
            event_id: ID of the event to update
            time_block: New time block data
            description: New description
            location: New location
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.service:
                return False
            
            # Get existing event
            event = self.service.events().get(
                calendarId=self.calendar_id,
                eventId=event_id
            ).execute()
            
            # Update event data
            event['summary'] = time_block.title
            event['description'] = self._create_event_description(time_block, description)
            event['start']['dateTime'] = time_block.start_time.isoformat()
            event['end']['dateTime'] = time_block.end_time.isoformat()
            
            if location:
                event['location'] = location
            
            # Update color coding
            color_id = self._get_color_id(time_block.block_type)
            if color_id:
                event['colorId'] = color_id
            
            # Update the event
            updated_event = self.service.events().update(
                calendarId=self.calendar_id,
                eventId=event_id,
                body=event
            ).execute()
            
            self.logger.info(f"Updated calendar event: {event_id}")
            return True
            
        except HttpError as e:
            self.logger.error(f"HTTP error updating event: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Error updating calendar event: {e}")
            return False
    
    def delete_event(self, event_id: str) -> bool:
        """
        Delete a calendar event
        
        Args:
            event_id: ID of the event to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.service:
                return False
            
            self.service.events().delete(
                calendarId=self.calendar_id,
                eventId=event_id
            ).execute()
            
            self.logger.info(f"Deleted calendar event: {event_id}")
            return True
            
        except HttpError as e:
            self.logger.error(f"HTTP error deleting event: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Error deleting calendar event: {e}")
            return False
    
    def get_events(self, time_min: datetime = None, 
                   time_max: datetime = None,
                   max_results: int = 100) -> List[Dict[str, Any]]:
        """
        Get calendar events within a time range
        
        Args:
            time_min: Start time for search
            time_max: End time for search
            max_results: Maximum number of events to return
            
        Returns:
            List of calendar events
        """
        try:
            if not self.service:
                return []
            
            # Set default time range if not provided
            if not time_min:
                time_min = datetime.now()
            if not time_max:
                time_max = time_min + timedelta(days=7)
            
            events_result = self.service.events().list(
                calendarId=self.calendar_id,
                timeMin=time_min.isoformat() + 'Z',
                timeMax=time_max.isoformat() + 'Z',
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            self.logger.info(f"Retrieved {len(events)} calendar events")
            return events
            
        except Exception as e:
            self.logger.error(f"Error getting calendar events: {e}")
            return []
    
    def _create_event_description(self, time_block: TimeBlock, 
                                additional_description: str = None) -> str:
        """Create a description for the calendar event"""
        description_parts = []
        
        # Add block type
        description_parts.append(f"Type: {time_block.block_type.value.title()}")
        
        # Add block description if available
        if time_block.description:
            description_parts.append(f"Details: {time_block.description}")
        
        # Add tags if available
        if time_block.tags:
            description_parts.append(f"Tags: {', '.join(time_block.tags)}")
        
        # Add additional description
        if additional_description:
            description_parts.append(additional_description)
        
        # Add duration
        duration_hours = time_block.duration_minutes / 60
        if duration_hours >= 1:
            description_parts.append(f"Duration: {duration_hours:.1f} hours")
        else:
            description_parts.append(f"Duration: {time_block.duration_minutes} minutes")
        
        return "\n".join(description_parts)
    
    def _get_color_id(self, block_type: BlockType) -> Optional[str]:
        """Get Google Calendar color ID based on block type"""
        # Google Calendar color mapping
        # These are default colors, users can customize
        color_mapping = {
            BlockType.STUDY: "1",      # Blue
            BlockType.CLASS: "2",      # Green
            BlockType.WORK: "3",       # Red
            BlockType.BREAK: "4",      # Yellow
            BlockType.PERSONAL: "5",   # Purple
            BlockType.BUFFER: "6",     # Orange
        }
        
        return color_mapping.get(block_type)
    
    def clear_calendar_events(self, time_min: datetime = None, 
                             time_max: datetime = None,
                             event_titles: List[str] = None) -> int:
        """
        Clear calendar events within a time range or with specific titles
        
        Args:
            time_min: Start time for search
            time_max: End time for search
            event_titles: List of event titles to delete (if provided, overrides time range)
            
        Returns:
            Number of events deleted
        """
        try:
            if not self.service:
                return 0
            
            if event_titles:
                # Delete specific events by title
                deleted_count = 0
                events = self.get_events(time_min, time_max, max_results=1000)
                
                for event in events:
                    if event.get('summary') in event_titles:
                        if self.delete_event(event['id']):
                            deleted_count += 1
                
                return deleted_count
            else:
                # Delete all events in time range
                events = self.get_events(time_min, time_max, max_results=1000)
                deleted_count = 0
                
                for event in events:
                    if self.delete_event(event['id']):
                        deleted_count += 1
                
                return deleted_count
                
        except Exception as e:
            self.logger.error(f"Error clearing calendar events: {e}")
            return 0
