import discord
from discord import app_commands
from discord.ext import commands
import asyncio
from aiohttp import ClientSession
import os
from pathlib import Path

from utils.db import db
from utils.config import BASE_API

class Setup(commands.Cog):
    """Commands for setting up the Canvas bot."""
    
    def __init__(self, bot):
        self.bot = bot
        self.setup_images = {
            "step_1": str(Path(__file__).parent.parent / "step_1.png"),
            "step_2": str(Path(__file__).parent.parent / "step_2.png"),
            "step_3": str(Path(__file__).parent.parent / "step_3.png"),
            "step_4": str(Path(__file__).parent.parent / "step_4.png"),
        }
    
    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        """Send a welcome message when the bot joins a new server."""
        embed = discord.Embed(title="Thanks for adding me to this server! :D")
        embed.add_field(name="Starting Out", value="To start and see a list of commands, type in /help.")
        embed.add_field(name="Setting Up The Bot", value="To setup the bot, use /setup.")
        embed.add_field(name="Bot Uses", value="This bot is used for tracking homework assignments on discord.")
        
        # Find a channel to send the welcome message
        for channel in guild.text_channels:
            if channel.permissions_for(guild.me).send_messages:
                await channel.send('Thanks for inviting me to your server!', embed=embed)
                break
    
    @app_commands.command(name="check", description="Check if you've set up the bot")
    async def check(self, interaction: discord.Interaction):
        """Check if a user has set up the bot."""
        user_id = str(interaction.user.id)
        
        if user_id in db:
            await interaction.response.send_message("You have successfully set up the bot!")
        else:
            await interaction.response.send_message("You have not set up the bot yet. Use the /setup command to begin this process.")
    
    @app_commands.command(name="setup", description="Connect your Canvas account to the bot")
    @app_commands.describe(
        institution="The Canvas institution URL (e.g., 'canvas.instructure.com' or school-specific URL)"
    )
    async def setup(self, interaction: discord.Interaction, institution: str = None):
        """Guide the user through setting up their Canvas API key."""
        # Create the setup embed
        setup_embed = discord.Embed(
            title="Canvas Bot Setup",
            description="This bot will help you track your Canvas assignments and send reminders through Discord."
        )
        setup_embed.add_field(
            name="Introduction", 
            value="Hello, and thanks for using the Canvas HW Bot! Follow the steps below to complete the setup process."
        )
        
        # Send initial message in the channel
        await interaction.response.send_message("Check your DMs for setup instructions. You have 5 minutes to complete this setup!")
        
        # Start the DM process
        try:
            dm_channel = await interaction.user.create_dm()
            await dm_channel.send(embed=setup_embed)
            
            # Step 1 - Handle the Canvas URL
            if institution:
                # Clean up the institution URL if needed
                clean_url = institution
                if not clean_url.startswith('http'):
                    clean_url = f"https://{clean_url}"
                if not clean_url.endswith('/'):
                    clean_url = f"{clean_url}/"
                
                await dm_channel.send(f"Using Canvas URL: **{clean_url}**\nIf this is incorrect, please type a different URL. Otherwise, type 'yes' to confirm.")
                
                # Wait for confirmation
                try:
                    confirmation = await self.bot.wait_for(
                        'message',
                        check=lambda m: m.author == interaction.user and m.channel == dm_channel,
                        timeout=300.0
                    )
                    
                    if confirmation.content.lower() != 'yes':
                        # User provided a different URL
                        clean_url = confirmation.content.strip()
                        if not clean_url.startswith('http'):
                            clean_url = f"https://{clean_url}"
                        if not clean_url.endswith('/'):
                            clean_url = f"{clean_url}/"
                        
                        await dm_channel.send(f"Updated Canvas URL to: **{clean_url}**")
                except asyncio.TimeoutError:
                    await dm_channel.send("Setup timed out. Please try again using the /setup command.")
                    return
            else:
                # Ask for the Canvas URL
                await dm_channel.send("Step 1: Copy paste the link of your Canvas after you log in. This may be something like: https://canvas.instructure.com/ (Make sure to have a slash at the end)")
            
            def check(m):
                return m.channel == dm_channel and m.author == interaction.user
            
            try:
                api_link_msg = await self.bot.wait_for('message', check=check, timeout=300.0)
                api_link = f"{api_link_msg.content}api/v1"
                
                # Step 2-5: Guide through the setup process with images
                await dm_channel.send("Step 2: In Canvas, click account then settings.", file=discord.File(self.setup_images["step_1"]))
                await dm_channel.send("Step 3: In the settings, scroll down to the section that says 'Approved Integrations' and click on the button '+ New Access Token'.", file=discord.File(self.setup_images["step_2"]))
                await dm_channel.send("Step 4: When writing a purpose, write 'Tracking Homework', and leave the expiration date blank. Once you are done, click the 'Generate Token' button.", file=discord.File(self.setup_images["step_3"]))
                await dm_channel.send("Step 5: Copy-paste the access token into this DM, and send the message. Once this is done, this bot should start to work for you if all information is correct!", file=discord.File(self.setup_images["step_4"]))
                
                # Wait for the token
                token_msg = await self.bot.wait_for('message', check=check, timeout=300.0)
                token = token_msg.content
                
                # Validate the token
                headers = {"Authorization": f"Bearer {token}"}
                try:
                    async with ClientSession() as session:
                        async with session.get(url=f"{api_link}/accounts/search", params={"name": "Poway"}, headers=headers) as response:
                            response.raise_for_status()
                    
                    # Save the user's token and settings
                    db[str(interaction.user.id)] = {
                        "id": token,
                        "dm": True,
                        "ping": False,
                        "daily": True,
                        "endpoint": api_link,
                        "starred": False
                    }
                    
                    await dm_channel.send("Congratulations! You have successfully setup the bot! You will receive notifications at 5:00 PST by default about your homework due tomorrow!")
                    
                except Exception as e:
                    await dm_channel.send("I'm sorry, that is not a valid token, or the endpoint link is wrong, setup process terminated.")
            
            except asyncio.TimeoutError:
                await dm_channel.send("I'm sorry, but your setup timed out.")
        
        except discord.Forbidden:
            await interaction.followup.send("I couldn't send you a DM. Please make sure your privacy settings allow DMs from server members.")

async def setup(bot):
    """Add the Setup cog to the bot. This is the cog setup entrypoint called by bot.load_extension()"""
    # Create and add our cog instance to the bot
    cog = Setup(bot)
    # Log that we're adding commands to the bot
    bot.logger.info(f"Adding setup cog commands: {[cmd.name for cmd in cog.get_app_commands()]}")
    await bot.add_cog(cog)
