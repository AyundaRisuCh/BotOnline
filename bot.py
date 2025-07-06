import discord
from discord.ext import tasks, commands
import json
import os
import datetime

intents = discord.Intents.default()
intents.presences = True
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

WEEKLY_FILE = "weekly_data.json"
TOTAL_FILE = "total_data.json"
LEADERBOARD_CHANNEL_ID = 1391240361913094224  # GANTI ke channel ID kamu

# Buat file jika belum ada
for file in [WEEKLY_FILE, TOTAL_FILE]:
    if not os.path.exists(file):
        with open(file, "w") as f:
            json.dump({}, f)

@bot.event
async def on_ready():
    print(f"{bot.user} is online!")
    track_online_time.start()
    weekly_post_and_reset.start()

@tasks.loop(minutes=1)
async def track_online_time():
    with open(WEEKLY_FILE, "r") as f:
        weekly = json.load(f)
    with open(TOTAL_FILE, "r") as f:
        total = json.load(f)

    for guild in bot.guilds:
        for member in guild.members:
            if member.status == discord.Status.online and not member.bot:
                uid = str(member.id)
                weekly[uid] = weekly.get(uid, 0) + 1
                total[uid] = total.get(uid, 0) + 1

    with open(WEEKLY_FILE, "w") as f:
        json.dump(weekly, f)
    with open(TOTAL_FILE, "w") as f:
        json.dump(total, f)

@tasks.loop(hours=24)
async def weekly_post_and_reset():
    now = datetime.datetime.utcnow()
    if now.weekday() == 0:
        await post_leaderboard()
        with open(WEEKLY_FILE, "w") as f:
            json.dump({}, f)
        print("Leaderboard mingguan telah direset.")

async def post_leaderboard():
    channel = bot.get_channel(LEADERBOARD_CHANNEL_ID)
    if channel is None:
        print("Channel tidak ditemukan.")
        return

    with open(WEEKLY_FILE, "r") as f:
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

# === COMMANDS ===

@bot.command(name="obtop")
async def obtop(ctx):
    with open(WEEKLY_FILE, "r") as f:
        data = json.load(f)

    if not data:
        await ctx.send(f"{ctx.author.mention}, belum ada data online minggu ini.")
        return

    sorted_users = sorted(data.items(), key=lambda x: x[1], reverse=True)
    msg = f"{ctx.author.mention}\n**🏆 Top 10 Online Mingguan:**\n"
    for i, (uid, minutes) in enumerate(sorted_users[:10], start=1):
        mention = f"<@{uid}>"
        hours = round(minutes / 60, 2)
        msg += f"{i}. {mention} — {hours} jam\n"

    await ctx.send(msg)

@bot.command(name="oball")
async def oball(ctx):
    with open(WEEKLY_FILE, "r") as f:
        data = json.load(f)

    if not data:
        await ctx.send(f"{ctx.author.mention}, belum ada data online.")
        return

    sorted_users = sorted(data.items(), key=lambda x: x[1], reverse=True)
    msg = f"{ctx.author.mention}\n**📊 Semua Waktu Online Mingguan:**\n"
    for i, (uid, minutes) in enumerate(sorted_users, start=1):
        mention = f"<@{uid}>"
        hours = round(minutes / 60, 2)
        msg += f"{i}. {mention} — {hours} jam\n"

    for chunk in [msg[i:i+1900] for i in range(0, len(msg), 1900)]:
        await ctx.send(chunk)

@bot.command(name="obme")
async def obme(ctx):
    uid = str(ctx.author.id)
    with open(WEEKLY_FILE, "r") as f:
        data = json.load(f)

    minutes = data.get(uid, 0)
    hours = round(minutes / 60, 2)
    await ctx.send(f"{ctx.author.mention}, kamu telah online selama **{hours} jam** minggu ini.")

@bot.command(name="obrank")
async def obrank(ctx):
    uid = str(ctx.author.id)
    with open(WEEKLY_FILE, "r") as f:
        data = json.load(f)

    if uid not in data:
        await ctx.send(f"{ctx.author.mention}, kamu belum memiliki waktu online minggu ini.")
        return

    sorted_users = sorted(data.items(), key=lambda x: x[1], reverse=True)
    for i, (user, minutes) in enumerate(sorted_users, start=1):
        if user == uid:
            hours = round(minutes / 60, 2)
            await ctx.send(f"{ctx.author.mention}, kamu berada di peringkat **#{i}** dengan waktu online **{hours} jam**.")
            return

@bot.command(name="obreset")
@commands.has_permissions(administrator=True)
async def obreset(ctx):
    with open(WEEKLY_FILE, "w") as f:
        json.dump({}, f)
    await ctx.send(f"{ctx.author.mention} telah mereset leaderboard mingguan.")

# === TOTAL DATA ===

@bot.command(name="obtotal")
async def obtotal(ctx):
    with open(TOTAL_FILE, "r") as f:
        data = json.load(f)

    if not data:
        await ctx.send(f"{ctx.author.mention}, belum ada data total online.")
        return

    sorted_users = sorted(data.items(), key=lambda x: x[1], reverse=True)
    msg = f"{ctx.author.mention}\n**📈 Top 10 Total Online:**\n"
    for i, (uid, minutes) in enumerate(sorted_users[:10], start=1):
        mention = f"<@{uid}>"
        hours = round(minutes / 60, 2)
        msg += f"{i}. {mention} — {hours} jam\n"

    await ctx.send(msg)

@bot.command(name="obmetotal")
async def obmetotal(ctx):
    uid = str(ctx.author.id)
    with open(TOTAL_FILE, "r") as f:
        data = json.load(f)

    minutes = data.get(uid, 0)
    hours = round(minutes / 60, 2)
    await ctx.send(f"{ctx.author.mention}, total waktu online kamu adalah **{hours} jam**.")

@bot.command(name="obranktotal")
async def obranktotal(ctx):
    uid = str(ctx.author.id)
    with open(TOTAL_FILE, "r") as f:
        data = json.load(f)

    if uid not in data:
        await ctx.send(f"{ctx.author.mention}, kamu belum memiliki waktu online.")
        return

    sorted_users = sorted(data.items(), key=lambda x: x[1], reverse=True)
    for i, (user, minutes) in enumerate(sorted_users, start=1):
        if user == uid:
            hours = round(minutes / 60, 2)
            await ctx.send(f"{ctx.author.mention}, kamu berada di peringkat total **#{i}** dengan waktu online **{hours} jam**.")
            return

# Command test
@bot.command(name="test")
async def test(ctx):
    await ctx.send("Bot aktif dan siap!")

# Jalankan bot
bot.run(os.environ["TOKEN"])
