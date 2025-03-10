# Environment Variables Setup Instructions

To ensure your bot works correctly with slash commands, please make sure your `.env` file contains the following variables:

```
# Bot Token
DISCORD_TOKEN=your_discord_token

# Application ID (important for slash commands)
APPLICATION_ID=your_application_id

# Development Guild ID (for faster command updates during development)
DEV_GUILD_ID=your_test_server_id

# Developer user IDs for feedback
DEVELOPER_ID_1=your_user_id
DEVELOPER_ID_2=optional_second_dev_id
DEVELOPER_ID_3=optional_third_dev_id
```

## How to Find These Values

1. **APPLICATION_ID**: This is the same as your bot's client ID. You can find it on the Discord Developer Portal:
   - Go to https://discord.com/developers/applications
   - Select your application
   - Look for "Application ID" on the General Information page

2. **DEV_GUILD_ID**: This is the ID of a server where you want to test your commands (they'll update instantly):
   - Enable Developer Mode in Discord (User Settings > Advanced)
   - Right-click on your test server and click "Copy ID"

After updating your `.env` file with these values, restart the bot to apply the changes.
