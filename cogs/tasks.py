import discord
from discord import app_commands
from discord.ext import commands, tasks
import datetime as dt
import asyncio
from aiohttp import ClientSession

from utils.db import db
from utils.helpers import get_homework

class TasksCog(commands.Cog):
    """Handles scheduled tasks like daily homework reminders."""
    
    def __init__(self, bot):
        self.bot = bot
        self.daily_homework_task.start()
    
    def cog_unload(self):
        """Cancel tasks when the cog is unloaded."""
        self.daily_homework_task.cancel()
    
    @tasks.loop(hours=24)
    async def daily_homework_task(self):
        """Send daily homework reminders to all users who have enabled them."""
        # Get all users from the database
        users = db.keys()
        
        for user_id in users:
            user_data = db[user_id]
            
            # Skip users who have disabled daily reminders
            if not user_data.get('daily', True):
                continue
            
            try:
                # Get user's token and endpoint
                token = user_data.get('id')
                endpoint = user_data.get('endpoint')
                headers = {"Authorization": f"Bearer {token}"}
                
                # Get course list based on user settings
                async with ClientSession() as session:
                    if user_data.get('starred', False):
                        url = f"{endpoint}/users/self/favorites/courses"
                    else:
                        url = f"{endpoint}/courses"
                    
                    async with session.get(
                        url=url, 
                        params={"enrollment_state": "active"}, 
                        headers=headers
                    ) as response:
                        if response.status != 200:
                            continue
                        
                        course_list = await response.json()
                
                # Get homework assignments
                homework_embeds = await get_homework(user_id, course_list, headers, endpoint)
                due_soon_embed = homework_embeds[0]
                overdue_embed = homework_embeds[1]
                undated_embed = homework_embeds[2]
                
                # Send DMs to the user
                try:
                    discord_user = await self.bot.fetch_user(int(user_id))
                    await discord_user.send(embed=overdue_embed)
                    await discord_user.send(embed=due_soon_embed)
                    await discord_user.send(embed=undated_embed)
                except (discord.NotFound, discord.Forbidden):
                    # User not found or DMs are blocked
                    continue
            
            except Exception as e:
                # Log the error but continue with other users
                print(f"Error sending daily homework reminder to user {user_id}: {e}")
                continue
    
    @daily_homework_task.before_loop
    async def before_daily_homework_task(self):
        """Wait until the specified time before starting the daily homework task."""
        await self.bot.wait_until_ready()
        
        # Set the time to run the task (5:00 AM PST)
        hour = 5
        minute = 0
        
        now = dt.datetime.now()
        future = dt.datetime(now.year, now.month, now.day, hour, minute)
        
        # If it's already past the scheduled time, schedule for tomorrow
        if now.hour >= hour and now.minute > minute:
            future += dt.timedelta(days=1)
        
        # Calculate seconds until the scheduled time
        seconds_until_scheduled_time = (future - now).total_seconds()
        
        # Wait until the scheduled time
        await asyncio.sleep(seconds_until_scheduled_time)
    
    @app_commands.command(name="invite", description="Get the invite link for the bot")
    @app_commands.describe(
        permissions="Permission level to grant the bot",
        ephemeral="Whether to show the invite link only to you"
    )
    @app_commands.choices(permissions=[
        app_commands.Choice(name="Administrator (Full Access)", value="admin"),
        app_commands.Choice(name="Basic (Recommended)", value="basic")
    ])
    async def invite(self, 
                      interaction: discord.Interaction, 
                      permissions: str = "basic", 
                      ephemeral: bool = True):
        """Get the invite link for the bot."""
        # Set appropriate permissions based on choice
        if permissions == "admin":
            perms = discord.Permissions(administrator=True)
        else:  # basic permissions
            perms = discord.Permissions(
                send_messages=True,
                read_messages=True,
                embed_links=True,
                attach_files=True,
                read_message_history=True,
                add_reactions=True,
                use_application_commands=True
            )
            
        # Create OAuth URL
        invite_url = discord.utils.oauth_url(
            self.bot.user.id,
            permissions=perms,
            scopes=("bot", "applications.commands")
        )
            
        # Create an embed with bot information
        invite_embed = discord.Embed(
            title="Invite Canvas Bot to Your Server",
            description="Share this bot with your classmates to help everyone keep track of assignments!",
            color=discord.Color.blue()
        )
        
        # Bot details
        invite_embed.add_field(
            name="Features",
            value="✅ Track Canvas assignments\n✅ Get assignment reminders\n✅ Daily homework updates",
            inline=True
        )
        
        invite_embed.add_field(
            name="Permissions",
            value=f"Selected: **{permissions.title()}**\nYou can change these on the Discord authorization page if needed.",
            inline=True
        )
        
        invite_embed.add_field(
            name="Invite Link",
            value=f"[Click here to add Canvas Bot to your server]({invite_url})",
            inline=False
        )
        
        # Add bot avatar if available
        if self.bot.user.avatar:
            invite_embed.set_thumbnail(url=self.bot.user.avatar.url)
            
        await interaction.response.send_message(embed=invite_embed, ephemeral=ephemeral)

async def setup(bot):
    """Add the Tasks cog to the bot. This is the cog setup entrypoint called by bot.load_extension()"""
    # Create and add our cog instance to the bot
    cog = TasksCog(bot)
    # Log that we're adding commands to the bot
    bot.logger.info(f"Adding tasks cog commands: {[cmd.name for cmd in cog.get_app_commands()]}")
    await bot.add_cog(cog)
