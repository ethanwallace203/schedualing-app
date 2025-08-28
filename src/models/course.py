"""
Course model for Canvas courses
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

class Course(BaseModel):
    """Represents a Canvas course"""
    
    id: int
    name: str
    course_code: str
    enrollment_state: str = "active"
    
    # Course details
    description: Optional[str] = None
    start_at: Optional[datetime] = None
    end_at: Optional[datetime] = None
    total_students: Optional[int] = None
    
    # Metadata
    is_public: bool = False
    is_public_to_auth_users: bool = False
    course_image: Optional[str] = None
    
    def __str__(self) -> str:
        return f"{self.course_code}: {self.name}"
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }
