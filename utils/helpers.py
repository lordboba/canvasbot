import discord
from discord import Embed, Color
import datetime as dt
from aiohttp import ClientSession
import asyncio
from datetime import datetime, timedelta
import pytz

async def get_token(user_id, db):
    """Get the Canvas API token for a user."""
    if str(user_id) not in db:
        return None
    return db[str(user_id)].get("id")

async def get_homework(user_id, course_list, headers, endpoint, days_to_look_ahead=7, include_overdue=True):
    """Fetch homework assignments from Canvas API.
    
    Args:
        user_id: Discord user ID
        course_list: List of Canvas courses
        headers: Authorization headers for Canvas API
        endpoint: Canvas API endpoint
        days_to_look_ahead: Number of days to look ahead for assignments (default: 7)
        include_overdue: Whether to include overdue assignments (default: True)
    """
    # Create embeds for different types of assignments
    overdue_embed = Embed(title=f"Overdue Assignments", color=Color.red())
    due_soon_embed = Embed(title=f"Assignments Due in the Next {days_to_look_ahead} Days", color=Color.blue())
    undated_embed = Embed(title="Undated Assignments", color=Color.green())
    
    # Set embed descriptions
    overdue_embed.description = "These assignments are past their due date."
    due_soon_embed.description = f"Here are your upcoming assignments due within {days_to_look_ahead} days."
    undated_embed.description = "These assignments have no due date set."
    
    # Get current time in UTC (timezone-aware)
    now = datetime.now(pytz.UTC)
    
    # Process each course
    for course in course_list:
        # Fetch overdue assignments
        async with ClientSession() as session:
            params = {"bucket": "overdue", "order_by": "due_at"}
            async with session.get(
                url=f"{endpoint}/courses/{course['id']}/assignments", 
                params=params, 
                headers=headers
            ) as response:
                if response.status == 200:
                    assignments = await response.json()
                    field_content = ""
                    
                    # Track the field content length to avoid exceeding Discord's limit
                    assignment_count = 0
                    max_assignments = 5  # Adjust as needed to stay under 1024 chars
                    
                    for assignment in assignments:
                        if assignment.get('due_at') and assignment_count < max_assignments:
                            try:
                                # Parse the due date string to a timezone-aware datetime
                                due_date_str = assignment['due_at']
                                due_date = datetime.fromisoformat(due_date_str.replace('Z', '+00:00'))
                                # Format nicely but keep it concise
                                formatted_date = due_date.strftime('%b %d, %Y')
                                # Truncate assignment name if too long
                                name = assignment['name']
                                if len(name) > 40:
                                    name = name[:37] + "..."
                                
                                field_content += f"\n• **{name}** - Due: {formatted_date}"  
                                assignment_count += 1
                            except (ValueError, TypeError):
                                # If parsing fails, just use the raw string
                                field_content += f"\n• **{assignment['name']}**\n  Due: {assignment.get('due_at', 'unknown date')}"
                    
                    if field_content:
                        overdue_embed.add_field(
                            name=f"Overdue For {course['name']}:",
                            value=field_content,
                            inline=False
                        )
        
        # Fetch upcoming assignments
        async with ClientSession() as session:
            params = {"bucket": "future", "order_by": "due_at"}
            async with session.get(
                url=f"{endpoint}/courses/{course['id']}/assignments", 
                params=params, 
                headers=headers
            ) as response:
                if response.status == 200:
                    assignments = await response.json()
                    field_content = ""
                    
                    # Calculate the cutoff date for assignments
                    # Use the now variable defined at the beginning of the function
                    cutoff_date = now + timedelta(days=days_to_look_ahead)
                    
                    # Track assignment count to avoid exceeding Discord's field length limit
                    assignment_count = 0
                    max_assignments = 5  # Adjust as needed to stay under 1024 chars
                    
                    for assignment in assignments:
                        if assignment.get('due_at') and assignment_count < max_assignments:
                            try:
                                # Parse the due date
                                due_date_str = assignment['due_at']
                                due_date = datetime.fromisoformat(due_date_str.replace('Z', '+00:00'))
                                
                                # Only include assignments due within the specified days
                                if due_date <= cutoff_date:
                                    # Truncate assignment name if too long
                                    name = assignment['name']
                                    if len(name) > 40:
                                        name = name[:37] + "..."
                                    
                                    # Format the due date concisely
                                    formatted_date = due_date.strftime('%b %d, %Y')
                                    field_content += f"\n• **{name}** - Due: {formatted_date}"
                                    assignment_count += 1
                            except (ValueError, TypeError):
                                continue
                    
                    if field_content:
                        due_soon_embed.add_field(
                            name=f"Due Soon For {course['name']}:",
                            value=field_content,
                            inline=False
                        )
        
        # Fetch undated assignments
        async with ClientSession() as session:
            params = {"bucket": "undated"}
            async with session.get(
                url=f"{endpoint}/courses/{course['id']}/assignments", 
                params=params, 
                headers=headers
            ) as response:
                if response.status == 200:
                    assignments = await response.json()
                    field_content = ""
                    
                    for assignment in assignments:
                        field_content += f"\n{assignment['name']}"
                    
                    if field_content:
                        undated_embed.add_field(
                            name=f"Undated For {course['name']}:",
                            value=field_content,
                            inline=False
                        )
    
    # Only return overdue embed if include_overdue is True
    if include_overdue:
        return [due_soon_embed, overdue_embed, undated_embed]
    else:
        return [due_soon_embed, Embed(title=""), undated_embed]  # Empty embed as placeholder
