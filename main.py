import discord
from discord import app_commands
import sqlite3
import random
import os

# 1. KHỞI TẠO BOT VÀ DATABASE
intents = discord.Intents.default()
bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)

# Kết nối đến Database (tạo file 'economy.db' nếu chưa có)
conn = sqlite3.connect('economy.db')
cursor = conn.cursor()

# Tạo bảng 'users' nếu nó chưa tồn tại
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        balance INTEGER DEFAULT 0
    )
''')
conn.commit()

# --- Các hàm Database hỗ trợ ---
def get_balance(user_id):
    cursor.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    return result[0] if result else 0

def update_balance(user_id, amount):
    # Dùng REPLACE INTO để INSERT nếu chưa có hoặc UPDATE nếu đã có
    cursor.execute('''
        INSERT OR REPLACE INTO users (user_id, balance)
        VALUES (?, COALESCE((SELECT balance FROM users WHERE user_id = ?), 0) + ?)
    ''', (user_id, user_id, amount))
    conn.commit()

# --- LỆNH SLASH 1: /balance (Kiểm tra số dư) ---
@tree.command(name="balance", description="Kiểm tra số tiền của bạn.")
async def balance_command(interaction: discord.Interaction):
    user_id = interaction.user.id
    balance = get_balance(user_id)
    await interaction.response.send_message(
        f'💵 Số dư hiện tại của bạn là: **{balance} xu**.'
    )

# --- LỆNH SLASH 2: /beg (Xin tiền) ---
@tree.command(name="beg", description="Xin tiền từ người lạ, hên xui!")
async def beg_command(interaction: discord.Interaction):
    user_id = interaction.user.id
    earnings = random.randint(10, 100)
    
    # Cập nhật số dư qua hàm Database
    update_balance(user_id, earnings)
    
    balance = get_balance(user_id)
    
    await interaction.response.send_message(
        f'🎉 Bạn đã xin được **{earnings} xu**! Số dư mới: **{balance} xu**.'
    )

# --- XỬ LÝ SỰ KIỆN KHI BOT ĐÃ SẴN SÀNG ---
@bot.event
async def on_ready():
    await tree.sync()
    print(f'Bot đã đăng nhập với tên: {bot.user}')

# --- CHẠY BOT ---
BOT_TOKEN = os.environ.get("MTQzNzk3OTMzMDk1MjMwMjcxNA.G6jlhY.OclcraTujEdMH_puZtWhZaVE6CajjOawqs7FJs") 
if BOT_TOKEN:
    bot.run(BOT_TOKEN)
else:
    print("Lỗi: Vui lòng thiết lập biến môi trường 'DISCORD_BOT_TOKEN' với Token của bot.")