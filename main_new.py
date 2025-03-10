import os
import asyncio
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
import logging
from pathlib import Path

from keep_alive import keep_alive
from utils.db import db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('canvasbot')

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Setup intents
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True  # Required for slash commands

class CanvasBot(commands.Bot):
    """Discord bot for tracking Canvas homework assignments."""
    
    def __init__(self):
        super().__init__(
            command_prefix=commands.when_mentioned,  # Only respond to mentions, no text prefix
            intents=intents,
            activity=discord.Game(name="Use /help for commands"),
            description="A Discord bot for tracking Canvas homework assignments",
            # Ensure application commands are enabled
            application_id=os.getenv('APPLICATION_ID')
        )
        self.synced = False
        self.logger = logger
    
    async def setup_hook(self):
        """Load cogs and sync app commands."""
        # First load all cogs
        logger.info("Starting to load cogs...")
        loaded_cogs = 0
        
        for cog_file in Path('./cogs').glob('*.py'):
            if cog_file.name.startswith('__'):
                continue
            
            cog_name = f"cogs.{cog_file.stem}"
            try:
                await self.load_extension(cog_name)
                loaded_cogs += 1
                logger.info(f"Loaded cog: {cog_name}")
            except Exception as e:
                logger.error(f"Failed to load cog {cog_name}: {e}")
        
        logger.info(f"Successfully loaded {loaded_cogs} cogs")
        
        # Debug: Print all commands in the tree before syncing
        commands_count = len(self.tree.get_commands())
        logger.info(f"Found {commands_count} commands in the tree before syncing")
        
        for command in self.tree.get_commands():
            logger.info(f"Command in tree: {command.name} - {type(command).__name__}")
        
        # Sync commands with Discord
        try:
            # Get environment variable for development guild ID (if set)
            dev_guild_id = os.getenv('DEV_GUILD_ID')
            
            # If in development, sync to a specific guild for faster updates
            if dev_guild_id:
                try:
                    dev_guild = discord.Object(id=int(dev_guild_id))
                    guild_commands = await self.tree.sync(guild=dev_guild)
                    logger.info(f"Synced {len(guild_commands)} commands to development guild {dev_guild_id}")
                    for cmd in guild_commands:
                        logger.info(f"  - Guild command: {cmd.name} (ID: {cmd.id})")
                except Exception as guild_sync_error:
                    logger.error(f"Failed to sync guild commands: {guild_sync_error}")
            
            # Always sync globally as well
            logger.info("Attempting to sync global commands...")
            # This syncs globally - can take up to an hour to propagate
            synced_commands = await self.tree.sync()
            
            logger.info(f"Synced {len(synced_commands)} global commands successfully")
            logger.info("Synced commands:")
            for cmd in synced_commands:
                logger.info(f"  - {cmd.name} (ID: {cmd.id})")
                
            if len(synced_commands) == 0:
                logger.warning("No commands were synced! This suggests that either no commands were registered or there was an issue with registration.")
        except Exception as e:
            logger.error(f"Failed to sync commands: {e}")
            # Print more detailed error information
            import traceback
            logger.error(traceback.format_exc())
    
    async def on_ready(self):
        """Event triggered when the bot is ready."""
        logger.info(f"Logged in as {self.user} (ID: {self.user.id})")
        logger.info(f"Bot is in {len(self.guilds)} guilds")
        
        # Log the invite link
        app_info = await self.application_info()
        invite_url = discord.utils.oauth_url(
            app_info.id,
            permissions=discord.Permissions(permissions=8),
            scopes=("bot", "applications.commands")
        )
        logger.info(f"Invite URL: {invite_url}")
        logger.info("Bot is ready!")
    
    async def on_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        """Handle app command errors."""
        error_msg = f"Error in command '{interaction.command.name if interaction.command else 'unknown'}': {error}"
        
        # Log the full traceback for debugging
        import traceback
        tb = ''.join(traceback.format_exception(type(error), error, error.__traceback__))
        logger.error(f"Command error full traceback:\n{tb}")
        
        # Provide a user-friendly message
        if isinstance(error, app_commands.CommandOnCooldown):
            await interaction.response.send_message(
                f"This command is on cooldown. Try again in {error.retry_after:.2f} seconds.",
                ephemeral=True
            )
        elif isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message(
                f"You don't have the required permissions to use this command.",
                ephemeral=True
            )
        else:
            # Generic error message for other errors
            await interaction.response.send_message(
                f"An error occurred while executing this command. The error has been logged.",
                ephemeral=True
            )
            logger.error(error_msg)
    
    async def on_command_error(self, ctx, error):
        """Handle command errors."""
        if isinstance(error, commands.CommandNotFound):
            return
        
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Missing required argument: {error.param}")
            return
        
        logger.error(f"Command error: {error}")
        await ctx.send(f"An error occurred: {error}")

async def main():
    """Main entry point for the bot."""
    bot = CanvasBot()
    
    # Start the Flask server to keep the bot alive
    keep_alive()
    
    async with bot:
        try:
            await bot.start(TOKEN)
        except discord.LoginFailure:
            logger.error("Invalid token provided")
        except Exception as e:
            logger.error(f"An error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(main())
