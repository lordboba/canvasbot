import discord
from discord import app_commands
from discord.ext import commands
from aiohttp import ClientSession
import asyncio
import datetime
import pytz

from utils.db import db
from utils.helpers import get_homework, get_token

class Homework(commands.Cog):
    """Commands for fetching and displaying homework information."""
    
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="homework", description="Get your homework assignments due soon")
    @app_commands.describe(
        days="Number of days to look ahead for assignments",
        course_filter="Filter by course name (leave empty for all courses)",
        show_overdue="Whether to include overdue assignments"
    )
    @app_commands.choices(days=[
        app_commands.Choice(name="3 days", value=3),
        app_commands.Choice(name="1 week", value=7),
        app_commands.Choice(name="2 weeks", value=14),
        app_commands.Choice(name="1 month", value=30)
    ])
    async def homework(self, interaction: discord.Interaction, 
                       days: int = 7, 
                       course_filter: str = None,
                       show_overdue: bool = True):
        """Get homework assignments from Canvas."""
        await interaction.response.defer(thinking=True)
        
        user_id = str(interaction.user.id)
        token = await get_token(user_id, db)
        
        if not token:
            await interaction.followup.send("I'm sorry, you haven't setup this bot yet. Use the /setup command to begin the setup process.")
            return
        
        try:
            endpoint = db[user_id]["endpoint"]
            headers = {"Authorization": f"Bearer {token}"}
            
            # Get course list based on user settings
            async with ClientSession() as session:
                if db[user_id].get('starred', False):
                    url = f"{endpoint}/users/self/favorites/courses"
                else:
                    url = f"{endpoint}/courses"
                
                async with session.get(
                    url=url, 
                    params={"enrollment_state": "active"}, 
                    headers=headers
                ) as response:
                    if response.status != 200:
                        await interaction.followup.send("There was an error fetching your courses. Please try again later.")
                        return
                    
                    all_courses = await response.json()
                    
                    # Filter courses if a filter was provided
                    if course_filter:
                        course_list = [c for c in all_courses if course_filter.lower() in c.get('name', '').lower()]
                        if not course_list:
                            await interaction.followup.send(f"No courses found matching '{course_filter}'")
                            return
                    else:
                        course_list = all_courses
            
            await interaction.followup.send(f"Looking for assignments due in the next {days} days...")
            
            # Update get_homework call to include the new parameters
            homework_embeds = await get_homework(
                user_id=interaction.user.id, 
                course_list=course_list, 
                headers=headers, 
                endpoint=endpoint, 
                days_to_look_ahead=days, 
                include_overdue=show_overdue
            )
            
            due_soon_embed = homework_embeds[0]
            overdue_embed = homework_embeds[1]
            undated_embed = homework_embeds[2]
            
            # Send embeds based on user settings
            if db[user_id].get("dm", True):
                try:
                    dm_channel = await interaction.user.create_dm()
                    await dm_channel.send(embed=overdue_embed)
                    await dm_channel.send(embed=due_soon_embed)
                    await dm_channel.send(embed=undated_embed)
                except discord.Forbidden:
                    await interaction.followup.send("I couldn't send you a DM. Your homework will be displayed here instead.")
                    await interaction.followup.send(embed=overdue_embed)
                    await interaction.followup.send(embed=due_soon_embed)
                    await interaction.followup.send(embed=undated_embed)
            
            if db[user_id].get("ping", False):
                await interaction.followup.send(embed=overdue_embed)
                await interaction.followup.send(embed=due_soon_embed)
                await interaction.followup.send(embed=undated_embed)
            
            if not db[user_id].get("dm", True) and not db[user_id].get("ping", False):
                await interaction.followup.send("Homework information sent to your DMs!")
        
        except Exception as e:
            await interaction.followup.send(f"An error occurred: {str(e)}")

async def setup(bot):
    """Add the Homework cog to the bot. This is the cog setup entrypoint called by bot.load_extension()"""
    # Create and add our cog instance to the bot
    cog = Homework(bot)
    # Log that we're adding commands to the bot
    bot.logger.info(f"Adding homework cog commands: {[cmd.name for cmd in cog.get_app_commands()]}")
    await bot.add_cog(cog)
