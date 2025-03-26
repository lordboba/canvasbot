import discord
from discord import app_commands
from discord.ext import commands
from typing import Literal, Optional
import datetime
import pytz

from utils.db_sqlite import db

class Settings(commands.Cog):
    """Commands for configuring bot settings."""
    
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="settings", description="View or change your bot settings")
    @app_commands.describe(
        setting="The setting to view or change",
        state="The new state for the setting (on/off)"
    )
    @app_commands.choices(setting=[
        app_commands.Choice(name="DM Messages", value="dm"),
        app_commands.Choice(name="Channel Messages", value="ping"),
        app_commands.Choice(name="Daily Reminders", value="daily"),
        app_commands.Choice(name="Starred Courses Only", value="starred")
    ])
    @app_commands.choices(state=[
        app_commands.Choice(name="On", value="on"),
        app_commands.Choice(name="Off", value="off")
    ])
    async def settings(
        self, 
        interaction: discord.Interaction, 
        setting: Optional[str] = None,
        state: Optional[str] = None
    ):
        """View or change bot settings."""
        user_id = str(interaction.user.id)
        
        if user_id not in db:
            await interaction.response.send_message(
                "You have not set up the bot yet. Use the /setup command to begin this process and to be able to configure your settings."
            )
            return
        
        user_settings = db[user_id]
        
        # If no state is provided, show current settings
        if state is None:
            embed = discord.Embed(title="Your Current Settings For the Canvas Bot")
            
            if setting is None or setting == "dm":
                embed.add_field(
                    name="dm:",
                    value=f"**Description:** Toggles Homework Reminders In Your DMs\n**Current Status:** {('Off', 'On')[user_settings.get('dm', True)]}"
                )
            
            if setting is None or setting == "ping":
                embed.add_field(
                    name="ping:",
                    value=f"**Description:** Sends Homework Info in the discord channel when using '/homework'\n**Current Status:** {('Off', 'On')[user_settings.get('ping', False)]}"
                )
            
            if setting is None or setting == "daily":
                daily_status = ('Off', 'On')[user_settings.get('daily', True)]
                
                # Check if user has muted notifications
                if 'muted_until' in user_settings:
                    try:
                        mute_end_time = datetime.datetime.fromisoformat(user_settings['muted_until'])
                        mute_end_display = mute_end_time.strftime("%B %d, %Y at %I:%M %p %Z")
                        
                        embed.add_field(
                            name="daily:",
                            value=f"**Description:** Sends Homework Reminders To You Daily\n**Current Status:** {daily_status}\n**Currently Muted Until:** {mute_end_display}"
                        )
                    except (ValueError, TypeError):
                        # If there's an issue with the date format, just display normal status
                        embed.add_field(
                            name="daily:",
                            value=f"**Description:** Sends Homework Reminders To You Daily\n**Current Status:** {daily_status}"
                        )
                else:
                    embed.add_field(
                        name="daily:",
                        value=f"**Description:** Sends Homework Reminders To You Daily\n**Current Status:** {daily_status}"
                    )
            
            if setting is None or setting == "starred":
                embed.add_field(
                    name="starred:",
                    value=f"**Description:** Returns homework only on starred courses\n**Current Status:** {('Off', 'On')[user_settings.get('starred', False)]}"
                )
            
            await interaction.response.send_message(embed=embed)
        
        # If state is provided, update the setting
        else:
            if setting not in ["dm", "ping", "daily", "starred"]:
                await interaction.response.send_message("I'm sorry, that setting is not available.")
                return
            
            new_state = state == "on"
            user_settings[setting] = new_state
            db[user_id] = user_settings
            
            await interaction.response.send_message(f"{setting} configuration successfully set to {state}!")
    
    @app_commands.command(name="mute", description="Mute daily notifications for a specified number of days")
    @app_commands.describe(days="Number of days to mute notifications (1-30)")
    async def mute(self, interaction: discord.Interaction, days: int):
        """Mute daily notifications for a specified number of days."""
        user_id = str(interaction.user.id)
        
        # Check if user has set up the bot
        if user_id not in db:
            await interaction.response.send_message(
                "You have not set up the bot yet. Use the /setup command to begin this process."
            )
            return
        
        # Validate days input
        if days < 1 or days > 30:
            await interaction.response.send_message(
                "Please provide a number of days between 1 and 30.",
                ephemeral=True
            )
            return
        
        # Calculate the end date for the mute
        current_time = datetime.datetime.now(pytz.UTC)
        mute_end_time = current_time + datetime.timedelta(days=days)
        
        # Format in ISO format for storage and display
        mute_end_iso = mute_end_time.isoformat()
        mute_end_display = mute_end_time.strftime("%B %d, %Y at %I:%M %p %Z")
        
        # Update user settings
        user_settings = db[user_id]
        user_settings['muted_until'] = mute_end_iso
        db[user_id] = user_settings
        
        # Create a response embed
        embed = discord.Embed(
            title="Notifications Muted",
            description=f"Daily notifications have been muted until {mute_end_display}.",
            color=discord.Color.blue()
        )
        embed.add_field(
            name="Unmute Early",
            value="You can unmute notifications at any time using the `/unmute` command."
        )
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="unmute", description="Unmute daily notifications")
    async def unmute(self, interaction: discord.Interaction):
        """Unmute daily notifications immediately."""
        user_id = str(interaction.user.id)
        
        # Check if user has set up the bot
        if user_id not in db:
            await interaction.response.send_message(
                "You have not set up the bot yet. Use the /setup command to begin this process."
            )
            return
        
        user_settings = db[user_id]
        
        # Check if user is muted
        if 'muted_until' not in user_settings:
            await interaction.response.send_message(
                "Your notifications are not currently muted.",
                ephemeral=True
            )
            return
        
        # Remove mute
        user_settings.pop('muted_until', None)
        db[user_id] = user_settings
        
        await interaction.response.send_message(
            "Daily notifications have been unmuted. You will now receive daily homework reminders again."
        )
    
    @app_commands.command(name="feedback", description="Send feedback to the bot developers")
    async def feedback(self, interaction: discord.Interaction):
        """Send feedback to the bot developers."""
        await interaction.response.send_message("Read the DM that I sent you.")
        
        try:
            # Create a DM channel
            dm_channel = await interaction.user.create_dm()
            
            # Send initial message
            setup_embed = discord.Embed(title="Feedback Form")
            setup_embed.add_field(
                name="Instructions", 
                value="Please write what you want to send to the creator of this discord bot. Please be mindful of what you send. You have 5 minutes."
            )
            await dm_channel.send(embed=setup_embed)
            
            # Wait for feedback message
            def check(m):
                return m.channel == dm_channel and m.author == interaction.user
            
            try:
                feedback_msg = await self.bot.wait_for('message', check=check, timeout=300.0)
                feedback_content = feedback_msg.content
                
                # Send feedback to developers
                from utils.config import DEVELOPER_IDS
                
                for dev_id in DEVELOPER_IDS:
                    if dev_id:
                        try:
                            dev_user = await self.bot.fetch_user(int(dev_id))
                            await dev_user.send(f"{interaction.user.name} says: {feedback_content}")
                        except:
                            pass
                
                await dm_channel.send("Thank you for your feedback! It has been sent to the developers.")
            
            except asyncio.TimeoutError:
                await dm_channel.send("I'm sorry, but your feedback session has timed out.")
        
        except discord.Forbidden:
            await interaction.followup.send("I couldn't send you a DM. Please make sure your privacy settings allow DMs from server members.")

async def setup(bot):
    """Add the Settings cog to the bot. This is the cog setup entrypoint called by bot.load_extension()"""
    # Create and add our cog instance to the bot
    cog = Settings(bot)
    # Log that we're adding commands to the bot
    bot.logger.info(f"Adding settings cog commands: {[cmd.name for cmd in cog.get_app_commands()]}")
    await bot.add_cog(cog)
