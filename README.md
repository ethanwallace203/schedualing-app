# MySchedualer - Smart Academic & Work Scheduling App

## Overview
A comprehensive scheduling application that automatically organizes your academic assignments, class schedules, and work commitments into an optimized Google Calendar.

## Features
- **Canvas Integration**: Automatically fetch assignments and due dates
- **Class Schedule Management**: Track class times and locations
- **Work Schedule Sync**: Import availability from Sling
- **Smart Scheduling Algorithm**: Distribute homework tasks optimally
- **Google Calendar Integration**: Post organized schedule automatically
- **Dashboard Interface**: View and manage your schedule

## Project Structure
```
mySchedualer/
├── src/
│   ├── api/           # API integrations (Canvas, Sling, Google)
│   ├── core/          # Scheduling algorithm and business logic
│   ├── models/        # Data models and types
│   ├── services/      # Core services (scheduler, calendar manager)
│   ├── ui/            # User interface components
│   └── utils/         # Helper functions and utilities
├── config/            # Configuration files
├── tests/             # Test files
├── requirements.txt   # Python dependencies
└── README.md         # This file
```

## Core Components

### 1. Data Fetchers
- **CanvasAPI**: Fetch courses, assignments, due dates
- **SlingAPI**: Get work schedule and availability
- **GoogleCalendarAPI**: Read/write calendar events

### 2. Scheduling Engine
- **TimeBlockCalculator**: Determine available time slots
- **TaskDistributor**: Spread homework tasks optimally
- **PriorityManager**: Handle assignment priorities and due dates

### 3. User Interface
- **Dashboard**: Overview of current schedule
- **Settings**: Configure preferences and API keys
- **ScheduleView**: Calendar-style view of tasks

## Implementation Plan

### Phase 1: Foundation
- [ ] Set up project structure
- [ ] Implement basic data models
- [ ] Create configuration system

### Phase 2: API Integration
- [ ] Canvas API integration
- [ ] Sling API integration
- [ ] Google Calendar API setup

### Phase 3: Core Logic
- [ ] Time availability calculator
- [ ] Basic scheduling algorithm
- [ ] Task distribution logic

### Phase 4: Calendar Integration
- [ ] Google Calendar posting
- [ ] Event management
- [ ] Schedule updates

### Phase 5: User Interface
- [ ] Dashboard development
- [ ] Settings configuration
- [ ] Schedule visualization

### Phase 6: Testing & Polish
- [ ] Algorithm optimization
- [ ] Error handling
- [ ] User experience improvements

## Technology Stack
- **Backend**: Python 3.9+
- **APIs**: Canvas API, Sling API, Google Calendar API
- **Scheduling**: Custom algorithm with optimization
- **UI**: Web-based dashboard (Flask/FastAPI + React)
- **Database**: SQLite for local storage, Google Calendar for sync

## Getting Started
1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Configure API keys in `config/settings.py`
4. Run the application: `python src/main.py`

## Configuration
You'll need to set up:
- Canvas API token
- Sling API credentials
- Google Calendar API credentials
- Personal preferences (work hours, study preferences, etc.)

## Contributing
This is a personal project, but feel free to fork and adapt for your own needs!
