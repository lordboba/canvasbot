# Copyright 2021, YaoXiao2, All rights reserved.
from discord.ext import commands, tasks
import discord
import os
import asyncio
import datetime as dt
from aiohttp import ClientSession
import aiohttp
from replit import db
from typing import Optional
from keep_alive import keep_alive
# intents = discord.Intents.default()
# intents.members = False
client = commands.Bot(command_prefix='hw ', activity=discord.Game(name="*Playing* hw help"))

commands = ["setup", "help", "reminder", "settings", "feedback"]

embed = discord.Embed(title="Thanks for adding me to this server! :D")
embed.add_field(name="Starting Out", value="To start and see a list of commands, type in hw help.")
embed.add_field(name="Setting Up The Bot",value="To setup the bot, type hw setup.")
embed.add_field(name="Bot Uses",value="This bot is used for tracking homework assignments on discord.")

setup_emb = discord.Embed(title="Bot Setup Instructions:")
setup_emb.add_field(name="Introduction:",value="Hello, and thanks for using the Canvas HW Bot! This bot can notify you through discord your homework assignments.")

# @client.event
# async def setup(ctx,user: discord.User):
#   await ctx.send("")
#   pass

base_API = "https://poway.instructure.com/api/v1"

@client.event
async def on_guild_join(guild):
  for channel in guild.text_channels:
    if channel.permissions_for(guild.me).send_messages:
      await channel.send('Thanks for inviting me to your server!',embed=embed)
      break
    # try:
    #     joinchannel = guild.system_channel
    #     # The system channel is where Discord’s join messages are sent
    #     await joinchannel.send('Thanks for inviting me to your server!',embed=embed)
    # except:
    #     # if no system channel is found send to the first channel in guild
    #     await guild.text_channels[0].send("Thanks for inviting me to your server!",embed=embed)

@client.event
async def on_ready():
  #async for server in client.servers:
  #  async for channel in server.channels:
  #    await channel.send(embed=embed)
  print("hi")

async def get_token(id):
  if id not in db:
    return "User not verified"
  return db[id]["id"]
  # async with aiofiles.open("temp.env",mode="r") as file:
  #   list = await file.readlines()
  #   async for line in list:
  #     if line.split("=")[0]==id:
  #       return line.split("=")[1]
  #   return "User not verified"

# @client.command(name="check")
# async def check(ctx):
#   #temp = os.environ[f"{ctx.author.id}"]
#   temp = await(get_token(f"{ctx.author.id}"))
#   msg = await ctx.channel.send(temp)
#   #await msg.delete


@client.command(name="check",help="Checks if you're have setup the bot")
async def check(ctx):
  id = f"{ctx.author.id}"
  if id in db:
    await ctx.channel.send("You have successfully set up the bot!")
  else:
    await ctx.channel.send("You have not set up the bot yet for you. Type in 'hw setup' to begin this process.")


async def append(id,content,api):
  db[f"{id}"] = {"id":content,"dm":True,"ping":False,"daily":True,"endpoint":api,"starred":False}
  # async with aiofiles.open("temp.env",mode="a") as file:
  #   await file.write(f"\n{id}={content}")

@client.command(name="setup", help="Sends a dm to help you set up your Canvas API key for the bot")
async def setup(ctx):
  # id_temp = f"{ctx.author.id}"
  # if id_temp in db:
  #   await ctx.channel.send("You have already setup the bot. Are you sure you want to proceed?")
  setup_1 = discord.File("step_1.png")
  setup_2 = discord.File("step_2.png")
  setup_3 = discord.File("step_3.png")
  setup_4 = discord.File("step_4.png")
  await ctx.channel.send("Read the DM that I sent you. You have 5 minutes to complete this setup!")
  dm_msg = await ctx.author.send(embed=setup_emb)
  await dm_msg.channel.send("Step 1: Copy paste the link of your Canvas after you log in. This may be something like: https://canvas.instructure.com/ (Make sure to have a slash at the end)")
  def check(m):
    return m.channel == dm_msg.channel and m.author != client.user
  try:
    api_link = f"{(await client.wait_for('message', check=check, timeout=300.0)).content}api/v1"
  except asyncio.TimeoutError:
    await dm_msg.channel.send("I'm sorry, but your setup timed out.")
  else:
    await dm_msg.channel.send("Step 2: In Canvas, click account then settings.",file=setup_1)
    await dm_msg.channel.send("Step 3: In the settings, scroll down to the section that says 'Approved Integrations' and click on the button '+ New Access Token'.",file=setup_2)
    await dm_msg.channel.send("Step 4: When writing a purpose, write 'Tracking Homework', and leave the expiration date blank. Once you are done, click the 'Generate Token' button.",file=setup_3)
    await dm_msg.channel.send("Step 5: Copy-paste the access token into this DM, and send the message. Once this is done, this bot should start to work for you if all information is correct!",file=setup_4)
    # message stuff
    
    try:
      msg = await client.wait_for('message', check=check, timeout=300.0)
    except asyncio.TimeoutError:
      await dm_msg.channel.send("I'm sorry, but your setup timed out.")
    else:
      headers = {"Authorization":f"Bearer {msg.content}"}
      try:
        # print(api_link)
        async with ClientSession() as session:
          async with session.get(url=f"{api_link}/accounts/search",params={"name":"Poway"},headers=headers) as response:
            response.raise_for_status()
            #response = await(response.json())
            
      except aiohttp.client_exceptions.ClientResponseError:
        await dm_msg.channel.send("I'm sorry, that is not a valid token, or the endpoint link is wrong, setup process terminated.")
        #print(await(response.json()))
      else:
        #os.environ[f"{ctx.author.id}"]=msg.content
        await append(f"{ctx.author.id}",msg.content,api_link)
        await dm_msg.channel.send("Congratulations! You have successfully setup the bot! You will receive notifications at 5:00 PST by default about your homework due tomorrrow!")

