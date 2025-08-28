"""
Canvas API integration for fetching assignments and course information
"""
import requests
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import json

from ..models.assignment import Assignment, AssignmentType, Priority
from ..models.schedule import TimeBlock, BlockType
from ..config.settings import settings

logger = logging.getLogger(__name__)

class CanvasAPI:
    """Canvas LMS API integration"""
    
    def __init__(self, api_url: str = None, api_token: str = None):
        self.api_url = api_url or settings.canvas_api_url
        self.api_token = api_token or settings.canvas_api_token
        
        if not self.api_token:
            raise ValueError("Canvas API token is required")
        
        self.headers = {
            'Authorization': f'Bearer {self.api_token}',
            'Content-Type': 'application/json'
        }
        
        self.base_url = f"{self.api_url}/api/v1"
        self.logger = logging.getLogger(__name__)
    
    def test_connection(self) -> bool:
        """Test if the Canvas API connection is working"""
        try:
            response = requests.get(f"{self.base_url}/users/self", headers=self.headers)
            return response.status_code == 200
        except Exception as e:
            self.logger.error(f"Canvas API connection test failed: {e}")
            return False
    
    def get_user_info(self) -> Optional[Dict[str, Any]]:
        """Get current user information"""
        try:
            response = requests.get(f"{self.base_url}/users/self", headers=self.headers)
            if response.status_code == 200:
                return response.json()
            else:
                self.logger.error(f"Failed to get user info: {response.status_code}")
                return None
        except Exception as e:
            self.logger.error(f"Error getting user info: {e}")
            return None
    
    def get_courses(self, include_archived: bool = False) -> List[Dict[str, Any]]:
        """Get all courses for the current user"""
        try:
            params = {
                'enrollment_state': 'active',
                'include': ['total_students', 'course_image']
            }
            
            if include_archived:
                params['enrollment_state'] = 'all'
            
            response = requests.get(f"{self.base_url}/courses", 
                                 headers=self.headers, params=params)
            
            if response.status_code == 200:
                courses = response.json()
                # Filter out non-student courses if needed
                return [course for course in courses if course.get('enrollment_state') == 'active']
            else:
                self.logger.error(f"Failed to get courses: {response.status_code}")
                return []
                
        except Exception as e:
            self.logger.error(f"Error getting courses: {e}")
            return []
    
    def get_assignments(self, course_id: int = None, 
                       include_submission: bool = True) -> List[Assignment]:
        """
        Get assignments from Canvas
        
        Args:
            course_id: Specific course ID, or None for all courses
            include_submission: Whether to include submission info
            
        Returns:
            List of Assignment objects
        """
        assignments = []
        
        try:
            if course_id:
                # Get assignments for specific course
                course_assignments = self._get_course_assignments(course_id, include_submission)
                assignments.extend(course_assignments)
            else:
                # Get assignments from all active courses
                courses = self.get_courses()
                for course in courses:
                    course_assignments = self._get_course_assignments(course['id'], include_submission)
                    assignments.extend(course_assignments)
            
            self.logger.info(f"Retrieved {len(assignments)} assignments")
            return assignments
            
        except Exception as e:
            self.logger.error(f"Error getting assignments: {e}")
            return []
    
    def _get_course_assignments(self, course_id: int, 
                               include_submission: bool) -> List[Assignment]:
        """Get assignments for a specific course"""
        try:
            params = {
                'include': ['submission', 'overrides'] if include_submission else [],
                'per_page': 100
            }
            
            response = requests.get(
                f"{self.base_url}/courses/{course_id}/assignments",
                headers=self.headers,
                params=params
            )
            
            if response.status_code != 200:
                self.logger.error(f"Failed to get assignments for course {course_id}: {response.status_code}")
                return []
            
            raw_assignments = response.json()
            assignments = []
            
            for raw_assignment in raw_assignments:
                assignment = self._parse_assignment(raw_assignment, course_id)
                if assignment:
                    assignments.append(assignment)
            
            return assignments
            
        except Exception as e:
            self.logger.error(f"Error getting assignments for course {course_id}: {e}")
            return []
    
    def _parse_assignment(self, raw_data: Dict[str, Any], course_id: int) -> Optional[Assignment]:
        """Parse raw Canvas assignment data into Assignment model"""
        try:
            # Get course name
            course_name = raw_data.get('course_name', 'Unknown Course')
            
            # Parse due date
            due_date = None
            if raw_data.get('due_at'):
                due_date = datetime.fromisoformat(raw_data['due_at'].replace('Z', '+00:00'))
            
            # Determine assignment type
            assignment_type = self._determine_assignment_type(raw_data)
            
            # Determine priority based on due date and points
            priority = self._determine_priority(raw_data, due_date)
            
            # Estimate duration based on assignment type and points
            estimated_duration = self._estimate_duration(raw_data, assignment_type)
            
            assignment = Assignment(
                id=raw_data['id'],
                name=raw_data['name'],
                course_id=course_id,
                course_name=course_name,
                due_date=due_date,
                points_possible=raw_data.get('points_possible'),
                submission_types=raw_data.get('submission_types', []),
                description=raw_data.get('description'),
                assignment_type=assignment_type,
                priority=priority,
                estimated_duration=estimated_duration,
                difficulty=self._estimate_difficulty(raw_data, assignment_type),
                requires_preparation=self._requires_preparation(assignment_type),
                preparation_time=self._estimate_preparation_time(assignment_type)
            )
            
            return assignment
            
        except Exception as e:
            self.logger.error(f"Error parsing assignment {raw_data.get('id')}: {e}")
            return None
    
    def _determine_assignment_type(self, raw_data: Dict[str, Any]) -> AssignmentType:
        """Determine assignment type from Canvas data"""
        name_lower = raw_data.get('name', '').lower()
        submission_types = raw_data.get('submission_types', [])
        
        if 'quiz' in name_lower or 'quiz' in submission_types:
            return AssignmentType.QUIZ
        elif 'exam' in name_lower or 'test' in name_lower:
            return AssignmentType.EXAM
        elif 'project' in name_lower:
            return AssignmentType.PROJECT
        elif 'discussion' in name_lower or 'discussion' in submission_types:
            return AssignmentType.DISCUSSION
        else:
            return AssignmentType.HOMEWORK
    
    def _determine_priority(self, raw_data: Dict[str, Any], due_date: datetime) -> Priority:
        """Determine assignment priority based on due date and points"""
        if not due_date:
            return Priority.MEDIUM
        
        days_until_due = (due_date - datetime.now()).days
        points = raw_data.get('points_possible', 0)
        
        # High priority if due soon or worth many points
        if days_until_due <= 2:
            return Priority.URGENT
        elif days_until_due <= 7 or points >= 100:
            return Priority.HIGH
        elif days_until_due <= 14:
            return Priority.MEDIUM
        else:
            return Priority.LOW
    
    def _estimate_duration(self, raw_data: Dict[str, Any], assignment_type: AssignmentType) -> int:
        """Estimate how long an assignment will take (in minutes)"""
        points = raw_data.get('points_possible', 0)
        name = raw_data.get('name', '').lower()
        
        # Base duration by type
        base_durations = {
            AssignmentType.QUIZ: 30,
            AssignmentType.EXAM: 120,
            AssignmentType.PROJECT: 180,
            AssignmentType.DISCUSSION: 45,
            AssignmentType.HOMEWORK: 90,
            AssignmentType.ESSAY: 120,
            AssignmentType.LAB_REPORT: 90
        }
        
        base_duration = base_durations.get(assignment_type, 90)
        
        # Adjust based on points (more points = more time)
        if points > 0:
            duration_multiplier = max(0.5, min(2.0, points / 50))
            base_duration = int(base_duration * duration_multiplier)
        
        # Adjust based on name keywords
        if any(word in name for word in ['essay', 'paper', 'research']):
            base_duration = int(base_duration * 1.5)
        elif any(word in name for word in ['short', 'quick', 'simple']):
            base_duration = int(base_duration * 0.7)
        
        return max(30, min(300, base_duration))  # Between 30 min and 5 hours
    
    def _estimate_difficulty(self, raw_data: Dict[str, Any], assignment_type: AssignmentType) -> int:
        """Estimate assignment difficulty (1-5 scale)"""
        points = raw_data.get('points_possible', 0)
        name = raw_data.get('name', '').lower()
        
        # Base difficulty by type
        base_difficulty = {
            AssignmentType.QUIZ: 2,
            AssignmentType.EXAM: 4,
            AssignmentType.PROJECT: 4,
            AssignmentType.DISCUSSION: 2,
            AssignmentType.HOMEWORK: 3,
            AssignmentType.ESSAY: 4,
            AssignmentType.LAB_REPORT: 3
        }.get(assignment_type, 3)
        
        # Adjust based on points
        if points >= 100:
            base_difficulty = min(5, base_difficulty + 1)
        elif points <= 10:
            base_difficulty = max(1, base_difficulty - 1)
        
        # Adjust based on name keywords
        if any(word in name for word in ['advanced', 'complex', 'research']):
            base_difficulty = min(5, base_difficulty + 1)
        elif any(word in name for word in ['basic', 'simple', 'intro']):
            base_difficulty = max(1, base_difficulty - 1)
        
        return base_difficulty
    
    def _requires_preparation(self, assignment_type: AssignmentType) -> bool:
        """Determine if assignment requires preparation time"""
        return assignment_type in [AssignmentType.EXAM, AssignmentType.PROJECT, AssignmentType.ESSAY]
    
    def _estimate_preparation_time(self, assignment_type: AssignmentType) -> int:
        """Estimate preparation time needed (in minutes)"""
        prep_times = {
            AssignmentType.QUIZ: 15,
            AssignmentType.EXAM: 60,
            AssignmentType.PROJECT: 45,
            AssignmentType.DISCUSSION: 20,
            AssignmentType.HOMEWORK: 10,
            AssignmentType.ESSAY: 30,
            AssignmentType.LAB_REPORT: 20
        }
        return prep_times.get(assignment_type, 10)
    
    def get_class_schedule(self, course_id: int = None) -> List[TimeBlock]:
        """Get class schedule from Canvas (if available)"""
        # Note: Canvas doesn't directly provide class schedules
        # This would need to be manually configured or imported from elsewhere
        # For now, return empty list
        self.logger.warning("Class schedule not available from Canvas API")
        return []
    
    def get_upcoming_assignments(self, days_ahead: int = 14) -> List[Assignment]:
        """Get assignments due within the next N days"""
        all_assignments = self.get_assignments()
        cutoff_date = datetime.now() + timedelta(days=days_ahead)
        
        upcoming = []
        for assignment in all_assignments:
            if assignment.due_date and assignment.due_date <= cutoff_date:
                upcoming.append(assignment)
        
        # Sort by due date
        upcoming.sort(key=lambda x: x.due_date or datetime.max)
        return upcoming
