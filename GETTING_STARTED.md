# Getting Started with MySchedualer

## Overview
MySchedualer is a smart scheduling application that automatically organizes your academic assignments, class schedules, and work commitments into an optimized Google Calendar. This guide will walk you through setting up and using the application.

## Prerequisites
- Python 3.9 or higher
- Canvas LMS account with API access
- Google Calendar account
- Sling work schedule account (optional)

## Installation

### 1. Clone or Download the Project
```bash
git clone <repository-url>
cd mySchedualer
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Set Up Configuration
The application will automatically create a `.env` file template. You'll need to fill in your API credentials:

#### Canvas API Setup
1. Go to your Canvas LMS instance
2. Navigate to Settings → API Access Tokens
3. Generate a new token
4. Copy the token to your `.env` file:
```
CANVAS_API_TOKEN=your_canvas_token_here
CANVAS_API_URL=https://your-institution.canvas.com
```

#### Google Calendar API Setup
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable the Google Calendar API
4. Create credentials (OAuth 2.0 Client ID)
5. Download the credentials JSON file
6. Update your `.env` file:
```
GOOGLE_CREDENTIALS_FILE=path/to/your/credentials.json
GOOGLE_TOKEN_FILE=path/to/save/token.json
```

#### Sling API Setup (Optional)
1. Contact Sling support for API access
2. Update your `.env` file:
```
SLING_API_URL=https://api.sling.is
SLING_API_KEY=your_sling_api_key
SLING_USERNAME=your_username
SLING_PASSWORD=your_password
```

## Basic Usage

### 1. Test Your Setup
```bash
python src/main.py --test
```
This will test your API connections and show which services are working.

### 2. Create a Basic Schedule
```bash
python src/main.py --days 7 --summary
```
This creates a 7-day schedule and shows a detailed summary.

### 3. Post to Google Calendar
```bash
python src/main.py --days 7 --calendar
```
This creates the schedule and posts it directly to your Google Calendar.

### 4. Run the Example
```bash
python example.py
```
This runs a demonstration with sample data to show how the app works.

## Advanced Usage

### Customizing Scheduling Preferences
Edit `config/settings.py` to customize:
- Preferred study hours
- Default study session duration
- Break duration
- Buffer time between tasks

### Command Line Options
- `--days N`: Schedule N days ahead (default: 7)
- `--calendar`: Post schedule to Google Calendar
- `--summary`: Show detailed schedule summary
- `--test`: Test API connections only

### Programmatic Usage
```python
from src.main import MySchedualer

app = MySchedualer()
schedules = app.create_schedule(days_ahead=14)
app.post_to_calendar(schedules)
```

## How It Works

### 1. Data Collection
- **Canvas API**: Fetches assignments, due dates, and course information
- **Sling API**: Gets work schedule and availability
- **Manual Input**: Class schedules (can be imported from external sources)

### 2. Smart Scheduling Algorithm
The scheduler:
- Calculates available time slots (excluding classes and work)
- Prioritizes assignments by urgency and due date
- Distributes homework tasks optimally across available time
- Adds breaks and buffer time
- Considers your preferred study hours

### 3. Calendar Integration
- Creates color-coded events in Google Calendar
- Sets appropriate reminders (15 min and 1 hour before)
- Includes detailed descriptions and metadata
- Syncs across all your devices

## Troubleshooting

### Common Issues

#### Canvas API Connection Failed
- Verify your API token is correct
- Check that your Canvas instance URL is correct
- Ensure your token has the necessary permissions

#### Google Calendar Authentication Failed
- Verify your credentials file path is correct
- Check that the Google Calendar API is enabled
- Ensure you've granted the necessary permissions

#### No Assignments Found
- Check that your Canvas courses are active
- Verify assignments have due dates
- Ensure your API token has access to course data

#### Schedule Creation Failed
- Check the logs in `myschedualer.log`
- Verify that you have available time slots
- Ensure assignments have estimated durations

### Getting Help
1. Check the log file: `myschedualer.log`
2. Run with `--test` to verify API connections
3. Check the example script to see expected behavior
4. Review the configuration in `config/settings.py`

## Customization

### Adding New Assignment Types
Edit `src/models/assignment.py` to add new assignment types and their properties.

### Modifying the Scheduling Algorithm
Edit `src/core/scheduler.py` to customize how tasks are distributed.

### Adding New Data Sources
Create new API classes in `src/api/` following the existing pattern.

## Future Enhancements
- Web-based dashboard interface
- Mobile app integration
- Advanced analytics and reporting
- Integration with other calendar services
- Machine learning for better time estimation
- Social features for study groups

## Contributing
This is a personal project, but feel free to:
- Report bugs and issues
- Suggest new features
- Fork and adapt for your own needs
- Share improvements with the community

## License
This project is provided as-is for educational and personal use.

---

**Need Help?** Check the logs, run the test command, and review this guide. The application is designed to be self-documenting through its logging and error messages.