@client.command(name="feedback",help="Allows you to send feedback to the creators.")
async def feedback(ctx):
  await ctx.channel.send("Read the DM that I sent you.")
  dm_msg = await ctx.author.send(embed=setup_emb)
  await dm_msg.channel.send("Please write what you want to send to the creator of this discord bot. Please be mindful of what you send. You have 5 minutes")
  def check(m):
    return m.channel == dm_msg.channel and m.author != client.user
  try:
    feed_back = await client.wait_for('message', check=check, timeout=300.0)
  except asyncio.TimeoutError:
    await dm_msg.channel.send("I'm sorry, but your feedback session has timed out.")
  else:
    dev_1 = await ctx.bot.fetch_user(int(os.environ['nerd_1']))
    dev_2 = await ctx.bot.fetch_user(int(os.environ['nerd_2']))
    dev_carry = await ctx.bot.fetch_user(int(os.environ['nerd_3']))
    # print(type(dev_1))
    await dev_1.send(f"{ctx.author.name} says: {feed_back.content}")
    await dev_2.send(f"{ctx.author.name} says: {feed_back.content}")
    await dev_carry.send(f"{ctx.author.name} says: {feed_back.content}")
    #await dev_1.send(feed_back)
    #await dev_2.send(feed_back)
    #await dev_carry.send(feed_back)
  # yay thx


@client.command(name="homework", help="Returns all homework assignments due the next school day.")
async def homework(ctx):
  # Send API Call to get homework
  # token is empty until database starts working
  id = f"{ctx.author.id}"
  token = await(get_token(f"{ctx.author.id}"))
  #print(token)
  headers = {"Authorization":f"Bearer {token}"}
  try:
    endpoint = db[f"{ctx.author.id}"]["endpoint"]
  except KeyError:
    await ctx.channel.send("I'm sorry, you haven't setup this bot yet. Type 'hw setup' to begin the setup process.")
  else:
    try:
      if db[f"{ctx.author.id}"]['starred']:
        async with ClientSession() as session:
          async with session.get(url=f"{endpoint}/users/self/favorites/courses",params={"enrollment_state":"active"},headers=headers) as response:
            response.raise_for_status()
            course_list = await response.json()
      else:
        async with ClientSession() as session:
          async with session.get(url=f"{endpoint}/courses",params={"enrollment_state":"active"},headers=headers) as response:
            response.raise_for_status()
            course_list = await response.json()
    except aiohttp.client_exceptions.ClientResponseError:
      await ctx.channel.send("I'm sorry, you haven't setup this bot yet. Type 'hw setup' to begin the setup process.")
    else:
      #course_list = (course_list.decode('utf8'))
      #course_list = await literal_eval(course_list)
      # print(course_list)
      # course_list = await response.read()
      #iterates through course ids to get course assignments with ids
      # print(type(ctx.author))
      await ctx.channel.send("Request sent! Note, this command may take a while to be sent.")
      message = await get_homework(ctx.author.name,course_list,headers,endpoint)
      overdue = message[1]
      due_tmrw = message[0]
      undated = message[2]
      # print(type(overdue))
      # print(type(due_tmrw))
      #if dm is on:
      if db[id]["dm"]:
        await ctx.author.send(embed=overdue)
        await ctx.author.send(embed=due_tmrw)
        await ctx.author.send(embed=undated)
      #if ping is on
      if db[id]["ping"]:
        await ctx.channel.send(embed=overdue)
        await ctx.channel.send(embed=due_tmrw)
        await ctx.channel.send(embed=undated)

