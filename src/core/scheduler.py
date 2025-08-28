"""
Core scheduling algorithm for distributing homework tasks optimally
"""
from datetime import datetime, timedelta, time
from typing import List, Dict, Tuple, Optional
import logging
from dataclasses import dataclass

from ..models.assignment import Assignment, Priority
from ..models.schedule import Schedule, TimeBlock, BlockType
from ..models.work_schedule import WorkShift

logger = logging.getLogger(__name__)

@dataclass
class SchedulingConstraints:
    """Constraints for the scheduling algorithm"""
    start_time: time = time(9, 0)  # 9 AM
    end_time: time = time(22, 0)   # 10 PM
    max_study_session: int = 120   # Max minutes per study session
    min_study_session: int = 30    # Min minutes per study session
    break_duration: int = 15       # Break between sessions
    buffer_time: int = 30          # Buffer between tasks
    preferred_study_hours: Tuple[int, int] = (9, 22)

class SmartScheduler:
    """
    Intelligent scheduler that distributes homework tasks optimally
    """
    
    def __init__(self, constraints: SchedulingConstraints = None):
        self.constraints = constraints or SchedulingConstraints()
        self.logger = logging.getLogger(__name__)
    
    def create_schedule(self, 
                       assignments: List[Assignment],
                       work_shifts: List[WorkShift],
                       class_schedule: List[TimeBlock],
                       start_date: datetime,
                       days_ahead: int = 7) -> List[Schedule]:
        """
        Create an optimized schedule for the given period
        
        Args:
            assignments: List of assignments to schedule
            work_shifts: Work schedule from Sling
            class_schedule: Fixed class times
            start_date: When to start scheduling
            days_ahead: How many days to schedule ahead
            
        Returns:
            List of daily schedules
        """
        self.logger.info(f"Creating schedule for {days_ahead} days starting {start_date}")
        
        # Sort assignments by urgency and priority
        sorted_assignments = self._sort_assignments_by_priority(assignments)
        
        # Create daily schedules
        schedules = []
        current_date = start_date
        
        for day in range(days_ahead):
            schedule = Schedule(date=current_date)
            
            # Add fixed blocks (classes, work)
            self._add_fixed_blocks(schedule, class_schedule, work_shifts, current_date)
            
            # Schedule assignments for this day
            self._schedule_assignments_for_day(schedule, sorted_assignments, current_date)
            
            # Add breaks and optimize
            self._add_breaks_and_optimize(schedule)
            
            schedules.append(schedule)
            current_date += timedelta(days=1)
        
        return schedules
    
    def _sort_assignments_by_priority(self, assignments: List[Assignment]) -> List[Assignment]:
        """Sort assignments by urgency score and priority"""
        def sort_key(assignment):
            # Primary: urgency score, Secondary: priority level
            priority_order = {Priority.LOW: 1, Priority.MEDIUM: 2, Priority.HIGH: 3, Priority.URGENT: 4}
            return (-assignment.urgency_score, -priority_order[assignment.priority])
        
        return sorted(assignments, key=sort_key)
    
    def _add_fixed_blocks(self, schedule: Schedule, 
                          class_schedule: List[TimeBlock],
                          work_shifts: List[WorkShift],
                          date: datetime):
        """Add fixed time blocks (classes, work) to the schedule"""
        # Add class blocks for this date
        for class_block in class_schedule:
            if class_block.start_time.date() == date.date():
                schedule.add_block(class_block)
        
        # Add work shifts for this date
        for work_shift in work_shifts:
            if work_shift.date.date() == date.date():
                work_block = TimeBlock(
                    start_time=work_shift.start_time,
                    end_time=work_shift.end_time,
                    block_type=BlockType.WORK,
                    title=f"Work - {work_shift.role}",
                    is_fixed=True
                )
                schedule.add_block(work_block)
    
    def _schedule_assignments_for_day(self, schedule: Schedule, 
                                     assignments: List[Assignment],
                                     date: datetime):
        """Schedule assignments for a specific day"""
        available_assignments = [a for a in assignments if not a.is_completed]
        
        if not available_assignments:
            return
        
        # Get available time slots
        available_slots = schedule.get_available_slots(
            self.constraints.min_study_session,
            self.constraints.start_time,
            self.constraints.end_time
        )
        
        if not available_slots:
            self.logger.warning(f"No available slots for {date.date()}")
            return
        
        # Try to schedule assignments in available slots
        for assignment in available_assignments:
            if self._can_schedule_assignment(assignment, date):
                self._schedule_single_assignment(schedule, assignment, available_slots)
    
    def _can_schedule_assignment(self, assignment: Assignment, date: datetime) -> bool:
        """Check if an assignment can be scheduled on a given date"""
        if assignment.is_completed:
            return False
        
        # Check if assignment is due on or before this date
        if assignment.due_date and assignment.due_date.date() < date.date():
            return False
        
        # Check if we have enough time before due date
        if assignment.due_date:
            days_until_due = (assignment.due_date - date).days
            if days_until_due < 0:
                return False
        
        return True
    
    def _schedule_single_assignment(self, schedule: Schedule, 
                                   assignment: Assignment,
                                   available_slots: List[Tuple[datetime, datetime]]):
        """Schedule a single assignment in the best available slot"""
        time_needed = assignment.total_time_needed
        
        # Find the best slot for this assignment
        best_slot = None
        best_score = -1
        
        for start_time, end_time in available_slots:
            slot_duration = (end_time - start_time).total_seconds() / 60
            
            if slot_duration >= time_needed:
                # Score this slot based on:
                # 1. How well it fits the time needed
                # 2. Proximity to due date
                # 3. Time of day preference
                
                fit_score = 1.0 - (abs(slot_duration - time_needed) / time_needed)
                time_score = self._calculate_time_preference_score(start_time)
                
                total_score = fit_score * 0.6 + time_score * 0.4
                
                if total_score > best_score:
                    best_score = total_score
                    best_slot = (start_time, end_time)
        
        if best_slot:
            start_time, end_time = best_slot
            
            # Create study block
            study_block = TimeBlock(
                start_time=start_time,
                end_time=start_time + timedelta(minutes=time_needed),
                block_type=BlockType.STUDY,
                title=f"Study: {assignment.name}",
                description=f"Course: {assignment.course_name}",
                assignment_id=assignment.id,
                course_id=assignment.course_id,
                tags=[assignment.assignment_type.value, assignment.priority.value]
            )
            
            if schedule.add_block(study_block):
                self.logger.info(f"Scheduled {assignment.name} for {start_time.strftime('%H:%M')}")
                # Update available slots
                available_slots.remove(best_slot)
            else:
                self.logger.warning(f"Failed to schedule {assignment.name}")
    
    def _calculate_time_preference_score(self, start_time: datetime) -> float:
        """Calculate preference score for a given time of day"""
        hour = start_time.hour
        
        # Morning preference (9-12): 1.0
        if 9 <= hour < 12:
            return 1.0
        # Afternoon (12-17): 0.8
        elif 12 <= hour < 17:
            return 0.8
        # Evening (17-22): 0.6
        elif 17 <= hour < 22:
            return 0.6
        # Late night: 0.2
        else:
            return 0.2
    
    def _add_breaks_and_optimize(self, schedule: Schedule):
        """Add breaks between study sessions and optimize the schedule"""
        study_blocks = schedule.get_study_blocks()
        
        if len(study_blocks) < 2:
            return
        
        # Sort blocks by start time
        sorted_blocks = sorted(study_blocks, key=lambda x: x.start_time)
        
        # Add breaks between consecutive study blocks
        for i in range(len(sorted_blocks) - 1):
            current_block = sorted_blocks[i]
            next_block = sorted_blocks[i + 1]
            
            # Check if we need a break
            time_between = (next_block.start_time - current_block.end_time).total_seconds() / 60
            
            if time_between >= self.constraints.break_duration:
                # Add a break
                break_start = current_block.end_time
                break_end = break_start + timedelta(minutes=self.constraints.break_duration)
                
                break_block = TimeBlock(
                    start_time=break_start,
                    end_time=break_end,
                    block_type=BlockType.BREAK,
                    title="Break",
                    description="Study break"
                )
                
                schedule.add_block(break_block)
    
    def optimize_existing_schedule(self, schedule: Schedule) -> Schedule:
        """Optimize an existing schedule by rearranging blocks"""
        # This is a placeholder for more advanced optimization
        # Could include:
        # - Moving blocks to better time slots
        # - Consolidating short sessions
        # - Balancing workload across days
        
        return schedule
    
    def get_schedule_summary(self, schedules: List[Schedule]) -> Dict:
        """Get a summary of the created schedules"""
        total_study_time = sum(s.total_study_time for s in schedules)
        total_days = len(schedules)
        avg_study_per_day = total_study_time / total_days if total_days > 0 else 0
        
        return {
            "total_days": total_days,
            "total_study_time_minutes": total_study_time,
            "average_study_per_day_minutes": avg_study_per_day,
            "total_study_time_hours": round(total_study_time / 60, 2),
            "average_study_per_day_hours": round(avg_study_per_day / 60, 2),
            "efficiency_score": sum(s.efficiency_score for s in schedules) / total_days if total_days > 0 else 0
        }
