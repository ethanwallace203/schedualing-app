"""
Schedule and TimeBlock models for managing time allocation
"""
from datetime import datetime, time, timedelta
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from enum import Enum

class BlockType(str, Enum):
    STUDY = "study"
    BREAK = "break"
    CLASS = "class"
    WORK = "work"
    PERSONAL = "personal"
    BUFFER = "buffer"

class TimeBlock(BaseModel):
    """Represents a time block in the schedule"""
    
    start_time: datetime
    end_time: datetime
    block_type: BlockType
    title: str
    description: Optional[str] = None
    
    # For study blocks
    assignment_id: Optional[int] = None
    course_id: Optional[int] = None
    
    # Metadata
    is_fixed: bool = False  # Can't be moved/rescheduled
    priority: int = 1
    tags: List[str] = []
    
    @property
    def duration_minutes(self) -> int:
        """Duration of the block in minutes"""
        delta = self.end_time - self.start_time
        return int(delta.total_seconds() / 60)
    
    @property
    def is_study_block(self) -> bool:
        """Check if this is a study block"""
        return self.block_type == BlockType.STUDY
    
    @validator('end_time')
    def end_time_after_start(cls, v, values):
        """Ensure end time is after start time"""
        if 'start_time' in values and v <= values['start_time']:
            raise ValueError('end_time must be after start_time')
        return v
    
    def overlaps_with(self, other: 'TimeBlock') -> bool:
        """Check if this block overlaps with another"""
        return (self.start_time < other.end_time and 
                self.end_time > other.start_time)
    
    def __str__(self) -> str:
        start_str = self.start_time.strftime("%H:%M")
        end_str = self.end_time.strftime("%H:%M")
        return f"{start_str}-{end_str}: {self.title} ({self.block_type})"

class Schedule(BaseModel):
    """Represents a complete schedule for a time period"""
    
    date: datetime
    time_blocks: List[TimeBlock] = []
    
    # Schedule metadata
    total_study_time: int = 0
    total_break_time: int = 0
    efficiency_score: float = 0.0
    
    def add_block(self, block: TimeBlock) -> bool:
        """Add a time block if it doesn't conflict"""
        if self._can_add_block(block):
            self.time_blocks.append(block)
            self._update_metrics()
            return True
        return False
    
    def remove_block(self, block_id: int) -> bool:
        """Remove a time block by index"""
        if 0 <= block_id < len(self.time_blocks):
            self.time_blocks.pop(block_id)
            self._update_metrics()
            return True
        return False
    
    def get_available_slots(self, duration_minutes: int, 
                           start_time: time = time(9, 0),
                           end_time: time = time(22, 0)) -> List[tuple]:
        """Find available time slots for a given duration"""
        available_slots = []
        
        # Convert date and times to datetime objects
        start_dt = datetime.combine(self.date.date(), start_time)
        end_dt = datetime.combine(self.date.date(), end_time)
        
        # Sort blocks by start time
        sorted_blocks = sorted(self.time_blocks, key=lambda x: x.start_time)
        
        current_time = start_dt
        
        for block in sorted_blocks:
            # Check if there's enough time before this block
            if (block.start_time - current_time).total_seconds() >= duration_minutes * 60:
                available_slots.append((current_time, block.start_time))
            
            current_time = block.end_time
        
        # Check if there's time after the last block
        if (end_dt - current_time).total_seconds() >= duration_minutes * 60:
            available_slots.append((current_time, end_dt))
        
        return available_slots
    
    def _can_add_block(self, block: TimeBlock) -> bool:
        """Check if a block can be added without conflicts"""
        for existing_block in self.time_blocks:
            if block.overlaps_with(existing_block):
                return False
        return True
    
    def _update_metrics(self):
        """Update schedule metrics"""
        self.total_study_time = sum(
            block.duration_minutes for block in self.time_blocks 
            if block.block_type == BlockType.STUDY
        )
        
        self.total_break_time = sum(
            block.duration_minutes for block in self.time_blocks 
            if block.block_type == BlockType.BREAK
        )
        
        # Calculate efficiency score (study time vs total time)
        total_time = sum(block.duration_minutes for block in self.time_blocks)
        if total_time > 0:
            self.efficiency_score = self.total_study_time / total_time
        else:
            self.efficiency_score = 0.0
    
    def get_blocks_by_type(self, block_type: BlockType) -> List[TimeBlock]:
        """Get all blocks of a specific type"""
        return [block for block in self.time_blocks if block.block_type == block_type]
    
    def get_study_blocks(self) -> List[TimeBlock]:
        """Get all study blocks"""
        return self.get_blocks_by_type(BlockType.STUDY)
    
    def __str__(self) -> str:
        blocks_str = "\n".join(f"  {block}" for block in self.time_blocks)
        return f"Schedule for {self.date.strftime('%Y-%m-%d')}:\n{blocks_str}"
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }
