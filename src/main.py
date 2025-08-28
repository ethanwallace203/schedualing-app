"""
Main application for MySchedualer
"""
import logging
import argparse
from datetime import datetime, timedelta
from typing import List, Optional
import sys
import os

from api.canvas_api import CanvasAPI
from api.google_calendar_api import GoogleCalendarAPI
from core.scheduler import SmartScheduler, SchedulingConstraints
from models.assignment import Assignment
from models.schedule import Schedule, TimeBlock, BlockType
from models.work_schedule import WorkShift
from config.settings import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('myschedualer.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class MySchedualer:
    """Main application class for MySchedualer"""
    
    def __init__(self):
        self.canvas_api = None
        self.google_calendar_api = None
        self.scheduler = None
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self._initialize_apis()
        self._initialize_scheduler()
    
    def _initialize_apis(self):
        """Initialize API connections"""
        try:
            # Initialize Canvas API
            if settings.canvas_api_token:
                self.canvas_api = CanvasAPI()
                if self.canvas_api.test_connection():
                    self.logger.info("Canvas API connected successfully")
                else:
                    self.logger.warning("Canvas API connection failed")
            else:
                self.logger.warning("Canvas API token not configured")
            
            # Initialize Google Calendar API
            if settings.google_credentials_file:
                try:
                    self.google_calendar_api = GoogleCalendarAPI()
                    if self.google_calendar_api.test_connection():
                        self.logger.info("Google Calendar API connected successfully")
                    else:
                        self.logger.warning("Google Calendar API connection failed")
                except Exception as e:
                    self.logger.error(f"Failed to initialize Google Calendar API: {e}")
            else:
                self.logger.warning("Google Calendar credentials not configured")
                
        except Exception as e:
            self.logger.error(f"Error initializing APIs: {e}")
    
    def _initialize_scheduler(self):
        """Initialize the scheduling engine"""
        try:
            constraints = SchedulingConstraints(
                start_time=settings.preferred_study_hours[0],
                end_time=settings.preferred_study_hours[1],
                default_study_session=settings.default_study_duration,
                break_duration=settings.break_duration,
                buffer_time=settings.buffer_time
            )
            
            self.scheduler = SmartScheduler(constraints)
            self.logger.info("Scheduler initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Error initializing scheduler: {e}")
    
    def fetch_assignments(self) -> List[Assignment]:
        """Fetch assignments from Canvas"""
        if not self.canvas_api:
            self.logger.error("Canvas API not available")
            return []
        
        try:
            assignments = self.canvas_api.get_assignments()
            self.logger.info(f"Fetched {len(assignments)} assignments from Canvas")
            return assignments
        except Exception as e:
            self.logger.error(f"Error fetching assignments: {e}")
            return []
    
    def get_work_schedule(self) -> List[WorkShift]:
        """Get work schedule (placeholder for Sling integration)"""
        # TODO: Implement Sling API integration
        # For now, return empty list
        self.logger.info("Work schedule integration not yet implemented")
        return []
    
    def get_class_schedule(self) -> List[TimeBlock]:
        """Get class schedule (placeholder for now)"""
        # TODO: Implement class schedule import
        # For now, return empty list
        self.logger.info("Class schedule integration not yet implemented")
        return []
    
    def create_schedule(self, days_ahead: int = 7) -> List[Schedule]:
        """Create a complete schedule for the specified period"""
        if not self.scheduler:
            self.logger.error("Scheduler not initialized")
            return []
        
        try:
            # Fetch data
            assignments = self.fetch_assignments()
            work_shifts = self.get_work_schedule()
            class_schedule = self.get_class_schedule()
            
            if not assignments:
                self.logger.warning("No assignments found to schedule")
                return []
            
            # Create schedule
            start_date = datetime.now()
            schedules = self.scheduler.create_schedule(
                assignments=assignments,
                work_shifts=work_shifts,
                class_schedule=class_schedule,
                start_date=start_date,
                days_ahead=days_ahead
            )
            
            # Get summary
            summary = self.scheduler.get_schedule_summary(schedules)
            self.logger.info(f"Schedule created: {summary}")
            
            return schedules
            
        except Exception as e:
            self.logger.error(f"Error creating schedule: {e}")
            return []
    
    def post_to_calendar(self, schedules: List[Schedule]) -> bool:
        """Post schedule to Google Calendar"""
        if not self.google_calendar_api:
            self.logger.error("Google Calendar API not available")
            return False
        
        try:
            # Extract all time blocks from schedules
            all_blocks = []
            for schedule in schedules:
                all_blocks.extend(schedule.time_blocks)
            
            if not all_blocks:
                self.logger.warning("No time blocks to post to calendar")
                return False
            
            # Post to Google Calendar
            results = self.google_calendar_api.create_events_from_schedule(
                all_blocks,
                description="Generated by MySchedualer",
                location="Study/Work"
            )
            
            self.logger.info(f"Posted {len(results)} events to Google Calendar")
            return len(results) > 0
            
        except Exception as e:
            self.logger.error(f"Error posting to calendar: {e}")
            return False
    
    def run_full_schedule(self, days_ahead: int = 7) -> bool:
        """Run the complete scheduling process"""
        try:
            self.logger.info(f"Starting full schedule generation for {days_ahead} days")
            
            # Create schedule
            schedules = self.create_schedule(days_ahead)
            if not schedules:
                self.logger.error("Failed to create schedule")
                return False
            
            # Post to calendar
            if self.post_to_calendar(schedules):
                self.logger.info("Schedule successfully posted to Google Calendar")
                return True
            else:
                self.logger.error("Failed to post schedule to Google Calendar")
                return False
                
        except Exception as e:
            self.logger.error(f"Error in full schedule run: {e}")
            return False
    
    def show_schedule_summary(self, schedules: List[Schedule]):
        """Display a summary of the created schedule"""
        if not schedules:
            print("No schedules to display")
            return
        
        print(f"\n{'='*60}")
        print("SCHEDULE SUMMARY")
        print(f"{'='*60}")
        
        for i, schedule in enumerate(schedules):
            date_str = schedule.date.strftime("%A, %B %d, %Y")
            print(f"\n{date_str}")
            print("-" * len(date_str))
            
            if not schedule.time_blocks:
                print("  No scheduled blocks")
                continue
            
            # Sort blocks by start time
            sorted_blocks = sorted(schedule.time_blocks, key=lambda x: x.start_time)
            
            for block in sorted_blocks:
                start_time = block.start_time.strftime("%H:%M")
                end_time = block.end_time.strftime("%H:%M")
                duration = block.duration_minutes
                
                print(f"  {start_time}-{end_time} ({duration} min): {block.title}")
                if block.description:
                    print(f"    {block.description}")
            
            # Show daily summary
            print(f"\n  Daily Summary:")
            print(f"    Study Time: {schedule.total_study_time} minutes ({schedule.total_study_time/60:.1f} hours)")
            print(f"    Break Time: {schedule.total_break_time} minutes")
            print(f"    Efficiency: {schedule.efficiency_score:.1%}")
        
        # Overall summary
        summary = self.scheduler.get_schedule_summary(schedules)
        print(f"\n{'='*60}")
        print("OVERALL SUMMARY")
        print(f"{'='*60}")
        print(f"Total Days: {summary['total_days']}")
        print(f"Total Study Time: {summary['total_study_time_hours']} hours")
        print(f"Average Study per Day: {summary['average_study_per_day_hours']} hours")
        print(f"Overall Efficiency: {summary['efficiency_score']:.1%}")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="MySchedualer - Smart Academic Scheduling")
    parser.add_argument("--days", "-d", type=int, default=7, 
                       help="Number of days to schedule ahead (default: 7)")
    parser.add_argument("--calendar", "-c", action="store_true",
                       help="Post schedule to Google Calendar")
    parser.add_argument("--summary", "-s", action="store_true",
                       help="Show detailed schedule summary")
    parser.add_argument("--test", "-t", action="store_true",
                       help="Test API connections only")
    
    args = parser.parse_args()
    
    try:
        app = MySchedualer()
        
        if args.test:
            print("Testing API connections...")
            # Test connections
            if app.canvas_api and app.canvas_api.test_connection():
                print("✓ Canvas API: Connected")
            else:
                print("✗ Canvas API: Failed")
            
            if app.google_calendar_api and app.google_calendar_api.test_connection():
                print("✓ Google Calendar API: Connected")
            else:
                print("✗ Google Calendar API: Failed")
            return
        
        # Create schedule
        print(f"Creating schedule for {args.days} days...")
        schedules = app.create_schedule(args.days)
        
        if not schedules:
            print("Failed to create schedule")
            return
        
        # Show summary if requested
        if args.summary:
            app.show_schedule_summary(schedules)
        
        # Post to calendar if requested
        if args.calendar:
            print("Posting schedule to Google Calendar...")
            if app.post_to_calendar(schedules):
                print("✓ Schedule posted to Google Calendar successfully!")
            else:
                print("✗ Failed to post schedule to Google Calendar")
        else:
            print("Schedule created successfully! Use --calendar to post to Google Calendar")
        
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
    except Exception as e:
        logger.error(f"Application error: {e}")
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
