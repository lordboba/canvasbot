import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional

class Help(commands.Cog):
    """Custom help command using slash commands."""
    
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="help", description="Get help with the Canvas bot")
    @app_commands.describe(
        command="Get details about a specific command"
    )
    @app_commands.choices(command=[
        app_commands.Choice(name="setup", value="setup"),
        app_commands.Choice(name="check", value="check"),
        app_commands.Choice(name="homework", value="homework"),
        app_commands.Choice(name="settings", value="settings"),
        app_commands.Choice(name="invite", value="invite"),
        app_commands.Choice(name="help", value="help")
    ])
    async def help_command(self, interaction: discord.Interaction, command: Optional[str] = None):
        """Display help information for the bot."""
        
        # If a specific command is requested
        if command:
            await self._show_command_help(interaction, command)
            return
            
        # Create the main help embed
        help_embed = discord.Embed(
            title="Canvas Bot Help",
            description="This bot connects to your Canvas account to help you track assignments and get reminders.",
            color=discord.Color.blue()
        )
        
        # Add fields for each category of commands
        help_embed.add_field(
            name="📝 Setup Commands",
            value="`/setup` - Connect your Canvas account\n"
                  "`/check` - Check if you've set up the bot",
            inline=False
        )
        
        help_embed.add_field(
            name="📚 Assignment Commands",
            value="`/homework` - Get your assignments\n",
            inline=False
        )
        
        help_embed.add_field(
            name="⚙️ Configuration Commands",
            value="`/settings` - Configure your preferences\n",
            inline=False
        )
        
        help_embed.add_field(
            name="ℹ️ Other Commands",
            value="`/invite` - Get a link to add the bot to another server\n"
                  "`/help` - Show this help message",
            inline=False
        )
        
        # Add usage tip
        help_embed.add_field(
            name="Detailed Help",
            value="To get detailed help for a command, use `/help command:name`",
            inline=False
        )
        
        # Add footer
        help_embed.set_footer(text="Canvas Bot • Made to make student life easier")
        
        await interaction.response.send_message(embed=help_embed, ephemeral=True)
    
    async def _show_command_help(self, interaction: discord.Interaction, command_name: str):
        """Show help for a specific command."""
        
        if command_name == "setup":
            embed = discord.Embed(
                title="Command: /setup",
                description="Connect your Canvas account to the bot.",
                color=discord.Color.blue()
            )
            embed.add_field(
                name="Usage",
                value="`/setup [institution]`",
                inline=False
            )
            embed.add_field(
                name="Parameters",
                value="`institution` - (Optional) The Canvas institution URL (e.g., 'canvas.instructure.com')",
                inline=False
            )
            embed.add_field(
                name="Details",
                value="This command starts a guided setup process in your DMs to connect your Canvas account.",
                inline=False
            )
            
        elif command_name == "check":
            embed = discord.Embed(
                title="Command: /check",
                description="Check if you've set up the bot correctly.",
                color=discord.Color.blue()
            )
            embed.add_field(
                name="Usage",
                value="`/check`",
                inline=False
            )
            embed.add_field(
                name="Details",
                value="Confirms whether your Canvas account is connected and working properly.",
                inline=False
            )
            
        elif command_name == "homework":
            embed = discord.Embed(
                title="Command: /homework",
                description="Get your Canvas assignments.",
                color=discord.Color.blue()
            )
            embed.add_field(
                name="Usage",
                value="`/homework [days] [course_filter] [show_overdue]`",
                inline=False
            )
            embed.add_field(
                name="Parameters",
                value="`days` - (Optional) Number of days to look ahead for assignments\n"
                      "`course_filter` - (Optional) Filter by course name\n"
                      "`show_overdue` - (Optional) Whether to include overdue assignments",
                inline=False
            )
            embed.add_field(
                name="Details",
                value="Fetches and displays your upcoming Canvas assignments based on the parameters you specify.",
                inline=False
            )
            
        elif command_name == "settings":
            embed = discord.Embed(
                title="Command: /settings",
                description="View or change your bot settings.",
                color=discord.Color.blue()
            )
            embed.add_field(
                name="Usage",
                value="`/settings [setting] [state]`",
                inline=False
            )
            embed.add_field(
                name="Parameters",
                value="`setting` - (Optional) The setting to change\n"
                      "`state` - (Optional) The new state for the setting (on/off)",
                inline=False
            )
            embed.add_field(
                name="Available Settings",
                value="`dm` - Toggle homework reminders in your DMs\n"
                      "`ping` - Toggle sending homework info in the channel\n"
                      "`daily` - Toggle daily reminders\n"
                      "`starred` - Toggle using only starred courses",
                inline=False
            )
            
        elif command_name == "invite":
            embed = discord.Embed(
                title="Command: /invite",
                description="Get an invite link for the bot.",
                color=discord.Color.blue()
            )
            embed.add_field(
                name="Usage",
                value="`/invite [permissions] [ephemeral]`",
                inline=False
            )
            embed.add_field(
                name="Parameters",
                value="`permissions` - (Optional) Permission level for the bot\n"
                      "`ephemeral` - (Optional) Whether to show the link only to you",
                inline=False
            )
            
        elif command_name == "help":
            embed = discord.Embed(
                title="Command: /help",
                description="Get help with the Canvas bot.",
                color=discord.Color.blue()
            )
            embed.add_field(
                name="Usage",
                value="`/help [command]`",
                inline=False
            )
            embed.add_field(
                name="Parameters",
                value="`command` - (Optional) Get details about a specific command",
                inline=False
            )
            
        else:
            embed = discord.Embed(
                title="Error",
                description=f"Command `/{command_name}` not found.",
                color=discord.Color.red()
            )
            
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    """Add the Help cog to the bot. This is the cog setup entrypoint called by bot.load_extension()"""
    # Create and add our cog instance to the bot
    cog = Help(bot)
    # Log that we're adding commands to the bot
    bot.logger.info(f"Adding help cog commands: {[cmd.name for cmd in cog.get_app_commands()]}")
    await bot.add_cog(cog)
