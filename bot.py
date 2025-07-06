import discord
from discord.ext import tasks, commands
import json
import os
import datetime

intents = discord.Intents.default()
intents.presences = True
intents.members = True
intents.message_content = True  # PENTING!
bot = commands.Bot(command_prefix="!", intents=intents)


DATA_FILE = "data.json"
LEADERBOARD_CHANNEL_ID = 1391240361913094224  # Ganti dengan ID channel leaderboard kamu

if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump({}, f)

@bot.event
async def on_ready():
    print(f"{bot.user} is online!")
    track_online_time.start()
    weekly_post_and_reset.start()

@tasks.loop(minutes=5)
async def track_online_time():
    with open(DATA_FILE, "r") as f:
        data = json.load(f)

    for guild in bot.guilds:
        for member in guild.members:
            if member.status == discord.Status.online and not member.bot:
                user_id = str(member.id)
                data[user_id] = data.get(user_id, 0) + 5

    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

@tasks.loop(hours=24)
async def weekly_post_and_reset():
    now = datetime.datetime.utcnow()
    if now.weekday() == 0:
        await post_leaderboard()
        with open(DATA_FILE, "w") as f:
            json.dump({}, f)
        print("Data mingguan telah di-reset.")

async def post_leaderboard():
    channel = bot.get_channel(LEADERBOARD_CHANNEL_ID)
    if channel is None:
        print("Channel leaderboard tidak ditemukan.")
        return

    with open(DATA_FILE, "r") as f:
        data = json.load(f)

    if not data:
        await channel.send("Tidak ada data online minggu ini.")
        return

    sorted_users = sorted(data.items(), key=lambda x: x[1], reverse=True)
    msg = "**🏆 Leaderboard Online Mingguan:**\n"
    for i, (user_id, minutes) in enumerate(sorted_users[:10], start=1):
        member = channel.guild.get_member(int(user_id))
        name = member.display_name if member else f"User ID {user_id}"
        hours = round(minutes / 60, 2)
        msg += f"{i}. {name} — {hours} jam\n"

    await channel.send(msg)

# !leaderboard - Top 10
@bot.command()
async def leaderboard(ctx):
    with open(DATA_FILE, "r") as f:
        data = json.load(f)

    if not data:
        await ctx.send("Belum ada data!")
        return

    sorted_users = sorted(data.items(), key=lambda x: x[1], reverse=True)
    msg = "**🏆 Leaderboard Online Mingguan:**\n"
    for i, (user_id, minutes) in enumerate(sorted_users[:10], start=1):
        member = ctx.guild.get_member(int(user_id))
        name = member.display_name if member else f"User ID {user_id}"
        hours = round(minutes / 60, 2)
        msg += f"{i}. {name} — {hours} jam\n"

    await ctx.send(msg)

# !onlineboard - semua user
@bot.command()
async def onlineboard(ctx):
    with open(DATA_FILE, "r") as f:
        data = json.load(f)

    if not data:
        await ctx.send("Belum ada data!")
        return

    sorted_users = sorted(data.items(), key=lambda x: x[1], reverse=True)
    msg = "**📊 Semua Waktu Online Mingguan:**\n"
    for i, (user_id, minutes) in enumerate(sorted_users, start=1):
        member = ctx.guild.get_member(int(user_id))
        name = member.display_name if member else f"User ID {user_id}"
        hours = round(minutes / 60, 2)
        msg += f"{i}. {name} — {hours} jam\n"

    await ctx.send(msg[:2000])  # max 2000 karakter per pesan

# !myonlinetime
@bot.command()
async def myonlinetime(ctx):
    user_id = str(ctx.author.id)
    with open(DATA_FILE, "r") as f:
        data = json.load(f)

    minutes = data.get(user_id, 0)
    hours = round(minutes / 60, 2)
    await ctx.send(f"{ctx.author.display_name}, kamu telah online selama **{hours} jam** minggu ini.")

# !rank
@bot.command()
async def rank(ctx):
    user_id = str(ctx.author.id)
    with open(DATA_FILE, "r") as f:
        data = json.load(f)

    if user_id not in data:
        await ctx.send("Kamu belum memiliki waktu online tercatat minggu ini.")
        return

    sorted_users = sorted(data.items(), key=lambda x: x[1], reverse=True)
    for i, (uid, minutes) in enumerate(sorted_users, start=1):
        if uid == user_id:
            hours = round(minutes / 60, 2)
            await ctx.send(f"{ctx.author.display_name}, kamu berada di peringkat **#{i}** dengan waktu online **{hours} jam**.")
            return

# !resetboard - admin only
@bot.command()
@commands.has_permissions(administrator=True)
async def resetboard(ctx):
    with open(DATA_FILE, "w") as f:
        json.dump({}, f)
    await ctx.send("Data leaderboard telah direset oleh admin.")

# Jalankan bot
bot.run(os.environ["TOKEN"])
