"""
Assignment model for Canvas assignments
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from enum import Enum

class AssignmentType(str, Enum):
    HOMEWORK = "homework"
    QUIZ = "quiz"
    EXAM = "exam"
    PROJECT = "project"
    DISCUSSION = "discussion"
    ESSAY = "essay"
    LAB_REPORT = "lab_report"
    OTHER = "other"

class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class Assignment(BaseModel):
    """Represents a Canvas assignment"""
    
    # Canvas data
    id: int
    name: str
    course_id: int
    course_name: str
    due_date: Optional[datetime] = None
    points_possible: Optional[float] = None
    submission_types: List[str] = []
    
    # Assignment details
    description: Optional[str] = None
    assignment_type: AssignmentType = AssignmentType.HOMEWORK
    priority: Priority = Priority.MEDIUM
    
    # Scheduling fields
    estimated_duration: int = Field(default=90, description="Estimated time in minutes")
    difficulty: int = Field(default=3, ge=1, le=5, description="Difficulty 1-5")
    requires_preparation: bool = False
    preparation_time: int = Field(default=0, description="Prep time in minutes")
    
    # Status tracking
    is_completed: bool = False
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Calculated fields
    @property
    def total_time_needed(self) -> int:
        """Total time needed including preparation"""
        return self.estimated_duration + self.preparation_time
    
    @property
    def days_until_due(self) -> Optional[int]:
        """Days until assignment is due"""
        if not self.due_date:
            return None
        delta = self.due_date - datetime.now()
        return max(0, delta.days)
    
    @property
    def urgency_score(self) -> float:
        """Calculate urgency score based on due date and priority"""
        if not self.due_date:
            return 0.0
        
        days_left = self.days_until_due
        if days_left == 0:
            return 10.0  # Due today
        
        # Base urgency based on priority
        priority_scores = {
            Priority.LOW: 1.0,
            Priority.MEDIUM: 2.0,
            Priority.HIGH: 3.0,
            Priority.URGENT: 4.0
        }
        
        base_score = priority_scores[self.priority]
        
        # Time urgency (exponential decay)
        if days_left <= 3:
            time_multiplier = 3.0
        elif days_left <= 7:
            time_multiplier = 2.0
        elif days_left <= 14:
            time_multiplier = 1.5
        else:
            time_multiplier = 1.0
            
        return base_score * time_multiplier
    
    def __str__(self) -> str:
        return f"{self.name} ({self.course_name}) - Due: {self.due_date}"
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }
