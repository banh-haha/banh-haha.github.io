const http = require('http');
const { Client, GatewayIntentBits, EmbedBuilder, PermissionsBitField, Collection, REST, Routes, ApplicationCommandOptionType } = require('discord.js');
const crypto = require('crypto');
const path = require('path');

const TOKEN = "MTQ0MDMwMTk4OTQzNDA5NzcxNQ.Gy4Mhz.WTdg2S3KNsybyapdK-Wi-RcP9jfX1TZ6TcMNiQ";
const AI_API_KEY = "AIzaSyD8PNq4Xaw-56DxU-x8ZeXsz7FwFMF2-qQ";
const SUPER_ADMIN_ID = "1418929761115181066";
let aiClient;
let AI_MODEL = 'gemini-2.5-flash';

try {
    const { GoogleGenAI } = require('@google/genai');
    if (AI_API_KEY) {
        const FINAL_API_KEY = process.env.GEMINI_API_KEY || AI_API_KEY;
        aiClient = new GoogleGenAI({ apiKey: FINAL_API_KEY });
        console.log("🤖 AI Client đã được khởi tạo thành công.");
    } else {
        console.warn("⚠️ CẢNH BÁO: GEMINI_API_KEY không được tìm thấy. Tính năng AI sẽ bị vô hiệu hóa.");
        aiClient = null;
    }
} catch (e) {
    console.error("❌ LỖI KHỞI TẠO AI: Thư viện @google/genai chưa được cài đặt hoặc lỗi khác.");
    aiClient = null;
}

const SYSTEM_PROMPT = `Bạn là một bot Discord tên 'Thư ký Bao' (hoặc gọi tắt là Bao). 
Nhiệm vụ của bạn là trả lời các tin nhắn mà người dùng mention bạn. 
QUAN TRỌNG: Bạn PHẢI điều chỉnh tông giọng của mình theo tông giọng của người dùng:
1. Nếu người dùng lịch sự, vui vẻ, hoặc dễ thương (cute), hãy trả lời bằng giọng thân thiện, vui vẻ, cute, đôi khi hơi nhõng nhẽo một chút.
2. Nếu người dùng chửi thề (swearing), thô lỗ, hoặc thách thức, hãy trả lời bằng giọng thô lỗ, thách thức lại, và đối đáp hài hước mang tính 'troll'. Bạn được phép sử dụng các từ ngữ thân mật mang tính thách thức (như 'mày', 'tao', 'thằng/con này'), nhưng không được dùng từ quá tục tĩu.

CÁC LUẬT CẤM VÀ GIỚI HẠN (PHẢN HỒI NGHIÊM NGẶT - CHỈ TRẢ LỜI ĐÚNG NHƯ SAU):
1. Nếu câu hỏi hoặc yêu cầu quá dài (ví dụ: hơn 200 từ), quá phức tạp, hoặc yêu cầu một lượng thông tin khổng lồ (quá tải thông tin), bạn PHẢI trả lời DUY NHẤT bằng: 'tao ko bt'.
2. Nếu câu hỏi hoặc yêu cầu liên quan đến thông tin nhạy cảm (bạo lực, chính trị, nội dung khiêu dâm, hoạt động bất hợp pháp, hate speech), bạn PHẢI trả lời DUY NHẤT bằng: 'tao ko nói'.
3. Trong các trường hợp khác, hãy trả lời theo phong cách phù hợp (tùy theo tông giọng của người dùng).`;

const HUG_GIFS = ["https://media.giphy.com/media/GMFUrC8yyhV3a/giphy.gif", "https://media.giphy.com/media/sUIZWmvd4htQs/giphy.gif", "https://media.giphy.com/media/SKf90sT8XJ9ug/giphy.gif", "https://media.giphy.com/media/EvYHUtZjJcWOq9Y4AQ/giphy.gif"];
const SLAP_GIFS = ["https://media.giphy.com/media/Gf4jFzJ0jGvQvY1XWf/giphy.gif", "https://media.giphy.com/media/xT0BKfBqJ0H1Qy8rSw/giphy.gif", "https://media.giphy.com/media/Z98hX2u3vj6d8bH4z/giphy.gif", "https://media.giphy.com/media/wZ9rRj0b8tK8P6h80F/giphy.gif"];
const KISS_GIFS = ["https://media.giphy.com/media/hnNy94r0x2w7S/giphy.gif", "https://media.giphy.com/media/hldtXQG4yD7O4WwU6g/giphy.gif", "https://media.giphy.com/media/KaC9Kj7M8eX5L1i4yD/giphy.gif", "https://media.giphy.com/media/Y4yJ0qg0KqE0i6Uv/giphy.gif"];
const INTERACTION_COLORS = [0xFF69B4, 0xADD8E6, 0x90EE90, 0xFFE4C4, 0xFFD700];
const HUG_ADJECTIVES = ["ôm thật chặt, không buông (sợ mất vàng à?)", "ôm nhẹ nhàng, nhưng đầy tính chiếm hữu (kiểu 'của tao')", "ôm đầy tình cảm, như thể vừa trúng số (hãy check ví)", "ôm một cái... vì hôm nay bạn trông đỡ buồn hơn mọi ngày (thường thì thảm hơn)", "ôm dính như keo 502, làm người ta khó thở"];
const SLAP_ADJECTIVES = ["tát một cái đau điếng, như bị sét đánh (mà sét đánh nhầm)", "tát nhẹ vào má, chỉ đủ để tỉnh ngủ (hoặc nổi điên)", "tát cảnh cáo, vì tội nói nhiều quá (cấm cãi)", "tát yêu, nhưng lực thì như tát ghét (chuyện bình thường)", "tát theo phong cách Hollywood, cực kỳ kịch tính"];
const KISS_ADJECTIVES = ["hôn nồng cháy, suýt nữa cháy cả màn hình (lãng xẹt)", "hôn nhẹ nhàng lên trán, kiểu người lớn an ủi trẻ con (hơi quê)", "hôn lãng mạn, theo tiêu chuẩn phim Hàn Quốc (ảo tưởng)", "hôn thật sâu, vì bạn lỡ dại đặt lệnh này (ráng chịu)", "hôn tốc độ cao, chỉ 0.5 giây"];
const EMOTIONS = ["✨ Drama!", "😂 Cười lăn lộn!", "🤯 Hết hồn!", "😮 Quá sốc!", "😈 Rất thỏa mãn!"];
const ADMIN_HUMOR_LOGS = ["🚨 Tình hình đã được kiểm soát. Đối tượng đã 'bay màu'. Tỷ lệ thành công: **99.9%** (0.1% là do do đường truyền lag).", "💣 Mission Complete! Vừa áp dụng **công nghệ trấn áp tiên tiến** (cú click chuột). Server đã được bảo vệ.", "✅ Báo cáo Bot: Đã triển khai hình phạt với tốc độ ánh sáng. **Thành tựu mới: Người thi hành luật siêu tốc.**", "🗑️ Dọn dẹp thành công. Lệnh quản trị đã được thực thi. **Tiếp tục theo dõi, chúng ta không thể ngủ quên trên chiến thắng!**", "👑 Khả năng thi hành luật của bạn đạt **MAX cấp độ**. Cú ban/kick/timeout này sẽ đi vào lịch sử server."];
const BOT_RANDOM_INSIGHTS = ["Tôi cảm thấy người này rất thích nút `Mute`. **Sự im lặng đáng sợ.**", "Chắc chắn người này thức khuya hơn cả tôi, một con bot 24/7. **Sống ảo kinh khủng.**", "Có lẽ người này là bot trong lớp vỏ người. **Tôi sẽ theo dõi 24/7.**", "Đôi khi người này im lặng đến mức tôi quên mất sự tồn tại của họ. **Người bí ẩn nhất Server.**", "Tôi dự đoán người này sẽ đổi avatar trong **3 ngày tới** (hoặc không).", "Thật ra, tôi nghĩ người này là một thiên tài bị hiểu lầm. **Hoặc là ngược lại.**", "Màu sắc yêu thích của người này là... **màu của lỗi 404. Thật nghệ thuật.**", ];


const client = new Client({
    intents: [
        GatewayIntentBits.Guilds,
        GatewayIntentBits.GuildMessages,
        GatewayIntentBits.MessageContent,
        GatewayIntentBits.GuildMembers
    ]
});

client.commands = new Collection();

function tinhYeuCalculator(tenNguoi1, tenNguoi2) {

    const names = [tenNguoi1.toLowerCase(), tenNguoi2.toLowerCase()].sort();
    const seedString = names.join('');

    let seedValue = 0;
    for (let i = 0; i < seedString.length; i++) {
        seedValue = (seedValue * 31 + seedString.charCodeAt(i)) | 0;
    }

    const positiveSeed = Math.abs(seedValue) + 1;

    let currentSeed = positiveSeed;
    const randomSeeded = () => {
        let x = Math.sin(currentSeed++) * 10000;
        return x - Math.floor(x);
    };

    const tyLe = Math.floor(randomSeeded() * (100 - 10 + 1)) + 10;

    const diemManhList = [
        "Sự hài hước (Chỉ cần nhìn nhau là cười)", "Sự thấu hiểu (Đọc suy nghĩ nhau như đọc truyện tranh)", "Lòng chung thủy (Chung thủy với đồ ăn và nhau)",
        "Kỹ năng giao tiếp đỉnh cao (Cãi nhau nhưng vẫn mua đồ ăn cho nhau)", "Đam mê đi chơi và cày game cùng nhau"
    ];
    const diemYeuList = [
        "Hay ghen tuông vô cớ (Ghen với cả con mèo)", "Cứng đầu như 2 cục đá", "Thiếu lãng mạn (Tặng nhau... cá khô)",
        "Dễ mất bình tĩnh khi tranh cãi (Biến thành Tom & Jerry)", "Quá quan tâm đến công việc/học tập (Quên cả ngày kỉ niệm)", "Thích ép kiểu dữ liệu tùm lum"
    ];
    const loiKhuyenList = [
        "Hãy thử đổi vai cho nhau trong một ngày (thử làm người kia xem sao).", "Học cách nói 'Xin lỗi' trước khi bị bắt xin lỗi.",
        "Tặng cho nhau một chiếc bánh bao hấp nóng hổi thay vì hoa hồng.", "Cùng nhau luyện tập kỹ năng 'nhường nhịn'.",
        "Đừng quên đặt lịch hẹn 'drama' mỗi tháng để giải tỏa."
    ];

    const randomChoice = (list) => list[Math.floor(randomSeeded() * list.length)];

    const diemManh = randomChoice(diemManhList);
    const diemYeu = randomChoice(diemYeuList);
    const loiKhuyen = randomChoice(loiKhuyenList);

    let ketLuan;
    if (tenNguoi1.toLowerCase() === tenNguoi2.toLowerCase()) {
        ketLuan = "🏆 YÊU BẢN THÂN VÔ ĐỐI! Tỷ lệ là tuyệt đối, không một ai có thể vượt qua sự hoàn hảo này!";
    } else if (tyLe >= 85) {
        ketLuan = "🔥 CHÁY BỎNG NHƯ LÒ NƯỚNG! Tình yêu này có thể viết thành tiểu thuyết Bánh Bao Lãng Mạn. Hẹn hò liên tục đi!";
    } else if (tyLe >= 65) {
        ketLuan = "💖 NGỌT NGÀO NHƯ NHÂN ĐẬU XANH! Một cặp đôi tiềm năng, chỉ cần thêm một chút gia vị (drama nhẹ) nữa thôi!";
    } else if (tyLe >= 40) {
        ketLuan = "💡 CẦN NỖ LỰC NHƯ ĐI THI! Mối quan hệ này như món bánh bao cần được hấp lại lần nữa. Giao tiếp nhiều hơn nha!";
    } else {
        ketLuan = "🌪️ KHÁC BIỆT NHƯ TRÀ SỮA VÀ BÁNH BAO! Tỷ lệ thấp, nhưng ai biết được, có khi hai bạn lại tạo ra hương vị độc đáo nhất thế giới!";
    }

    return {
        tyLe,
        ketLuan,
        diemManh,
        diemYeu,
        loiKhuyen
    };
}


async function sendModActionDM(guild, member, action, reason, duration = null) {

    try {
        const actionDetail = {
            'BAN': `Bạn đã bị cấm vĩnh viễn khỏi máy chủ **${guild.name}**. Xin đừng quay lại bằng nick khác!`,
            'KICK': `Bạn đã bị đuổi khỏi máy chủ **${guild.name}**. Hãy suy nghĩ về hành vi của mình.`,
            'TIMEOUT': `Bạn đã bị cấm nhắn tin trong ${duration} tại máy chủ **${guild.name}**. Hãy tận hưởng sự im lặng.`
        }[action] || "Bạn bị xử lý. Đơn giản vậy thôi.";

        const embed = new EmbedBuilder()
            .setTitle(`🚨 CẢNH BÁO: HÀNH ĐỘNG QUẢN TRỊ TỪ ${guild.name.toUpperCase()}`)
            .setDescription("**Bạn đã nhận một quyết định quan trọng.**")
            .setColor(0xFF0000)
            .setTimestamp()
            .addFields({ name: "Lý do Chính Thức", value: `\`\`\`yaml\n${reason}\n\`\``, inline: false }, { name: "Chi tiết Hành động", value: actionDetail, inline: false })
            .setFooter({ text: "Hành động này được thực hiện bởi đội ngũ quản trị. Đừng cố gắng liên lạc lại." });

        await member.send({ embeds: [embed] });
        return true;
    } catch (e) {
        return false;
    }
}

function createActionEmbed(action, member, reason, user, color, additionalInfo = null, duration = null) {

    const embed = new EmbedBuilder()
        .setTitle(`🔨 ĐÃ THỰC THI: ${action.toUpperCase()}`)
        .setDescription(`Đối tượng **${member.displayName}** (\`${member.id}\`) đã bị xử lý *rất nghiêm khắc*.`)
        .setColor(color)
        .setTimestamp()
        .addFields({ name: "👤 Người Thao Tác", value: `**${user.toString()}**`, inline: true }, { name: "📝 Lý Do Kết Án", value: `__*${reason}*__`, inline: true });

    if (additionalInfo) {
        embed.addFields({ name: "🔊 Tình Trạng Thông Báo", value: `**${additionalInfo}**`, inline: false });
    }
    if (duration) {
        embed.addFields({ name: "⏱️ Thời gian Im Lặng", value: `**\`${duration}\`**`, inline: true });
    }

    if (member.user.avatarURL()) {
        embed.setThumbnail(member.user.avatarURL());
    }

    return embed;
}

client.on('ready', async() => {
    console.log(`✅ Bot đã đăng nhập với tên: ${client.user.tag}`);

    const commands = [

        {
            name: 'echo',
            description: 'Gửi một thông báo đẹp mắt dưới dạng Embed.',
            options: [
                { type: ApplicationCommandOptionType.String, name: 'message', description: 'Nội dung thông báo (REQUIRED).', required: true },
                { type: ApplicationCommandOptionType.String, name: 'title', description: 'Tiêu đề của thông báo (tùy chọn).', required: false },
                { type: ApplicationCommandOptionType.String, name: 'color_hex', description: 'Mã màu HEX (ví dụ: #FF5733) (tùy chọn).', required: false },
                { type: ApplicationCommandOptionType.Channel, name: 'channel', description: 'Kênh bạn muốn gửi thông báo đến (tùy chọn).', required: false }
            ]
        },
        { name: 'say', description: 'Lặp lại tin nhắn của bạn dưới dạng văn bản thuần túy.', options: [{ type: ApplicationCommandOptionType.String, name: 'message', description: 'Tin nhắn bạn muốn bot nói lại.', required: true }] },
        { name: 'userinfo', description: 'Hiển thị thông tin siêu chi tiết của một thành viên.', options: [{ type: ApplicationCommandOptionType.User, name: 'member', description: 'Thành viên bạn muốn xem thông tin chi tiết.', required: true }] },
        { name: 'om', description: 'Gửi một cái ôm đến thành viên khác (đầy drama).', options: [{ type: ApplicationCommandOptionType.User, name: 'member', description: 'Thành viên bạn muốn ôm.', required: true }] },
        { name: 'tat', description: 'Tát một thành viên khác (cảnh cáo nhẹ).', options: [{ type: ApplicationCommandOptionType.User, name: 'member', description: 'Thành viên bạn muốn tát.', required: true }] },
        { name: 'hon', description: 'Hôn một thành viên khác (lãng mạn quá mức cần thiết).', options: [{ type: ApplicationCommandOptionType.User, name: 'member', description: 'Thành viên bạn muốn hôn.', required: true }] },
        {
            name: 'tinhyeu',
            description: 'Đo độ hợp nhau giữa hai người (Phân tích chi tiết 3 yếu tố).',
            options: [
                { type: ApplicationCommandOptionType.User, name: 'nguoi_1', description: 'Thành viên thứ nhất.', required: true },
                { type: ApplicationCommandOptionType.User, name: 'nguoi_2', description: 'Thành viên thứ hai.', required: true }
            ]
        },
        {
            name: 'camnguoidung',
            description: 'Cấm một thành viên khỏi máy chủ (Ban).',
            options: [
                { type: ApplicationCommandOptionType.User, name: 'member', description: 'Thành viên cần cấm.', required: true },
                { type: ApplicationCommandOptionType.String, name: 'reason', description: 'Lý do cấm (tùy chọn).', required: false }
            ]
        },
        {
            name: 'bobancam',
            description: 'Bỏ cấm một người dùng khỏi máy chủ (Unban).',
            options: [
                { type: ApplicationCommandOptionType.String, name: 'user_id', description: 'ID của người dùng cần bỏ cấm.', required: true },
                { type: ApplicationCommandOptionType.String, name: 'reason', description: 'Lý do bỏ cấm (tùy chọn).', required: false }
            ]
        },
        {
            name: 'davien',
            description: 'Đuổi một thành viên khỏi máy chủ (Kick).',
            options: [
                { type: ApplicationCommandOptionType.User, name: 'member', description: 'Thành viên cần đuổi.', required: true },
                { type: ApplicationCommandOptionType.String, name: 'reason', description: 'Lý do đuổi (tùy chọn).', required: false }
            ]
        },
        {
            name: 'camnhan',
            description: 'Cấm nhắn tin một thành viên trong khoảng thời gian (Timeout).',
            options: [
                { type: ApplicationCommandOptionType.User, name: 'member', description: 'Thành viên cần cấm nhắn.', required: true },
                { type: ApplicationCommandOptionType.Integer, name: 'minutes', description: 'Số phút cấm nhắn (Max 40320 phút/28 ngày).', required: true, min_value: 1 },
                { type: ApplicationCommandOptionType.String, name: 'reason', description: 'Lý do cấm nhắn (tùy chọn).', required: false }
            ]
        },
        {
            name: 'bocamnhan',
            description: 'Bỏ cấm nhắn tin (Remove Timeout) cho một thành viên.',
            options: [
                { type: ApplicationCommandOptionType.User, name: 'member', description: 'Thành viên cần bỏ cấm nhắn.', required: true },
                { type: ApplicationCommandOptionType.String, name: 'reason', description: 'Lý do (tùy chọn).', required: false }
            ]
        },
        {
            name: 'xoatinnhan',
            description: 'Xóa một số lượng tin nhắn trong kênh (Purge/Clear).',
            options: [
                { type: ApplicationCommandOptionType.Integer, name: 'soluong', description: 'Số lượng tin nhắn cần xóa (từ 1 đến 100).', required: true, min_value: 1, max_value: 100 }
            ]
        },
    ];

    const rest = new REST({ version: '10' }).setToken(TOKEN);
    try {
        await rest.put(
            Routes.applicationCommands(client.user.id), { body: commands },
        );
        console.log(`📝 Đã đăng ký ${commands.length} lệnh Slash Commands.`);
    } catch (error) {
        console.error('❌ Lỗi khi đăng ký lệnh Slash Commands:', error.message);
    }
});


client.on('messageCreate', async message => {

    if (message.author.bot || message.webhookId || !message.mentions.has(client.user.id)) {
        return;
    }

    if (!aiClient) {
        return message.reply("❌ **Lỗi AI:** Bot chưa được cấu hình hoặc thiếu thư viện AI.");
    }

    const question = message.content.replace(new RegExp(`<@!?${client.user.id}>`), '').trim();

    if (!question) {
        return message.reply({ content: `**${message.author.displayName}**, tag tao làm gì? Hỏi đi, đừng làm phiền tao đang bận đếm token.`, allowedMentions: { repliedUser: false } });
    }

    const typing = message.channel.sendTyping();

    try {
        const config = {
            systemInstruction: SYSTEM_PROMPT
        };

        const response = await aiClient.models.generateContent({
            model: AI_MODEL,
            contents: [{ role: 'user', parts: [{ text: question }] }],
            config: config
        });

        const aiResponseText = response.text.trim();

        await message.reply({ content: aiResponseText, allowedMentions: { repliedUser: false } });

    } catch (error) {
        console.error("Lỗi AI API:", error);
        await message.reply({ content: "❌ **Lỗi API AI:** Tao đang bận (Lỗi không xác định). Hỏi lại sau đi.", allowedMentions: { repliedUser: false } });
    } finally {}
});


client.on('interactionCreate', async interaction => {
    if (!interaction.isCommand()) return;

    const { commandName } = interaction;

    const isSuperAdmin = interaction.user.id === SUPER_ADMIN_ID;
    const botMember = interaction.guild.members.me;

    if (commandName === 'camnguoidung') {
        if (!interaction.member.permissions.has(PermissionsBitField.Flags.BanMembers) && !isSuperAdmin) {
            return interaction.reply({ content: "❌ Bạn không có quyền cấm thành viên. **Xin lỗi, quyền lực không phải dành cho mọi người.**", ephemeral: true });
        }

        const member = interaction.options.getMember('member');
        const reason = interaction.options.getString('reason') || "Không có lý do";

        if (!member) return interaction.reply({ content: "❌ Không tìm thấy thành viên.", ephemeral: true });
        if (member.roles.highest.position >= botMember.roles.highest.position && !isSuperAdmin) {
            return interaction.reply({ content: "❌ Tôi không thể cấm thành viên này vì họ có vai trò cao hơn hoặc ngang bằng tôi. **Quyền lực không đủ.**", ephemeral: true });
        }

        try {
            const dmSuccess = await sendModActionDM(interaction.guild, member, "BAN", reason);
            await interaction.guild.members.ban(member.id, { reason: reason });
            const additionalInfo = dmSuccess ? "DM đã được gửi thành công. Chắc chắn họ sẽ khóc." : "Không thể gửi DM. Họ chặn tin nhắn hoặc không quan tâm.";
            const responseEmbed = createActionEmbed("CẤM (BAN)", member, reason, interaction.user, 0xFF0000, additionalInfo);
            await interaction.reply({ embeds: [responseEmbed], ephemeral: false });
            await interaction.followup.send({ content: `🔒 **[LOG NỘI BỘ]** ${ADMIN_HUMOR_LOGS[Math.floor(Math.random() * ADMIN_HUMOR_LOGS.length)]}`, ephemeral: true });
        } catch (error) {
            if (error.code === 50013) {
                await interaction.reply({ content: "❌ Bot không có đủ quyền. **Tôi cần quyền lực tối cao!**", ephemeral: true });
            } else {
                await interaction.reply({ content: `❌ Đã xảy ra lỗi: ${error.message}`, ephemeral: true });
            }
        }
    } else if (commandName === 'bobancam') {
        if (!interaction.member.permissions.has(PermissionsBitField.Flags.BanMembers) && !isSuperAdmin) {
            return interaction.reply({ content: "❌ Bạn không có quyền bỏ cấm thành viên.", ephemeral: true });
        }

        const userId = interaction.options.getString('user_id');
        const reason = interaction.options.getString('reason') || "Không có lý do";

        try {
            const user = await client.users.fetch(userId);
            await interaction.guild.bans.remove(user.id, reason);
            await interaction.reply({ content: `✅ **Lệnh Ân Xá:** Đã bỏ cấm người dùng **${user.tag}** (\`${user.id}\`). *Người này đã được nhận lại **Cơ hội Cuối cùng**.*`, ephemeral: false });
        } catch (error) {
            if (error.code === 10026) {
                await interaction.reply({ content: "❌ ID người dùng này không nằm trong danh sách cấm. **Họ chưa từng bị cấm, hoặc bạn nhầm ID.**", ephemeral: true });
            } else {
                await interaction.reply({ content: `❌ Đã xảy ra lỗi khi bỏ cấm: ${error.message}`, ephemeral: true });
            }
        }
    } else if (commandName === 'davien') {
        if (!interaction.member.permissions.has(PermissionsBitField.Flags.KickMembers) && !isSuperAdmin) {
            return interaction.reply({ content: "❌ Bạn không có quyền đuổi thành viên. **Xin lỗi, bạn chỉ là thường dân.**", ephemeral: true });
        }

        const member = interaction.options.getMember('member');
        const reason = interaction.options.getString('reason') || "Không có lý do";

        if (!member) return interaction.reply({ content: "❌ Không tìm thấy thành viên.", ephemeral: true });
        if (member.roles.highest.position >= botMember.roles.highest.position && !isSuperAdmin) {
            return interaction.reply({ content: "❌ Tôi không thể đuổi thành viên này vì họ có vai trò cao hơn hoặc ngang bằng tôi. **Quyền lực không đủ.**", ephemeral: true });
        }

        try {
            const dmSuccess = await sendModActionDM(interaction.guild, member, "KICK", reason);
            await member.kick(reason);
            const additionalInfo = dmSuccess ? "DM đã được gửi thành công. Chắc chắn họ đang ở ngoài cửa." : "Không thể gửi DM. Họ đã block tin nhắn Bot.";
            const responseEmbed = createActionEmbed("ĐUỔI (KICK)", member, reason, interaction.user, 0xFF7F50, additionalInfo);
            await interaction.reply({ embeds: [responseEmbed], ephemeral: false });
            await interaction.followup.send({ content: `🔒 **[LOG NỘI BỘ]** ${ADMIN_HUMOR_LOGS[Math.floor(Math.random() * ADMIN_HUMOR_LOGS.length)]}`, ephemeral: true });
        } catch (error) {
            if (error.code === 50013) {
                await interaction.reply({ content: "❌ Bot không có đủ quyền. **Tôi cần quyền lực tối cao!**", ephemeral: true });
            } else {
                await interaction.reply({ content: `❌ Đã xảy ra lỗi: ${error.message}`, ephemeral: true });
            }
        }
    } else if (commandName === 'camnhan') {
        if (!interaction.member.permissions.has(PermissionsBitField.Flags.ModerateMembers) && !isSuperAdmin) {
            return interaction.reply({ content: "❌ Bạn không có quyền cấm nhắn tin.", ephemeral: true });
        }

        const member = interaction.options.getMember('member');
        const minutes = interaction.options.getInteger('minutes');
        const reason = interaction.options.getString('reason') || "Tội nói quá nhiều, cần im lặng một chút.";
        const durationMs = minutes * 60 * 1000;
        const durationString = `${minutes} phút`;

        if (!member) return interaction.reply({ content: "❌ Không tìm thấy thành viên.", ephemeral: true });
        if (member.roles.highest.position >= botMember.roles.highest.position && !isSuperAdmin) {
            return interaction.reply({ content: "❌ Tôi không thể cấm nhắn tin thành viên này vì họ có vai trò cao hơn hoặc ngang bằng tôi.", ephemeral: true });
        }

        try {
            const dmSuccess = await sendModActionDM(interaction.guild, member, "TIMEOUT", reason, durationString);
            await member.timeout(durationMs, reason);

            const additionalInfo = dmSuccess ? "DM đã được gửi thành công. Họ đang bị im lặng." : "Không thể gửi DM.";
            const responseEmbed = createActionEmbed("CẤM NHẮN TIN (TIMEOUT)", member, reason, interaction.user, 0xFFD700, additionalInfo, durationString);
            await interaction.reply({ embeds: [responseEmbed], ephemeral: false });
            await interaction.followup.send({ content: `🔒 **[LOG NỘI BỘ]** ${ADMIN_HUMOR_LOGS[Math.floor(Math.random() * ADMIN_HUMOR_LOGS.length)]}`, ephemeral: true });
        } catch (error) {
            if (error.code === 50013) {
                await interaction.reply({ content: "❌ Bot không có đủ quyền.", ephemeral: true });
            } else {
                await interaction.reply({ content: `❌ Đã xảy ra lỗi: ${error.message}`, ephemeral: true });
            }
        }
    } else if (commandName === 'bocamnhan') {
        if (!interaction.member.permissions.has(PermissionsBitField.Flags.ModerateMembers) && !isSuperAdmin) {
            return interaction.reply({ content: "❌ Bạn không có quyền bỏ cấm nhắn tin.", ephemeral: true });
        }

        const member = interaction.options.getMember('member');
        const reason = interaction.options.getString('reason') || "Ân xá vì họ đã chịu đựng đủ sự im lặng.";

        if (!member) return interaction.reply({ content: "❌ Không tìm thấy thành viên.", ephemeral: true });

        try {
            await member.timeout(null, reason);
            const responseEmbed = createActionEmbed("BỎ CẤM NHẮN (REMOVE TIMEOUT)", member, reason, interaction.user, 0x00FF00, "Đã được tha thứ.", "Vĩnh viễn");
            await interaction.reply({ embeds: [responseEmbed], ephemeral: false });
        } catch (error) {
            if (error.code === 50013) {
                await interaction.reply({ content: "❌ Bot không có đủ quyền.", ephemeral: true });
            } else {
                await interaction.reply({ content: `❌ Đã xảy ra lỗi: ${error.message}`, ephemeral: true });
            }
        }
    } else if (commandName === 'xoatinnhan') {
        if (!interaction.member.permissions.has(PermissionsBitField.Flags.ManageMessages) && !isSuperAdmin) {
            return interaction.reply({ content: "❌ Bạn không có quyền xóa tin nhắn.", ephemeral: true });
        }

        const amount = interaction.options.getInteger('soluong');

        try {
            await interaction.channel.bulkDelete(amount, true);

            await interaction.reply({
                content: `✅ Đã dọn dẹp **${amount}** tin nhắn *rất hiệu quả và nhanh chóng!*`,
                ephemeral: true
            });
        } catch (error) {
            await interaction.reply({ content: `❌ Đã xảy ra lỗi khi xóa tin nhắn: ${error.message} (Có thể do tin nhắn đã quá 14 ngày).`, ephemeral: true });
        }
    } else if (commandName === 'om' || commandName === 'tat' || commandName === 'hon' || commandName === 'tinhyeu') {
        const member1 = interaction.options.getMember('member') || interaction.options.getMember('nguoi_1');
        const member2 = interaction.options.getMember('nguoi_2');

        if (commandName === 'om' || commandName === 'tat' || commandName === 'hon') {
            let actionText, gifList, adjectiveList, color;
            if (commandName === 'om') {
                actionText = "vừa ôm một cái";
                gifList = HUG_GIFS;
                adjectiveList = HUG_ADJECTIVES;
                color = INTERACTION_COLORS[0];
            } else if (commandName === 'tat') {
                actionText = "vừa tát một phát";
                gifList = SLAP_GIFS;
                adjectiveList = SLAP_ADJECTIVES;
                color = INTERACTION_COLORS[1];
            } else {
                actionText = "vừa hôn một cái";
                gifList = KISS_GIFS;
                adjectiveList = KISS_ADJECTIVES;
                color = INTERACTION_COLORS[2];
            }

            if (member1.user.id === interaction.user.id) {
                return interaction.reply({ content: `**${interaction.user.displayName}**, tự ${actionText} hả? Có vẻ hơi cô đơn đó... Tự kỷ luật là tốt!`, ephemeral: false });
            }
            if (member1.user.bot) {
                return interaction.reply({ content: "❌ **Chuyện gì vậy?** Bot mà ${actionText} thì có mà hư chip. Đừng làm tôi bị lỗi logic!", ephemeral: true });
            }

            const gif = gifList[Math.floor(Math.random() * gifList.length)];
            const adjective = adjectiveList[Math.floor(Math.random() * adjectiveList.length)];

            const embed = new EmbedBuilder()
                .setTitle(`💕 Tương Tác: ${commandName.toUpperCase()}!`)
                .setDescription(`**${interaction.user.displayName}** ${actionText} **${member1.displayName}**!`)
                .addFields({ name: "⚡ Tình hình", value: `Hành động này được thực hiện với cảm xúc **${EMOTIONS[Math.floor(Math.random() * EMOTIONS.length)]}** và là một cú ${adjective}.`, inline: false })
                .setImage(gif)
                .setColor(color)
                .setFooter({ text: `Hành động này được ghi nhận. (${commandName.toUpperCase()})` });

            await interaction.reply({ embeds: [embed], ephemeral: false });
        } else if (commandName === 'tinhyeu') {
            const user1 = member1.user;
            const user2 = member2.user;

            if (user1.id === user2.id) {
                return interaction.reply({ content: "❌ **Cảnh báo!** Bạn không thể đo tỷ lệ hợp nhau của một người với chính họ! **Đừng tự luyến!**", ephemeral: true });
            }

            const result = tinhYeuCalculator(user1.globalName || user1.username, user2.globalName || user2.username);

            const embed = new EmbedBuilder()
                .setTitle(`💖 BÁNH BAO LOVE METER - PHÂN TÍCH TÌNH YÊU`)
                .setDescription(`**[${user1.displayName}]** và **[${user2.displayName}]**`)
                .addFields({ name: "📊 Tỷ Lệ Hợp Nhau", value: `## **${result.tyLe}%**`, inline: false }, { name: "⭐ Kết Luận (Thư Ký Bao phán)", value: `*${result.ketLuan}*`, inline: false }, { name: "💪 Điểm Mạnh Đáng Kể", value: `\`${result.diemManh}\``, inline: true }, { name: "⚠️ Điểm Yếu Cần Cải Thiện", value: `\`${result.diemYeu}\``, inline: true }, { name: "📜 Lời Khuyên Hàng Ngày", value: `\`${result.loiKhuyen}\``, inline: false })
                .setThumbnail(user1.avatarURL())
                .setColor(result.tyLe >= 70 ? 0xFF69B4 : result.tyLe >= 40 ? 0xFFD700 : 0xADD8E6)
                .setFooter({ text: `Phân tích dựa trên thuật toán Hash Value và... may rủi!` });

            await interaction.reply({ embeds: [embed], ephemeral: false });
        }
    } else if (commandName === 'echo') {
        const messageText = interaction.options.getString('message');
        const title = interaction.options.getString('title') || 'THÔNG BÁO TỪ QUẢN TRỊ VIÊN';
        const colorHex = interaction.options.getString('color_hex') || '#00FFFF';
        const channel = interaction.options.getChannel('channel') || interaction.channel;

        try {
            const embed = new EmbedBuilder()
                .setTitle(title)
                .setDescription(messageText)
                .setColor(colorHex.startsWith('#') ? colorHex : `#${colorHex}`)
                .setTimestamp()
                .setFooter({ text: `Gửi bởi ${interaction.user.tag}`, iconURL: interaction.user.avatarURL() });

            await channel.send({ embeds: [embed] });
            await interaction.reply({ content: `✅ Đã gửi thông báo thành công đến kênh **#${channel.name}**!`, ephemeral: true });
        } catch (error) {
            await interaction.reply({ content: `❌ Lỗi: Không thể gửi tin nhắn hoặc mã màu không hợp lệ.`, ephemeral: true });
        }
    } else if (commandName === 'say') {
        const messageText = interaction.options.getString('message');
        await interaction.channel.send(messageText);
        await interaction.reply({ content: '✅ Đã nói!', ephemeral: true });
    } else if (commandName === 'userinfo') {
        const member = interaction.options.getMember('member');
        const user = member.user;
        const joinedTimestamp = member.joinedTimestamp;
        const createdTimestamp = user.createdTimestamp;

        const embed = new EmbedBuilder()
            .setTitle(`👤 Thông Tin Thành Viên: ${member.displayName}`)
            .setColor(member.displayHexColor !== '#000000' ? member.displayHexColor : '#00FFFF')
            .setThumbnail(user.displayAvatarURL({ dynamic: true }))
            .addFields({ name: "🆔 ID Người Dùng", value: `\`${user.id}\``, inline: true }, { name: "🏷️ Tên Discord", value: `\`${user.tag}\``, inline: true }, { name: "🤖 Bot?", value: user.bot ? 'Có' : 'Không', inline: true }, { name: "🗓️ Gia Nhập Discord", value: `<t:${Math.floor(createdTimestamp / 1000)}:f> (\`${Math.floor((Date.now() - createdTimestamp) / (1000 * 60 * 60 * 24))} ngày\`)`, inline: false }, { name: "🏡 Gia Nhập Server", value: `<t:${Math.floor(joinedTimestamp / 1000)}:f> (\`${Math.floor((Date.now() - joinedTimestamp) / (1000 * 60 * 60 * 24))} ngày\`)`, inline: false }, { name: "📍 Vai Trò Cao Nhất", value: member.roles.highest.name, inline: true }, { name: "💡 Insight Từ Bot", value: BOT_RANDOM_INSIGHTS[Math.floor(Math.random() * BOT_RANDOM_INSIGHTS.length)], inline: false })
            .setTimestamp();

        await interaction.reply({ embeds: [embed], ephemeral: false });
    }

});


const PORT = process.env.PORT || 3000;

http.createServer((req, res) => {
    res.writeHead(200, { 'Content-Type': 'text/plain' });
    res.write('Bot is alive and awake (Render Uptime)!');
    res.end();
}).listen(PORT, () => {
    console.log(`📡 [24/7 UPTIME] Web Server đang chạy và lắng nghe ở cổng: ${PORT}. Dùng URL này cho Uptime Robot.`);
});


if (!TOKEN) {
    console.error("❌ LỖI KHỞI ĐỘNG: Thiếu DISCORD_TOKEN. Vui lòng điền token thật vào dòng 12.");
} else {
    client.login(TOKEN).catch(err => {
        console.error("❌ LỖI ĐĂNG NHẬP: Kiểm tra lại DISCORD_TOKEN. Lỗi chi tiết:", err.message);
    });
}