async def get_homework(id, course_list,headers,endpoint):
  overdue = f"""
    Hello <@!{id}>:
    Here is your homework report:
    
    Overdue Assignments:"""
  due_tmrw = "Assignments Due Soon:"
  overdue = discord.Embed(title=f"Hello <@!{id}>, here is your homework report:")
  # overdue.add_field(name="Overdue Assignments",value=" ")
  due_tmrw = discord.Embed(title=due_tmrw)
  undated = discord.Embed(title="Here are some undated assignments:")
  #print(course_list)
  for l in course_list:
    # print(l)
    # print(type(l))
    
    
    async with ClientSession() as session:
      async with session.get(url=f"{endpoint}/courses/{l['id']}/assignments",params={"bucket":"overdue","order_by":"due_at"},headers=headers) as response:
        response.raise_for_status()
        assign = await response.json()
        see = True
        temp = ""
        for asgnm in assign:
          # if see:
            # overdue = overdue + f"\nOverdue For {l['name']}:"
            #temp = temp + 
          # overdue = overdue + f"\n{asgnm['name']} {asgnm['due_at'].split('T')[0]}"
          temp = temp + f"\n{asgnm['name']} {asgnm['due_at'].split('T')[0]}"
          see = False
        if not see:
          overdue.add_field(name=f"\nOverdue For {l['name']}:",value=temp)
        # if see:
        #   overdue = overdue + f"\nN/A"
    async with ClientSession() as session:
      async with session.get(url=f"{endpoint}/courses/{l['id']}/assignments",params={"bucket":"future","order_by":"due_at"},headers=headers) as response:
        response.raise_for_status()
        assign = await response.json()
        see = True
        temp = ""
        for asgnm in assign:
          if asgnm['due_at'] == None:
            pass
          else:
            # if see:
              # due_tmrw = due_tmrw + f"\nDue Soon For {l['name']}:"
            # due_tmrw = due_tmrw + f"\n{asgnm['name']} {asgnm['due_at'].split('T')[0]}"
            temp = temp + f"\n{asgnm['name']} {asgnm['due_at'].split('T')[0]}"
            see = False
        if not see:
          due_tmrw.add_field(name=f"\nDue Soon For {l['name']}:", value=temp)
        # if see:
        #   due_tmrw = due_tmrw + f"\nN/A"
    async with ClientSession() as session:
      async with session.get(url=f"{endpoint}/courses/{l['id']}/assignments",params={"bucket":"undated"},headers=headers) as response:
        response.raise_for_status()
        assign = await response.json()
        see = True
        temp = ""
        for asgnm in assign:
          # if see:
            # overdue = overdue + f"\nOverdue For {l['name']}:"
            #temp = temp + 
          # overdue = overdue + f"\n{asgnm['name']} {asgnm['due_at'].split('T')[0]}"
          temp = temp + f"\n{asgnm['name']}"
          see = False
        if not see:
          undated.add_field(name=f"\nUndated For {l['name']}:",value=temp)
  return [due_tmrw,overdue,undated]
# @client.command(name="upd")
# async def upd(ctx):
#   tex = db.keys()
#   for key in tex:
#     temp = db[key]
#     if "starred" not in temp:
#       temp["starred"] = False
#     db[key] = temp

@client.command(name="settings", help="Lists settings of the bot. Can be changed to fit your needs.")
async def settings(ctx, setting: Optional[str], state: Optional[str]):
  #commands dm and daily
  id = f"{ctx.author.id}" 
  if id not in db:
    await ctx.send("You have not set up the bot yet for you. Type in 'hw setup' to begin this process and to be able to configure your settings.")
  else:
    client_set = db[id]
    
    #print(client_set)
    states_list = ["dm","ping","daily","starred"]
    if state == None:
      #print(client_set)
      setting_emb = discord.Embed(title="Your Current Settings For the Canvas Bot")
      if setting == None or setting == "dm":
        setting_emb.add_field(name="dm:",value=f"**Description:** Toggles Homework Reminders In Your DMs\n**Current Status:** {('Off','On')[client_set['dm']]}")
      if setting == None or setting == "ping":
        setting_emb.add_field(name="ping:",value=f"**Description:** Sends Homework Info in the discord channel when using 'hw homework'\n**Current Status:** {('Off','On')[client_set['ping']]}")
      if setting == None or setting == "daily":
        setting_emb.add_field(name="daliy:",value=f"**Description:** Sends Homework Reminders To You Daily\n**Current Status:** {('Off','On')[client_set['daily']]}")
      if setting == None or setting == "starred":
        setting_emb.add_field(name="starred:",value=f"**Description:** Returns homework only on starred courses\n**Current Status:** {('Off','On')[client_set['starred']]}")
      await ctx.send(embed=setting_emb)
    else:
      seen = True
      state = state.lower()
      real_state = (False,True)[state=='on'] or (False,True)[state=='true']
      if state != "on" and state != "off" and state != "true" and state != "false":
        await ctx.channel.send(f"You need to use the format: 'hw settings [setting] [on/off]'")
        pass
      else: 
        for s in states_list:
          if setting.lower() == s:
            db[id][s] = real_state
            seen = False
            await ctx.send(f"{setting} configuration successfully set to {state}!")
        if seen:
          await ctx.send("I'm sorry that setting is not available.")
