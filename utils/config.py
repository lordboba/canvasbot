import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Bot configuration
PREFIX = "hw "
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

# Developer user IDs
DEVELOPER_IDS = [
    os.getenv("DEVELOPER_ID_1"),
    os.getenv("DEVELOPER_ID_2"),
    os.getenv("DEVELOPER_ID_3")
]

# Base API URL for Canvas
BASE_API = "https://poway.instructure.com/api/v1"
