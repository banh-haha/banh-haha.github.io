import discord
from discord.ext import commands
from discord import ui
from discord import app_commands
from flask import Flask, request, render_template_string, url_for, redirect, session
import threading
import json
import re
import random
import os
import asyncio
import google.genai as genai # Thư viện cho Gemini API

# -------------------------------------------------------------
# 1. CẤU HÌNH BAN ĐẦU VÀ DATA HANDLING
# -------------------------------------------------------------

# --- CẤU HÌNH THÔNG SỐ VÀ FILE ---
os.makedirs('data', exist_ok=True)
os.makedirs('static', exist_ok=True) 
LEVELS_FILE = 'data/levels.json'
CONFIG_FILE = 'data/config.json'

# --- THÔNG SỐ BẮT BUỘC PHẢI THAY ĐỔI ---
TOKEN = "MTQzMDcyNDEwNzM3NjI2MzIzMA.Gk8Sv6.4rX1dQplNG412DjQlZaVyOG739ivuWobaMhqqM" # THAY THẾ BẰNG TOKEN BOT THẬT
SECRET_KEY = "daylamatkhaucuaban12345" 
ID_KENH_CHAO_MUNG = 1417506375369621591 
# THAY THẾ BẰNG KHÓA API GEMINI CỦA BẠN
GEMINI_API_KEY = "AIzaSyBmgS7UZw-yOfZEefb7OKHupIokMDPlk5o" 
# ----------------------------------------

# Biến toàn cục để lưu cấu hình
config = {} 
# Khóa giá trị Background URL
DEFAULT_BACKGROUND_URL = "room.gif" 

# --- Hàm xử lý Config (JSON) ---
def load_config():
    """Tải cấu hình từ config.json."""
    default_config = {
        "ID_KENH_CHAO_MUNG": str(ID_KENH_CHAO_MUNG), 
        "LEVEL_REWARDS": {
            "5": "1430724107376263231", 
            "10": "1430724107376263232",
        },
        "AUTO_RESPONSES": [ 
            {"trigger": "hi", "response": "Chào {mem}! Chúc {mem} một ngày vui vẻ!"},
            {"trigger": "bot", "response": "Tôi là {sever} Bot. Bạn cần gì?"}
        ],
        "CAU_CHAO_HIEN_TAI": "Chào mừng {mem} đến server! {soluong} thành viên.",
        "URL_GIF_MAIN": "https://tenor.com/view/minions-hi-hello-wave-greetings-gif-17409241.gif",
        "EMBED_CHAO_MUNG_MAU": "#3498db",
        "DASHBOARD_BACKGROUND_URL": DEFAULT_BACKGROUND_URL # Đặt mặc định là file room.gif
    }
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            try:
                loaded_config = json.load(f)
                for key, default_val in default_config.items():
                    if key not in loaded_config:
                        loaded_config[key] = default_val
                # KHÓA BACKGROUND: Luôn ép giá trị về DEFAULT_BACKGROUND_URL
                loaded_config["DASHBOARD_BACKGROUND_URL"] = DEFAULT_BACKGROUND_URL 
                save_config(loaded_config)
                return loaded_config
            except json.JSONDecodeError:
                print(f"CẢNH BÁO: File {CONFIG_FILE} bị lỗi cấu trúc. Sử dụng cấu hình mặc định.")
                return default_config
    else:
        save_config(default_config)
        return default_config

def save_config(new_config):
    """Lưu cấu hình vào config.json."""
    # KHÓA BACKGROUND: Trước khi lưu, đảm bảo giá trị vẫn là DEFAULT_BACKGROUND_URL
    new_config["DASHBOARD_BACKGROUND_URL"] = DEFAULT_BACKGROUND_URL 
    with open(CONFIG_FILE, 'w') as f:
        json.dump(new_config, f, indent=4)

def load_levels():
    if os.path.exists(LEVELS_FILE):
        with open(LEVELS_FILE, 'r') as f:
            try:
                content = f.read()
                return json.loads(content) if content else {}
            except json.JSONDecodeError:
                return {}
    return {}

def save_levels(levels_data):
    with open(LEVELS_FILE, 'w') as f:
        json.dump(levels_data, f, indent=4)

def get_level_info(xp):
    level = 0
    xp_required = 100
    current_xp = xp
    while current_xp >= xp_required:
        level += 1
        current_xp -= xp_required
        xp_required = 5 * (level ** 2) + (50 * level) + 100 
    xp_next_level = 5 * (level ** 2) + (50 * level) + 100
    xp_current_level = current_xp
    return level, xp_current_level, xp_next_level

# -------------------------------------------------------------
# 2. CODE BOT DISCORD (INTENTS VÀ CÁC HÀM XỬ LÝ)
# -------------------------------------------------------------

# Cấu hình Discord Intents
intents = discord.Intents.default()
intents.members = True 
intents.message_content = True 
bot = commands.Bot(command_prefix='!', intents=intents) 
levels = {} 

# --- CẤU HÌNH GEMINI AI ---
try:
    gemini_client = genai.Client(api_key=GEMINI_API_KEY)
