from telethon import TelegramClient, events
from telethon.sessions import StringSession

BOT_TOKEN = "7943293334:AAHSxLV82W7C7Qtp6IIzyGiNgW03BKvGn3k"

pending = {}

# هنا ممكن تحط أي api_id / api_hash ثابتين
bot = TelegramClient('bot_session', api_id=28725696, api_hash='4254d53414182d2ea793853ff84a6747')

@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    user_id = event.sender_id
    pending[user_id] = {}
    await event.reply("🔹 أهلاً بك! أرسل لي الـ API ID الخاص بك:")

@bot.on(events.NewMessage)
async def handle_all(event):
    user_id = event.sender_id
    text = event.raw_text.strip()

    if user_id not in pending:
        return

    # خطوة الـ API ID
    if "api_id" not in pending[user_id]:
        if text.isdigit():
            pending[user_id]["api_id"] = int(text)
            await event.reply("✅ تم حفظ API ID.\nالآن أرسل الـ API HASH:")
        else:
            await event.reply("❌ API ID يجب أن يكون رقم.")
        return

    # خطوة الـ API HASH
    if "api_hash" not in pending[user_id]:
        pending[user_id]["api_hash"] = text
        await event.reply("📱 أرسل الآن رقم الهاتف مع كود الدولة (مثال: +201234567890):")
        return

    # خطوة رقم الهاتف
    if "phone" not in pending[user_id]:
        if text.startswith("+") and text[1:].isdigit():
            pending[user_id]["phone"] = text
            await event.reply("📩 سيتم إرسال كود التحقق...\nأرسل الكود الآن:")

            try:
                client = TelegramClient(StringSession(), pending[user_id]["api_id"], pending[user_id]["api_hash"])
                await client.connect()
                await client.send_code_request(pending[user_id]["phone"])
                pending[user_id]["client"] = client
            except Exception as e:
                await event.reply(f"❌ خطأ: {e}")
                pending.pop(user_id, None)
        else:
            await event.reply("❌ رقم الهاتف غير صحيح.")
        return

    # خطوة الكود
    if "code" not in pending[user_id] and not pending[user_id].get("ask_password"):
        pending[user_id]["code"] = text
        client = pending[user_id]["client"]
        try:
            await client.sign_in(pending[user_id]["phone"], pending[user_id]["code"])
            session_str = client.session.save()
            await event.reply(f"✅ تم إنشاء الجلسة بنجاح:\n\n\n{session_str}\n", parse_mode="md")
        except Exception as e:
            if "SESSION_PASSWORD_NEEDED" in str(e):
                await event.reply("🔒 الحساب محمي بباسورد، أرسل الباسورد الآن:")
                pending[user_id]["ask_password"] = True
                return
            else:
                await event.reply(f"❌ خطأ أثناء تسجيل الدخول: {e}")
                pending.pop(user_id, None)
        else:
            await client.disconnect()
            pending.pop(user_id, None)
        return

    # خطوة الباسورد
    if pending[user_id].get("ask_password"):
        client = pending[user_id]["client"]
        try:
            await client.sign_in(password=text)
            session_str = client.session.save()
            await event.reply(f"✅ تم إنشاء الجلسة بنجاح:\n\n\n{session_str}\n", parse_mode="md")
        except Exception as e:
            await event.reply(f"❌ خطأ: {e}")
        finally:
            await client.disconnect()
            pending.pop(user_id, None)

print("🚀 البوت شغال...")
bot.start(bot_token=BOT_TOKEN)
bot.run_until_disconnected()
