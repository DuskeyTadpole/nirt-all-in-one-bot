import discord
from discord.ext import commands, tasks
import openai
import datetime
from discord.utils import get
from flask import Flask
import threading
import json
import os

# ====== SETUP ======
TOKEN = 'YOUR_DISCORD_BOT_TOKEN'
OPENAI_API_KEY = 'YOUR_OPENAI_KEY'
GUILD_ID = 'YOUR_SERVER_ID'

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='/', intents=intents)
openai.api_key = OPENAI_API_KEY

# ====== XP DATA STORAGE ======
xp_file = "xp_data.json"

if os.path.exists(xp_file):
    with open(xp_file, "r") as f:
        xp = json.load(f)
else:
    xp = {}

def save_xp():
    with open(xp_file, "w") as f:
        json.dump(xp, f)

# ====== BASIC EVENTS ======
@bot.event
async def on_ready():
    print(f"Bot is online as {bot.user}")

# ====== AI DOUBT SOLVER ======
@bot.command(name='ask')
async def ask(ctx, *, question):
    await ctx.send("Thinking...")
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": question}]
    )
    await ctx.send(response.choices[0].message['content'])

# ====== CLUB INFORMATION ======
@bot.command(name='clubinfo')
async def clubinfo(ctx, club_name):
    clubs = {
        'coding': '💻 Coding Club meets every Wed at 5PM.',
        'music': '🎵 Music Club jamming every Fri at 6PM.',
        'sports': '⚽ Sports Club meets Sat 4PM.',
    }
    info = clubs.get(club_name.lower(), "Club not found. Try: coding, music, sports")
    await ctx.send(info)

# ====== RESOURCE FETCH ======
@bot.command(name='resource')
async def resource(ctx, branch):
    drive_links = {
        'cse': 'https://drive.google.com/cse-resources',
        'ece': 'https://drive.google.com/ece-resources',
        'mech': 'https://drive.google.com/mech-resources'
    }
    await ctx.send(drive_links.get(branch.lower(), 'Branch not found.'))

# ====== ASSIGNMENT NOTIFY ======
@bot.command(name='assign')
async def assign(ctx):
    await ctx.author.send("Upcoming Assignments:\n1. Physics - 20 June\n2. Math - 22 June\n3. C Programming - 25 June")

# ====== EVENT LIST ======
@bot.command(name='event')
async def event(ctx):
    events = [
        "🎤 Hackathon - 21 June",
        "🎵 Music Fest - 23 June",
        "🧠 Quiz Bowl - 24 June"
    ]
    await ctx.send("Upcoming Events:\n" + '\n'.join(events))

# ====== GPT UTILITY COMMAND ======
@bot.command(name='gpt')
async def gpt(ctx, *, prompt):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    await ctx.send(response.choices[0].message['content'])

# ====== DEVELOPER PING ======
@bot.command(name='pingdev')
async def pingdev(ctx):
    dev_ids = ['@SujalBharti']
    await ctx.send(f"Summoning developers: {' '.join(dev_ids)} 🚀")

# ====== MODERATION COMMANDS ======
@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason=None):
    await member.kick(reason=reason)
    await ctx.send(f"{member} has been kicked.")

@bot.command()
@commands.has_permissions(ban_members=True)
async def mute(ctx, member: discord.Member):
    mute_role = get(ctx.guild.roles, name="Muted")
    if not mute_role:
        mute_role = await ctx.guild.create_role(name="Muted")
        for channel in ctx.guild.channels:
            await channel.set_permissions(mute_role, speak=False, send_messages=False)
    await member.add_roles(mute_role)
    await ctx.send(f"{member.mention} has been muted.")

@bot.command()
@commands.has_permissions(manage_messages=True)
async def warn(ctx, member: discord.Member, *, reason=None):
    await ctx.send(f"⚠️ {member.mention} has been warned. Reason: {reason}")

# ====== TICKET SYSTEM (DM-based) ======
@bot.command()
async def ticket(ctx, *, issue=None):
    await ctx.author.send("Thanks for creating a ticket. We'll assist you shortly!")
    log = discord.utils.get(ctx.guild.text_channels, name='log-archive')
    if log:
        await log.send(f"🎫 Ticket from {ctx.author}: {issue or 'No description'}")

# ====== XP/LEVEL SYSTEM (Persistent) ======
@bot.event
async def on_message(message):
    if message.author.bot:
        return
    user_id = str(message.author.id)
    xp[user_id] = xp.get(user_id, 0) + 10
    save_xp()
    if xp[user_id] % 100 == 0:
        await message.channel.send(f"🎉 {message.author.mention} leveled up! Total XP: {xp[user_id]}")
    await bot.process_commands(message)

@bot.command()
async def rank(ctx):
    user_id = str(ctx.author.id)
    user_xp = xp.get(user_id, 0)
    await ctx.send(f"🏅 {ctx.author.mention}, your XP is {user_xp}.")

@bot.command()
async def leaderboard(ctx):
    sorted_xp = sorted(xp.items(), key=lambda x: x[1], reverse=True)[:5]
    result = "🏆 Top 5 XP Users:\n"
    for i, (user_id, score) in enumerate(sorted_xp):
        user = await bot.fetch_user(int(user_id))
        result += f"{i+1}. {user.name} - {score} XP\n"
    await ctx.send(result)

# ====== MUSIC COMMANDS (Join/Leave) ======
@bot.command()
async def join(ctx):
    if ctx.author.voice:
        await ctx.author.voice.channel.connect()
        await ctx.send("🎶 Joined the voice channel!")
    else:
        await ctx.send("You must be in a VC to summon me!")

@bot.command()
async def leave(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("👋 Left the voice channel!")
    else:
        await ctx.send("I'm not in a voice channel!")

# ====== WEB DASHBOARD (Flask) ======
app = Flask(__name__)

@app.route('/')
def index():
    return "NIRT BOT Dashboard - Online"

def run_dashboard():
    app.run(host='0.0.0.0', port=8080)

dashboard_thread = threading.Thread(target=run_dashboard)
dashboard_thread.start()

# ====== RUN BOT ======
bot.run(TOKEN)