except Exception as e:
    print(f"LỖI CẤU HÌNH GEMINI: Không thể khởi tạo client. Lỗi: {e}")
    gemini_client = None


def process_custom_placeholders(message: str, member: discord.Member) -> str:
    """Thay thế các placeholders tùy chỉnh bằng cú pháp Discord thực tế."""
    guild = member.guild
    message = message.replace("{mem}", member.mention)
    message = message.replace("{sever}", guild.name)
    member_count = guild.member_count if guild.member_count is not None else len(guild.members)
    message = message.replace("{soluong}", str(member_count))

    def replace_id(match):
        target_id = match.group(1)
        return f"<@{target_id}>" 

    message = re.sub(r'\{id(\d+)\}', replace_id, message)
    return message

# --- EVENTS VÀ LỆNH CƠ BẢN ---

@bot.event
async def on_ready():
    global levels, config
    levels = load_levels() 
    config = load_config()
    print(f'🤖 Bot đã đăng nhập với tên: {bot.user}')
    await bot.change_presence(activity=discord.Game(name="Quản lý bởi Web Dashboard"))
    
    # --- ĐỒNG BỘ HÓA LỆNH APP COMMANDS ---
    try:
        synced = await bot.tree.sync()
        print(f"✅ Đã đồng bộ hóa {len(synced)} lệnh Context/Slash.")
    except Exception as e:
        print(f"❌ Lỗi khi đồng bộ hóa lệnh: {e}")
        
@bot.event
async def on_member_join(member):
    """Gửi Lời Chào bằng Embed."""
    channel_id_str = config.get("ID_KENH_CHAO_MUNG", "")
    try:
        channel_id = int(channel_id_str)
    except ValueError:
        print("LỖI CẤU HÌNH: ID Kênh chào mừng không hợp lệ.")
        return

    CAU_CHAO_HIEN_TAI = config.get("CAU_CHAO_HIEN_TAI", "")
    EMBED_MAU_HEX = config.get("EMBED_CHAO_MUNG_MAU", "#3498db").replace("#", "0x")
    URL_GIF_MAIN = config.get("URL_GIF_MAIN", "")
    
    channel = bot.get_channel(channel_id)
    
    if channel and CAU_CHAO_HIEN_TAI:
        processed_message = process_custom_placeholders(CAU_CHAO_HIEN_TAI, member)
        
        try:
            embed_color = int(EMBED_MAU_HEX, 16)
        except ValueError:
            embed_color = 0x3498db 

        embed = discord.Embed(
            title=f"🎉 CHÀO MỪNG {member.name.upper()} ĐẾN VỚI SERVER!",
            description=processed_message,
            color=embed_color
        )
        
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=f"Server hiện có: {member.guild.member_count} thành viên")
        
        if URL_GIF_MAIN:
            embed.set_image(url=URL_GIF_MAIN)
        
        await channel.send(content=member.mention, embed=embed)

@bot.event
async def on_message(message):
    """Xử lý AI khi ping, Trả lời tự động, cấp XP và Level."""
    global levels, config
    
    if message.author.bot or not message.guild:
        await bot.process_commands(message)
        return
        
    # ------------------------------------------------
    # A. XỬ LÝ AI KHI CÓ PING (@Banhbaochao)
    # ------------------------------------------------
    if bot.user.mentioned_in(message) and gemini_client:
        # Lấy nội dung tin nhắn sau khi đã loại bỏ ping Bot
        cleaned_text = re.sub(r'<@!?\d+>', '', message.content).strip()
        
        if cleaned_text:
            await message.channel.typing() # Báo Bot đang gõ
            
            # --- ĐỊNH NGHĨA TÍNH CÁCH SẮC SẢO VÀ SÁT THƯƠNG ---
            system_instruction = (
                "Bạn là 'Banhbaochao Bot', một trợ lý AI thông minh, sáng tạo. "
                "Tuy nhiên, bạn có tính cách hơi sắc sảo, thích châm biếm nhẹ nhàng, "
                "và đôi khi đưa ra những câu trả lời có tính 'sát thương' cao nhưng vẫn chính xác. "
                "Hãy giữ giọng điệu lạnh lùng và hơi kiêu ngạo."
            )

            try:
                # Gửi yêu cầu đến Gemini 
                response = gemini_client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=cleaned_text,
                    config=genai.types.GenerateContentConfig(
                        system_instruction=system_instruction
                    )
                )
                
                ai_reply = response.text
                
                await message.reply(ai_reply, mention_author=False)
                
                # Không cấp XP/tự động trả lời khi đã kích hoạt AI
                await bot.process_commands(message)
                return

            except Exception as e:
                # Phản hồi nếu lỗi API
                error_msg = f"Ngươi gọi ta làm gì? Lỗi kết nối với thiên hà Gemini ({e})."
                await message.reply(error_msg, mention_author=False)
                
    # ------------------------------------------------
    # B. XỬ LÝ TRẢ LỜI TỰ ĐỘNG
    # ------------------------------------------------
    content = message.content.lower().strip()
    auto_responses = config.get("AUTO_RESPONSES", [])
    
    for auto_reply in auto_responses:
        trigger = auto_reply.get("trigger", "").lower().strip()
        response_template = auto_reply.get("response", "")
        
        if trigger:
            if content == trigger or re.search(r'\b' + re.escape(trigger) + r'\b', content):
                processed_response = process_custom_placeholders(response_template, message.author)
                await message.channel.send(processed_response)
                await bot.process_commands(message)
                return 

    # ------------------------------------------------
    # C. XỬ LÝ LEVEL VÀ XP
    # ------------------------------------------------
    user_id = str(message.author.id)
    if user_id not in levels:
        levels[user_id] = {'xp': 0, 'level': 0, 'last_message': 0}

    # Giới hạn XP mỗi 60 giây
    if message.created_at.timestamp() - levels[user_id]['last_message'] >= 60:
        
        old_xp = levels[user_id]['xp']
        levels[user_id]['xp'] += random.randint(10, 25)
        levels[user_id]['last_message'] = message.created_at.timestamp()
        
        old_level, _, _ = get_level_info(old_xp)
        new_level, _, _ = get_level_info(levels[user_id]['xp'])
        levels[user_id]['level'] = new_level
        
        if new_level > old_level:
            await message.channel.send(f"Chúc mừng {message.author.mention} đã đạt cấp độ **{new_level}**! 🎉")
            
            LEVEL_REWARDS = config.get("LEVEL_REWARDS", {})
            new_level_str = str(new_level) 
            
            if new_level_str in LEVEL_REWARDS:
                try:
                    role_id_to_assign = int(LEVEL_REWARDS[new_level_str])
                except ValueError:
                    role_id_to_assign = None
                    
                if role_id_to_assign:
                    role_to_assign = message.guild.get_role(role_id_to_assign)
                    
                    if role_to_assign and message.guild.me.top_role.position > role_to_assign.position:
                        try:
                            if role_to_assign not in message.author.roles:
                                await message.author.add_roles(role_to_assign)
                                await message.channel.send(f"Và bạn đã được tặng Role **{role_to_assign.name}**! Chúc mừng! 🏅")
                        except discord.Forbidden:
                            print(f"Lỗi: Bot không có quyền gán Role {role_to_assign.name}.")

        save_levels(levels) 

    # Xử lý các lệnh prefix khác (nếu có)
    await bot.process_commands(message)

# ----------------------------------------------------------------------------------
# LỆNH APP COMMANDS (SLASH & CONTEXT MENU)
# ----------------------------------------------------------------------------------

# --- Lệnh Slash: /rank ---
@bot.tree.command(name='rank', description='Kiểm tra cấp độ và XP hiện tại của bạn hoặc người khác.')
async def slash_rank(interaction: discord.Interaction, member: discord.Member = None):
    """Hiển thị cấp độ, XP và tiến trình lên cấp."""
    
    target_member = member or interaction.user
    user_id = str(target_member.id)
    global levels
    
    if user_id not in levels or levels[user_id]['xp'] == 0:
        msg = f"😔 Người dùng **{target_member.display_name}** chưa có XP. Hãy nhắn tin để bắt đầu tích lũy!" if target_member == interaction.user else f"😔 Người dùng **{target_member.display_name}** chưa có XP."
        await interaction.response.send_message(msg, ephemeral=True)
        return

    xp = levels[user_id]['xp']
    level, xp_current_level, xp_next_level = get_level_info(xp)
    
    progress_percent = (xp_current_level / xp_next_level) * 100 if xp_next_level > 0 else 100
    
    BAR_LENGTH = 15
    fill_char = '█'
    empty_char = '—'
    num_filled = int(progress_percent / (100 / BAR_LENGTH))
    progress_bar = fill_char * num_filled + empty_char * (BAR_LENGTH - num_filled)
    
    embed = discord.Embed(
        title=f"🎖️ Xếp Hạng của {target_member.display_name}",
        color=0x00bcd4
    )
    
    embed.add_field(name="Cấp Độ (Level)", value=f"**{level}**", inline=True)
    embed.add_field(name="Tổng XP", value=f"**{xp:,}** XP", inline=True)
    embed.add_field(name="Tiến Trình", 
                    value=f"`{progress_bar}` **{progress_percent:.0f}%**\n*{xp_current_level:,}/{xp_next_level:,} XP cần để lên Level {level + 1}*", 
                    inline=False)
    
    embed.set_thumbnail(url=target_member.display_avatar.url)
    embed.set_footer(text="Gõ /rank để kiểm tra cấp độ của bạn!")
    
    await interaction.response.send_message(embed=embed)


# --- Lệnh Slash: /resetxp ---
@bot.tree.command(name='resetxp', description='Xóa XP và Level của một người dùng. (Chỉ Admin)')
@app_commands.checks.has_permissions(administrator=True)
async def slash_reset_xp(interaction: discord.Interaction, member: discord.Member):
    """Xóa XP và Level của một người dùng."""
    
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Bạn không có quyền quản trị để sử dụng lệnh này.", ephemeral=True)
        return

    user_id = str(member.id)
    global levels
    
    if user_id in levels:
        levels[user_id] = {'xp': 0, 'level': 0, 'last_message': 0}
        save_levels(levels)
        
        await interaction.response.send_message(
            f"✅ Đã reset XP và Level của **{member.mention}** về 0.",
            ephemeral=False
        )
    else:
        await interaction.response.send_message(
            f"❌ Người dùng **{member.mention}** chưa có dữ liệu Level.",
            ephemeral=True
        )


# --- Lệnh Context Menu (Giữ nguyên) ---

@bot.tree.context_menu(name='Slap (Tát)')
async def slap_member(interaction: discord.Interaction, member: discord.Member):
    if member == interaction.user:
        await interaction.response.send_message(f"Bạn tự tát chính mình à? 😅", ephemeral=True)
        return

    gif_url = random.choice([
        "https://tenor.com/view/slap-anime-gif-5374974", 
        "https://tenor.com/view/slap-hand-hit-slapping-slapped-gif-17032909"
    ])

    embed = discord.Embed(
        description=f"💥 **{interaction.user.display_name}** vừa tát **{member.display_name}** một cái trời giáng!",
        color=0xf04747
    )
    embed.set_image(url=gif_url)

    await interaction.response.send_message(embed=embed)


@bot.tree.context_menu(name='Hug (Ôm)')
async def hug_member(interaction: discord.Interaction, member: discord.Member):
    if member == interaction.user:
        await interaction.response.send_message(f"Bạn tự ôm mình ư? Tội nghiệp quá 🥺", ephemeral=True)
        return
        
    gif_url = random.choice([
        "https://tenor.com/view/cuddle-hug-love-in-love-happy-gif-14666579", 
        "https://tenor.com/view/mochi-peach-cat-hug-love-pat-gif-17417534"
    ])

    embed = discord.Embed(
        description=f"💖 **{interaction.user.display_name}** vừa tặng **{member.display_name}** một cái ôm thật chặt!",
        color=0x57f287
    )
    embed.set_image(url=gif_url)
    
    await interaction.response.send_message(embed=embed)


@bot.tree.context_menu(name='Pat (Xoa đầu)')
async def pat_member(interaction: discord.Interaction, member: discord.Member):
    gif_url = random.choice([
        "https://tenor.com/view/anime-pat-head-gif-17070183", 
        "https://tenor.com/view/anime-pat-head-k-on-gif-10255532"
    ])

    embed = discord.Embed(
        description=f"👋 **{interaction.user.display_name}** xoa đầu **{member.display_name}** đầy trìu mến.",
        color=0xfee75c
    )
    embed.set_image(url=gif_url)
    
    await interaction.response.send_message(embed=embed)

# -------------------------------------------------------------
# 3. CODE WEB DASHBOARD BẰNG FLASK 
# -------------------------------------------------------------

# Khởi tạo Flask và khai báo thư mục static
app = Flask(__name__, static_folder='static')
app.secret_key = SECRET_KEY 

def generate_level_dashboard_html(active_tab):
    """Tạo nội dung cho các tab Level, Auto-Reply."""
    levels_data = load_levels()
    leaderboard = []
    is_bot_ready = bot.is_ready() 
    LEVEL_REWARDS = config.get("LEVEL_REWARDS", {})
    AUTO_RESPONSES = config.get("AUTO_RESPONSES", [])

    guild = bot.guilds[0] if bot.guilds and is_bot_ready else None 

    # --- STYLE CHUNG CHO CÁC TAB ---
    style_common = """
        <style>
            .config-note { background-color: rgba(255, 255, 255, 0.1); padding: 15px; border-radius: 8px; margin-bottom: 20px; }
            .reward-row { display: flex; align-items: center; margin-bottom: 10px; }
            .reward-row input { width: 100px; margin-right: 10px; }
            .reward-row input[type="text"] { width: 250px; }
            .reward-row span { color: #00bcd4; font-weight: bold; }
            #add_reward, #add_auto_reply { background-color: #f39c12; margin-top: 20px; }
            #add_reward:hover, #add_auto_reply:hover { background-color: #e67e22; }
            .reply-row textarea { height: 80px; resize: vertical; margin-bottom: 5px; width: calc(90% - 2px);}
            .ready-status { background-color: #e74c3c; color: white; padding: 10px; border-radius: 5px; text-align: center; font-weight: bold; margin-bottom: 20px; }
            .locked-field { background-color: #444; color: #aaa; cursor: not-allowed; }
        </style>
    """
    
    ready_status = ""
    if not is_bot_ready or not guild:
         ready_status = "<div class='ready-status'>⚠️ **CẢNH BÁO:** Bot Discord chưa hoàn tất kết nối hoặc không tìm thấy Server. Dữ liệu (tên Role, tên User) có thể bị thiếu hoặc lỗi 'Lỗi máy chủ nội bộ' có thể xảy ra. Vui lòng chờ Bot báo Ready.</div>"

    if active_tab == 'level_config':
        # --- Tab cấu hình Role thưởng ---
        reward_rows = ""
        sorted_rewards = sorted(LEVEL_REWARDS.items(), key=lambda x: int(x[0]) if x[0].isdigit() else 0)
        
        for level, role_id in sorted_rewards:
            role_name = ""
            if guild: 
                try:
                    role = guild.get_role(int(role_id)) if role_id.isdigit() else None
                    role_name = role.name if role else f"ID: {role_id} (Không tìm thấy)"
                except ValueError:
                    role_name = f"ID: {role_id} (ID Lỗi)"
            else:
                role_name = f"ID: {role_id} (Bot đang tải...)"


            reward_rows += f"""
            <div class="reward-row">
                <input type="number" name="level[]" value="{level}" min="1" required>
                <input type="text" name="role_id[]" value="{role_id}" required>
                <span>{role_name}</span>
            </div>
            """
        
        return style_common + ready_status + f"""
        <div class="config-note">
            Nhập Level và ID của Role tương ứng. ID Role phải là số nguyên (Copy ID từ Discord).
        </div>
        <form method="POST" action="{url_for('dashboard')}?tab=level_config">
            <label>Level Thưởng Role:</label>
            <div id="rewards_container">
                {reward_rows}
            </div>
            <button type="button" id="add_reward" onclick="addRewardRow()">+ Thêm Level Thưởng</button>
            <button type="submit" style="margin-top: 15px;">Lưu Cấu Hình Level Thưởng</button>
        </form>

        <script>
            function addRewardRow() {{
                const container = document.getElementById('rewards_container');
                const newRow = document.createElement('div');
                newRow.className = 'reward-row';
                newRow.innerHTML = `
                    <input type="number" name="level[]" placeholder="Level mới" min="1" required>
                    <input type="text" name="role_id[]" placeholder="ID Role (ví dụ: 123456789...)" required>
                    <span>(Chưa lưu)</span>
                `;
                container.appendChild(newRow);
            }}
        </script>
        """
        
    elif active_tab == 'auto_reply_config':
        # --- Tab Cấu hình Trả Lời Tự Động ---
        reply_rows = ""
        for i, reply in enumerate(AUTO_RESPONSES):
            trigger = reply.get("trigger", "")
            response = reply.get("response", "")
            reply_rows += f"""
            <div class="reply-row" data-index="{i}" style="margin-bottom: 15px; border: 1px solid #555; padding: 10px; border-radius: 8px;">
                <label>Từ khóa (Trigger):</label>
                <input type="text" name="trigger[]" value="{trigger}" placeholder="Ví dụ: hi, help, link" style="width: 90%; margin-bottom: 5px;" required>
                <label>Tin nhắn Bot trả lời (Response):</label>
                <textarea name="response[]" placeholder="Ví dụ: Chào {{mem}}!">{response}</textarea>
                <button type="button" onclick="removeReplyRow(this)" style="width: auto; background-color: #e74c3c; padding: 5px 10px; font-size: 0.9em; margin-top: 5px;">Xóa</button>
            </div>
            """
        
        return style_common + ready_status + f"""
        <div class="config-note">
            Bot sẽ trả lời nếu tin nhắn **chứa chính xác từ khóa** (trigger).
            Sử dụng placeholders: <code>{{mem}}</code>, <code>{{sever}}</code>, <code>{{soluong}}</code>, v.v.
        </div>
        <form method="POST" action="{url_for('dashboard')}?tab=auto_reply_config">
            <div id="auto_replies_container">
                {reply_rows}
            </div>
            <button type="button" id="add_auto_reply" onclick="addAutoReplyRow()">+ Thêm Trả Lời Tự Động</button>
            <button type="submit" style="margin-top: 15px;">Lưu Cấu Hình Trả Lời Tự Động</button>
        </form>
        
        <script>
            function addAutoReplyRow() {{
                const container = document.getElementById('auto_replies_container');
                const newRow = document.createElement('div');
                newRow.className = 'reply-row';
                newRow.style.cssText = "margin-bottom: 15px; border: 1px solid #555; padding: 10px; border-radius: 8px;";
                newRow.innerHTML = `
                    <label>Từ khóa (Trigger):</label>
                    <input type="text" name="trigger[]" placeholder="Ví dụ: hi, help" style="width: 90%; margin-bottom: 5px;" required>
                    <label>Tin nhắn Bot trả lời (Response):</label>
                    <textarea name="response[]" placeholder="Ví dụ: Chào {{mem}}!" style="height: 80px; resize: vertical; margin-bottom: 5px; width: calc(90% - 2px);"></textarea>
                    <button type="button" onclick="removeReplyRow(this)" style="width: auto; background-color: #e74c3c; padding: 5px 10px; font-size: 0.9em; margin-top: 5px;">Xóa</button>
                `;
                container.appendChild(newRow);
            }}
            function removeReplyRow(button) {{
                button.closest('.reply-row').remove();
            }}
        </script>
        """
        
    elif active_tab == 'level_leaderboard':
        # --- Tab Bảng xếp hạng ---
        
        for user_id, data in levels_data.items():
            if 'xp' not in data: continue
            
            member = bot.get_user(int(user_id)) if is_bot_ready else None
            if member: username = member.global_name or member.name 
            elif is_bot_ready: username = f"Người dùng cũ (ID: {user_id})"
            else: username = f"Đang tải... (ID: {user_id})" 
            
            level, xp_current_level, xp_next_level = get_level_info(data['xp'])
            leaderboard.append({'name': username, 'level': level, 'xp': data['xp'], 'xp_current_level': xp_current_level, 'xp_next_level': xp_next_level})

        leaderboard.sort(key=lambda x: (x['level'], x['xp']), reverse=True)

        table_rows = ""
        if not leaderboard:
            table_rows = "<tr><td colspan='5' style='text-align: center;'>Chưa có dữ liệu. Vui lòng nhắn tin trong Discord để bắt đầu tích lũy XP.</td></tr>"
        else:
            for rank, entry in enumerate(leaderboard, 1):
                progress_percent = (entry['xp_current_level'] / entry['xp_next_level']) * 100 if entry['xp_next_level'] > 0 else 100
                reward_info = " ⭐" if str(entry['level']) in LEVEL_REWARDS else ""
                
                table_rows += f"""
                <tr>
                    <td>{rank}</td>
                    <td>{entry['name']}</td>
                    <td>{entry['level']}{reward_info}</td>
                    <td>{entry['xp']:,} XP</td>
                    <td>
                        <div class="progress-bar">
                            <div style="width: {progress_percent:.0f}%;">{progress_percent:.0f}%</div>
                        </div>
                        <small>{entry['xp_current_level']:,}/{entry['xp_next_level']:,} XP</small>
                    </td>
                </tr>
                """
        
        return style_common + ready_status + f"""
        <style>
        .level-table {{ width: 100%; border-collapse: collapse; margin-top: 15px; background-color: rgba(255, 255, 255, 0.1); border-radius: 8px; overflow: hidden; }}
        .level-table th, .level-table td {{ padding: 12px; text-align: left; border-bottom: 1px solid rgba(255, 255, 255, 0.1); }}
        .level-table th {{ background-color: rgba(255, 255, 255, 0.2); font-weight: bold; color: #fff; }}
        .level-table tr:hover {{ background-color: rgba(255, 255, 255, 0.05); }}
        .progress-bar {{ height: 20px; background-color: #444; border-radius: 10px; overflow: hidden; }}
        .progress-bar div {{ height: 100%; background-color: #00bcd4; text-align: center; color: white; line-height: 20px; font-weight: bold; font-size: 0.8em; transition: width 0.5s; }}
        </style>
        <div class="level-container">
            <h3>Bảng Xếp Hạng Cấp Độ (Server Leaders)</h3>
            <table class="level-table">
                <thead>
                    <tr>
                        <th>#</th>
                        <th>Tên Người Dùng</th>
                        <th>Cấp Độ</th>
                        <th>Tổng XP</th>
                        <th>Tiến Trình</th>
                    </tr>
                </thead>
                <tbody>
                    {table_rows}
                </tbody>
            </table>
            <div class="note" style="margin-top: 20px; color: #fff;">
                ⭐ Các cấp độ có gắn dấu sao là cấp độ thưởng (Level Reward).
            </div>
        </div>
        """
    return ""

@app.route('/', methods=['GET', 'POST'])
def dashboard():
    global config
    
    active_tab = request.args.get('tab', 'chao_mung') 
    thong_bao = ""
    
    if request.method == 'POST':
        if active_tab == 'chao_mung':
            # Xử lý tab Lời Chào
            noi_dung_moi = request.form.get('loi_chao_moi')
            if noi_dung_moi:
                config["CAU_CHAO_HIEN_TAI"] = noi_dung_moi
                config["URL_GIF_MAIN"] = request.form.get('url_gif_main', default="")
                config["EMBED_CHAO_MUNG_MAU"] = request.form.get('embed_mau_hex', default="#3498db")
                config["ID_KENH_CHAO_MUNG"] = request.form.get('id_kenh_chao_mung', default="")
                
                # Bỏ qua giá trị dashboard_bg_url từ form (đã bị khóa)
                
                save_config(config)
                thong_bao = "✅ Đã lưu cấu hình Lời Chào thành công! (Ảnh nền Dashboard đã được khóa)."
            else:
                thong_bao = "❌ Lời chào không được để trống!"
                
        elif active_tab == 'level_config':
            # Xử lý tab Cấu Hình Level Thưởng
            levels_input = request.form.getlist('level[]')
            role_ids_input = request.form.getlist('role_id[]')
            
            new_rewards = {}
            valid_config = True
            
            for level, role_id in zip(levels_input, role_ids_input):
                level = level.strip()
                role_id = role_id.strip()
                
                if not level.isdigit() or not role_id.isdigit():
                    valid_config = False
                    thong_bao = "❌ Level và Role ID phải là số nguyên hợp lệ!"
                    break
                    
                new_rewards[level] = role_id
            
            if valid_config:
                config["LEVEL_REWARDS"] = new_rewards
                save_config(config)
                thong_bao = "✅ Đã lưu cấu hình Level Thưởng thành công!"
            
            return redirect(url_for('dashboard', tab='level_config'))
            
        elif active_tab == 'auto_reply_config':
            # Xử lý tab Trả Lời Tự Động
            triggers_input = request.form.getlist('trigger[]')
            responses_input = request.form.getlist('response[]')
            
            new_auto_responses = []
            valid_config = True
            
            for trigger, response in zip(triggers_input, responses_input):
                if trigger.strip() and response.strip():
                    new_auto_responses.append({"trigger": trigger.strip(), "response": response.strip()})
                else:
                    valid_config = False
                    thong_bao = "❌ Từ khóa và Tin nhắn trả lời không được để trống!"
                    break
            
            if valid_config:
                config["AUTO_RESPONSES"] = new_auto_responses
                save_config(config)
                thong_bao = "✅ Đã lưu cấu hình Trả Lời Tự Động thành công!"
            
            return redirect(url_for('dashboard', tab='auto_reply_config'))

    # Lấy dữ liệu config cho template
    CAU_CHAO_HIEN_TAI = config.get("CAU_CHAO_HIEN_TAI", "")
    URL_GIF_MAIN = config.get("URL_GIF_MAIN", "")
    EMBED_MAU_HEX = config.get("EMBED_CHAO_MUNG_MAU", "#3498db")
    ID_KENH_CHAO_MUNG = config.get("ID_KENH_CHAO_MUNG", "")
    DASHBOARD_BACKGROUND_URL = config.get("DASHBOARD_BACKGROUND_URL", DEFAULT_BACKGROUND_URL) # Luôn lấy giá trị đã khóa

    
    # Tạo nội dung Tab
    if active_tab == 'chao_mung':
        tab_content = f"""
            <form method="POST" action="{url_for('dashboard')}?tab=chao_mung">
                <div class="input-group">
                    <label for="id_kenh_chao_mung">ID Kênh Chào Mừng:</label>
                    <input type="text" id="id_kenh_chao_mung" name="id_kenh_chao_mung" value="{ID_KENH_CHAO_MUNG}" placeholder="ID kênh (ví dụ: 123456789...)">
                    <div class="note">
                        Bot sẽ gửi lời chào vào kênh có ID này.
                    </div>
                </div>
                <div class="input-group">
                    <label for="loi_chao_moi">Nội dung Lời Chào (sẽ là Mô tả Embed):</label>
                    <textarea id="loi_chao_moi" name="loi_chao_moi">{CAU_CHAO_HIEN_TAI}</textarea>
                    <div class="note">
                        Sử dụng Placeholders: <code>{{mem}}</code>, <code>{{sever}}</code>, <code>{{soluong}}</code>, <code>{{id[ID]}}</code>.
                    </div>
                </div>

                <div class="input-group">
                    <label for="embed_mau_hex">Màu Viền Embed (Mã HEX):</label>
                    <input type="text" id="embed_mau_hex" name="embed_mau_hex" value="{EMBED_MAU_HEX}" placeholder="#3498db">
                </div>

                <div class="input-group">
                    <label for="url_gif_main">URL Ảnh Lớn (Image/GIF cho Embed):</label>
                    <input type="text" id="url_gif_main" name="url_gif_main" value="{URL_GIF_MAIN}" placeholder="Sẽ dùng làm ảnh chính trong Embed">
                </div>
                
                <hr style="border: 1px solid #555; margin: 30px 0;">

                <div class="input-group">
                    <label for="dashboard_bg_url">Tên/URL Ảnh/GIF Nền Dashboard (Đã khóa):</label>
                    <input type="text" id="dashboard_bg_url" name="dashboard_bg_url" value="{DASHBOARD_BACKGROUND_URL}" class="locked-field" readonly>
                    <div class="note">
                        Ảnh nền đã được cố định là room.giftrong thư mụcnstatic/ .
                    </div>
                </div>

                <button type="submit">Lưu Cấu Hình Lời Chào</button>
            </form>
        """
    elif active_tab == 'level_leaderboard':
        tab_content = generate_level_dashboard_html('level_leaderboard')
    elif active_tab == 'level_config':
        tab_content = generate_level_dashboard_html('level_config')
    elif active_tab == 'auto_reply_config':
        tab_content = generate_level_dashboard_html('auto_reply_config')

    # Tạo URL ảnh nền bằng url_for('static', filename='...')
    background_url_for_css = url_for('static', filename=DASHBOARD_BACKGROUND_URL)


    # Template HTML & CSS chính
    html_template = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Banhbaochao Quản lý</title>
        <style>
            /* CSS Giao diện Chung */
            body {{ 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                margin: 0; 
                padding: 0; 
                color: #f0f0f0; 
                display: flex; 
                justify-content: center; 
                align-items: flex-start; 
                min-height: 100vh; 
                padding-top: 50px;
                padding-bottom: 50px;
                background-color: #2f3136;
                background-image: url('{background_url_for_css}');
                background-attachment: fixed;
                background-position: center;
                background-repeat: no-repeat;
                background-size: cover; 
            }}
            .container {{
                max-width: 900px; 
                width: 90%; 
                background-color: rgba(0, 0, 0, 0.8); 
                border-radius: 12px; 
                box-shadow: 0 8px 16px rgba(0, 0, 0, 0.8); 
                backdrop-filter: blur(5px); 
                border: 1px solid rgba(255, 255, 255, 0.1);
                padding: 0; 
            }}
            h2 {{ 
                text-align: center; 
                color: #e0e0e0; 
                margin: 20px 0; 
                font-size: 2.2em; 
                text-shadow: 2px 2px 4px rgba(0,0,0,0.6);
            }}
            .alert {{ 
                padding: 12px; 
                margin: 20px; 
                border-radius: 8px; 
                font-weight: bold; 
                text-align: center;
                background-color: #5cb85c; 
                color: white; 
                border: 1px solid #4cae4c; 
            }}
            
            /* CSS Tabs */
            .tabs {{
                display: flex;
                border-bottom: 2px solid rgba(255, 255, 255, 0.2);
                padding-left: 10px;
                flex-wrap: wrap;
            }}
            .tab-button {{
                padding: 10px 15px;
                cursor: pointer;
                background-color: transparent;
                border: none;
                color: #aaa;
                font-size: 1.0em;
                font-weight: bold;
                transition: color 0.3s, background-color 0.3s;
                margin-bottom: -2px; 
            }}
            .tab-button.active {{
                color: #00bcd4;
                border-bottom: 2px solid #00bcd4;
                background-color: rgba(255, 255, 255, 0.05);
            }}
            .tab-content {{
                padding: 30px;
            }}
            
            /* CSS Input/Form */
            form {{ padding: 0; }}
            label {{ display: block; margin-bottom: 5px; font-weight: bold; color: #c0c0c0; }}
            input[type="text"], input[type="number"], textarea {{ 
                padding: 12px; 
                box-sizing: border-box; 
                border: 1px solid #555; 
                border-radius: 8px; 
                background-color: #333; 
                color: #eee; 
                font-size: 1.1em;
            }}
            input[type="text"], textarea {{ width: calc(100% - 2px); margin-bottom: 15px; }}
            textarea {{ height: 180px; resize: vertical; }}
            button {{ 
                display: block; 
                width: 100%;
                padding: 15px 20px; 
                background-color: #5cb85c; 
                color: white; 
                border: none; 
                border-radius: 8px; 
                cursor: pointer; 
                font-size: 1.2em;
                font-weight: bold;
                transition: background-color 0.3s, transform 0.2s;
            }}
            button:hover {{ 
                background-color: #4cae4c; 
                transform: translateY(-2px); 
            }}
            .note {{ color: #b0b0b0; font-size: 0.95em; margin-top: 15px; line-height: 1.5; }}
            .input-group {{ margin-bottom: 15px; }}
        </style>
        <script>
            function changeTab(tabName) {{
                window.location.href = '?tab=' + tabName;
            }}
        </script>
    </head>
    <body>
        <div class="container">
            <h2>⚙️ Quản Lý Discord Bot ☕</h2>
            
            <div class="tabs">
                <button class="tab-button {'active' if active_tab == 'chao_mung' else ''}" onclick="changeTab('chao_mung')">Lời Chào & Background</button>
                <button class="tab-button {'active' if active_tab == 'level_leaderboard' else ''}" onclick="changeTab('level_leaderboard')">Bảng Xếp Hạng</button>
                <button class="tab-button {'active' if active_tab == 'level_config' else ''}" onclick="changeTab('level_config')">Cấu Hình Level</button>
                <button class="tab-button {'active' if active_tab == 'auto_reply_config' else ''}" onclick="changeTab('auto_reply_config')">Tự Động Trả Lời</button>
            </div>
            
            <div class="tab-content">
                {'<div class="alert success">' + thong_bao + '</div>' if thong_bao else ''}
                {tab_content}
            </div>
        </div>
    </body>
    </html>
    """
    return render_template_string(html_template, url_for=url_for) 

def run_flask():
    app.run(host='0.0.0.0', port=5000, use_reloader=False)

# -------------------------------------------------------------
# 4. KHỞI CHẠY CẢ HAI
# -------------------------------------------------------------

if __name__ == '__main__':
    # Kiểm tra và cài đặt thư viện GenAI (nếu thiếu)
    try:
        import google.genai
    except ImportError:
        print("\n!!! LỖI QUAN TRỌNG: Thư viện 'google-genai' chưa được cài đặt. Vui lòng chạy lệnh: pip install google-genai")
        exit()

    config = load_config()
    levels = load_levels() 
    
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True 
    flask_thread.start()
    
    try:
        # Bắt đầu chạy Bot Discord
        bot.run(TOKEN)
    except discord.errors.LoginFailure:
        print("LỖI: Token Discord không hợp lệ. Vui lòng kiểm tra lại TOKEN đã nhập.")
    except Exception as e:
        print(f"Lỗi khi chạy Bot Discord: {e}")
        print("Vui lòng kiểm tra lại TOKEN, API Key Gemini và Intents trong Developer Portal.")