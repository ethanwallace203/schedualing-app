#!/usr/bin/env python3
"""
Example usage of MySchedualer with sample data
"""
from datetime import datetime, timedelta, time
from src.models.assignment import Assignment, AssignmentType, Priority
from src.models.schedule import Schedule, TimeBlock, BlockType
from src.models.work_schedule import WorkShift
from src.core.scheduler import SmartScheduler, SchedulingConstraints

def create_sample_data():
    """Create sample data for demonstration"""
    
    # Sample assignments
    assignments = [
        Assignment(
            id=1,
            name="Math Homework - Chapter 5",
            course_id=101,
            course_name="Calculus I",
            due_date=datetime.now() + timedelta(days=3),
            estimated_duration=90,
            difficulty=3,
            assignment_type=AssignmentType.HOMEWORK,
            priority=Priority.HIGH
        ),
        Assignment(
            id=2,
            name="Essay - Literary Analysis",
            course_id=102,
            course_name="English Literature",
            due_date=datetime.now() + timedelta(days=7),
            estimated_duration=180,
            difficulty=4,
            assignment_type=AssignmentType.ESSAY,
            priority=Priority.MEDIUM
        ),
        Assignment(
            id=3,
            name="Physics Lab Report",
            course_id=103,
            course_name="Physics I",
            due_date=datetime.now() + timedelta(days=2),
            estimated_duration=120,
            difficulty=3,
            assignment_type=AssignmentType.LAB_REPORT,
            priority=Priority.URGENT
        ),
        Assignment(
            id=4,
            name="History Quiz",
            course_id=104,
            course_name="World History",
            due_date=datetime.now() + timedelta(days=5),
            estimated_duration=45,
            difficulty=2,
            assignment_type=AssignmentType.QUIZ,
            priority=Priority.MEDIUM
        )
    ]
    
    # Sample work shifts
    work_shifts = [
        WorkShift(
            id="shift1",
            start_time=datetime.now().replace(hour=9, minute=0, second=0, microsecond=0),
            end_time=datetime.now().replace(hour=17, minute=0, second=0, microsecond=0),
            role="Cashier",
            location="Grocery Store"
        ),
        WorkShift(
            id="shift2",
            start_time=(datetime.now() + timedelta(days=1)).replace(hour=10, minute=0, second=0, microsecond=0),
            end_time=(datetime.now() + timedelta(days=1)).replace(hour=16, minute=0, second=0, microsecond=0),
            role="Cashier",
            location="Grocery Store"
        )
    ]
    
    # Sample class schedule
    class_schedule = [
        TimeBlock(
            start_time=datetime.now().replace(hour=14, minute=0, second=0, microsecond=0),
            end_time=datetime.now().replace(hour=15, minute=30, second=0, microsecond=0),
            block_type=BlockType.CLASS,
            title="Calculus I Lecture",
            description="Room 201, Building A",
            is_fixed=True
        ),
        TimeBlock(
            start_time=(datetime.now() + timedelta(days=1)).replace(hour=10, minute=0, second=0, microsecond=0),
            end_time=(datetime.now() + timedelta(days=1)).replace(hour=11, minute=30, second=0, microsecond=0),
            block_type=BlockType.CLASS,
            title="English Literature",
            description="Room 105, Building B",
            is_fixed=True
        )
    ]
    
    return assignments, work_shifts, class_schedule

def main():
    """Main example function"""
    print("MySchedualer - Example Usage")
    print("=" * 50)
    
    # Create sample data
    assignments, work_shifts, class_schedule = create_sample_data()
    
    print(f"Sample Data Created:")
    print(f"  - {len(assignments)} assignments")
    print(f"  - {len(work_shifts)} work shifts")
    print(f"  - {len(class_schedule)} class blocks")
    
    # Initialize scheduler
    constraints = SchedulingConstraints(
        start_time=time(8, 0),    # 8 AM
        end_time=time(22, 0),     # 10 PM
        max_study_session=120,     # 2 hours max
        min_study_session=30,      # 30 min min
        break_duration=15,         # 15 min breaks
        buffer_time=30             # 30 min buffer
    )
    
    scheduler = SmartScheduler(constraints)
    
    # Create schedule for next 7 days
    start_date = datetime.now()
    schedules = scheduler.create_schedule(
        assignments=assignments,
        work_shifts=work_shifts,
        class_schedule=class_schedule,
        start_date=start_date,
        days_ahead=7
    )
    
    print(f"\nSchedule created for {len(schedules)} days")
    
    # Show schedule summary
    scheduler.show_schedule_summary(schedules)
    
    # Show detailed daily schedules
    print("\n" + "=" * 60)
    print("DETAILED DAILY SCHEDULES")
    print("=" * 60)
    
    for i, schedule in enumerate(schedules):
        if schedule.time_blocks:
            print(f"\nDay {i+1}: {schedule.date.strftime('%A, %B %d')}")
            print("-" * 40)
            
            # Sort blocks by start time
            sorted_blocks = sorted(schedule.time_blocks, key=lambda x: x.start_time)
            
            for block in sorted_blocks:
                start_str = block.start_time.strftime("%H:%M")
                end_str = block.end_time.strftime("%H:%M")
                duration = block.duration_minutes
                
                print(f"  {start_str}-{end_str} ({duration:3d} min) [{block.block_type.value:>8}] {block.title}")
                if block.description:
                    print(f"    {block.description}")
            
            # Daily stats
            study_time = schedule.total_study_time
            break_time = schedule.total_break_time
            efficiency = schedule.efficiency_score
            
            print(f"\n  Daily Stats: Study: {study_time} min, Breaks: {break_time} min, Efficiency: {efficiency:.1%}")
    
    print("\n" + "=" * 60)
    print("Example completed successfully!")
    print("=" * 60)

if __name__ == "__main__":
    main()
