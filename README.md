# Canvas Discord Bot

A Discord bot for tracking Canvas homework assignments. This bot allows you to receive notifications about your homework assignments directly through Discord.

## Features

- Set up your Canvas API key to connect to your courses
- View homework assignments due soon
- Get daily reminders about upcoming assignments
- Customize notification settings
- Works with starred courses in Canvas

## Requirements

- Python 3.8 or higher
- Discord.py 2.3.2 or higher
- A Discord bot token
- Canvas API access token

## Setup

1. Clone this repository
2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Create a `.env` file in the root directory with the following content:
   ```
   DISCORD_TOKEN=your_discord_bot_token
   DEVELOPER_ID_1=your_discord_user_id
   DEVELOPER_ID_2=another_developer_id (optional)
   DEVELOPER_ID_3=another_developer_id (optional)
   ```
4. Run the bot:
   ```
   python main_new.py
   ```

## Bot Commands

### Slash Commands

- `/setup` - Set up your Canvas API key
- `/check` - Check if you've set up the bot
- `/homework` - View your homework assignments
- `/settings` - View or change your bot settings
- `/feedback` - Send feedback to the bot developers

### Settings Options

- `dm` - Toggle homework reminders in your DMs
- `ping` - Send homework info in the Discord channel
- `daily` - Toggle daily homework reminders
- `starred` - Only show homework from starred courses

## Migration Notes

This bot has been updated from an older codebase to use the latest Discord.py library and implement slash commands. The command structure has been reorganized into cogs for better maintainability.

## License

Copyright © 2021-2025, YaoXiao2, All rights reserved.
