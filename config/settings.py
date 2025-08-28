"""
Configuration settings for MySchedualer
"""
import os
from pathlib import Path
from typing import Optional
from pydantic import BaseSettings

class Settings(BaseSettings):
    # App settings
    app_name: str = "MySchedualer"
    debug: bool = False
    timezone: str = "America/New_York"
    
    # Canvas API settings
    canvas_api_url: str = "https://canvas.instructure.com"
    canvas_api_token: Optional[str] = None
    
    # Sling API settings
    sling_api_url: Optional[str] = None
    sling_api_key: Optional[str] = None
    sling_username: Optional[str] = None
    sling_password: Optional[str] = None
    
    # Google Calendar API settings
    google_calendar_id: str = "primary"
    google_credentials_file: Optional[str] = None
    google_token_file: Optional[str] = None
    
    # Scheduling preferences
    default_study_duration: int = 90  # minutes
    break_duration: int = 15  # minutes
    buffer_time: int = 30  # minutes between tasks
    preferred_study_hours: tuple = (9, 22)  # 9 AM to 10 PM
    
    # Database
    database_url: str = "sqlite:///./myschedualer.db"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# Create settings instance
settings = Settings()

# Ensure config directory exists
config_dir = Path(__file__).parent
config_dir.mkdir(exist_ok=True)

# Create .env template if it doesn't exist
env_template = """
# Canvas API Configuration
CANVAS_API_URL=https://your-institution.canvas.com
CANVAS_API_TOKEN=your_canvas_token_here

# Sling API Configuration
SLING_API_URL=https://api.sling.is
SLING_API_KEY=your_sling_api_key
SLING_USERNAME=your_username
SLING_PASSWORD=your_password

# Google Calendar Configuration
GOOGLE_CREDENTIALS_FILE=path/to/credentials.json
GOOGLE_TOKEN_FILE=path/to/token.json

# App Configuration
DEBUG=False
TIMEZONE=America/New_York
"""

env_file = Path(__file__).parent.parent / ".env"
if not env_file.exists():
    with open(env_file, "w") as f:
        f.write(env_template.strip())
