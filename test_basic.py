#!/usr/bin/env python3
"""
Basic test script for MySchedualer components
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_models():
    """Test basic model functionality"""
    print("Testing models...")
    
    try:
        from models.assignment import Assignment, AssignmentType, Priority
        from models.schedule import Schedule, TimeBlock, BlockType
        from models.work_schedule import WorkShift
        
        # Test Assignment model
        assignment = Assignment(
            id=1,
            name="Test Assignment",
            course_id=101,
            course_name="Test Course",
            estimated_duration=60
        )
        print(f"✓ Assignment model: {assignment.name}")
        
        # Test TimeBlock model
        from datetime import datetime
        block = TimeBlock(
            start_time=datetime.now(),
            end_time=datetime.now(),
            block_type=BlockType.STUDY,
            title="Test Block"
        )
        print(f"✓ TimeBlock model: {block.title}")
        
        # Test WorkShift model
        shift = WorkShift(
            id="test1",
            start_time=datetime.now(),
            end_time=datetime.now(),
            role="Tester"
        )
        print(f"✓ WorkShift model: {shift.role}")
        
        print("✓ All models working correctly")
        return True
        
    except Exception as e:
        print(f"✗ Model test failed: {e}")
        return False

def test_scheduler():
    """Test basic scheduler functionality"""
    print("\nTesting scheduler...")
    
    try:
        from core.scheduler import SmartScheduler, SchedulingConstraints
        from datetime import time
        
        constraints = SchedulingConstraints(
            start_time=time(9, 0),
            end_time=time(17, 0)
        )
        
        scheduler = SmartScheduler(constraints)
        print(f"✓ Scheduler initialized with constraints: {constraints.start_time} - {constraints.end_time}")
        
        print("✓ Scheduler working correctly")
        return True
        
    except Exception as e:
        print(f"✗ Scheduler test failed: {e}")
        return False

def test_imports():
    """Test that all imports work"""
    print("\nTesting imports...")
    
    try:
        # Test API imports
        from api.canvas_api import CanvasAPI
        from api.google_calendar_api import GoogleCalendarAPI
        print("✓ API imports successful")
        
        # Test model imports
        from models import Assignment, Schedule, WorkShift
        print("✓ Model imports successful")
        
        # Test core imports
        from core import SmartScheduler
        print("✓ Core imports successful")
        
        print("✓ All imports working correctly")
        return True
        
    except Exception as e:
        print(f"✗ Import test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("MySchedualer - Basic Tests")
    print("=" * 40)
    
    tests = [
        test_imports,
        test_models,
        test_scheduler
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print(f"\n{'='*40}")
    print(f"Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("✓ All tests passed! Basic functionality is working.")
        return 0
    else:
        print("✗ Some tests failed. Check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

