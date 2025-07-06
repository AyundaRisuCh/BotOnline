import discord
from discord.ext import tasks, commands
import json
import os
import datetime

intents = discord.Intents.default()
intents.presences = True
intents.members = True
bot = commands.Bot(command_prefix="/", intents=intents)

DATA_FILE = "data.json"
LEADERBOARD_CHANNEL_ID = 1391240361913094224  # Ganti dengan ID channel kamu

# Buat data.json jika belum ada
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump({}, f)

@bot.event
async def on_ready():
    print(f"{bot.user} is online!")
    track_online_time.start()
    weekly_post_and_reset.start()

# Loop untuk update online time tiap 5 menit
@tasks.loop(minutes=5)
async def track_online_time():
    with open(DATA_FILE, "r") as f:
        data = json.load(f)

    for guild in bot.guilds:
        for member in guild.members:
            if member.status == discord.Status.online and not member.bot:
                user_id = str(member.id)
                data[user_id] = data.get(user_id, 0) + 5  # menit

    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

# Reset dan kirim leaderboard tiap minggu (Senin UTC)
@tasks.loop(hours=24)
async def weekly_post_and_reset():
    now = datetime.datetime.utcnow()
    if now.weekday() == 0:  # 0 = Senin
        await post_leaderboard()

        # Reset data
        with open(DATA_FILE, "w") as f:
            json.dump({}, f)
        print("Data mingguan telah di-reset.")

# Fungsi untuk membuat leaderboard dan kirim ke channel
async def post_leaderboard():
    channel = bot.get_channel(LEADERBOARD_CHANNEL_ID)
    if channel is None:
        print("Channel tidak ditemukan.")
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

# Command manual (jika dibutuhkan)
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
        name = member.display_name if member else "User tidak dikenal"
        hours = round(minutes / 60, 2)
        msg += f"{i}. {name} — {hours} jam\n"

    await ctx.send(msg)

# Jalankan bot
import os
bot.run(os.environ["TOKEN"])
