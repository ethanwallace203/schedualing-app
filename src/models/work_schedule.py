"""
Work schedule models for Sling integration
"""
from datetime import datetime, time
from typing import Optional, List
from pydantic import BaseModel, Field
from enum import Enum

class ShiftStatus(str, Enum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class WorkShift(BaseModel):
    """Represents a work shift from Sling"""
    
    id: str
    start_time: datetime
    end_time: datetime
    role: str
    location: Optional[str] = None
    status: ShiftStatus = ShiftStatus.SCHEDULED
    
    # Additional metadata
    notes: Optional[str] = None
    is_break_included: bool = True
    break_duration: int = Field(default=30, description="Break time in minutes")
    
    @property
    def duration_minutes(self) -> int:
        """Duration of the shift in minutes"""
        delta = self.end_time - self.start_time
        return int(delta.total_seconds() / 60)
    
    @property
    def date(self) -> datetime:
        """Date of the shift"""
        return self.start_time
    
    @property
    def start_time_only(self) -> time:
        """Start time as time object"""
        return self.start_time.time()
    
    @property
    def end_time_only(self) -> time:
        """End time as time object"""
        return self.end_time.time()
    
    def __str__(self) -> str:
        start_str = self.start_time.strftime("%H:%M")
        end_str = self.end_time.strftime("%H:%M")
        return f"{start_str}-{end_str}: {self.role} ({self.location or 'No location'})"
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }
