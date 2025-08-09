from telethon import TelegramClient, events
from telethon.sessions import StringSession

BOT_TOKEN = "7943293334:AAHSxLV82W7C7Qtp6IIzyGiNgW03BKvGn3k"  # توكن البوت هنا

# البوت نفسه
bot = TelegramClient('bot_session', 0, '', bot_token=BOT_TOKEN)
pending = {}  # تخزين بيانات الجلسة المؤقتة لكل مستخدم

@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    await event.reply(
        "👋 أهلاً! أنا بوت توليد StringSession.\n"
        "للبدء أرسل الأمر:\n"
        "`/gen API_ID API_HASH PHONE`\n\n"
        "📌 مثال:\n"
        "`/gen 123456 0123456789abcdef123456789abcdef +201234567890`",
        parse_mode='md'
    )

@bot.on(events.NewMessage(pattern=r'^/gen\s+(\d+)\s+([0-9a-fA-F]+)\s+(\+\d+)$'))
async def generate_session(event):
    api_id = int(event.pattern_match.group(1))
    api_hash = event.pattern_match.group(2)
    phone = event.pattern_match.group(3)
    user_id = event.sender_id

    pending[user_id] = {
        'api_id': api_id,
        'api_hash': api_hash,
        'phone': phone
    }

    await event.reply(f"📲 جاري إرسال كود التحقق إلى {phone}...\nأرسل الكود بالأمر:\n`/code الكود`", parse_mode='md')

    client = TelegramClient(StringSession(), api_id, api_hash)
    await client.connect()
    try:
        await client.send_code_request(phone)
    except Exception as e:
        await event.reply(f"❌ خطأ: {str(e)}")
        pending.pop(user_id, None)
        return

    pending[user_id]['client'] = client

@bot.on(events.NewMessage(pattern=r'^/code\s+(.+)$'))
async def enter_code(event):
    user_id = event.sender_id
    if user_id not in pending:
        await event.reply("❌ لا يوجد عملية توليد جلسة قيد التنفيذ.")
        return

    code = event.pattern_match.group(1)
    data = pending[user_id]
    client = data['client']

    try:
        await client.sign_in(data['phone'], code)
        string_session = client.session.save()
        await event.reply(f"✅ تم إنشاء الجلسة بنجاح!\n\n```\n{string_session}\n```", parse_mode='md')
    except Exception as e:
        await event.reply(f"❌ خطأ أثناء تسجيل الدخول: {str(e)}")
    finally:
        await client.disconnect()
        pending.pop(user_id, None)

print("🚀 البوت شغال...")
bot.start()
bot.run_until_disconnected()