# @client.event
# async def on_message(message):
#   print(type(message))
#   if message.author != client.user:
#     temp = message.content.lower()
#     if temp.startswith("hw "):
#       command = temp.split("hw ", maxsplit=1)[1]
#       isnt_valid = True
#       for cmd in commands: # test if it is valid
#         if command.startswith(cmd):
#           test = False
#           # run the command that passes in message
#       if test:
#         await message.channel.send("Sorry, this command is not available")
#         # run command here or something
#       print(command)
#       #await message.channel.send("this feature is not available noob")


#link https://discord.com/api/oauth2/authorize?client_id=859640222542069770&permissions=2147601424&redirect_uri=https%3A%2F%2Fbit.ly%2F3f9VhZo&scope=bot

@client.command(name="invite",help="Invites the bot to other servers")
async def invite(ctx):
  invite_emb = discord.Embed(title="Inviting The Bot To Other Servers")
  invite_emb.add_field(name="Link:",value="[Click here to invite the bot to another server.](https://discord.com/api/oauth2/authorize?client_id=859640222542069770&permissions=2147601424&redirect_uri=https%3A%2F%2Fbit.ly%2F3f9VhZo&scope=bot)")
  await ctx.channel.send(embed=invite_emb)

# keeps bot alive, add maybe https://uptimerobot.com/ later to keep bot alive
@tasks.loop(hours=24)
async def my_task():
  #notifies all users about hw
  #print("starting task")
  tex = db.keys()
  # print(len(tex))
  for user in tex:
    temp = db[user]
    
    if temp['daily']:
      id = user
      #print(user)
      #print(token)
      headers = {"Authorization":f"Bearer {temp['id']}"}
      # print(temp['id'])
      if db[user]['starred']:
        async with ClientSession() as session:
          async with session.get(url=f"{temp['endpoint']}/users/self/favorites/courses",params={"enrollment_state":"active"},headers=headers) as response:
            #print("amog us")
            # response.raise_for_status()
            print("among us")
            course_list = await response.json()
            # print(course_list)
            msg = await get_homework(id, course_list,headers,temp['endpoint'])
            overdue = msg[1]
            due_tmrw = msg[0]
            person = await client.fetch_user(int(id))
            await person.send(embed=overdue)
            await person.send(embed=due_tmrw)
            await person.send(embed=msg[2])
      else:
        async with ClientSession() as session:
          async with session.get(url=f"{temp['endpoint']}/courses",params={"enrollment_state":"active"},headers=headers) as response:
            #print("amog us")
            # response.raise_for_status()
            print("among us")
            course_list = await response.json()
            # print(course_list)
            msg = await get_homework(id, course_list,headers,temp['endpoint'])
            overdue = msg[1]
            due_tmrw = msg[0]
            person = await client.fetch_user(int(id))
            await person.send(embed=overdue)
            await person.send(embed=due_tmrw)
            await person.send(embed=msg[2])
  
@my_task.before_loop
async def before_my_task():
    hour = 0
    minute = 0
    #print("hiafwefaweff")
    await client.wait_until_ready()
    #print("hiawefawfafafefdhiawewafahiwdheafefadwihafahidiedfdaifeafida")
    now = dt.datetime.now()
    #print(now)
    future = dt.datetime(now.year, now.month, now.day, hour, minute)
    # print(future)
    if now.hour >= hour and now.minute > minute:
        future += dt.timedelta(days=1)
    print((future-now).seconds)
    await asyncio.sleep((future-now).seconds)

my_task.start()
keep_alive()
DISCORD_TOKEN = os.environ["DISCORD_TOKEN"]
client.run(DISCORD_TOKEN)